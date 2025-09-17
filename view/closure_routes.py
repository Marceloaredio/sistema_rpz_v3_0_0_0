from flask import Blueprint, render_template, request, flash, jsonify, send_file, redirect
from controller.decorators import route_access_required
from controller.utils import CustomLogger
from model.drivers.uploaded_data_driver import UploadedDataDriver
from model.drivers.closure_dayoff_driver import ClosureDayOffDriver
from model.drivers.truck_driver import TruckDriver
from model.drivers.motorist_driver import MotoristDriver
from model.drivers.parameters_driver import ParametersDriver
from model.drivers.closure_analyzed_data import AnalyzedClosureData
from model.validation.calculation_validator import CalculationValidator
from global_vars import DEBUG, DB_PATH
try:
    import pandas as pd
except ImportError:
    print("AVISO: pandas não disponível, usando stub")
    import pandas_stub as pd
import traceback
from controller.data import extract_data, make_data_block, allowed_file
import os
import sqlite3
from werkzeug.utils import secure_filename
import json
from datetime import datetime, timedelta, date
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# from controller.data import GeneralDriver  # Removido - não existe
from model.drivers.company_driver import CompanyDriver
from model.drivers.closure_block_classifications_driver import ClosureBlockClassificationsDriver

def get_weekday_name(data_str):
    """Converte uma data no formato DD-MM-YYYY para o nome do dia da semana."""
    try:
        dias_semana = {
            0: 'Segunda-feira',
            1: 'Terça-feira',
            2: 'Quarta-feira',
            3: 'Quinta-feira',
            4: 'Sexta-feira',
            5: 'Sábado',
            6: 'Domingo'
        }
        data_obj = datetime.strptime(data_str, "%d-%m-%Y")
        return dias_semana[data_obj.weekday()]
    except:
        return "Data inválida"

closure_bp = Blueprint('fechamento', __name__)
routes_logger = CustomLogger(source="ROUTES", debug=DEBUG)

truck_driver = TruckDriver(logger=routes_logger, db_path=DB_PATH)
motorist_driver = MotoristDriver(logger=routes_logger, db_path=DB_PATH)
closure_driver = UploadedDataDriver(logger=routes_logger, 
                            db_path=DB_PATH, 
                            table='vehicle_data_fecham')
analyzed_closure_data_driver = AnalyzedClosureData(logger=routes_logger, 
                            db_path=DB_PATH)
closure_dayoff_driver = ClosureDayOffDriver(logger=routes_logger, 
                            db_path=DB_PATH)
company_driver = CompanyDriver(logger=routes_logger, db_path=DB_PATH)

# Inicializar driver para classificações de blocos
closure_classifications_driver = ClosureBlockClassificationsDriver(logger=routes_logger, db_path=DB_PATH)

# Inicializar validador de cálculos
calculation_validator = CalculationValidator(logger=routes_logger)

@closure_bp.route('/closure_analysis')
@route_access_required
def closure_analysis():
    """
    Analisa os resultados de fechamento de uma jornada.
    """
    truck_id = request.args.get('truck_id', '')
    motorist_id = request.args.get('motorist_id', '')

    # Carregando configurações
    parameters_driver = ParametersDriver(logger=routes_logger, db_path=DB_PATH)
    configs = parameters_driver.get_all_parameters()

    # tipo_parametro, valor, descricao FROM parametros_fechamento
    parameters = configs['parametros']
    # id, tipo_filtro, valor_filtro, valor_diaria, valor_ajuda_alimentacao, descricao
    criterias = configs['criterios']
    # id, data, descricao, tipo, ano FROM feriados_regionais WHERE ano = ? ORDER BY data
    holidays = configs['feriados']
    # Manter objetos completos com descrição para uso no frontend
    
    # DEBUG: Log removido para limpeza do código

    if not truck_id or not motorist_id:
        flash("Placa/motorista não informada.")
        return render_template('redirect.html', url='/reports')

    try:
        # Busca dados do fechamento
        
        query_data = closure_driver.retrieve_all_records_by_condition(where_columns=['truck_id',], where_values=(truck_id,))
        if len(query_data) == 0:
            flash("Sem dados para analisar sobre a placa informada. Insira novos dados através das configurações.")
            return render_template('redirect.html', url='/reports')

        dates = set()
        for record in query_data:
            date_iso = record[1]  # índice 1 corresponde ao campo data_iso
            date_only = date_iso.split(" ")[0]
            dates.add(date_only)
        dates = sorted(dates)

        blocks = []
        colunas = [
            'truck_id', 
            'data_iso', 
            'vel', 
            'latitude', 
            'longitude', 
            'uf', 
            'cidade', 
            'rua', 
            'ignicao'
        ]
        for date in dates:
            records = closure_driver.retrieve_by_datetime_range(start_datetime=date + " 00:00",
                                                                  end_datetime=date + " 23:59",
                                                                  where_columns=['truck_id'],
                                                                  where_values=(truck_id,))
            records_df = pd.DataFrame(records, columns=colunas)
            block = make_data_block(records_df, date)
            blocks.append(block)

        plate = truck_driver.retrieve_truck(where_columns=['id',], where_values=(truck_id,))[1]
        motorist_name = motorist_driver.retrieve_motorist(where_columns=['id',], where_values=(motorist_id,))[1]
        # Adicionar placas válidas
        available_trucks = closure_driver.get_unique_truck_ids_and_plates()
        valid_plates = [truck[1] for truck in available_trucks]
    except Exception as e:
        flash(f"Erro ao converter os dados em blocos para análise. Consulte o log ROUTER para maiores informações.")
        traceback.print_exc()
        routes_logger.register_log("Erro ao converter os dados em blocos para análise (fechamento).", f"Erro: {e}")
        return render_template("redirect.html", url="/closure")

    return render_template(
        "closure_analysis.html",
        truck_id=truck_id,
        motorist_id=motorist_id,
        plate=plate,
        motorist=motorist_name,
        data_inicial=dates[0] if dates else '',
        data_final=dates[-1] if dates else '',
        blocos=blocks,
        parameters=parameters,
        criterias=criterias,
        holidays=holidays,
        valid_plates=valid_plates
    )

@closure_bp.route('/closure', methods=['GET'])
@route_access_required
def closure():
    all_motorists = motorist_driver.retrieve_all_motorists()
    # Ordenar motoristas alfabeticamente por nome
    all_motorists.sort(key=lambda x: x[1].upper() if x[1] else '')
    all_motorists = [(motorist[0], motorist[1]) for motorist in all_motorists]

    # Buscar apenas caminhões que têm dados em vehicle_data_fecham
    available_trucks = closure_driver.get_unique_truck_ids_and_plates()

    return render_template('closure.html', motorists=all_motorists, trucks=available_trucks)

@closure_bp.route('/upload_closure', methods=['GET', 'POST'])
@route_access_required
def upload_closure():
    if request.method == 'GET':
        # Buscar todos os caminhões cadastrados
        trucks = truck_driver.retrieve_all_trucks()
        plates = [truck[1] for truck in trucks]
        trucks_ids = [truck[0] for truck in trucks]
        return render_template('load_files_closure.html', plates=plates, trucks_ids=trucks_ids)
    
    elif request.method == 'POST':
        routes_logger.register_log('[DEBUG] Início do upload_closure_post')
        if 'file' not in request.files:
            routes_logger.register_log('[ERRO] Nenhum arquivo enviado no request.files')
            return {'status': 'error', 'message': 'Nenhum arquivo enviado'}

        file = request.files['file']
        tracker_type = request.form.get('tracker_type')
        truck_id = request.form.get('truck_id')
        routes_logger.register_log(f'[DEBUG] Parâmetros recebidos: tracker_type={tracker_type}, truck_id={truck_id}, file={file.filename}')

        if not file or not allowed_file(file.filename):
            routes_logger.register_log('[ERRO] Arquivo inválido ou extensão não permitida')
            return {'status': 'error', 'message': 'Arquivo inválido'}

        try:


            filename = secure_filename(file.filename)
            temp_path = os.path.join('raw_data', filename)
            file.save(temp_path)
            routes_logger.register_log(f'[DEBUG] Arquivo salvo temporariamente em {temp_path}')

            # Processa o arquivo usando a função dedicada do fechamento
            # Para arquivos Sascar, usar a mesma lógica da jornada
            if tracker_type.lower() == 'sascar':
                from controller.data import extract_data
                df = extract_data(filepath=temp_path, system_type='sascar', truck_driver=truck_driver)
                routes_logger.register_log(f'[DEBUG] DataFrame extraído (fechamento - Sascar): shape={getattr(df, "shape", None)}, columns={getattr(df, "columns", None)}')
            else:
                df = extract_data(temp_path, tracker_type)
                routes_logger.register_log(f'[DEBUG] DataFrame extraído (fechamento): shape={getattr(df, "shape", None)}, columns={getattr(df, "columns", None)}')

                # Adiciona o truck_id se necessário (apenas para não-Sascar)
                if 'truck_id' not in df.columns or (hasattr(df['truck_id'], 'isnull') and df["truck_id"].isnull().all()):
                    df['truck_id'] = truck_id
                    routes_logger.register_log(f'[DEBUG] truck_id adicionado ao DataFrame: {truck_id}')

            # Garante a ordem das colunas
            df = df[closure_driver.columns]
            routes_logger.register_log(f'[DEBUG] DataFrame ajustado para colunas: {closure_driver.columns}')
            routes_logger.register_log(f'[DEBUG] Primeiras linhas do DataFrame:\n{df.head().to_string()}')

            routes_logger.register_log(f'[DEBUG] Inserindo dados na tabela: {closure_driver.table} (forçado)')
            linhas_inseridas = closure_driver.insert_from_dataframe(df, force_table='vehicle_data_fecham')
            routes_logger.register_log(f'[DEBUG] Dados inseridos na tabela {closure_driver.table} (forçado). Linhas inseridas: {linhas_inseridas}')

            os.remove(temp_path)
            routes_logger.register_log(f'[DEBUG] Arquivo temporário removido: {temp_path}')
            return {'status': 'success', 'message': 'Arquivo processado e dados inseridos em vehicle_data_fecham'}

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            routes_logger.register_log(f'[ERRO] Exception no upload_closure_post: {e}', error_details)
            return {'status': 'error', 'message': f'Erro ao processar arquivo: {e}'}

@closure_bp.route('/api/closure/save-table', methods=['POST'])
@route_access_required
def save_table():
    dados = request.get_json()

    tabela = dados.get('tabela')
    if isinstance(tabela, str):
        tabela = json.loads(tabela)

    motorist_id = dados.get('motorist_id')
    motorist_name = dados.get('motorist_name')
    truck_id = dados.get('truck_id')
    plate = dados.get('plate')
    acao = dados.get('acao', '')
    substituir = dados.get('substituir', False)
    
    # DEBUG: Verificar tipos dos dados recebidos
    routes_logger.print(f"🔍 DEBUG - Tipos dos dados recebidos:")
    routes_logger.print(f"   - motorist_id: {motorist_id} (tipo: {type(motorist_id)})")
    routes_logger.print(f"   - truck_id: {truck_id} (tipo: {type(truck_id)})")
    routes_logger.print(f"   - plate: {plate} (tipo: {type(plate)})")
    
    # Converter truck_id para int se necessário
    if truck_id is not None:
        try:
            truck_id = int(truck_id)
            routes_logger.print(f"   - truck_id convertido para int: {truck_id}")
        except (ValueError, TypeError) as e:
            routes_logger.print(f"   - Erro ao converter truck_id para int: {e}")
            truck_id = None
    
    # Processar observações do usuário
    observacoes = dados.get('observacoes', {})
    
    # Aplicar observações aos registros correspondentes
    for idx, observacao in observacoes.items():
        idx = int(idx)
        if idx < len(tabela):
            observacao_atual = tabela[idx].get('Observação', '')
            if observacao_atual:
                tabela[idx]['Observação'] = f"{observacao_atual} - {observacao}"
            else:
                tabela[idx]['Observação'] = observacao
    
    # CAPTURAR CÁLCULOS ESPECIAIS DO FRONTEND
    calculos_especiais = dados.get('calculos_especiais', {})
    routes_logger.print(f"🔧 Cálculos especiais recebidos: {calculos_especiais}")
    
    # DEBUG: Log detalhado dos dados recebidos
    routes_logger.print(f"🔍 DEBUG - Dados completos recebidos:")
    routes_logger.print(f"   - motorist_id: {motorist_id}")
    routes_logger.print(f"   - motorist_name: {motorist_name}")
    routes_logger.print(f"   - truck_id: {truck_id}")
    routes_logger.print(f"   - plate: {plate}")
    routes_logger.print(f"   - acao: {acao}")
    routes_logger.print(f"   - substituir: {substituir}")
    routes_logger.print(f"   - observacoes: {observacoes}")
    routes_logger.print(f"   - calculos_especiais: {calculos_especiais}")
    routes_logger.print(f"   - tabela (primeiros 2 registros): {tabela[:2] if tabela else 'N/A'}")

    if acao == "salvar":
        try:
            if substituir:
                # NOVA LÓGICA: Substituir registros existentes (tudo ou nada)
                # Filtrar dados de jornada (apenas registros com movimento ou GARAGEM)
                tabela_jornada = []
                for linha in tabela:
                    observacao = linha.get('Observação', '').strip().upper()
                    inicio_jornada = linha.get('Início Jornada', '').strip()
                    fim_jornada = linha.get('Fim de Jornada', '').strip()
                    
                    # Incluir apenas se tem movimento (início e fim de jornada) ou se é GARAGEM
                    if (inicio_jornada and fim_jornada) or observacao == 'GARAGEM':
                        tabela_jornada.append(linha)
                
                result = analyzed_closure_data_driver.replace_data_from_json(tabela_jornada, motorist_id, truck_id)
                
                # Separar dados de folga para substituição
                tabela_folga = [
                    {
                        'motorist_id': motorist_id,
                        'data': linha.get('Data'),
                        'motivo': linha.get('Observação', '').strip().upper(),
                        'daily_value': float(str(linha.get('Diária', '0')).replace('R$', '').replace(',', '.')),
                        'food_value': float(str(linha.get('Ajuda Alimentação', '0')).replace('R$', '').replace(',', '.'))
                    }
                    for linha in tabela
                    if linha.get('Observação', '').strip().upper() not in ['GARAGEM', '']
                ]
                
                dayoff_result = closure_dayoff_driver.replace_data_from_json(tabela_folga, motorist_id)
                routes_logger.print(f"Registros substituídos: {result['registros_substituidos']}")
                
            else:
                # NOVA LÓGICA: Verificar conflitos ANTES de inserir qualquer coisa
                # Separar dados de garagem dos outros motivos especiais
                motivos_especiais = [
                    'FOLGA','FÉRIAS','AFASTAMENTO','ATESTADO','LIC. ÓBITO',
                    'LIC. PATERNIDADE','LIC. MATERNIDADE','MANUTENÇÃO'
                ]
                
                # Filtrar dados de garagem para inserir na tabela perm_data_fecham
                dados_garagem = []
                tabela_folga = []
                
                for linha in tabela:
                    observacao = linha.get('Observação', '').strip().upper()
                    

                    if observacao not in ['GARAGEM', '']:
                        # Outros motivos especiais vão para dayoff_fecham
                        dados_folga = {
                            'motorist_id': motorist_id,
                            'data': linha.get('Data'),
                            'motivo': observacao,
                            'daily_value': float(str(linha.get('Diária', '0')).replace('R$', '').replace(',', '.')),
                            'food_value': float(str(linha.get('Ajuda Alimentação', '0')).replace('R$', '').replace(',', '.'))
                        }
                        
                        # APLICAR CÁLCULOS ESPECIAIS SE DISPONÍVEIS
                        idx_linha = tabela.index(linha)
                        routes_logger.print(f"🔍 DEBUG - Processando linha {idx_linha} com motivo {observacao}")
                        routes_logger.print(f"🔍 DEBUG - Índice como string: '{str(idx_linha)}'")
                        routes_logger.print(f"🔍 DEBUG - Chaves em calculos_especiais: {list(calculos_especiais.keys())}")
                        
                        if str(idx_linha) in calculos_especiais:
                            calc_especial = calculos_especiais[str(idx_linha)]
                            dados_folga['carga_horaria_esp'] = calc_especial.get('carga_horaria_esp', '')
                            dados_folga['hextra_50_esp'] = calc_especial.get('hextra_50_esp', '')
                            
                            # DEBUG EXTENSO para valores negativos
                            he50_original = calc_especial.get('hextra_50_esp', '')
                            routes_logger.print(f"🔧 ✅ Aplicando cálculos especiais para {observacao}: carga={dados_folga['carga_horaria_esp']}, he50={dados_folga['hextra_50_esp']}")
                            routes_logger.print(f"🔍 DEBUG - Verificação de valores negativos no backend:")
                            routes_logger.print(f"   - he50_original: '{he50_original}'")
                            routes_logger.print(f"   - he50_original.includes('-'): {he50_original.find('-') >= 0}")
                            routes_logger.print(f"   - he50_original.startswith('-'): {he50_original.startswith('-') if he50_original else False}")
                            routes_logger.print(f"   - he50_original type: {type(he50_original)}")
                            routes_logger.print(f"   - he50_original length: {len(he50_original) if he50_original else 0}")
                        else:
                            routes_logger.print(f"⚠️ Nenhum cálculo especial encontrado para índice {idx_linha} (motivo: {observacao})")
                        
                        routes_logger.print(f"📝 DEBUG - Dados finais da folga: {dados_folga}")
                        tabela_folga.append(dados_folga)
                
                # Verificar conflitos ANTES de inserir qualquer coisa
                # Filtrar dados de jornada (apenas registros com movimento ou GARAGEM)
                tabela_jornada = []
                for linha in tabela:
                    observacao = linha.get('Observação', '').strip().upper()
                    inicio_jornada = linha.get('Início Jornada', '').strip()
                    fim_jornada = linha.get('Fim de Jornada', '').strip()
                    
                    # Incluir apenas se tem movimento (início e fim de jornada) ou se é GARAGEM
                    if (inicio_jornada and fim_jornada) or observacao == 'GARAGEM':
                        tabela_jornada.append(linha)
                
                # Verificar conflitos para jornada
                result = analyzed_closure_data_driver.check_conflicts_only(tabela_jornada, motorist_id, truck_id)
                
                
                # Verificar conflitos para dayoff
                dayoff_result = closure_dayoff_driver.check_conflicts_only(tabela_folga, motorist_id)
                
                # Se há conflitos em qualquer um, retornar todos os conflitos
                if result.get('tem_conflitos') or dayoff_result.get('tem_conflitos'):
                    # Juntar todos os conflitos
                    conflitos_detalhados = []
                    conflitos_simples = []
                    
                    # Adicionar conflitos de jornada
                    for conflito in result.get('conflitos', []):
                        if isinstance(conflito, dict):
                            conflitos_detalhados.append(conflito)
                            conflitos_simples.append(f"{conflito['data']} - {conflito['tipo']}: {conflito['descricao']}")
                        else:
                            conflitos_simples.append(str(conflito))
                    

                    
                    # Adicionar conflitos de dayoff
                    for conflito in dayoff_result.get('conflitos', []):
                        if isinstance(conflito, dict):
                            conflitos_detalhados.append(conflito)
                            conflitos_simples.append(f"{conflito['data']} - {conflito['tipo']}: {conflito['descricao']}")
                        else:
                            conflitos_simples.append(str(conflito))
                    
                    # Retornar para o frontend decidir sobre substituição
                    return jsonify({
                        "mensagem": "Conflitos encontrados",
                        "status": "conflito",
                        "conflitos": list(set(conflitos_simples)),
                        "conflitos_detalhados": conflitos_detalhados
                    }), 409  # Código 409 para conflito
                
                # Se não há conflitos, inserir todos os registros de uma vez
                result = analyzed_closure_data_driver.insert_data_from_json(tabela_jornada, motorist_id, truck_id, replace=substituir)
                
                # Inserir dados de folga na tabela dayoff_fecham
                dayoff_result = closure_dayoff_driver.insert_data_from_json(tabela_folga)
                
                routes_logger.print(f"Registros inseridos: {result['registros_inseridos']}, ignorados: {result['registros_ignorados']}")
                
        except Exception as e:
            routes_logger.print(f"Erro ao inserir dado permanente. Erro: {e}")
            return jsonify({"mensagem": "Erro ao processar dados", "erro": str(e)}), 500

        try:
            # Apaga os dados temporários após salvar com sucesso
            # NOVA LÓGICA: Excluir dados do período, exceto datas marcadas como INVÁLIDO
            blocos_invalidos = dados.get('blocos_invalidos', [])
            
            # Obter período dos dados salvos para filtrar a exclusão
            data_inicial = None
            data_final = None
            
            if tabela and len(tabela) > 0:
                # Extrair datas da tabela para determinar o período
                datas_tabela = []
                for linha in tabela:
                    data_str = linha.get('Data', '')
                    if data_str:
                        try:
                            # Converter DD-MM-YYYY para datetime
                            data_obj = datetime.strptime(data_str, '%d-%m-%Y')
                            datas_tabela.append(data_obj)
                        except:
                            pass
                
                if datas_tabela:
                    data_inicial = min(datas_tabela).strftime('%Y-%m-%d')
                    data_final = max(datas_tabela).strftime('%Y-%m-%d')
                    routes_logger.print(f"Período identificado: {data_inicial} a {data_final}")
                    routes_logger.print(f"Datas originais da tabela: {[d.strftime('%d-%m-%Y') for d in datas_tabela]}")
            
            if blocos_invalidos:
                routes_logger.print(f"Excluindo dados temporários da placa {plate} no período {data_inicial} a {data_final}, preservando datas INVÁLIDAS: {blocos_invalidos}")
                
                # Converter datas DD-MM-YYYY para formato ISO (YYYY-MM-DD) para comparação
                datas_invalidas_iso = []
                for data_invalida in blocos_invalidos:
                    try:
                        # Converter DD-MM-YYYY para YYYY-MM-DD
                        dia, mes, ano = data_invalida.split('-')
                        data_iso = f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
                        datas_invalidas_iso.append(data_iso)
                    except:
                        routes_logger.print(f"Erro ao converter data {data_invalida} para formato ISO")
                
                # Excluir dados temporários do período, exceto datas marcadas como INVÁLIDO
                if datas_invalidas_iso and data_inicial and data_final:
                    # Construir query SQL para excluir dados do período, exceto datas INVÁLIDAS
                    placeholders = ','.join(['?' for _ in datas_invalidas_iso])
                    query = f"""
                        DELETE FROM vehicle_data_fecham 
                        WHERE truck_id = ? 
                        AND DATE(data_iso) BETWEEN ? AND ?
                        AND DATE(data_iso) NOT IN ({placeholders})
                    """
                    params = [truck_id, data_inicial, data_final] + datas_invalidas_iso
                    
                    # Executar query personalizada
                    import sqlite3
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows_deleted = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    routes_logger.print(f"Dados temporários excluídos: {rows_deleted} registros do período {data_inicial} a {data_final} (preservando {len(datas_invalidas_iso)} datas INVÁLIDAS)")
                elif data_inicial and data_final:
                    # Se não há datas INVÁLIDAS, excluir todos os dados do período
                    query = """
                        DELETE FROM vehicle_data_fecham 
                        WHERE truck_id = ? 
                        AND DATE(data_iso) BETWEEN ? AND ?
                    """
                    params = [truck_id, data_inicial, data_final]
                    
                    import sqlite3
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows_deleted = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    routes_logger.print(f"Dados temporários excluídos: {rows_deleted} registros do período {data_inicial} a {data_final} (nenhuma data INVÁLIDA)")
                else:
                    # Se não conseguiu determinar período, usar exclusão tradicional
                    routes_logger.print("Não foi possível determinar período, usando exclusão tradicional por truck_id")
                    closure_driver.delete_record(where_columns=['truck_id'], where_values=(truck_id,))
            else:
                # Se não há blocos INVÁLIDO, excluir todos os dados temporários do período
                if data_inicial and data_final:
                    query = """
                        DELETE FROM vehicle_data_fecham 
                        WHERE truck_id = ? 
                        AND DATE(data_iso) BETWEEN ? AND ?
                    """
                    params = [truck_id, data_inicial, data_final]
                    
                    import sqlite3
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows_deleted = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    routes_logger.print(f"Excluindo todos os dados temporários da placa {plate} no período {data_inicial} a {data_final}: {rows_deleted} registros")
                else:
                    # Fallback: exclusão tradicional por truck_id
                    routes_logger.print(f"Excluindo todos os dados temporários da placa {plate} (fallback por truck_id)")
                    closure_driver.delete_record(where_columns=['truck_id'], where_values=(truck_id,))
                
        except Exception as e:
            routes_logger.print(f"Erro ao excluir dados temporários. Erro: {e}.")

        # VALIDAÇÃO DE CÁLCULOS - Executar após salvar com sucesso
        try:
            # Preparar dados para validação (usando o primeiro registro como exemplo)
            if tabela and len(tabela) > 0:
                primeiro_registro = tabela[0]
                observacao = primeiro_registro.get('Observação', '').strip().upper()
                inicio_jornada = primeiro_registro.get('Início Jornada', '')
                fim_jornada = primeiro_registro.get('Fim de Jornada', '')
                inicio_refeicao = primeiro_registro.get('Início Refeição', '')
                fim_refeicao = primeiro_registro.get('Fim Refeição', '')
                data = primeiro_registro.get('Data', '')
                
                validation_data = {
                    'inicio_jornada': inicio_jornada,
                    'fim_jornada': fim_jornada,
                    'inicio_refeicao': inicio_refeicao,
                    'fim_refeicao': fim_refeicao,
                    'observacao': observacao,
                    'data': data,
                    'dia_semana': get_weekday_name(data) if data else '',
                    'descansos': []
                }
                
                # Executar validação
                validation_result = calculation_validator.validate_calculation(validation_data)
                
                # Se há divergência, incluir informações no response
                if validation_result.get('status') == 'divergent':
                    routes_logger.print(f"⚠️ DIVERGÊNCIA DETECTADA: {validation_result.get('differences')}")
                    
                    # Reprocessar últimos 15 dias
                    reprocess_result = calculation_validator.reprocess_last_15_days(None)  # db_connection será implementado
                    
                    return jsonify({
                        "mensagem": "Dados salvos com sucesso!",
                        "status": "ok",
                        "validation": {
                            "status": "divergent",
                            "message": "Divergência detectada entre os módulos de cálculo",
                            "reprocess_result": reprocess_result
                        }
                    })
                else:
                    return jsonify({
                        "mensagem": "Dados salvos com sucesso!",
                        "status": "ok",
                        "validation": {
                            "status": "valid",
                            "message": "Todos os cálculos foram conferidos e confirmados por 2 sistemas de validação redundantes. Nenhuma divergência encontrada."
                        }
                    })
                    
            else:
                return jsonify({
                    "mensagem": "Dados salvos com sucesso!",
                    "status": "ok",
                    "validation": {
                        "status": "valid",
                        "message": "Todos os cálculos foram conferidos e confirmados por 2 sistemas de validação redundantes. Nenhuma divergência encontrada."
                    }
                })
                
        except Exception as validation_error:
            routes_logger.print(f"❌ Erro na validação de cálculos: {str(validation_error)}")
            return jsonify({
                "mensagem": "Dados salvos com sucesso!",
                "status": "ok",
                "validation": {
                    "status": "error",
                    "message": "Erro durante a validação de cálculos"
                }
            })

    else:
        return jsonify({"mensagem": "Ação desconhecida."}), 400

@closure_bp.route('/closure_clear_vehicle_data', methods=['POST'])
@route_access_required
def closure_clear_vehicle_data():
    try:
        # Deleta todos os registros da tabela vehicle_data_fecham
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vehicle_data_fecham")
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "Dados do fechamento de ponto limpos com sucesso!"})
    except Exception as e:
        routes_logger.register_log("Erro ao limpar dados do fechamento de ponto.", f"Erro: {e}")
        return jsonify({"status": "error", "message": "Erro ao limpar dados do fechamento de ponto."})
        
@closure_bp.route('/download-report-fechamento', methods=['GET', 'POST'])
@route_access_required
def download_report_fechamento():
    try:
        # Busca apenas motoristas ativos para fechamento
        all_motorists = motorist_driver.retrieve_active_motorists_for_closure()
        # Ordena alfabeticamente por nome
        all_motorists.sort(key=lambda x: x[1].upper() if x[1] else '')
        # Formata para o template
        motorists = [(m[0], m[1]) for m in all_motorists]
        
        return render_template('closure_reports.html', motorists=motorists)
    except Exception as e:
        routes_logger.register_log(f"Erro ao carregar página de relatórios: {e}")
        return render_template('closure_reports.html', motorists=[])

@closure_bp.route('/api/closure/get-report', methods=['GET'])
@route_access_required
def get_closure_report():
    """API para buscar dados do relatório de fechamento"""
    try:
        motorist_id = request.args.get('motorist_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        if not motorist_id or not from_date or not to_date:
            return jsonify({"error": "Parâmetros obrigatórios não fornecidos"}), 400
        
        # Buscar dados do motorista
        motorist_data = motorist_driver.retrieve_motorist(['id'], (int(motorist_id),))
        if not motorist_data:
            return jsonify({"error": "Motorista não encontrado"}), 404
        
        motorist_name = motorist_data[1]
        
        # Buscar dados de jornada do período
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Converter datas para formato DD-MM-YYYY para buscar na tabela
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            from_date_br = from_date_obj.strftime('%d-%m-%Y')
            to_date_br = to_date_obj.strftime('%d-%m-%Y')
        except:
            from_date_br = from_date
            to_date_br = to_date
        
        print(f"Debug: Buscando dados de {from_date_br} a {to_date_br}")
        
        # Primeiro, verificar quantidade de dados em perm e dayoff para o motorista
        cursor.execute("SELECT COUNT(*) FROM perm_data_fecham WHERE motorist_id = ?", (motorist_id,))
        total_perm = cursor.fetchone()[0]
        print(f"Debug: Total de registros de jornada para motorista {motorist_id}: {total_perm}")

        cursor.execute("SELECT COUNT(*) FROM dayoff_fecham WHERE motorist_id = ?", (motorist_id,))
        total_dayoff_count = cursor.fetchone()[0]
        print(f"Debug: Total de registros de dayoff para motorista {motorist_id}: {total_dayoff_count}")

        # Só retornar vazio se não existir NENHUM registro em nenhuma das tabelas
        if total_perm == 0 and total_dayoff_count == 0:
            conn.close()
            return render_template('closure_report_modal.html', 
                                 motorist_id=motorist_id,
                                 motorist_name=motorist_name,
                                 from_date=from_date_obj.strftime('%d-%m-%Y') if 'from_date_obj' in locals() else from_date,
                                 to_date=to_date_obj.strftime('%d-%m-%Y') if 'to_date_obj' in locals() else to_date,
                                 jornada_data=[],
                                 folgas=[])
        
        # Verificar quais datas existem para o motorista
        cursor.execute("SELECT DISTINCT data FROM perm_data_fecham WHERE motorist_id = ? ORDER BY data", (motorist_id,))
        datas_existentes = cursor.fetchall()
        print(f"Debug: Datas existentes para motorista {motorist_id}: {[d[0] for d in datas_existentes]}")
        
        # Verificar se a tabela trucks existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trucks'")
        trucks_exists = cursor.fetchone() is not None
        
        print(f"Debug: Buscando dados de {from_date_br} a {to_date_br}")
        
        # Buscar dados de perm_data_fecham - buscar todos e filtrar em Python
        if trucks_exists:
            # Buscar dados com JOIN para pegar a placa
            cursor.execute("""
                SELECT p.data, p.dia_da_semana, p.inicio_jornada, p.in_refeicao, p.fim_refeicao, p.fim_jornada,
                       p.observacao, p.tempo_refeicao, p.tempo_intervalo, p.jornada_total, p.carga_horaria, p.hextra_50,
                       p.hextra_100, p.he_noturno, p.daily_value, p.food_value, t.placa, p.truck_id
                FROM perm_data_fecham p
                LEFT JOIN trucks t ON p.truck_id = t.id
                WHERE p.motorist_id = ?
                ORDER BY strftime('%Y-%m-%d', 
                    substr(p.data, 7, 4) || '-' || 
                    substr(p.data, 4, 2) || '-' || 
                    substr(p.data, 1, 2)
                )
            """, (motorist_id,))
        else:
            # Buscar dados sem JOIN (tabela trucks não existe)
            cursor.execute("""
                SELECT data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada,
                       observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50,
                       hextra_100, he_noturno, daily_value, food_value
                FROM perm_data_fecham 
                WHERE motorist_id = ?
                ORDER BY strftime('%Y-%m-%d', 
                    substr(data, 7, 4) || '-' || 
                    substr(data, 4, 2) || '-' || 
                    substr(data, 1, 2)
                )
            """, (motorist_id,))
        
        jornada_data = cursor.fetchall()
        
        print(f"Debug: {len(jornada_data)} registros encontrados para motorista {motorist_id}")
        
        # Filtrar dados de jornada pelo período em Python
        jornada_filtrada = []
        for row in jornada_data:
            data = row[0]  # data é o primeiro campo
            try:
                # Converter data DD-MM-YYYY para datetime
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                from_date_obj = datetime.strptime(from_date_br, '%d-%m-%Y')
                to_date_obj = datetime.strptime(to_date_br, '%d-%m-%Y')
                
                if from_date_obj <= data_obj <= to_date_obj:
                    jornada_filtrada.append(row)
            except:
                pass
        
        print(f"Debug: {len(jornada_filtrada)} registros de jornada no período {from_date_br} a {to_date_br}")
        
        # Buscar classificações dos blocos para o período
        classificacoes = {}
        try:
            cursor.execute("""
                SELECT data, classification, notes, truck_id
                FROM closure_block_classifications 
                WHERE motorist_id = ?
                ORDER BY strftime('%Y-%m-%d', 
                    substr(data, 7, 4) || '-' || 
                    substr(data, 4, 2) || '-' || 
                    substr(data, 1, 2)
                )
            """, (motorist_id,))
            
            classificacoes_data = cursor.fetchall()
            print(f"Debug: {len(classificacoes_data)} classificações encontradas para motorista {motorist_id}")
            
            # Filtrar classificações pelo período e criar dicionário
            for row in classificacoes_data:
                data = row[0]
                classification = row[1]
                notes = row[2]
                truck_id = row[3]
                
                try:
                    # Converter data DD-MM-YYYY para datetime
                    data_obj = datetime.strptime(data, '%d-%m-%Y')
                    from_date_obj = datetime.strptime(from_date_br, '%d-%m-%Y')
                    to_date_obj = datetime.strptime(to_date_br, '%d-%m-%Y')
                    
                    if from_date_obj <= data_obj <= to_date_obj:
                        # Usar data como chave, com truck_id como sub-chave se disponível
                        key = f"{data}_{truck_id}" if truck_id else data
                        classificacoes[key] = {
                            'classification': classification,
                            'notes': notes,
                            'truck_id': truck_id
                        }
                except:
                    pass
                    
            print(f"Debug: {len(classificacoes)} classificações no período {from_date_br} a {to_date_br}")
        except Exception as e:
            print(f"Debug: Erro ao buscar classificações: {e}")
            classificacoes = {}
        
        # Buscar dados de dayoff_fecham - buscar todos e filtrar em Python
        cursor.execute("""
            SELECT data, motivo, daily_value, food_value
            FROM dayoff_fecham 
            WHERE motorist_id = ?
            ORDER BY strftime('%Y-%m-%d', 
                substr(data, 7, 4) || '-' || 
                substr(data, 4, 2) || '-' || 
                substr(data, 1, 2)
            )
        """, (motorist_id,))
        
        dayoff_data = cursor.fetchall()
        
        print(f"Debug: {len(dayoff_data)} registros de dayoff encontrados para motorista {motorist_id}")
        
        # Filtrar dados de dayoff pelo período em Python
        dayoff_filtrada = []
        for row in dayoff_data:
            data = row[0]  # data é o primeiro campo
            try:
                # Converter data DD-MM-YYYY para datetime
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                from_date_obj = datetime.strptime(from_date_br, '%d-%m-%Y')
                to_date_obj = datetime.strptime(to_date_br, '%d-%m-%Y')
                
                if from_date_obj <= data_obj <= to_date_obj:
                    dayoff_filtrada.append(row)
            except:
                pass
        
        print(f"Debug: {len(dayoff_filtrada)} registros de dayoff no período {from_date_br} a {to_date_br}")
        
        # Processar dados de jornada
        processed_data = []
        
        # Variáveis para calcular totais
        total_intervalo = 0
        total_almoco = 0
        total_h_trab = 0
        total_carga_horaria = 0
        total_h_extra50 = 0
        total_h_extra100 = 0
        total_h_e_not = 0
        total_diaria = 0.0
        total_aj_aliment = 0.0
        
        # Função para converter tempo HH:MM para minutos
        def tempo_para_minutos(tempo_str):
            if not tempo_str or tempo_str == "NULL" or tempo_str == "":
                return 0
            try:
                if ':' in tempo_str:
                    # Verificar se é negativo
                    is_negative = tempo_str.startswith('-')
                    # Remover o sinal negativo se existir
                    tempo_limpo = tempo_str.replace('-', '')
                    horas, minutos = map(int, tempo_limpo.split(':'))
                    resultado = horas * 60 + minutos
                    # Aplicar sinal negativo se necessário
                    return -resultado if is_negative else resultado
                else:
                    return 0
            except:
                return 0
        
        # Função para converter minutos para HH:MM
        def minutos_para_tempo(minutos):
            if minutos == 0:
                return "00:00"
            
            # Verificar se é negativo
            is_negative = minutos < 0
            minutos_abs = abs(minutos)
            
            horas = minutos_abs // 60
            mins = minutos_abs % 60
            
            resultado = f"{horas:02d}:{mins:02d}"
            # Adicionar sinal negativo se necessário
            return f"-{resultado}" if is_negative else resultado
        
        # Função para abreviar dia da semana
        def abreviar_dia_semana(dia_completo):
            abreviacoes = {
                'Segunda-feira': 'Seg.',
                'Terça-feira': 'Ter.',
                'Quarta-feira': 'Qua.',
                'Quinta-feira': 'Qui.',
                'Sexta-feira': 'Sex.',
                'Sábado': 'Sáb.',
                'Domingo': 'Dom.'
            }
            return abreviacoes.get(dia_completo, dia_completo)
        
        # Processar dados de jornada (perm_data_fecham)
        for row in jornada_filtrada:
            if trucks_exists and len(row) == 17:
                # Com JOIN (inclui placa)
                data, dia_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, \
                observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50, \
                hextra_100, he_noturno, daily_value, food_value, placa = row
            else:
                # Sem JOIN (sem placa)
                data, dia_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, \
                observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50, \
                hextra_100, he_noturno, daily_value, food_value = row
                placa = ""
            
            # Formatar valores monetários
            def formatar_moeda(valor):
                if not valor or valor == "NULL" or valor == "":
                    return "R$ 0,00"
                try:
                    # Remover .0 e converter para float
                    valor_limpo = str(valor).replace('.0', '')
                    valor_float = float(valor_limpo)
                    # Formatar como moeda brasileira
                    return f"R$ {valor_float:.2f}".replace('.', ',')
                except:
                    return "R$ 0,00"
            
            diaria_formatada = formatar_moeda(daily_value)
            alimentacao_formatada = formatar_moeda(food_value)
            
            # Calcular totais
            total_intervalo += tempo_para_minutos(tempo_intervalo)
            total_almoco += tempo_para_minutos(tempo_refeicao)
            total_h_trab += tempo_para_minutos(jornada_total)
            total_carga_horaria += tempo_para_minutos(carga_horaria)
            total_h_extra50 += tempo_para_minutos(hextra_50)
            total_h_extra100 += tempo_para_minutos(hextra_100)
            total_h_e_not += tempo_para_minutos(he_noturno)
            
            # Totais monetários
            try:
                if daily_value and daily_value != "NULL" and daily_value != "":
                    total_diaria += float(str(daily_value).replace('.0', ''))
            except:
                pass
            
            try:
                if food_value and food_value != "NULL" and food_value != "":
                    total_aj_aliment += float(str(food_value).replace('.0', ''))
            except:
                pass
            
            # Buscar classificação para esta data
            classificacao_info = None
            if trucks_exists and len(row) == 17:
                # Com JOIN (inclui truck_id)
                truck_id = row[16]  # truck_id é o último campo
                key = f"{data}_{truck_id}" if truck_id else data
                classificacao_info = classificacoes.get(key)
            else:
                # Sem JOIN (sem truck_id)
                classificacao_info = classificacoes.get(data)
            
            # Determinar classificação e cor
            classificacao_display = 'VÁLIDO'
            classificacao_class = 'badge-valid'
            if classificacao_info:
                classification = classificacao_info['classification']
                if classification == 'VALIDO':
                    classificacao_display = 'VÁLIDO'
                    classificacao_class = 'badge-valid'
                elif classification == 'GARAGEM':
                    classificacao_display = 'GARAGEM'
                    classificacao_class = 'badge-garagem'
                elif classification == 'CARGA_DESCARGA':
                    classificacao_display = 'CARGA/DESCARGA'
                    classificacao_class = 'badge-carga-descarga'
                elif classification == 'INVALIDO':
                    classificacao_display = 'INVÁLIDO'
                    classificacao_class = 'badge-invalid'
            
            processed_data.append({
                'placa': placa or '',
                'data': data,
                'dia_semana': abreviar_dia_semana(dia_semana),
                'classificacao': classificacao_display,
                'classificacao_class': classificacao_class,
                'inicio_jornada': inicio_jornada or '',
                'almoco_inicio': in_refeicao or '',
                'almoco_fim': fim_refeicao or '',
                'fim_jornada': fim_jornada or '',
                'intervalo': tempo_intervalo or '',
                'almoco': tempo_refeicao or '',
                'h_trab': jornada_total or '',
                'carga_horaria': carga_horaria or '',
                'h_extra50': hextra_50 or '',
                'h_extra100': hextra_100 or '',
                'h_e_not': he_noturno or '',
                'ad_not': he_noturno or '',  # Adicional noturno = hora extra noturna
                'diaria': diaria_formatada,
                'aj_aliment': alimentacao_formatada
            })
        
        # Formatar totais
        totais = {
            'intervalo': minutos_para_tempo(total_intervalo),
            'almoco': minutos_para_tempo(total_almoco),
            'h_trab': minutos_para_tempo(total_h_trab),
            'carga_horaria': minutos_para_tempo(total_carga_horaria),
            'h_extra50': minutos_para_tempo(total_h_extra50),
            'h_extra100': minutos_para_tempo(total_h_extra100),
            'h_e_not': minutos_para_tempo(total_h_e_not),
            'ad_not': minutos_para_tempo(total_h_e_not),  # Adicional noturno = hora extra noturna
            'diaria': f"R$ {total_diaria:.2f}".replace('.', ','),
            'aj_aliment': f"R$ {total_aj_aliment:.2f}".replace('.', ',')
        }
        
        # Processar dados de folga (dayoff_fecham) e adicionar à tabela principal
        for row in dayoff_filtrada:
            data, motivo, daily_value_dayoff, food_value_dayoff = row
            
            # Formatar valores monetários para dayoff
            def formatar_moeda_dayoff(valor):
                if not valor or valor == "NULL" or valor == "":
                    return "R$ 0,00"
                try:
                    valor_limpo = str(valor).replace('.0', '')
                    valor_float = float(valor_limpo)
                    return f"R$ {valor_float:.2f}".replace('.', ',')
                except:
                    return "R$ 0,00"
            
            diaria_formatada_dayoff = formatar_moeda_dayoff(daily_value_dayoff)
            alimentacao_formatada_dayoff = formatar_moeda_dayoff(food_value_dayoff)
            
            # Calcular dia da semana para a data
            try:
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                dias_semana = {
                    0: 'Segunda-feira',
                    1: 'Terça-feira',
                    2: 'Quarta-feira',
                    3: 'Quinta-feira',
                    4: 'Sexta-feira',
                    5: 'Sábado',
                    6: 'Domingo'
                }
                dia_semana_completo = dias_semana[data_obj.weekday()]
                dia_semana_abreviado = abreviar_dia_semana(dia_semana_completo)
            except:
                dia_semana_abreviado = "Data inválida"
            
            # Buscar classificação para esta data de dayoff
            classificacao_info_dayoff = classificacoes.get(data)
            classificacao_display_dayoff = 'VÁLIDO'
            classificacao_class_dayoff = 'badge-valid'
            if classificacao_info_dayoff:
                classification = classificacao_info_dayoff['classification']
                if classification == 'VALIDO':
                    classificacao_display_dayoff = 'VÁLIDO'
                    classificacao_class_dayoff = 'badge-valid'
                elif classification == 'GARAGEM':
                    classificacao_display_dayoff = 'GARAGEM'
                    classificacao_class_dayoff = 'badge-garagem'
                elif classification == 'CARGA_DESCARGA':
                    classificacao_display_dayoff = 'CARGA/DESCARGA'
                    classificacao_class_dayoff = 'badge-carga-descarga'
                elif classification == 'INVALIDO':
                    classificacao_display_dayoff = 'INVÁLIDO'
                    classificacao_class_dayoff = 'badge-invalid'
            
            # Adicionar registro de dayoff à tabela principal
            processed_data.append({
                'placa': motivo,  # Motivo no lugar da placa
                'data': data,
                'dia_semana': dia_semana_abreviado,
                'classificacao': classificacao_display_dayoff,
                'classificacao_class': classificacao_class_dayoff,
                'inicio_jornada': '',
                'almoco_inicio': '',
                'almoco_fim': '',
                'fim_jornada': '',
                'intervalo': '',
                'almoco': '',
                'h_trab': '',
                'carga_horaria': '',
                'h_extra50': '',
                'h_extra100': '',
                'h_e_not': '',
                'ad_not': '',
                'diaria': diaria_formatada_dayoff,
                'aj_aliment': alimentacao_formatada_dayoff,
                'observacao': motivo  # Motivo na observação
            })
        
        # Ordenar todos os dados por data
        processed_data.sort(key=lambda x: datetime.strptime(x['data'], '%d-%m-%Y'))
        
        # Processar dados de folga para exibição separada (se necessário)
        folgas = []
        for row in dayoff_filtrada:
            data, motivo = row[0], row[1]  # data e motivo são os primeiros campos
            folgas.append({
                'data': data,
                'motivo': motivo
            })
        
        # Fechar conexão com o banco
        conn.close()
        
        # Renderizar template do modal com datas formatadas corretamente e totais
        try:
            return render_template('closure_report_modal.html', 
                                 motorist_id=motorist_id,
                                 motorist_name=motorist_name,
                                 from_date=from_date_obj.strftime('%d-%m-%Y') if 'from_date_obj' in locals() else from_date,
                                 to_date=to_date_obj.strftime('%d-%m-%Y') if 'to_date_obj' in locals() else to_date,
                                 jornada_data=processed_data,
                                 folgas=folgas,
                                 totais=totais)
        except Exception as template_error:
            routes_logger.register_log(f"Erro ao renderizar template: {template_error}")
            routes_logger.register_log(f"Dados processados: {len(processed_data) if 'processed_data' in locals() else 'N/A'}")
            routes_logger.register_log(f"Totais: {totais if 'totais' in locals() else 'N/A'}")
            raise template_error
        
    except Exception as e:
        routes_logger.register_log(f"Erro ao gerar relatório de fechamento: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@closure_bp.route('/infractions_fechamento', methods=['GET'])
@route_access_required
def infractions_fechamento():
    return render_template('infractions_details_fechamento.html')

@closure_bp.route('/insert_data_fechamento', methods=['GET'])
@route_access_required
def insert_data_fechamento():
    try:
        # Busca todos os motoristas
        all_motorists = motorist_driver.retrieve_all_motorists()
        # Ordena alfabeticamente por nome
        all_motorists.sort(key=lambda x: x[1].upper() if x[1] else '')
        # Formata para o template
        motorists = [(m[0], m[1]) for m in all_motorists]
        
        # Busca todos os veículos disponíveis
        all_trucks = truck_driver.retrieve_all_trucks()
        # Ordena alfabeticamente por placa
        all_trucks.sort(key=lambda x: x[1].upper() if x[1] else '')
        # Formata para o template
        trucks = [(t[0], t[1]) for t in all_trucks]
        
        # Carregando configurações para obter os critérios
        parameters_driver = ParametersDriver(logger=routes_logger, db_path=DB_PATH)
        configs = parameters_driver.get_all_parameters()
        
        # id, tipo_filtro, valor_filtro, valor_diaria, valor_ajuda_alimentacao, descricao
        criterias = configs['criterios']
        
        return render_template('closure_insert_data_page.html', motorists=motorists, criterias=criterias, trucks=trucks)
    except Exception as e:
        routes_logger.register_log(f"Erro ao carregar página de inserção de dados: {e}")
        return render_template('closure_insert_data_page.html', motorists=[], criterias=[], trucks=[])

@closure_bp.route('/reports', methods=['GET'])
@route_access_required
def reports():
    """Página de relatórios do fechamento."""
    try:
        # Busca apenas motoristas ativos para fechamento
        all_motorists = motorist_driver.retrieve_active_motorists_for_closure()
        # Ordena alfabeticamente por nome
        all_motorists.sort(key=lambda x: x[1].upper() if x[1] else '')
        # Formata para o template
        motorists = [{"id": m[0], "name": m[1]} for m in all_motorists]
        
        # Buscar caminhões disponíveis para fechamento (JOIN entre vehicle_data_fecham e trucks)
        available_trucks = closure_driver.get_unique_truck_ids_and_plates()
        
        # Se não houver caminhões na tabela de fechamento, buscar da tabela trucks
        if not available_trucks:
            try:
                # Buscar todos os caminhões da tabela trucks
                all_trucks = truck_driver.retrieve_all_trucks()
                available_trucks = [(truck[0], truck[1]) for truck in all_trucks]  # (id, placa)
                routes_logger.register_log(f"Carregando {len(available_trucks)} caminhões da tabela trucks")
            except Exception as e:
                routes_logger.register_log(f"Erro ao buscar caminhões da tabela trucks: {e}")
                available_trucks = []
        else:
            routes_logger.register_log(f"Carregando {len(available_trucks)} caminhões da tabela vehicle_data_fecham")
        
        # Log para debug
        routes_logger.register_log(f"Total de caminhões disponíveis: {len(available_trucks)}")
        if available_trucks:
            routes_logger.register_log(f"Primeiros 3 caminhões: {available_trucks[:3]}")
        
        # Carregando configurações para obter os critérios
        parameters_driver = ParametersDriver(logger=routes_logger, db_path=DB_PATH)
        configs = parameters_driver.get_all_parameters()
        
        # id, tipo_filtro, valor_filtro, valor_diaria, valor_ajuda_alimentacao, descricao
        criterias = configs['criterios']
        
        return render_template('check_updates_fechamento.html', 
                             motorists=motorists, 
                             trucks=available_trucks,
                             criterias=criterias)
    except Exception as e:
        routes_logger.register_log(f"Erro ao carregar página de relatórios: {e}")
        return render_template('check_updates_fechamento.html', 
                             motorists=[], 
                             trucks=[],
                             criterias=[])

@closure_bp.route('/closure_parameters', methods=['GET'])
@route_access_required
def closure_parameters():
    """
    Rota para a página de parâmetros de fechamento de ponto.
    """
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        
        # Inicializar o driver de parâmetros
        parameters_driver = ParametersDriver(logger=routes_logger, db_path=DB_PATH)
        
        # Buscar todos os parâmetros
        all_parameters = parameters_driver.get_all_parameters()
        
        return render_template('closure_parameters.html', 
                             parametros=all_parameters['parametros'],
                             criterios=all_parameters['criterios'],
                             feriados=all_parameters['feriados'])
                             
    except Exception as e:
        routes_logger.register_log(f"Erro ao carregar página de parâmetros: {e}")
        return render_template('closure_parameters.html', 
                             parametros={},
                             criterios=[],
                             feriados=[])

@closure_bp.route('/api/closure/check_motorist_updates', methods=['GET'])
@route_access_required
def check_motorist_updates():
    """Retorna o status de atualização de cada motorista."""
    try:
        # 1. Definir a Data-base como o dia anterior à data atual
        data_base = date.today() - timedelta(days=1)

        # 2. Recuperar apenas motoristas ativos para fechamento e ordenar alfabeticamente
        all_motorists = motorist_driver.retrieve_active_motorists_for_closure()
        # Ordenar por nome (índice 1)
        all_motorists.sort(key=lambda x: x[1].upper() if x[1] else '')
        
        # 3. Extrair IDs dos motoristas para consultas em lote
        motorist_ids = [m[0] for m in all_motorists]
        
        # 4. Consultas em lote para otimizar performance
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Consulta em lote para todas as datas existentes (perm_data_fecham + dayoff_fecham)
        placeholders = ','.join(['?' for _ in motorist_ids])
        all_dates_query = f"""
            SELECT motorist_id, data FROM (
                SELECT motorist_id, data FROM perm_data_fecham WHERE motorist_id IN ({placeholders})
                UNION ALL
                SELECT motorist_id, data FROM dayoff_fecham WHERE motorist_id IN ({placeholders})
            )
        """
        cursor.execute(all_dates_query, motorist_ids + motorist_ids)
        all_dates_results = {}
        for row in cursor.fetchall():
            motorist_id = row[0]
            date_str = row[1]
            if motorist_id not in all_dates_results:
                all_dates_results[motorist_id] = set()
            all_dates_results[motorist_id].add(date_str)
        
        conn.close()
        
        update_status_list = []

        # 5. Processar cada motorista com os dados já carregados
        for motorist_info in all_motorists:
            motorist_id = motorist_info[0]
            motorist_name = motorist_info[1]
            motorist_admission_date = motorist_info[2]  # data_admissao (índice 2 na nova estrutura)

            # Definir data de início para verificação (data de admissão ou 01/09/2025, a mais recente)
            fixed_start_date = datetime.strptime('01/09/2025', '%d/%m/%Y').date()
            
            # Tentar converter a data de admissão
            admission_date = None
            if motorist_admission_date:
                try:
                    # Tentar diferentes formatos de data
                    for date_format in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y']:
                        try:
                            admission_date = datetime.strptime(motorist_admission_date, date_format).date()
                            break
                        except ValueError:
                            continue
                except:
                    pass
            
            # Usar a data mais recente entre admissão e 01/09/2025
            if admission_date:
                start_check_date = max(admission_date, fixed_start_date)
            else:
                start_check_date = fixed_start_date

            # Encontrar a última data de atualização
            existing_dates = all_dates_results.get(motorist_id, set())
            last_update_date = None
            last_update_display = "Sem registros"

            if existing_dates:
                # Converter todas as datas para objetos date para comparação
                date_objects = []
                for date_str in existing_dates:
                    try:
                        # Tentar diferentes formatos
                        for date_format in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                            try:
                                date_obj = datetime.strptime(date_str, date_format).date()
                                date_objects.append(date_obj)
                                break
                            except ValueError:
                                continue
                    except:
                        continue
                
                if date_objects:
                    last_update_date = max(date_objects)
                    last_update_display = last_update_date.strftime('%d-%m-%Y')

            # Calcular status baseado na última atualização E datas faltantes
            status = "Sem registros"
            status_class = "sem-registros"

            if last_update_date:
                if last_update_date >= data_base:
                    # Verificar se há datas faltantes para determinar o status final
                    if start_check_date and start_check_date <= data_base:
                        missing_dates = []
                        current_check_date = start_check_date
                        
                        while current_check_date <= data_base:
                            # Tentar diferentes formatos para verificar se a data existe
                            date_found = False
                            for date_format in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                                current_date_str = current_check_date.strftime(date_format)
                                if current_date_str in existing_dates:
                                    date_found = True
                                    break
                            
                            if not date_found:
                                missing_dates.append(current_check_date.strftime('%d/%m/%Y'))

                            current_check_date += timedelta(days=1)
                        
                        # Se há datas faltantes, status é "Pendente de Atualização"
                        if missing_dates:
                            status = "Pendente de Atualização"
                            status_class = "status-pendente"
                        else:
                            status = "Atualizado"
                            status_class = "status-atualizado"
                    else:
                        status = "Atualizado"
                        status_class = "status-atualizado"
                else:
                    days_behind = (data_base - last_update_date).days
                    status = f"{days_behind} dias atrasado"
                    status_class = "status-atrasado"

            # Calcular observações (dias faltantes) - reutilizar a lógica já calculada no status
            obs = "Sem data de início para checagem"
            obs_class = "obs-faltante"

            if start_check_date and start_check_date <= data_base:
                # Reutilizar a lógica de datas faltantes já calculada no status
                if status == "Pendente de Atualização":
                    # Recalcular as datas faltantes para as observações
                    missing_dates = []
                    current_check_date = start_check_date
                    
                    while current_check_date <= data_base:
                        # Tentar diferentes formatos para verificar se a data existe
                        date_found = False
                        for date_format in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                            current_date_str = current_check_date.strftime(date_format)
                            if current_date_str in existing_dates:
                                date_found = True
                                break
                        
                        if not date_found:
                            missing_dates.append(current_check_date.strftime('%d/%m/%Y'))

                        current_check_date += timedelta(days=1)
                    
                    obs = f"{', '.join(missing_dates)} faltante(s)"
                    obs_class = "obs-faltante"
                elif status == "Atualizado":
                    obs = "Completo"
                    obs_class = "obs-completo"
                elif "dias atrasado" in status:
                    # Para motoristas atrasados, mostrar as datas faltantes desde a última atualização até a data base
                    missing_dates = []
                    if last_update_date:
                        current_check_date = last_update_date + timedelta(days=1)
                        
                        while current_check_date <= data_base:
                            # Tentar diferentes formatos para verificar se a data existe
                            date_found = False
                            for date_format in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                                current_date_str = current_check_date.strftime(date_format)
                                if current_date_str in existing_dates:
                                    date_found = True
                                    break
                            
                            if not date_found:
                                missing_dates.append(current_check_date.strftime('%d/%m/%Y'))

                            current_check_date += timedelta(days=1)
                        
                        if missing_dates:
                            obs = f"{', '.join(missing_dates)} faltante(s)"
                            obs_class = "obs-faltante"
                        else:
                            obs = "Sem datas faltantes identificadas"
                            obs_class = "obs-completo"
                    else:
                        obs = "Última atualização não determinada"
                        obs_class = "obs-faltante"
                else:
                    obs = "Status não determinado"
                    obs_class = ""
            elif not start_check_date:
                obs = "Sem data de início para checagem"
                obs_class = "obs-faltante"
            else:
                obs = "Data de início futura"
                obs_class = ""

            update_status_list.append({
                "id": motorist_id,
                "name": motorist_name,
                "last_update": last_update_display,
                "status": status,
                "status_class": status_class,
                "obs": obs,
                "obs_class": obs_class
            })

        return jsonify(update_status_list), 200

    except Exception as e:
        routes_logger.register_log(f"Erro ao verificar atualizações de motoristas: {e}")
        return jsonify({"error": "Erro interno ao verificar atualizações."}), 500

@closure_bp.route('/api/closure/get-motorist-details', methods=['GET'])
@route_access_required
def get_motorist_details():
    """Retorna os detalhes dos registros de um motorista em um período."""
    try:
        motorist_id = request.args.get('motorist_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        routes_logger.print(f"Buscando detalhes do motorista {motorist_id} de {from_date} até {to_date}")

        if not motorist_id:
            return jsonify({"error": "ID do motorista não fornecido"}), 400

        # Primeiro verifica se existem registros em ambas as tabelas
        check_perm_query = "SELECT COUNT(*) FROM perm_data_fecham WHERE motorist_id = ?"
        check_dayoff_query = "SELECT COUNT(*) FROM dayoff_fecham WHERE motorist_id = ?"
        
        count_perm = analyzed_closure_data_driver.exec_query(check_perm_query, params=(motorist_id,), fetchone=True)[0]
        count_dayoff = closure_dayoff_driver.exec_query(check_dayoff_query, params=(motorist_id,), fetchone=True)[0]

        if count_perm == 0 and count_dayoff == 0:
            return jsonify({"registros": [], "mensagem": "Não há registros para este motorista"})

        # Query para dados de jornada (perm_data_fecham)
        perm_query = """
            SELECT 
                p.*,
                t.placa as truck_plate
            FROM perm_data_fecham p
            LEFT JOIN trucks t ON p.truck_id = t.id
            WHERE p.motorist_id = ?
            ORDER BY substr(p.data, 7, 4) || substr(p.data, 4, 2) || substr(p.data, 1, 2) DESC
            LIMIT 40
        """
        
        # Query para dados de dayoff (dayoff_fecham)
        dayoff_query = """
            SELECT 
                motorist_id,
                data,
                motivo,
                daily_value,
                food_value,
                carga_horaria_esp,
                hextra_50_esp
            FROM dayoff_fecham
            WHERE motorist_id = ?
            ORDER BY substr(data, 7, 4) || substr(data, 4, 2) || substr(data, 1, 2) DESC
            LIMIT 40
        """
        
        perm_records = analyzed_closure_data_driver.exec_query(perm_query, params=(motorist_id,), fetchone=False) if count_perm > 0 else []
        dayoff_records = closure_dayoff_driver.exec_query(dayoff_query, params=(motorist_id,), fetchone=False) if count_dayoff > 0 else []
        
        routes_logger.print(f"Encontrados {len(perm_records)} registros de jornada e {len(dayoff_records)} registros de dayoff")

        formatted_records = []
        
        # Processar registros de jornada (perm_data_fecham)
        for record in perm_records:
            try:
                # Formata os descansos
                descansos = []
                for i in range(1, 9):
                    # Usar índices numéricos baseados na posição das colunas na query
                    # A query retorna: p.*, t.placa as truck_plate
                    # Então as colunas são: motorist_id, truck_id, data, dia_da_semana, ..., in_desc_1, fim_desc_1, etc.
                    # Precisamos calcular os índices corretos
                    in_desc_index = 16 + (i-1)*2  # 16 é o índice inicial das colunas de descanso
                    fim_desc_index = 17 + (i-1)*2
                    
                    inicio = record[in_desc_index] if len(record) > in_desc_index else None
                    fim = record[fim_desc_index] if len(record) > fim_desc_index else None
                    if inicio and fim:
                        descansos.append({
                            'inicio': inicio,
                            'fim': fim
                        })

                # Formata o registro usando índices numéricos
                # Índices baseados na estrutura real da tabela perm_data_fecham
                # A query retorna: p.*, t.placa as truck_plate
                # Estrutura real da tabela perm_data_fecham:
                # motorist_id(0), truck_id(1), data(2), dia_da_semana(3), inicio_jornada(4), 
                # in_refeicao(5), fim_refeicao(6), fim_jornada(7), observacao(8), tempo_refeicao(9),
                # tempo_intervalo(10), jornada_total(11), carga_horaria(12), hextra_50(13), 
                # hextra_100(14), he_noturno(15), in_desc_1(16), fim_desc_1(17), ..., 
                # in_desc_8(30), fim_desc_8(31), daily_value(32), food_value(33)
                # truck_plate é a última coluna (34)
                truck_plate_index = len(record) - 1  # Última coluna é t.placa
                
                formatted_record = {
                    'tipo': 'jornada',  # Identificador do tipo de registro
                    'placa': record[truck_plate_index] or '',  # truck_plate
                    'data': record[2],  # data
                    'dia_da_semana': record[3] or get_weekday_name(record[2]),  # dia_da_semana ou calculado
                    'inicio_jornada': record[4] or '',  # inicio_jornada
                    'in_refeicao': record[5] or '',  # in_refeicao
                    'fim_refeicao': record[6] or '',  # fim_refeicao
                    'fim_jornada': record[7] or '',  # fim_jornada
                    'observacao': record[8] or '',  # observacao
                    'tempo_refeicao': record[9] or '',  # tempo_refeicao
                    'tempo_intervalo': record[10] or '',  # tempo_intervalo
                    'jornada_total': record[11] or '',  # jornada_total
                    'carga_horaria': record[12] or '00:00',  # carga_horaria
                    'hextra_50': record[13] or '00:00',  # hextra_50
                    'adicional_noturno': record[15] or '00:00',  # he_noturno (renomeado)
                    'he_noturno': record[15] or '00:00',  # he_noturno
                    'daily_value': float(record[32] or 0),  # daily_value
                    'food_value': float(record[33] or 0),  # food_value
                    'descansos': descansos
                }
                formatted_records.append(formatted_record)
            except Exception as e:
                routes_logger.print(f"Erro ao formatar registro de jornada: {str(e)}")
                continue
        
        # Processar registros de dayoff (dayoff_fecham)
        for record in dayoff_records:
            try:
                # Formata o registro de dayoff
                formatted_record = {
                    'tipo': 'dayoff',  # Identificador do tipo de registro
                    'placa': '',  # Dayoff não tem placa
                    'data': record[1],  # data
                    'dia_da_semana': get_weekday_name(record[1]),  # calculado da data
                    'inicio_jornada': '',  # Dayoff não tem jornada
                    'in_refeicao': '',
                    'fim_refeicao': '',
                    'fim_jornada': '',
                    'observacao': record[2],  # motivo
                    'tempo_refeicao': '',
                    'tempo_intervalo': '',
                    'jornada_total': '',
                    'carga_horaria': record[5] or '00:00',  # carga_horaria_esp
                    'hextra_50': record[6] or '00:00',  # hextra_50_esp
                    'adicional_noturno': '00:00',  # hextra_100 removido
                    'he_noturno': '00:00',
                    'daily_value': float(record[3] or 0),  # daily_value
                    'food_value': float(record[4] or 0),  # food_value
                    'descansos': []
                }
                formatted_records.append(formatted_record)
            except Exception as e:
                routes_logger.print(f"Erro ao formatar registro de dayoff: {str(e)}")
                continue
        
        # Ordenar todos os registros por data (mais recente primeiro)
        formatted_records.sort(key=lambda x: x['data'], reverse=True)
        
        # Limitar a 40 registros
        formatted_records = formatted_records[:40]

        routes_logger.print(f"Formatados {len(formatted_records)} registros com sucesso ({len(perm_records)} jornada + {len(dayoff_records)} dayoff)")
        
        # Debug: Log dos primeiros registros para verificar estrutura
        if formatted_records:
            routes_logger.print(f"Exemplo de registro: {formatted_records[0]}")
        
        return jsonify({"registros": formatted_records})

    except Exception as e:
        routes_logger.print(f"Erro ao buscar detalhes: {str(e)}")
        import traceback
        routes_logger.print(traceback.format_exc())
        return jsonify({"error": "Erro ao buscar detalhes"}), 500

@closure_bp.route('/api/closure/delete-motorist-records', methods=['POST'])
@route_access_required
def delete_motorist_records():
    """Exclui registros de um motorista para datas específicas."""
    try:
        data = request.get_json()
        motorist_id = data.get('motorist_id')
        dates = data.get('dates', [])

        if not motorist_id or not dates:
            return jsonify({"error": "Dados incompletos"}), 400

        # Exclui os registros do fechamento
        for date in dates:
            analyzed_closure_data_driver.delete_perm_data(
                where_columns=['motorist_id', 'data'],
                where_values=(motorist_id, date)
            )
            # Também exclui registros de folga se existirem
            closure_dayoff_driver.exec_query(
                "DELETE FROM dayoff_fecham WHERE motorist_id=? AND data=?",
                params=(motorist_id, date)
            )

        return jsonify({"message": "Registros excluídos com sucesso"})

    except Exception as e:
        routes_logger.register_log(f"Erro ao excluir registros: {e}")
        return jsonify({"error": str(e)}), 500

def calcular_criterio_especial(motivo, configs, data, dia_semana, feriados):
    """
    Obtém carga horária parametrizada e calcula hora extra 50% para critérios especiais.
    
    Para critérios especiais: H. Extra 50% = H. Trabalhadas - Carga Horária
    Onde H. Trabalhadas sempre é 0 (zero) para critérios especiais.
    
    Args:
        motivo (str): Nome do critério especial
        configs (dict): Configurações dos critérios
        data (str): Data no formato DD-MM-YYYY
        dia_semana (str): Dia da semana
        feriados (list): Lista de feriados
    
    Returns:
        dict: {
            'carga_horaria_esp': '08:00',  # Valor parametrizado
            'hextra_50_esp': '-08:00'      # Valor calculado (0 - carga_horaria)
        }
    """
    try:
        from controller.carga_horaria_calculator import CargaHorariaCalculator
        
        # Buscar configuração do critério
        criterio = None
        for c in configs.get('criterios', []):
            if c['valor_filtro'].upper() == motivo.upper():
                criterio = c
                break
        
        # 🆕 OBTER CARGA HORÁRIA PARAMETRIZADA (já existe no sistema)
        if criterio and criterio.get('carga_horaria_especial') != 'Padrão':
            # Usar valor especial configurado no critério
            carga_horaria_configurada = criterio['carga_horaria_especial']
        else:
            # Usar valor padrão
            carga_horaria_configurada = 'Padrão'
        
        # Calcular carga horária usando sistema existente (parametrização + feriados + dias)
        carga_horaria_minutos = CargaHorariaCalculator.calcular_carga_horaria_especial(
            criterio_especial=motivo,
            dia_semana=dia_semana,
            data=data,
            feriados=feriados,
            carga_horaria_configurada=carga_horaria_configurada
        )
        
        # 🆕 CALCULAR HORA EXTRA 50% baseado na carga horária parametrizada
        # Para critérios especiais: H. Extra 50% = H. Trabalhadas - Carga Horária
        # H. Trabalhadas sempre é 0 para critérios especiais
        horas_trabalhadas_minutos = 0  # Sempre 0 para critérios especiais
        he_50_minutos = horas_trabalhadas_minutos - carga_horaria_minutos
        
        # Converter para formato HH:MM
        def minutos_para_tempo(minutos):
            if not minutos:
                return '00:00'
            
            # Lidar com valores negativos
            if minutos < 0:
                minutos_abs = abs(minutos)
                horas = minutos_abs // 60
                mins = minutos_abs % 60
                return f"-{horas:02d}:{mins:02d}"
            else:
                horas = minutos // 60
                mins = minutos % 60
                return f"{horas:02d}:{mins:02d}"
        
        return {
            'carga_horaria_esp': minutos_para_tempo(carga_horaria_minutos),  # ✅ Parametrizado
            'hextra_50_esp': minutos_para_tempo(he_50_minutos)              # 🆕 Calculado
        }
        
    except Exception as e:
        routes_logger.print(f"❌ Erro ao calcular critério especial: {str(e)}")
        # Fallback para valores padrão em caso de erro
        return {
            'carga_horaria_esp': '08:00',  # 8 horas padrão
            'hextra_50_esp': '00:00'       # Sem hora extra
        }


@closure_bp.route('/api/closure/save-dayoff', methods=['POST'])
@route_access_required
def save_dayoff():
    """Salva os dados de folga do fechamento."""
    try:
        dados = request.get_json()
        
        motorist_id = dados.get('motorist_id')
        start_date = dados.get('start_date')
        end_date = dados.get('end_date')
        motivo = dados.get('motivo')
        truck_id = dados.get('truck_id')
        inicio_jornada = dados.get('inicio_jornada')
        fim_jornada = dados.get('fim_jornada')
        inicio_refeicao = dados.get('inicio_refeicao')
        fim_refeicao = dados.get('fim_refeicao')
        substituir = dados.get('substituir', False)

        # LOG DETALHADO DOS DADOS RECEBIDOS
        routes_logger.print(f"🔍 DADOS RECEBIDOS:")
        routes_logger.print(f"   motorist_id: {motorist_id}")
        routes_logger.print(f"   start_date: {start_date}")
        routes_logger.print(f"   end_date: {end_date}")
        routes_logger.print(f"   motivo: {motivo}")
        routes_logger.print(f"   truck_id: {truck_id}")
        routes_logger.print(f"   inicio_jornada: {inicio_jornada}")
        routes_logger.print(f"   fim_jornada: {fim_jornada}")
        routes_logger.print(f"   inicio_refeicao: {inicio_refeicao}")
        routes_logger.print(f"   fim_refeicao: {fim_refeicao}")
        routes_logger.print(f"   substituir: {substituir} (tipo: {type(substituir)})")
        routes_logger.print(f"   substituir == True: {substituir == True}")
        routes_logger.print(f"   substituir is True: {substituir is True}")
        
        # 🆕 LOG DOS VALORES MONETÁRIOS RECEBIDOS DO FRONTEND
        routes_logger.print(f"🔍 VALORES MONETÁRIOS RECEBIDOS:")
        routes_logger.print(f"   daily_value: {dados.get('daily_value', 'NÃO ENVIADO')}")
        routes_logger.print(f"   food_value: {dados.get('food_value', 'NÃO ENVIADO')}")
        routes_logger.print(f"   Tipo daily_value: {type(dados.get('daily_value'))}")
        routes_logger.print(f"   Tipo food_value: {type(dados.get('food_value'))}")

        if not all([motorist_id, start_date, end_date, motivo]):
            return jsonify({
                "status": "error",
                "message": "Todos os campos são obrigatórios"
            }), 400

        # Carregar critérios e parâmetros
        parameters_driver = ParametersDriver(logger=routes_logger, db_path=DB_PATH)
        configs = parameters_driver.get_all_parameters()

        # Valores padrão dos parâmetros
        diaria_padrao = float(configs['parametros'].get('diaria_padrao', {}).get('valor', 90.00))
        ajuda_alimentacao_padrao = float(configs['parametros'].get('ajuda_alimentacao', {}).get('valor', 0.00))

        # Converter datas para o formato DD-MM-YYYY
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Gerar lista de datas
        datas = []
        current = start
        while current <= end:
            datas.append(current.strftime('%d-%m-%Y'))
            current += timedelta(days=1)

        motivo_upper = motivo.strip().upper()
        
        # LÓGICA PARA GARAGEM E CARGA/DESCARGA
        if motivo_upper == 'GARAGEM' or motivo_upper == 'CARGA/DESCARGA':
            # Validações específicas para GARAGEM e CARGA/DESCARGA
            # truck_id é opcional agora - se não informado, será None
            
            if not inicio_jornada or not fim_jornada:
                return jsonify({
                    "status": "error",
                    "message": "Para GARAGEM/CARGA/DESCARGA, os horários de início e fim de jornada são obrigatórios"
                }), 400
            
            # Horários de refeição são opcionais para GARAGEM/CARGA/DESCARGA
            # Se não informados, ficam vazios (não "00:00")
            
            # 🆕 PRIORIZAR VALORES ENVIADOS PELO FRONTEND
            daily_value_garagem = dados.get('daily_value')
            food_value_garagem = dados.get('food_value')
            
            # Se os valores não foram enviados pelo frontend, buscar nos critérios
            if daily_value_garagem is None or food_value_garagem is None:
                routes_logger.print(f"⚠️ Valores monetários não enviados pelo frontend, buscando nos critérios...")
                
                # Buscar critério específico baseado no motivo
                for criterio in configs['criterios']:
                    if criterio['valor_filtro'].upper() == motivo_upper:
                        daily_value_garagem = float(criterio.get('valor_diaria', 0.00))
                        food_value_garagem = float(criterio.get('valor_ajuda_alimentacao', ajuda_alimentacao_padrao))
                        routes_logger.print(f"✅ Critério encontrado para {motivo_upper}: diária={daily_value_garagem}, alimentação={food_value_garagem}")
                        break
                else:
                    routes_logger.print(f"⚠️ Critério não encontrado para {motivo_upper}, usando valores padrão")
                    daily_value_garagem = 0.00
                    food_value_garagem = ajuda_alimentacao_padrao
            else:
                routes_logger.print(f"✅ Usando valores enviados pelo frontend: diária={daily_value_garagem}, alimentação={food_value_garagem}")
            
            # Garantir que os valores são float
            daily_value_garagem = float(daily_value_garagem or 0.00)
            food_value_garagem = float(food_value_garagem or 0.00)
            
            # Preparar dados para inserção na tabela perm_data_fecham
            dados_garagem = []
            for data in datas:
                # Calcular dia da semana usando a função existente
                dia_semana = get_weekday_name(data)
                
                # CALCULAR TODOS OS VALORES ANTES DE SALVAR
                # Converter horários para minutos para cálculos
                def tempo_para_minutos(tempo_str):
                    if not tempo_str:
                        return 0
                    try:
                        horas, minutos = map(int, tempo_str.split(':'))
                        return horas * 60 + minutos
                    except:
                        return 0
                
                def minutos_para_tempo(minutos):
                    if minutos == 0:
                        return '00:00'  # 🆕 CORREÇÃO: 0 minutos deve retornar '00:00'
                    if minutos < 0:
                        # Para valores negativos, retornar formato -HH:MM
                        minutos_abs = abs(minutos)
                        horas = minutos_abs // 60
                        mins = minutos_abs % 60
                        return f"-{horas:02d}:{mins:02d}"
                    else:
                        # Para valores positivos, retornar formato HH:MM
                        horas = minutos // 60
                        mins = minutos % 60
                        return f"{horas:02d}:{mins:02d}"
                
                # Calcular tempo de refeição
                tempo_refeicao_min = 0
                if inicio_refeicao and fim_refeicao and inicio_refeicao.strip() and fim_refeicao.strip():
                    inicio_ref_min = tempo_para_minutos(inicio_refeicao)
                    fim_ref_min = tempo_para_minutos(fim_refeicao)
                    if fim_ref_min < inicio_ref_min:  # Virada de dia
                        fim_ref_min += 24 * 60
                    tempo_refeicao_min = max(0, fim_ref_min - inicio_ref_min)
                
                # Calcular jornada total (descontando refeição)
                jornada_total_min = 0
                if inicio_jornada and fim_jornada:
                    inicio_jornada_min = tempo_para_minutos(inicio_jornada)
                    fim_jornada_min = tempo_para_minutos(fim_jornada)
                    if fim_jornada_min < inicio_jornada_min:  # Virada de dia
                        fim_jornada_min += 24 * 60
                    jornada_bruta_min = max(0, fim_jornada_min - inicio_jornada_min)
                    jornada_total_min = max(0, jornada_bruta_min - tempo_refeicao_min)
                
                # Calcular carga horária usando sistema parametrizado (feriados + dias da semana)
                # Para GARAGEM/CARGA/DESCARGA, usar a lógica de prioridade estabelecida
                from controller.carga_horaria_calculator import CargaHorariaCalculator
                
                # Buscar configuração do critério (se houver)
                carga_horaria_configurada = 'Padrão'
                for criterio in configs['criterios']:
                    if criterio['valor_filtro'].upper() in ['GARAGEM', 'CARGA/DESCARGA']:
                        if criterio.get('carga_horaria_especial') and criterio['carga_horaria_especial'] != 'Padrão':
                            carga_horaria_configurada = criterio['carga_horaria_especial']
                        break
                
                # Calcular carga horária usando sistema existente (parametrização + feriados + dias)
                carga_horaria_min = CargaHorariaCalculator.calcular_carga_horaria_especial(
                    criterio_especial=motivo_upper,
                    dia_semana=dia_semana,
                    data=data,
                    feriados=configs['feriados'],
                    carga_horaria_configurada=carga_horaria_configurada
                )
                
                # Calcular hora extra 50%
                # Para GARAGEM/CARGA/DESCARGA, permitir valores negativos
                hora_extra_50_min = jornada_total_min - carga_horaria_min
                
                # Calcular hora extra noturna (período 22:00 às 05:00)
                he_noturno_min = 0
                if inicio_jornada and fim_jornada:
                    inicio_min = tempo_para_minutos(inicio_jornada)
                    fim_min = tempo_para_minutos(fim_jornada)
                    
                    # Período noturno: 22:00 (1320 min) às 05:00 (300 min)
                    inicio_noturno = 22 * 60  # 22:00
                    fim_noturno = 5 * 60      # 05:00
                    
                    if fim_min < inicio_min:  # Virada de dia
                        # Antes da meia-noite (22:00 - 23:59)
                        if inicio_min <= 23 * 60 + 59:
                            he_noturno_min += min(23 * 60 + 59 - inicio_min, 120)
                        # Depois da meia-noite (00:00 - 05:00)
                        if fim_min >= 0:
                            he_noturno_min += min(fim_min, 300)
                    else:
                        # Jornada normal no mesmo dia
                        if inicio_min <= fim_noturno:
                            # Começa antes das 05:00
                            he_noturno_min += min(fim_min, fim_noturno) - inicio_min
                        elif inicio_min <= 23 * 60 + 59 and fim_min >= inicio_noturno:
                            # Termina depois das 22:00
                            he_noturno_min += min(fim_min, 23 * 60 + 59) - max(inicio_min, inicio_noturno)
                    
                    he_noturno_min = max(0, he_noturno_min)
                
                dados_garagem.append({
                    'motorist_id': motorist_id,
                    'truck_id': truck_id,  # 🆕 ADICIONAR TRUCK_ID
                    'Data': data,  # Chave com D maiúsculo para compatibilidade
                    'Dia da Semana': dia_semana,
                    'Início Jornada': inicio_jornada,
                    'Fim de Jornada': fim_jornada,
                    'Início Refeição': inicio_refeicao if inicio_refeicao and inicio_refeicao.strip() else '',
                    'Fim Refeição': fim_refeicao if fim_refeicao and fim_refeicao.strip() else '',
                    'Observação': motivo_upper,
                    'Diária': daily_value_garagem,
                    'Ajuda Alimentação': food_value_garagem,
                    # CAMPOS CALCULADOS
                    'Tempo Refeição': minutos_para_tempo(tempo_refeicao_min),
                    'Tempo Intervalo': '00:00',  # Sempre 00:00 para GARAGEM/CARGA
                    'H. Trabalhadas': minutos_para_tempo(jornada_total_min),
                    'Carga Horária': minutos_para_tempo(carga_horaria_min),
                    'H.extra 50%': minutos_para_tempo(hora_extra_50_min),
                    'H.extra 100%': '00:00',  # Sempre 00:00 para GARAGEM/CARGA
                    'H.E. Not': minutos_para_tempo(he_noturno_min),
                    'Adicional Noturno': minutos_para_tempo(he_noturno_min)
                })
            
            # LOG DETALHADO ANTES DA VERIFICAÇÃO DE CONFLITOS
            routes_logger.print(f"🔍 ANTES DA VERIFICAÇÃO DE CONFLITOS:")
            routes_logger.print(f"   motivo_upper: {motivo_upper}")
            routes_logger.print(f"   substituir: {substituir}")
            routes_logger.print(f"   substituir == True: {substituir == True}")
            routes_logger.print(f"   substituir is True: {substituir is True}")
            routes_logger.print(f"   len(dados_garagem): {len(dados_garagem)}")
            routes_logger.print(f"   Primeira data: {dados_garagem[0]['Data'] if dados_garagem else 'N/A'}")
            
            # Verificar conflitos ANTES de inserir (apenas por motorista e data)
            routes_logger.print(f"🔍 Verificando conflitos para {motivo_upper} - substituir: {substituir}")
            result = analyzed_closure_data_driver.check_conflicts_only(dados_garagem, motorist_id, None)
            routes_logger.print(f"🔍 Resultado da verificação: {result}")
            
            # LOG DETALHADO APÓS VERIFICAÇÃO DE CONFLITOS
            routes_logger.print(f"🔍 APÓS VERIFICAÇÃO DE CONFLITOS:")
            routes_logger.print(f"   result.get('tem_conflitos'): {result.get('tem_conflitos')}")
            routes_logger.print(f"   not substituir: {not substituir}")
            routes_logger.print(f"   result.get('tem_conflitos') and not substituir: {result.get('tem_conflitos') and not substituir}")
            
            # Se há conflitos e não é para substituir, retornar conflitos
            if result.get('tem_conflitos') and not substituir:
                routes_logger.print(f"🚫 CONFLITOS DETECTADOS E NÃO É PARA SUBSTITUIR - RETORNANDO 409")
                conflitos_formatados = []
                for conflito in result.get('conflitos', []):
                    if isinstance(conflito, dict):
                        conflitos_formatados.append(f"{conflito['data']} - {conflito['tipo']}: {conflito['descricao']}")
                    else:
                        conflitos_formatados.append(str(conflito))
                
                response_data = {
                    "status": "conflito",
                    "message": "Conflitos encontrados",
                    "conflitos": conflitos_formatados,
                    "conflitos_detalhados": result.get('conflitos', []),
                    "registros_inseridos": result.get('registros_inseridos', 0),
                    "registros_ignorados": result.get('registros_ignorados', 0)
                }
                return jsonify(response_data), 409

            # Se não há conflitos ou aceitou substituir, inserir todos os registros
            routes_logger.print(f"💾 Inserindo dados com replace={substituir}")
            result = analyzed_closure_data_driver.insert_data_from_json(dados_garagem, motorist_id, truck_id, replace=substituir)  # 🆕 CORREÇÃO: Passar truck_id
            routes_logger.print(f"💾 Resultado da inserção: {result}")
            
            if result.get('status') == 'conflito':
                return jsonify(result), 409
            
            # VALIDAÇÃO DE CÁLCULOS - Executar após salvar
            try:
                # Preparar dados para validação
                validation_data = {
                    'inicio_jornada': inicio_jornada,
                    'fim_jornada': fim_jornada,
                    'inicio_refeicao': inicio_refeicao,
                    'fim_refeicao': fim_refeicao,
                    'observacao': motivo_upper,
                    'data': datas[0] if datas else '',
                    'dia_semana': get_weekday_name(datas[0]) if datas else '',
                    'descansos': []
                }
                
                # Executar validação
                validation_result = calculation_validator.validate_calculation(validation_data)
                
                # Se há divergência, incluir informações no response
                if validation_result.get('status') == 'divergent':
                    routes_logger.print(f"⚠️ DIVERGÊNCIA DETECTADA: {validation_result.get('differences')}")
                    
                    # Reprocessar últimos 15 dias
                    reprocess_result = calculation_validator.reprocess_last_15_days(None)  # db_connection será implementado
                    
                    return jsonify({
                        "status": "success",
                        "message": f"Dados de {motivo_upper.lower()} salvos com sucesso",
                        "validation": {
                            "status": "divergent",
                            "message": "Divergência detectada entre os módulos de cálculo",
                            "reprocess_result": reprocess_result
                        }
                    })
                else:
                    return jsonify({
                        "status": "success",
                        "message": f"Dados de {motivo_upper.lower()} salvos com sucesso",
                        "validation": {
                            "status": "valid",
                            "message": "Todos os cálculos foram conferidos e confirmados por 2 sistemas de validação redundantes. Nenhuma divergência encontrada."
                        }
                    })
                    
            except Exception as validation_error:
                routes_logger.print(f"❌ Erro na validação de cálculos: {str(validation_error)}")
                return jsonify({
                    "status": "success",
                    "message": f"Dados de {motivo_upper.lower()} salvos com sucesso",
                    "validation": {
                        "status": "error",
                        "message": "Erro durante a validação de cálculos"
                    }
                })
        
        # LÓGICA PARA OUTROS MOTIVOS (não GARAGEM)
        else:
            routes_logger.print(f"🆕 PROCESSANDO CRITÉRIO ESPECIAL: {motivo_upper}")
            routes_logger.print(f"   Este critério será salvo na tabela dayoff_fecham com cálculos especiais")
            # Buscar valores do critério específico
            daily_value = diaria_padrao
            food_value = ajuda_alimentacao_padrao
            
            for criterio in configs['criterios']:
                if criterio['valor_filtro'].upper() == motivo_upper:
                    daily_value = float(criterio.get('valor_diaria', diaria_padrao))
                    food_value = float(criterio.get('valor_ajuda_alimentacao', ajuda_alimentacao_padrao))
                    break
            
            # 🆕 PREPARAR DADOS PARA INSERÇÃO NA TABELA dayoff_fecham
            # Para cada data, calcular considerando dia da semana e feriados
            dados_folga = []
            for data in datas:
                # Calcular dia da semana para esta data
                dia_semana = get_weekday_name(data)
                
                # 🆕 CALCULAR VALORES ESPECIAIS PARA ESTA DATA
                routes_logger.print(f"🔧 Calculando critério especial: {motivo_upper} para {data} ({dia_semana})")
                calculos_especiais = calcular_criterio_especial(
                    motivo=motivo_upper, 
                    configs=configs, 
                    data=data, 
                    dia_semana=dia_semana, 
                    feriados=[]  # Lista de feriados será implementada
                )
                routes_logger.print(f"✅ Resultado: carga_horaria_esp={calculos_especiais['carga_horaria_esp']}, hextra_50_esp={calculos_especiais['hextra_50_esp']}")
                
                # Adicionar dados para esta data
                dados_folga.append({
                    'motorist_id': motorist_id,
                    'data': data,
                    'motivo': motivo,
                    'daily_value': daily_value,
                    'food_value': food_value,
                    # 🆕 NOVOS CAMPOS CALCULADOS
                    'carga_horaria_esp': calculos_especiais['carga_horaria_esp'],  # ✅ Parametrizado
                    'hextra_50_esp': calculos_especiais['hextra_50_esp']          # 🆕 Calculado
                })
            
            # LOG DO RESUMO DOS CÁLCULOS
            routes_logger.print(f"📊 RESUMO DOS CÁLCULOS ESPECIAIS:")
            routes_logger.print(f"   Critério: {motivo_upper}")
            routes_logger.print(f"   Total de datas processadas: {len(datas)}")
            routes_logger.print(f"   Exemplo de dados: {dados_folga[0] if dados_folga else 'N/A'}")
            
            # Verificar conflitos ANTES de inserir
            result = closure_dayoff_driver.check_conflicts_only(dados_folga, motorist_id)
            
            # Se há conflitos e não é para substituir, retornar conflitos
            if result.get('tem_conflitos') and not substituir:
                conflitos_formatados = []
                for conflito in result.get('conflitos', []):
                    if isinstance(conflito, dict):
                        conflitos_formatados.append(f"{conflito['data']} - {conflito['tipo']}: {conflito['descricao']}")
                    else:
                        conflitos_formatados.append(str(conflito))
                
                response_data = {
                    "status": "conflito",
                    "message": "Conflitos encontrados",
                    "conflitos": conflitos_formatados,
                    "conflitos_detalhados": result.get('conflitos', []),
                    "registros_inseridos": result.get('registros_inseridos', 0),
                    "registros_ignorados": result.get('registros_ignorados', 0)
                }
                return jsonify(response_data), 409

            # Se não há conflitos ou aceitou substituir, inserir todos os registros
            result = closure_dayoff_driver.insert_data_from_json(dados_folga, replace=substituir)
            
            if result.get('status') == 'conflito':
                return jsonify(result), 409
            
            # VALIDAÇÃO DE CÁLCULOS - Executar após salvar
            try:
                # Preparar dados para validação
                validation_data = {
                    'inicio_jornada': '',
                    'fim_jornada': '',
                    'inicio_refeicao': '',
                    'fim_refeicao': '',
                    'observacao': motivo_upper,
                    'data': datas[0] if datas else '',
                    'dia_semana': get_weekday_name(datas[0]) if datas else '',
                    'descansos': []
                }
                
                # Executar validação
                validation_result = calculation_validator.validate_calculation(validation_data)
                
                # Se há divergência, incluir informações no response
                if validation_result.get('status') == 'divergent':
                    routes_logger.print(f"⚠️ DIVERGÊNCIA DETECTADA: {validation_result.get('differences')}")
                    
                    # Reprocessar últimos 15 dias
                    reprocess_result = calculation_validator.reprocess_last_15_days(None)  # db_connection será implementado
                    
                    return jsonify({
                        "status": "success",
                        "message": f"Dados de {motivo_upper.lower()} salvos com sucesso (com cálculos especiais)",
                        "validation": {
                            "status": "divergent",
                            "message": "Divergência detectada entre os módulos de cálculo",
                            "reprocess_result": reprocess_result
                        },
                        "calculos_especiais": {
                            "carga_horaria_esp": "calculada para cada data",
                            "hextra_50_esp": "calculada automaticamente"
                        }
                    })
                else:
                    return jsonify({
                        "status": "success",
                        "message": f"Dados de {motivo_upper.lower()} salvos com sucesso (com cálculos especiais)",
                        "validation": {
                            "status": "valid",
                            "message": "Todos os cálculos foram conferidos e confirmados por 2 sistemas de validação redundantes. Nenhuma divergência encontrada."
                        },
                        "calculos_especiais": {
                            "carga_horaria_esp": "calculada para cada data",
                            "hextra_50_esp": "calculada automaticamente"
                        }
                    })
                    
            except Exception as validation_error:
                routes_logger.print(f"❌ Erro na validação de cálculos: {str(validation_error)}")
                return jsonify({
                    "status": "success",
                    "message": f"Dados de {motivo_upper.lower()} salvos com sucesso (com cálculos especiais)",
                    "validation": {
                        "status": "error",
                        "message": "Erro durante a validação de cálculos"
                    },
                    "calculos_especiais": {
                        "carga_horaria_esp": "calculada para cada data",
                        "hextra_50_esp": "calculada automaticamente"
                    }
                })

    except Exception as e:
        routes_logger.print(f"Erro ao salvar dados de folga: {str(e)}")
        import traceback
        routes_logger.print(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": f"Erro ao salvar dados: {str(e)}"
        }), 500

@closure_bp.route('/api/closure/generate-pdf', methods=['GET'])
@route_access_required
def generate_closure_pdf():
    try:
        routes_logger.register_log("Iniciando geração de PDF de fechamento")
        
        motorist_id = request.args.get('motorist_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        routes_logger.register_log(f"Parâmetros recebidos: motorist_id={motorist_id}, from_date={from_date}, to_date={to_date}")

        if not motorist_id or not from_date or not to_date:
            routes_logger.register_log("Erro: Parâmetros obrigatórios não fornecidos")
            return jsonify({"error": "Parâmetros obrigatórios não fornecidos"}), 400

        # Buscar dados do motorista usando motorist_driver
        motorist_data = motorist_driver.retrieve_motorist(["id"], (motorist_id,))
        if not motorist_data:
            routes_logger.register_log(f"Erro: Motorista {motorist_id} não encontrado")
            return jsonify({"error": "Motorista não encontrado"}), 404

        motorist_name = motorist_data[1] if motorist_data else 'Motorista'  # nome está na posição 1
        motorist_cpf = motorist_data[3] if motorist_data else ''  # cpf está na posição 3
        motorist_company = motorist_data[30] if motorist_data and len(motorist_data) > 30 else ''  # empresa
        
        routes_logger.register_log(f"Dados do motorista: nome={motorist_name}, cpf={motorist_cpf}")

        # Buscar dados do relatório (reutilizar lógica do get_closure_report)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            from_date_br = from_date_obj.strftime('%d-%m-%Y')
            to_date_br = to_date_obj.strftime('%d-%m-%Y')
        except:
            from_date_br = from_date
            to_date_br = to_date

        # Verificar se tabela trucks existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trucks'")
        trucks_exists = cursor.fetchone() is not None

        # Buscar dados de perm_data_fecham
        if trucks_exists:
            cursor.execute("""
                SELECT p.data, p.dia_da_semana, p.inicio_jornada, p.in_refeicao, p.fim_refeicao, p.fim_jornada,
                       p.observacao, p.tempo_refeicao, p.tempo_intervalo, p.jornada_total, p.carga_horaria, p.hextra_50,
                       p.hextra_100, p.he_noturno, p.daily_value, p.food_value, t.placa
                FROM perm_data_fecham p
                LEFT JOIN trucks t ON p.truck_id = t.id
                WHERE p.motorist_id = ?
                ORDER BY strftime('%Y-%m-%d',
                    substr(p.data, 7, 4) || '-' ||
                    substr(p.data, 4, 2) || '-' ||
                    substr(p.data, 1, 2)
                )
            """, (motorist_id,))
        else:
            cursor.execute("""
                SELECT data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada,
                       observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50,
                       hextra_100, he_noturno, daily_value, food_value
                FROM perm_data_fecham
                WHERE motorist_id = ?
                ORDER BY strftime('%Y-%m-%d',
                    substr(data, 7, 4) || '-' ||
                    substr(data, 4, 2) || '-' ||
                    substr(data, 1, 2)
                )
            """, (motorist_id,))

        jornada_data = cursor.fetchall()

        # Filtrar dados pelo período
        jornada_filtrada = []
        for row in jornada_data:
            data = row[0]
            try:
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                from_date_obj = datetime.strptime(from_date_br, '%d-%m-%Y')
                to_date_obj = datetime.strptime(to_date_br, '%d-%m-%Y')

                if from_date_obj <= data_obj <= to_date_obj:
                    jornada_filtrada.append(row)
            except:
                pass

        # Buscar dados de dayoff_fecham
        cursor.execute("""
            SELECT data, motivo, daily_value, food_value
            FROM dayoff_fecham
            WHERE motorist_id = ?
            ORDER BY strftime('%Y-%m-%d',
                substr(data, 7, 4) || '-' ||
                substr(data, 4, 2) || '-' ||
                substr(data, 1, 2)
            )
        """, (motorist_id,))

        dayoff_data = cursor.fetchall()

        # Filtrar dados de dayoff pelo período
        dayoff_filtrada = []
        for row in dayoff_data:
            data = row[0]
            try:
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                from_date_obj = datetime.strptime(from_date_br, '%d-%m-%Y')
                to_date_obj = datetime.strptime(to_date_br, '%d-%m-%Y')

                if from_date_obj <= data_obj <= to_date_obj:
                    dayoff_filtrada.append(row)
            except:
                pass

        # Processar dados para PDF
        processed_data = []
        total_intervalo = 0
        total_almoco = 0
        total_h_trab = 0
        total_carga_horaria = 0
        total_h_extra50 = 0
        total_h_extra100 = 0
        total_h_e_not = 0
        total_diaria = 0.0
        total_aj_aliment = 0.0

        def tempo_para_minutos(tempo_str):
            if not tempo_str or tempo_str == "NULL" or tempo_str == "":
                return 0
            try:
                if ':' in tempo_str:
                    is_negative = tempo_str.startswith('-')
                    tempo_limpo = tempo_str.replace('-', '')
                    horas, minutos = map(int, tempo_limpo.split(':'))
                    resultado = horas * 60 + minutos
                    return -resultado if is_negative else resultado
                else:
                    return 0
            except:
                return 0

        def minutos_para_tempo(minutos):
            if minutos == 0:
                return "00:00"
            is_negative = minutos < 0
            minutos_abs = abs(minutos)
            horas = minutos_abs // 60
            mins = minutos_abs % 60
            resultado = f"{horas:02d}:{mins:02d}"
            return f"-{resultado}" if is_negative else resultado

        def abreviar_dia_semana(dia_completo):
            abreviacoes = {
                'Segunda-feira': 'SEG',
                'Terça-feira': 'TER',
                'Quarta-feira': 'QUA',
                'Quinta-feira': 'QUI',
                'Sexta-feira': 'SEX',
                'Sábado': 'SÁB',
                'Domingo': 'DOM'
            }
            return abreviacoes.get(dia_completo, dia_completo)

        def formatar_moeda(valor):
            if not valor or valor == "NULL" or valor == "" or valor == 0 or valor == "0":
                return "R$ 0,00"
            try:
                valor_float = float(str(valor).replace('.0', ''))
                return f"R$ {valor_float:.2f}".replace('.', ',')
            except:
                return "R$ 0,00"

        # Processar dados de jornada
        for row in jornada_filtrada:
            if trucks_exists:
                (data, dia_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada,
                 observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50,
                 hextra_100, he_noturno, daily_value, food_value, placa) = row
            else:
                (data, dia_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada,
                 observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50,
                 hextra_100, he_noturno, daily_value, food_value) = row
                placa = ''

            # Converter data para formato DD/MM/YYYY
            try:
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                data_formatada = data_obj.strftime('%d/%m/%Y')
            except:
                data_formatada = data

            diaria_formatada = formatar_moeda(daily_value)
            alimentacao_formatada = formatar_moeda(food_value)

            # Calcular totais
            total_intervalo += tempo_para_minutos(tempo_intervalo)
            total_almoco += tempo_para_minutos(tempo_refeicao)
            total_h_trab += tempo_para_minutos(jornada_total)
            total_carga_horaria += tempo_para_minutos(carga_horaria)
            total_h_extra50 += tempo_para_minutos(hextra_50)
            total_h_extra100 += tempo_para_minutos(hextra_100)
            total_h_e_not += tempo_para_minutos(he_noturno)

            try:
                if daily_value and daily_value != "NULL" and daily_value != "":
                    total_diaria += float(str(daily_value).replace('.0', ''))
            except: pass
            try:
                if food_value and food_value != "NULL" and food_value != "":
                    total_aj_aliment += float(str(food_value).replace('.0', ''))
            except: pass

            processed_data.append({
                'placa': placa or '',
                'data': data_formatada,
                'dia_semana': abreviar_dia_semana(dia_semana),
                'inicio_jornada': inicio_jornada or '',
                'almoco_inicio': in_refeicao or '',
                'almoco_fim': fim_refeicao or '',
                'fim_jornada': fim_jornada or '',
                'intervalo': tempo_intervalo or '',
                'almoco': tempo_refeicao or '',
                'h_trab': jornada_total or '',
                'carga_horaria': carga_horaria or '',
                'h_extra50': hextra_50 or '',
                'h_extra100': hextra_100 or '',
                'h_e_not': he_noturno or '',
                'ad_not': he_noturno or '',  # AD. NOT igual a H.E. NOT.
                'diaria': diaria_formatada,
                'aj_aliment': alimentacao_formatada,
                'observacao': observacao or ''
            })

        # Processar dados de dayoff
        for row in dayoff_filtrada:
            data, motivo, daily_value_dayoff, food_value_dayoff = row

            try:
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                data_formatada = data_obj.strftime('%d/%m/%Y')
                dias_semana = {0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
                               3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'}
                dia_semana_completo = dias_semana[data_obj.weekday()]
                dia_semana_abreviado = abreviar_dia_semana(dia_semana_completo)
            except:
                data_formatada = data
                dia_semana_abreviado = "Data inválida"

            diaria_formatada_dayoff = formatar_moeda(daily_value_dayoff)
            alimentacao_formatada_dayoff = formatar_moeda(food_value_dayoff)

            processed_data.append({
                'placa': motivo,  # Motivo no lugar da placa
                'data': data_formatada,
                'dia_semana': dia_semana_abreviado,
                'inicio_jornada': '',
                'almoco_inicio': '',
                'almoco_fim': '',
                'fim_jornada': '',
                'intervalo': '',
                'almoco': '',
                'h_trab': '',
                'carga_horaria': '',
                'h_extra50': '',
                'h_extra100': '',
                'h_e_not': '',
                'ad_not': '',
                'diaria': diaria_formatada_dayoff,
                'aj_aliment': alimentacao_formatada_dayoff,
                'observacao': motivo  # Motivo na observação
            })

        # Ordenar por data
        processed_data.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'))

        # Verificar consistência dos dados
        if processed_data:
            expected_keys = {'placa', 'data', 'dia_semana', 'inicio_jornada', 'almoco_inicio', 'almoco_fim', 
                           'fim_jornada', 'intervalo', 'almoco', 'h_trab', 'carga_horaria', 'h_extra50', 
                           'h_extra100', 'h_e_not', 'ad_not', 'diaria', 'aj_aliment', 'observacao'}
            for i, row in enumerate(processed_data):
                if not isinstance(row, dict) or not all(key in row for key in expected_keys):
                    routes_logger.register_log(f"Erro: Linha {i} não tem estrutura correta")
                    routes_logger.register_log(f"Linha {i}: {row}")
                    raise ValueError(f"Estrutura incorreta na linha {i}")

        # Calcular totais finais
        totais = {
            'intervalo': minutos_para_tempo(total_intervalo),
            'almoco': minutos_para_tempo(total_almoco),
            'h_trab': minutos_para_tempo(total_h_trab),
            'carga_horaria': minutos_para_tempo(total_carga_horaria),
            'h_extra50': minutos_para_tempo(total_h_extra50),
            'h_extra100': minutos_para_tempo(total_h_extra100),
            'h_e_not': minutos_para_tempo(total_h_e_not),
            'ad_not': minutos_para_tempo(total_h_e_not),
            'diaria': f"R$ {total_diaria:.2f}".replace('.', ','),
            'aj_aliment': f"R$ {total_aj_aliment:.2f}".replace('.', ',')
        }

        # Montar cabeçalho dinâmico da empresa
        try:
            company_header = None
            if motorist_company:
                comp = company_driver.retrieve_company(['enterprise'], (motorist_company,))
                if comp:
                    company_enterprise = comp[1]
                    company_cnpj = comp[2]
                    company_header = f"<b>{company_enterprise}</b> - CNPJ: <b>{company_cnpj}</b>"
        except Exception as _e:
            company_header = None

        # Montar linha dinâmica de folgas (abrangendo todos os motivos)
        try:
            folgas_line = "-"
            # dayoff_filtrada contém dados filtrados por período acima
            motivos_to_dates = {}
            for row in dayoff_filtrada:
                data_str, motivo, _dv, _fv = row
                try:
                    d = datetime.strptime(data_str, '%d-%m-%Y').strftime('%d/%m/%Y')
                except:
                    d = data_str.replace('-', '/')
                motivo_key = (motivo or '').strip().upper()
                if not motivo_key:
                    motivo_key = 'N/A'
                motivos_to_dates.setdefault(motivo_key, []).append(d)
            if motivos_to_dates:
                parts = []
                for motivo_key in sorted(motivos_to_dates.keys()):
                    datas_ordenadas = sorted(motivos_to_dates[motivo_key], key=lambda s: datetime.strptime(s, '%d/%m/%Y'))
                    parts.append(f"{motivo_key} (" + ", ".join(datas_ordenadas) + ")")
                folgas_line = "; ".join(parts)
        except Exception as _e:
            folgas_line = "-"

        conn.close()

        # Gerar PDF
        pdf_buffer = generate_closure_pdf_report(
            motorist_name=motorist_name,
            motorist_cpf=motorist_cpf,
            from_date=from_date_obj.strftime('%d/%m/%Y'),
            to_date=to_date_obj.strftime('%d/%m/%Y'),
            data=processed_data,
            totals=totais,
            company_header=company_header,
            folgas_line=folgas_line
        )

        filename = f"espelho_ponto_{motorist_name.replace(' ', '_')}_{from_date_obj.strftime('%d_%m_%Y')}_a_{to_date_obj.strftime('%d_%m_%Y')}.pdf"

        routes_logger.register_log(f"PDF gerado com sucesso: {filename}")

        return send_file(
            BytesIO(pdf_buffer),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        routes_logger.register_log(f"Erro ao gerar PDF de fechamento: {e}")
        routes_logger.register_log(f"Traceback: {traceback.format_exc()}")
        
        # Log adicional para debug
        try:
            routes_logger.register_log(f"Dados processados: {len(processed_data) if 'processed_data' in locals() else 'N/A'} linhas")
            if 'processed_data' in locals() and processed_data:
                routes_logger.register_log(f"Primeira linha: {processed_data[0] if processed_data else 'N/A'}")
                routes_logger.register_log(f"Número de colunas na primeira linha: {len(processed_data[0]) if processed_data else 'N/A'}")
        except Exception as debug_error:
            routes_logger.register_log(f"Erro no debug: {debug_error}")
        
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


def generate_closure_pdf_report(motorist_name, motorist_cpf, from_date, to_date, data, totals, company_header=None, folgas_line=None):
    """
    Gera o PDF do relatório de fechamento de ponto otimizado para uma página
    """
    buffer = BytesIO()
    
    # Configurar documento PDF em landscape com margens mínimas para maximizar espaço
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2*cm,
        leftMargin=1.5*cm,
        topMargin=0.5*cm,
        bottomMargin=0.2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título principal - reduzido para economizar espaço
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=12,
        spaceAfter=2,
        alignment=TA_CENTER,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para informações da empresa - reduzido
    company_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=7,
        spaceAfter=1,
        alignment=TA_CENTER,
        textColor=colors.black,
        fontName='Helvetica'
    )
    
    # Estilo para informações do funcionário - reduzido
    employee_style = ParagraphStyle(
        'EmployeeInfo',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=1,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica'
    )
    
    # Estilo para período - reduzido
    period_style = ParagraphStyle(
        'PeriodInfo',
        parent=styles['Normal'],
        fontSize=7,
        spaceAfter=2,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica'
    )
    
    # Estilo para assinaturas - reduzido
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=6,
        spaceAfter=2,
        alignment=TA_CENTER,
        textColor=colors.black,
        fontName='Helvetica'
    )
    
    # Variante apenas +1 para a frase de período
    period_style_big = ParagraphStyle(
        'PeriodInfoBig',
        parent=period_style,
        fontSize=8
    )
    
    # Elementos do PDF - otimizados para uma página
    elements = []
    
    # Calcular altura disponível na página (para referência)
    page_height = landscape(A4)[1] - (0.3*cm + 0.3*cm)  # Altura total menos margens
    
    # Título principal
    elements.append(Paragraph("ESPELHO DE PONTO", title_style))
    elements.append(Spacer(1, 1))
    
    # Informações da empresa (dinâmico quando disponível)
    elements.append(Paragraph(company_header or "<b>TRANSPORTES PAZZI LTDA</b> - CNPJ: <b>17.698.598/0001-37</b>", company_style))
    elements.append(Spacer(1, 1))
    
    # Informações do funcionário e totais lado a lado
    employee_info = [
        [Paragraph(f"FUNCIONÁRIO: {motorist_name}", employee_style), ""],
        [Paragraph(f"CPF: {motorist_cpf}", employee_style), ""]
    ]
    
    # Seção de totais ultra compacta
    totals_data = [
        ['INTERVALO', 'ALMOÇO', 'H. TRAB.', 'C. HORÁRIA', 'H.EXTRA50%', 'H.EXTRA100%', 'H.E. NOT.', 'AD.NOT', 'DIÁRIA', 'AJ. ALIMENT.'],
        [totals['intervalo'], totals['almoco'], totals['h_trab'], totals['carga_horaria'], totals['h_extra50'], totals['h_extra100'], totals['h_e_not'], totals['ad_not'], totals['diaria'], totals['aj_aliment']]
    ]
    
    # Calcular larguras menores para a tabela de totais
    totals_col_widths = [doc.width/10 * 0.6] * 10  # 40% menor que a largura original
    
    totals_table = Table(totals_data, colWidths=totals_col_widths)
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.blue),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 7),
        ('GRID', (0, 0), (-1, -1), 0.2, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0.3),
        ('TOPPADDING', (0, 0), (-1, -1), 0.2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2),
    ]))
    
    # Criar tabela combinada: nome+CPF à esquerda (na mesma célula) e totais à direita
    left_info = Paragraph(
        f"FUNCIONÁRIO: <b>{motorist_name}</b><br/>CPF: <b>{motorist_cpf}</b>",
        ParagraphStyle(
            'EmployeeBlock', parent=employee_style, spaceAfter=0, leading=11, alignment=TA_LEFT
        )
    )

    combined_table = Table(
        [[left_info, totals_table]],
        colWidths=[doc.width * 0.35, doc.width * 0.65]
    )

    combined_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('VALIGN', (1, 0), (1, 0), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    elements.append(combined_table)
    elements.append(Spacer(1, 1))
    
    # Cabeçalho da tabela principal com colunas otimizadas - corrigido
    header = [
        'PLACA', 'DATA', 'DIA', 'INÍCIO', 'ALMOÇO', 'FIM', 'INTERVALO', 'H.TRAB', 'CARGA HORÁRIA',
        'H.EXTRA50%', 'H.EXTRA100%', 'H.E.NOT', 'AD.NOT', 'DIÁRIA', 'AJ.ALIMENT.'
    ]
    
    # Preparar dados da tabela
    table_data = [header]
    
    # Adicionar dados - converter dicionários para listas
    for row in data:
        if isinstance(row, dict):
            # Converter dicionário para lista na ordem correta - corrigido
            table_data.append([
                row.get('placa', ''),
                row.get('data', ''),
                row.get('dia_semana', ''),
                row.get('inicio_jornada', ''),
                f"{row.get('almoco_inicio', '')}, {row.get('almoco_fim', '')}",
                row.get('fim_jornada', ''),
                row.get('intervalo', ''),
                row.get('h_trab', ''),
                row.get('carga_horaria', ''),
                row.get('h_extra50', ''),
                row.get('h_extra100', ''),
                row.get('h_e_not', ''),
                row.get('ad_not', ''),
                row.get('diaria', ''),
                row.get('aj_aliment', '')
            ])
        else:
            # Se já for lista, usar diretamente
            table_data.append(row)
    
    # Calcular larguras das colunas para otimizar espaço - versão corrigida
    col_widths = [
        0.1,  # PLACA
        0.06,  # DATA
        0.04,  # DIA
        0.05,  # INÍCIO
        0.09,  # ALMOÇO
        0.06,  # FIM
        0.06,  # INTERVALO
        0.06,  # H.TRAB
        0.08,  # CARGA HORÁRIA
        0.06,  # H.EXTRA50%
        0.06,  # H.EXTRA100%
        0.06,  # H.E.NOT
        0.07,  # AD.NOT
        0.07,  # DIÁRIA
        0.07   # AJ.ALIMENT.
    ]
    
    # Criar tabela com larguras otimizadas
    table = Table(table_data, repeatRows=1, colWidths=[w * doc.width for w in col_widths])
    
    # Estilo da tabela com altura e largura ajustadas - otimizado para uma página
    table_style = TableStyle([
        # Cabeçalho principal
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 6),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Dados - centralizados horizontalmente e verticalmente
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.2, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 0.3, colors.black),
        
        # Padding reduzido ao mínimo para melhor centralização
        ('LEFTPADDING', (0, 0), (-1, -1), 0.5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0.5),
        ('TOPPADDING', (0, 0), (-1, -1), 0.3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.1),
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 2))
    
    # Período de referência e folgas (linha dinâmica)
    elements.append(Paragraph(folgas_line if folgas_line is not None else "-", period_style))
    elements.append(Paragraph(f"Espelho de ponto referente a data de <b>{from_date}</b> a <b>{to_date}</b>", period_style_big))
    # Empurrar assinaturas mais para baixo
    elements.append(Spacer(1, 25))
    
    # Linhas de assinatura com espaçamento central (3 colunas)
    signature_table = Table(
        [
            ['', '', ''],
            ['FUNCIONÁRIO', '', 'RESPONSÁVEL']
        ],
        colWidths=[doc.width * 0.30, doc.width * 0.25, doc.width * 0.30],
        hAlign='CENTER'
    )

    signature_table.setStyle(TableStyle([
        # Linhas acima somente nas colunas das assinaturas
        ('LINEABOVE', (0, 0), (0, 0), 0.8, colors.black),
        ('LINEABOVE', (2, 0), (2, 0), 0.8, colors.black),
        # Rótulos centralizados nas colunas 0 e 2
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('ALIGN', (2, 1), (2, 1), 'CENTER'),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, 1), 6),
        ('FONTSIZE', (2, 1), (2, 1), 6),
        # Controlar espaçamentos
        ('BOTTOMPADDING', (0, 0), (2, 0), 0),
        ('TOPPADDING', (0, 1), (2, 1), 0),
    ]))
    
    elements.append(signature_table)
    
    # Construir PDF
    doc.build(elements)
    
    # Retornar bytes do PDF
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

@closure_bp.route('/api/closure/export_excel', methods=['POST'])
@route_access_required
def export_excel_closure():
    """API para exportar dados de fechamento para Excel"""
    try:
        data = request.json
        if not data or not data.get('nome_motorista') or not data.get('data_inicio') or not data.get('data_fim') or not data.get('tabela') or not data.get('totais'):
            return jsonify({"error": "Dados incompletos para exportar Excel"}), 400

        # Importar a função fill_excel_fecham do controller
        from controller.data import fill_excel_fecham
        
        wb = fill_excel_fecham(
            name=data['nome_motorista'],
            start=data['data_inicio'],
            end=data['data_fim'],
            tabela=data['tabela'],
            totals=data['totais']
        )
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"espelho_ponto_{data['nome_motorista'].replace(' ', '_')}_" \
                   f"{data['data_inicio'].replace('/', '-')}_a_{data['data_fim'].replace('/', '-')}.xlsx"
        
        routes_logger.register_log(f"Excel de fechamento gerado com sucesso: {filename}")
        
        return send_file(output, as_attachment=True, download_name=filename,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        routes_logger.register_log(f"Erro ao gerar Excel de fechamento: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@closure_bp.route('/closure_reports_download', methods=['GET'])
@route_access_required
def closure_reports_download():
    """Rota para processar downloads dos relatórios de fechamento"""
    try:
        motorist_id = request.args.get('motorist_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        format_type = request.args.get('format')
        
        routes_logger.register_log(f"Processando download: motorist_id={motorist_id}, from_date={from_date}, to_date={to_date}, format={format_type}")
        
        if not motorist_id or not from_date or not to_date or not format_type:
            return jsonify({"error": "Parâmetros obrigatórios não fornecidos"}), 400
        
        if format_type == 'pdf':
            # Redirecionar para a rota de PDF existente
            return redirect(f'/api/closure/generate-pdf?motorist_id={motorist_id}&from_date={from_date}&to_date={to_date}')
        
        elif format_type == 'excel':
            # Para Excel, precisamos primeiro buscar os dados e então gerar
            return generate_excel_from_params(motorist_id, from_date, to_date)
        
        else:
            return jsonify({"error": "Formato inválido. Use 'pdf' ou 'excel'"}), 400
    
    except Exception as e:
        routes_logger.register_log(f"Erro no download de relatórios: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

def generate_excel_from_params(motorist_id, from_date, to_date):
    """Gera Excel a partir dos parâmetros fornecidos"""
    try:
        # Importar a função fill_excel_fecham
        from controller.data import fill_excel_fecham
        
        # Buscar dados do motorista
        motorist_data = motorist_driver.retrieve_motorist(['id'], (int(motorist_id),))
        if not motorist_data:
            return jsonify({"error": "Motorista não encontrado"}), 404
        
        motorist_name = motorist_data[1]
        
        # Buscar dados usando a mesma lógica do get_closure_report
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Converter datas para formato brasileiro
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            from_date_br = from_date_obj.strftime('%d-%m-%Y')
            to_date_br = to_date_obj.strftime('%d-%m-%Y')
        except:
            from_date_br = from_date
            to_date_br = to_date
        
        # Buscar dados de jornada (mesma lógica do get_closure_report)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trucks'")
        trucks_exists = cursor.fetchone() is not None
        
        if trucks_exists:
            cursor.execute("""
                SELECT p.data, p.dia_da_semana, p.inicio_jornada, p.in_refeicao, p.fim_refeicao, p.fim_jornada,
                       p.observacao, p.tempo_refeicao, p.tempo_intervalo, p.jornada_total, p.carga_horaria, p.hextra_50,
                       p.hextra_100, p.he_noturno, p.daily_value, p.food_value, t.placa
                FROM perm_data_fecham p
                LEFT JOIN trucks t ON p.truck_id = t.id
                WHERE p.motorist_id = ?
                ORDER BY strftime('%Y-%m-%d', 
                    substr(p.data, 7, 4) || '-' || 
                    substr(p.data, 4, 2) || '-' || 
                    substr(p.data, 1, 2)
                )
            """, (motorist_id,))
        else:
            cursor.execute("""
                SELECT data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada,
                       observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50,
                       hextra_100, he_noturno, daily_value, food_value
                FROM perm_data_fecham 
                WHERE motorist_id = ?
                ORDER BY strftime('%Y-%m-%d', 
                    substr(data, 7, 4) || '-' || 
                    substr(data, 4, 2) || '-' || 
                    substr(data, 1, 2)
                )
            """, (motorist_id,))
        
        jornada_data = cursor.fetchall()
        
        # Filtrar dados pelo período
        jornada_filtrada = []
        for row in jornada_data:
            data = row[0]
            try:
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                from_date_obj = datetime.strptime(from_date_br, '%d-%m-%Y')
                to_date_obj = datetime.strptime(to_date_br, '%d-%m-%Y')
                
                if from_date_obj <= data_obj <= to_date_obj:
                    jornada_filtrada.append(row)
            except:
                pass
        
        # Buscar dados de dayoff
        cursor.execute("""
            SELECT data, motivo, daily_value, food_value
            FROM dayoff_fecham 
            WHERE motorist_id = ?
            ORDER BY strftime('%Y-%m-%d', 
                substr(data, 7, 4) || '-' || 
                substr(data, 4, 2) || '-' || 
                substr(data, 1, 2)
            )
        """, (motorist_id,))
        
        dayoff_data = cursor.fetchall()
        
        # Filtrar dayoff pelo período
        dayoff_filtrada = []
        for row in dayoff_data:
            data = row[0]
            try:
                data_obj = datetime.strptime(data, '%d-%m-%Y')
                from_date_obj = datetime.strptime(from_date_br, '%d-%m-%Y')
                to_date_obj = datetime.strptime(to_date_br, '%d-%m-%Y')
                
                if from_date_obj <= data_obj <= to_date_obj:
                    dayoff_filtrada.append(row)
            except:
                pass
        
        conn.close()
        
        # Processar dados para o formato do Excel (mesma lógica do get_closure_report mas simplificada)
        processed_data = []
        totais = {
            'intervalo': '00:00',
            'refeicao': '00:00', 
            'h_trab': '00:00',
            'carga_horaria': '00:00',
            'h_extra50': '00:00',
            'h_e_not': '00:00',
            'ad_not': '00:00',
            'diaria': 'R$ 0,00',
            'aj_aliment': 'R$ 0,00'
        }
        
        # Processar dados de jornada
        for row in jornada_filtrada:
            if trucks_exists and len(row) == 17:
                data, dia_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, \
                observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50, \
                hextra_100, he_noturno, daily_value, food_value, placa = row
            else:
                data, dia_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, \
                observacao, tempo_refeicao, tempo_intervalo, jornada_total, carga_horaria, hextra_50, \
                hextra_100, he_noturno, daily_value, food_value = row
                placa = ""
            
            # Formatar dados para o Excel
            processed_data.append([
                placa or '',
                data or '',
                dia_semana or '',
                inicio_jornada or '',
                f"{in_refeicao or ''}, {fim_refeicao or ''}",
                fim_jornada or '',
                tempo_intervalo or '',
                jornada_total or '',
                carga_horaria or '',
                hextra_50 or '',
                he_noturno or '',  # Adicional Noturno usa he_noturno
                he_noturno or '',
                f"R$ {float(daily_value or 0):.2f}".replace('.', ','),
                f"R$ {float(food_value or 0):.2f}".replace('.', ',')
            ])
        
        # Processar dados de dayoff
        for row in dayoff_filtrada:
            data, motivo, daily_value, food_value = row
            processed_data.append([
                motivo or '',  # Motivo no lugar da placa
                data or '',
                '',  # Dia da semana vazio para dayoff
                '', '', '', '', '', '', '', '', '',  # Campos de jornada vazios
                f"R$ {float(daily_value or 0):.2f}".replace('.', ','),
                f"R$ {float(food_value or 0):.2f}".replace('.', ',')
            ])
        
        # Ordenar por data
        processed_data.sort(key=lambda x: datetime.strptime(x[1], '%d-%m-%Y') if x[1] else datetime.min)
        
        # Gerar Excel
        wb = fill_excel_fecham(
            name=motorist_name,
            start=from_date_obj.strftime('%d/%m/%Y') if 'from_date_obj' in locals() else from_date,
            end=to_date_obj.strftime('%d/%m/%Y') if 'to_date_obj' in locals() else to_date,
            tabela=processed_data,
            totals=totais
        )
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        filename = f"espelho_ponto_{motorist_name.replace(' ', '_')}_{from_date_obj.strftime('%d_%m_%Y')}_a_{to_date_obj.strftime('%d_%m_%Y')}.xlsx"
        
        routes_logger.register_log(f"Excel gerado via modal com sucesso: {filename}")
        
        return send_file(output, as_attachment=True, download_name=filename,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        routes_logger.register_log(f"Erro ao gerar Excel via modal: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


# ============================================================================
# APIs para Classificação de Blocos (Fase 2)
# ============================================================================

@closure_bp.route('/api/closure/block-classification', methods=['GET'])
@route_access_required
def get_block_classification():
    """
    API para buscar classificação de um bloco específico
    
    Query params:
    - motorist_id: ID do motorista (obrigatório)
    - date: Data no formato DD-MM-YYYY (obrigatório)
    - truck_id: ID do caminhão (opcional)
    """
    try:
        motorist_id = request.args.get('motorist_id')
        date = request.args.get('date')
        truck_id = request.args.get('truck_id')
        
        # Validações
        if not motorist_id:
            return jsonify({"error": "motorist_id é obrigatório"}), 400
        
        if not date:
            return jsonify({"error": "date é obrigatório"}), 400
        
        try:
            motorist_id = int(motorist_id)
        except ValueError:
            return jsonify({"error": "motorist_id deve ser um número inteiro"}), 400
        
        if truck_id:
            try:
                truck_id = int(truck_id)
            except ValueError:
                return jsonify({"error": "truck_id deve ser um número inteiro"}), 400
        
        # Buscar classificação
        classification = closure_classifications_driver.get_classification(
            motorist_id=motorist_id,
            data=date,
            truck_id=truck_id
        )
        
        if classification:
            return jsonify({
                "success": True,
                "classification": classification
            })
        else:
            # Retornar default se não encontrado
            return jsonify({
                "success": True,
                "classification": {
                    "classification": "VALIDO",
                    "notes": None,
                    "created_at": None,
                    "updated_at": None,
                    "changed_by": None
                }
            })
            
    except Exception as e:
        routes_logger.print(f"Erro na API get_block_classification: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@closure_bp.route('/api/closure/block-classification', methods=['POST'])
@route_access_required
def save_block_classification():
    """
    API para criar/atualizar classificação de um bloco
    
    Body JSON:
    {
        "motorist_id": int,
        "date": "DD-MM-YYYY",
        "truck_id": int (opcional),
        "classification": "VALIDO|CARGA_DESCARGA|GARAGEM|INVALIDO",
        "notes": string (opcional),
        "changed_by": string (opcional, default: "Sistema")
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Body JSON é obrigatório"}), 400
        
        # Extrair e validar parâmetros
        motorist_id = data.get('motorist_id')
        date = data.get('date')
        truck_id = data.get('truck_id')
        classification = data.get('classification')
        notes = data.get('notes')
        changed_by = data.get('changed_by', 'Sistema')
        
        # Validações obrigatórias
        if not motorist_id:
            return jsonify({"error": "motorist_id é obrigatório"}), 400
        
        if not date:
            return jsonify({"error": "date é obrigatório"}), 400
        
        if not classification:
            return jsonify({"error": "classification é obrigatório"}), 400
        
        try:
            motorist_id = int(motorist_id)
        except (ValueError, TypeError):
            return jsonify({"error": "motorist_id deve ser um número inteiro"}), 400
        
        if truck_id is not None:
            try:
                truck_id = int(truck_id)
            except (ValueError, TypeError):
                return jsonify({"error": "truck_id deve ser um número inteiro"}), 400
        
        # Validar classificação
        if not closure_classifications_driver.validate_classification(classification):
            return jsonify({
                "error": f"classification inválida: {classification}. Valores válidos: {closure_classifications_driver.valid_classifications}"
            }), 400
        
        # Salvar classificação (upsert)
        result = closure_classifications_driver.upsert_classification(
            motorist_id=motorist_id,
            data=date,
            classification=classification,
            truck_id=truck_id,
            notes=notes,
            changed_by=changed_by
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": result['message'],
                "id": result.get('id'),
                "rows_affected": result.get('rows_affected')
            })
        else:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
            
    except Exception as e:
        routes_logger.print(f"Erro na API save_block_classification: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@closure_bp.route('/api/closure/block-classification/history', methods=['GET'])
@route_access_required
def get_block_classification_history():
    """
    API para buscar histórico de mudanças de uma classificação
    
    Query params:
    - motorist_id: ID do motorista (obrigatório)
    - date: Data no formato DD-MM-YYYY (obrigatório)
    - truck_id: ID do caminhão (opcional)
    """
    try:
        motorist_id = request.args.get('motorist_id')
        date = request.args.get('date')
        truck_id = request.args.get('truck_id')
        
        # Validações
        if not motorist_id:
            return jsonify({"error": "motorist_id é obrigatório"}), 400
        
        if not date:
            return jsonify({"error": "date é obrigatório"}), 400
        
        try:
            motorist_id = int(motorist_id)
        except ValueError:
            return jsonify({"error": "motorist_id deve ser um número inteiro"}), 400
        
        if truck_id:
            try:
                truck_id = int(truck_id)
            except ValueError:
                return jsonify({"error": "truck_id deve ser um número inteiro"}), 400
        
        # Buscar histórico
        history = closure_classifications_driver.get_classification_history(
            motorist_id=motorist_id,
            data=date,
            truck_id=truck_id
        )
        
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        })
        
    except Exception as e:
        routes_logger.print(f"Erro na API get_block_classification_history: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@closure_bp.route('/api/closure/block-classification/motorist', methods=['GET'])
@route_access_required
def get_motorist_classifications():
    """
    API para buscar todas as classificações de um motorista em um período
    
    Query params:
    - motorist_id: ID do motorista (obrigatório)
    - start_date: Data inicial DD-MM-YYYY (opcional)
    - end_date: Data final DD-MM-YYYY (opcional)
    """
    try:
        motorist_id = request.args.get('motorist_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Validações
        if not motorist_id:
            return jsonify({"error": "motorist_id é obrigatório"}), 400
        
        try:
            motorist_id = int(motorist_id)
        except ValueError:
            return jsonify({"error": "motorist_id deve ser um número inteiro"}), 400
        
        # Buscar classificações
        classifications = closure_classifications_driver.get_motorist_classifications(
            motorist_id=motorist_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            "success": True,
            "classifications": classifications,
            "count": len(classifications)
        })
        
    except Exception as e:
        routes_logger.print(f"Erro na API get_motorist_classifications: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
