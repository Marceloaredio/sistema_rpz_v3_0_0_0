# Rotas disponíveis para todos os usuários autenticados que possuem acesso ao módulo de Configurações.

from flask import render_template, request, redirect, url_for, abort, flash, Blueprint, jsonify

try:
    import pandas as pd
except ImportError:
    print("AVISO: pandas não disponível, usando stub")
    import pandas_stub as pd
import os
import sqlite3
import json

from controller.decorators import route_access_required
from controller.data import allowed_file, extract_data

from controller.utils import CustomLogger

from model.drivers.uploaded_data_driver import UploadedDataDriver
from model.drivers.motorist_driver import MotoristDriver
from model.drivers.truck_driver import TruckDriver
from model.drivers.user_driver import UserDriver
from model.drivers.former_motorist_driver import FormerMotoristDriver
from model.drivers.company_driver import CompanyDriver
from model.db_model import User, Truck, Motorist, Company

from werkzeug.utils import secure_filename

from global_vars import *
from datetime import datetime, timedelta

from controller.google_integration import GoogleIntegration


def calculate_motorist_status(motorist):
    """
    Calcula o status do motorista baseado nos critérios especificados.
    Retorna um dicionário com 'type' e 'text'.
    """
    # Lista de campos obrigatórios para verificar se estão vazios (exceto codigo_sap)
    required_fields = [
        'nome', 'data_admissao', 'cpf', 'cnh', 'rg', 'operacao', 'ctps', 'serie',
        'data_nascimento', 'primeira_cnh', 'data_expedicao', 'vencimento_cnh',
        'done_mopp', 'vencimento_mopp', 'done_aso_semestral', 'vencimento_aso_semestral',
        'done_aso_periodico', 'vencimento_aso_periodico', 'done_buonny', 'vencimento_buonny',
        'telefone', 'endereco', 'filiacao', 'estado_civil', 'filhos', 'cargo', 'empresa',
        'status', 'conf_jornada', 'conf_fecham', 'done_toxicologico_cnh',
        'vencimento_toxicologico_cnh', 'email', 'done_toxicologico_clt', 'vencimento_toxicologico_clt'
    ]
    
    # Verificar se algum campo obrigatório está vazio
    for field in required_fields:
        value = getattr(motorist, field, None)
        if not value or str(value).strip() == '' or str(value).lower() == 'nan':
            return {
                "type": "incompleto",
                "text": "Informações Incompletas"
            }
    
    # Lista de campos de vencimento para verificar
    vencimento_fields = [
        'vencimento_cnh', 'vencimento_mopp', 'vencimento_aso_semestral',
        'vencimento_aso_periodico', 'vencimento_buonny', 'vencimento_toxicologico_cnh',
        'vencimento_toxicologico_clt'
    ]
    
    # Data atual em GMT-3
    now = datetime.now()
    gmt3_offset = timedelta(hours=3)
    current_date = now + gmt3_offset
    
    # Verificar vencimentos (em ordem de prioridade)
    for field in vencimento_fields:
        value = getattr(motorist, field, None)
        if value and str(value).strip() != '' and str(value).lower() != 'nan':
            try:
                # Converter data do formato dd/mm/aaaa para datetime
                if '/' in str(value):
                    day, month, year = str(value).split('/')
                    expiration_date = datetime(int(year), int(month), int(day), 23, 59, 59)
                    
                    # Calcular diferença em dias
                    diff_days = (expiration_date - current_date).days
                    
                    # Verificar se está vencido (prioridade mais alta)
                    if diff_days < 0:
                        return {
                            "type": "documento-vencido",
                            "text": "Atenção! Documento Vencido"
                        }
                    
                    # Verificar se está próximo do vencimento (10 dias ou menos)
                    if diff_days <= 10:
                        return {
                            "type": "atencao-vencimento",
                            "text": "Atenção! Vencimento Identificado"
                        }
                    
                    # Verificar se está próximo do vencimento (30 dias ou menos)
                    if diff_days <= 30:
                        return {
                            "type": "vencimento-proximo",
                            "text": "Vencimento Próximo"
                        }
            except (ValueError, TypeError):
                continue
    
    # Se não se encaixar em nenhum critério, está tudo certo
    return {
        "type": "tudo-certo",
        "text": "Tudo Certo!"
    }


config_bp = Blueprint('config', __name__)

routes_logger = CustomLogger(source="ROUTES", debug=DEBUG)

user_driver = UserDriver(logger=routes_logger, db_path=DB_PATH)
truck_driver = TruckDriver(logger=routes_logger, db_path=DB_PATH)
motorist_driver = MotoristDriver(logger=routes_logger, db_path=DB_PATH)
company_driver = CompanyDriver(logger=routes_logger, db_path=DB_PATH)

former_motorist_driver = FormerMotoristDriver(logger=routes_logger, db_path=DB_PATH)

# Inicializar integração com Google (será inicializada quando necessário)
google_integration = None

user_driver.create_table()
truck_driver.create_table()
motorist_driver.create_table()

# Verificando se tem pelo menos um usuário, para poder fazer o login
all_users = user_driver.retrieve_all_users()

if all_users is None or len(all_users) == 0:
    user_driver.create_user(name="Admin", email="admin@admin.com", password="root12345", is_admin=True)


@config_bp.route('/user_config')
@route_access_required
def user_config():
    all_users = user_driver.retrieve_all_users()
    all_users = [User(user) for user in all_users]
    
    # Obter todas as rotas disponíveis organizadas por categoria
    try:
        from controller.route_utils import get_routes_sectors
        routes_sectors = get_routes_sectors()
    except Exception as e:
        routes_logger.register_log("Erro ao obter rotas", str(e))
        routes_sectors = set()
    
    return render_template('user_config.html', 
                           users=all_users, 
                           routes_sectors=routes_sectors)


@config_bp.route('/truck_config')
@route_access_required
def truck_config():
    all_trucks = truck_driver.retrieve_all_trucks()
    all_trucks = [Truck(truck) for truck in all_trucks]
    return render_template('truck_config.html', trucks=all_trucks)


@config_bp.route('/motorist_config')
@route_access_required
def motorist_config():
    # Buscar todos os motoristas do banco
    all_motorists = motorist_driver.retrieve_all_motorists()
    print(f"DEBUG: Total de motoristas encontrados: {len(all_motorists)}")
    
    # Filtrar apenas motoristas ativos (case insensitive) e calcular status
    active_motorists = []
    for motorist_data in all_motorists:
        motorist = Motorist(motorist_data)
        print(f"DEBUG: Processando motorista: {motorist.nome}, Status: {motorist.status}")
        
        if motorist.status and 'ativo' in motorist.status.lower():
            print(f"DEBUG: Motorista ativo encontrado: {motorist.nome}")
            # Calcular status do motorista
            status_info = calculate_motorist_status(motorist)
            
            motorist_dict = {
                "id": motorist.id,
                "nome": motorist.nome,
                "cpf": motorist.cpf,
                "cnh": motorist.cnh,
                "operacao": motorist.operacao,
                "empresa": motorist.empresa,
                "status_type": status_info["type"],
                "status_text": status_info["text"]
            }
            print(f"DEBUG: Status calculado para {motorist.nome}: {status_info}")
            print(f"DEBUG: Dicionário criado: {motorist_dict}")
            active_motorists.append(motorist_dict)
            
            print(f"DEBUG: Total de motoristas ativos até agora: {len(active_motorists)}")
    
    # Ordenar por nome
    active_motorists.sort(key=lambda x: x["nome"].upper() if x["nome"] else '')
    
    # Debug final antes de passar para o template
    print(f"DEBUG: Dados finais que serão passados para o template:")
    for i, motorist in enumerate(active_motorists[:3]):
        print(f"  Motorista {i+1}: {motorist}")
    
    # Debug: verificar dados que serão passados para o template
    routes_logger.register_log("DEBUG_TEMPLATE_DATA", f"Total de motoristas ativos: {len(active_motorists)}")
    for i, motorist in enumerate(active_motorists[:3]):  # Log dos primeiros 3 motoristas
        routes_logger.register_log("DEBUG_TEMPLATE_DATA", f"Motorista {i+1}: {motorist}")
    
    # Contar por operação
    operacoes_count = {}
    for motorist in active_motorists:
        operacao = motorist["operacao"] if motorist["operacao"] else 'Sem Operação'
        operacoes_count[operacao] = operacoes_count.get(operacao, 0) + 1
    
    # Preparar dados de resumo por operação
    operacoes_summary = [(operacao, count) for operacao, count in operacoes_count.items()]
    operacoes_summary.sort(key=lambda x: x[0])
    
    return render_template('motorist_config.html', 
                        motorists=active_motorists, 
                        operacoes_summary=operacoes_summary)





@config_bp.route('/users', methods=['GET', 'POST'])
@route_access_required
def manage_users():
    routes_logger.print(f"Método chamado: {request.method}")

    users_db = user_driver.retrieve_all_users()
    users_db = [User(user) for user in users_db]

    if request.method == 'GET':
        # Obter todos os setores disponíveis
        try:
            from controller.route_utils import get_routes_sectors
            routes_sectors = get_routes_sectors()
        except Exception as e:
            routes_logger.register_log("Erro ao obter setores", str(e))
            routes_sectors = set()
        
        # Exibe todos os usuários
        return render_template('user_config.html', users=users_db, routes_sectors=routes_sectors)

    elif request.method == 'POST':
        hidden_method = request.form.get('_method')

        if hidden_method == "DELETE":
            # Deleta um usuário
            user_email = request.form['selected_email']
            routes_logger.print(f"Deletando usuário {user_email}")
            rows = user_driver.delete_user(where_columns=['email', ],
                                           where_values=(user_email,)
                                           )

            if rows == 0:
                return abort(403)

            return redirect(url_for('config.manage_users'))  # Redireciona para a mesma página

        if hidden_method == "PUT":
            # Editar um usuário

            edited_email = request.form['_edited_email']

            new_name = request.form['user_name']
            new_email = request.form['user_email']
            new_password = request.form['user_password']
            new_is_admin = request.form.get('is_admin') == 'on'  # checkbox
            
            # Processar setores autorizados
            authorized_sectors = request.form.getlist('authorized_routes')  # Mantém o nome do campo por compatibilidade
            authorized_sectors_json = json.dumps(authorized_sectors)

            rows = user_driver.update_user(set_columns=['name', 'email', 'password', 'is_admin', 'authorized_routes'],
                                           set_values=(new_name, new_email, new_password, int(new_is_admin), authorized_sectors_json),
                                           where_columns=['email'],
                                           where_values=(edited_email,))

            if rows == 0:
                return abort(403)

            return redirect(url_for('config.manage_users'))  # Redireciona para a mesma página

        # Adiciona um novo usuário
        user_name = request.form['name']
        user_email = request.form['email']
        user_password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'  # checkbox
        
        # Processar setores autorizados
        authorized_sectors = request.form.getlist('authorized_routes')  # Mantém o nome do campo por compatibilidade
        authorized_sectors_json = json.dumps(authorized_sectors)

        new_user = User([user_name, user_email, user_password, is_admin, authorized_sectors_json])
        user_driver.create_user(new_user.name, new_user.email, new_user.password, is_admin, authorized_sectors_json)

        return redirect(url_for('config.manage_users'))  # Redireciona para a mesma página

    elif request.method == 'PUT':
        # Edita um usuário existente
        user_email = request.form['selected_email']

        new_user_name = request.form['user_name']
        new_user_email = request.form['user_email']
        new_user_password = request.form['user_password']
        new_user_role = request.form['user_role']

        rows = user_driver.update_user(set_columns=['name', 'email', 'password', 'role'],
                                       set_values=(new_user_name, new_user_email, new_user_password, new_user_role),
                                       where_columns=['email',],
                                       where_values=(user_email,)
                                       )

        if rows == 0:
            return abort(403)

        return redirect(url_for('config.manage_users'))  # Redireciona para a mesma página


@config_bp.route('/trucks', methods=['GET', 'POST'])
@route_access_required
def manage_trucks():
    routes_logger.print(f"Método chamado: {request.method}")

    trucks_db = truck_driver.retrieve_all_trucks()
    trucks_db = [Truck(truck) for truck in trucks_db]

    if request.method == 'GET':
        # Exibe todos os caminhões
        return render_template('truck_config.html', trucks=trucks_db)

    elif request.method == 'POST':
        hidden_method = request.form.get('_method')

        if hidden_method == "DELETE":
            # Deleta um caminhão
            truck_id = request.form['selected_id']
            routes_logger.print(f"Deletando caminhão com a id {truck_id}")
            rows = truck_driver.delete_truck(where_columns=['id'],
                                             where_values=(truck_id,)
                                             )

            if rows == 0:
                return abort(403)

            return redirect(url_for('config.manage_trucks'))  # Redireciona para a mesma página

        if hidden_method == "PUT":
            # Editar um caminhão
            edited_id = request.form['_id']

            new_placa = request.form['placa']
            
            new_ano = request.form['ano']
            new_modelo = request.form['modelo']
            new_vencimento_aet_dnit = request.form['vencimento_aet_dnit']
            new_vencimento_aet_mg = request.form['vencimento_aet_mg']
            new_vencimento_aet_sp = request.form['vencimento_aet_sp']
            new_vencimento_aet_go = request.form['vencimento_aet_go']
            new_vencimento_civ_cipp = request.form['vencimento_civ_cipp']
            new_vencimento_cronotografo = request.form['vencimento_cronotografo']
            new_exercicio_crlv = request.form['exercicio_crlv']
            new_peso_tara = request.form['peso_tara']
            
            new_status = request.form['status']

            rows = truck_driver.update_truck(
                set_columns=['placa', 'ano', 'modelo', 'vencimento_aet_dnit', 'vencimento_aet_mg',
                             'vencimento_aet_sp', 'vencimento_aet_go', 'vencimento_civ_cipp', 'vencimento_cronotografo',
                             'exercicio_crlv', 'peso_tara', 'status'],
                set_values=(new_placa, new_ano, new_modelo, new_vencimento_aet_dnit, new_vencimento_aet_mg,
                            new_vencimento_aet_sp, new_vencimento_aet_go, new_vencimento_civ_cipp, new_vencimento_cronotografo,
                            new_exercicio_crlv, new_peso_tara, new_status),
                where_columns=['id'],
                where_values=(edited_id,)
            )

            if rows == 0:
                return abort(403)

            return redirect(url_for('config.manage_trucks'))  # Redireciona para a mesma página

        # Adiciona um novo caminhão
        truck_placa = request.form['placa']
        truck_identificacao = request.form['identificacao']
        truck_ano = request.form['ano']
        truck_modelo = request.form['modelo']
        truck_vencimento_aet_dnit = request.form['vencimento_aet_dnit']
        truck_vencimento_aet_mg = request.form['vencimento_aet_mg']
        truck_vencimento_aet_sp = request.form['vencimento_aet_sp']
        truck_vencimento_aet_go = request.form['vencimento_aet_go']
        truck_vencimento_civ_cipp = request.form['vencimento_civ_cipp']
        truck_vencimento_cronotografo = request.form['vencimento_cronotografo']
        truck_exercicio_crlv = request.form['exercicio_crlv']
        truck_peso_tara = request.form['peso_tara']
        truck_link_documentacao = request.form['link_documentacao']
        truck_status = request.form['status']

        new_truck = Truck([None, truck_placa, truck_identificacao, truck_ano, truck_modelo, truck_vencimento_aet_dnit, truck_vencimento_aet_mg,
                           truck_vencimento_aet_sp, truck_vencimento_aet_go, truck_vencimento_civ_cipp, truck_vencimento_cronotografo,
                           truck_exercicio_crlv, truck_peso_tara, truck_link_documentacao, truck_status])

        truck_driver.create_truck(new_truck.placa, new_truck.identificacao, new_truck.ano, new_truck.modelo,
                                  new_truck.vencimento_aet_dnit, new_truck.vencimento_aet_mg, new_truck.vencimento_aet_sp,
                                  new_truck.vencimento_aet_go, new_truck.vencimento_civ_cipp, new_truck.vencimento_cronotografo,
                                  new_truck.exercicio_crlv, new_truck.peso_tara, new_truck.link_documentacao, new_truck.status)

        return redirect(url_for('config.manage_trucks'))  # Redireciona para a mesma página


@config_bp.route('/motorists', methods=['GET', 'POST'])
@route_access_required
def manage_motorists():
    routes_logger.print(f"Método chamado: {request.method}")

    motorists_db = motorist_driver.retrieve_all_motorists()
    # Ordenar motoristas alfabeticamente por nome
    motorists_db.sort(key=lambda x: x[1].upper() if x[1] else '')
    motorists_db = [Motorist(motorist) for motorist in motorists_db]

    if request.method == 'GET':
        # Exibe todos os motoristas
        return render_template('motorist_config.html', motorists=motorists_db)

    elif request.method == 'POST':
        hidden_method = request.form.get('_method')

        if hidden_method == "DELETE":
            # Deleta um motorista
            motorist_id = request.form['id']
            routes_logger.print(f"Deletando motorista com a id {motorist_id}")
            
            # Primeiro, recupera os dados do motorista antes de excluí-lo
            motorist = motorist_driver.retrieve_motorist(['id'], (motorist_id,))
            
            if motorist:
                # Adiciona o motorista à tabela de ex-motoristas
                former_motorist_driver.add_former_motorist(
                    original_id=motorist[0],
                    nome=motorist[1],
                    
                    data_admissao=motorist[3],
                    cpf=motorist[4],
                    cnh=motorist[5],
                    rg=motorist[6],
                    ctps=motorist[7],
                    serie=motorist[8],
                    data_nascimento=motorist[9],
                    primeira_cnh=motorist[10],
                    vencimento_cnh=motorist[11],
                    data_expedicao=motorist[12],
                    vencimento_mopp=motorist[13],
                    vencimento_toxicologico=motorist[14],
                    vencimento_aso_semestral=motorist[15],
                    vencimento_aso_periodico=motorist[16],
                    vencimento_buonny=motorist[17],
                    
                    
                    
                    
                    telefone=motorist[22],
                    endereco=motorist[23],
                    filiacao=motorist[24],
                    estado_civil=motorist[25],
                    filhos=motorist[26],
                    cargo=motorist[27],
                    empresa=motorist[28],
                    
                    status=motorist[30]
                )
                
                # Agora exclui o motorista da tabela original
                rows = motorist_driver.delete_motorist(where_columns=['id'],
                                                   where_values=(motorist_id,)
                                                   )

                if rows == 0:
                    return abort(403)

            return redirect(url_for('config.manage_motorists'))  # Redireciona para a mesma página

        if hidden_method == "PUT":
            # Editar um motorista
            id = request.form['_id']

            new_nome = request.form['nome']
            
            new_data_admissao = request.form['data_admissao']
            new_cpf = request.form['cpf']
            new_cnh = request.form['cnh']
            new_rg = request.form['rg']
            new_ctps = request.form['ctps']
            new_serie = request.form['serie']
            new_data_nascimento = request.form['data_nascimento']
            new_primeira_cnh = request.form['primeira_cnh']
            new_vencimento_cnh = request.form['vencimento_cnh']
            new_data_expedicao = request.form['data_expedicao']
            new_vencimento_mopp = request.form['vencimento_mopp']
            new_vencimento_toxicologico = request.form['vencimento_toxicologico']
            new_vencimento_aso_semestral = request.form['vencimento_aso_semestral']
            new_vencimento_aso_periodico = request.form['vencimento_aso_periodico']
            new_vencimento_buonny = request.form['vencimento_buonny']
            
            
            
            
            new_telefone = request.form['telefone']
            new_endereco = request.form['endereco']
            new_filiacao = request.form['filiacao']
            new_estado_civil = request.form['estado_civil']
            new_filhos = request.form['filhos']
            new_cargo = request.form['cargo']
            new_empresa = request.form['empresa']
            
            new_status = request.form['status']

            rows = motorist_driver.update_motorist(
            set_columns=['nome', 'data_admissao', 'cpf', 'cnh', 'rg', 'codigo_sap', 'operacao', 'ctps', 'serie',
                         'data_nascimento', 'primeira_cnh', 'vencimento_cnh', 'data_expedicao', 'vencimento_mopp',
                         'done_mopp', 'vencimento_mopp', 'done_toxicologico_clt', 'vencimento_toxicologico_clt', 
                         'done_aso_semestral', 'vencimento_aso_semestral', 'done_aso_periodico', 'vencimento_aso_periodico',
                         'done_buonny', 'vencimento_buonny', 'telefone', 'endereco',
                         'filiacao', 'estado_civil', 'filhos', 'cargo', 'empresa', 'status', 'conf_jornada', 'conf_fecham'],
                set_values=(new_nome, new_data_admissao, new_cpf, new_cnh, new_rg, new_ctps,
                            new_serie, new_data_nascimento, new_primeira_cnh, new_vencimento_cnh, new_data_expedicao,
                            new_vencimento_mopp, new_vencimento_toxicologico, new_vencimento_aso_semestral,
                                                         new_vencimento_aso_periodico, new_vencimento_buonny,
                            new_telefone, new_endereco, new_filiacao, new_estado_civil, new_filhos,
                            new_cargo, new_empresa, new_status),
                where_columns=['id'],
                where_values=(id,)
            )

            if rows == 0:
                return abort(403)

            return redirect(url_for('config.manage_motorists'))  # Redireciona para a mesma página

        # Adiciona um novo motorista
        motorist_nome = request.form['nome']
        
        motorist_data_admissao = request.form['data_admissao']
        motorist_cpf = request.form['cpf']
        motorist_cnh = request.form['cnh']
        motorist_rg = request.form['rg']
        motorist_codigo_sap = request.form['codigo_sap']
        motorist_operacao = request.form['operacao']
        motorist_ctps = request.form['ctps']
        motorist_serie = request.form['serie']
        motorist_data_nascimento = request.form['data_nascimento']
        motorist_primeira_cnh = request.form['primeira_cnh']
        motorist_vencimento_cnh = request.form['vencimento_cnh']
        motorist_done_mopp = request.form['done_mopp']
        motorist_data_expedicao = request.form['data_expedicao']
        motorist_vencimento_mopp = request.form['vencimento_mopp']
        motorist_done_toxicologico_clt = request.form['done_toxicologico_clt']
        motorist_vencimento_toxicologico_clt = request.form['vencimento_toxicologico_clt']
        motorist_done_aso_semestral = request.form['done_aso_semestral']
        motorist_vencimento_aso_semestral = request.form['vencimento_aso_semestral']
        motorist_done_aso_periodico = request.form['done_aso_periodico']
        motorist_vencimento_aso_periodico = request.form['vencimento_aso_periodico']
        motorist_done_buonny = request.form['done_buonny']
        motorist_vencimento_buonny = request.form['vencimento_buonny']
        motorist_conf_jornada = request.form['conf_jornada']
        motorist_conf_fecham = request.form['conf_fecham']
        
        
        
        
        motorist_telefone = request.form['telefone']
        motorist_endereco = request.form['endereco']
        motorist_filiacao = request.form['filiacao']
        motorist_estado_civil = request.form['estado_civil']
        motorist_filhos = request.form['filhos']
        motorist_cargo = request.form['cargo']
        motorist_empresa = request.form['empresa']
        motorist_email = request.form.get('email', '')  # Campo opcional
        
        motorist_status = request.form['status']

        new_motorist = Motorist([None, motorist_nome, motorist_data_admissao, motorist_cpf, motorist_cnh,
                                 motorist_rg, motorist_codigo_sap, motorist_operacao, motorist_ctps, motorist_serie, 
                                 motorist_data_nascimento, motorist_primeira_cnh, motorist_data_expedicao, motorist_vencimento_cnh,
                                 motorist_done_mopp, motorist_vencimento_mopp, motorist_done_toxicologico_clt, motorist_vencimento_toxicologico_clt,
                                 motorist_done_aso_semestral, motorist_vencimento_aso_semestral, motorist_done_aso_periodico, 
                                 motorist_vencimento_aso_periodico, motorist_done_buonny, motorist_vencimento_buonny,
                                 motorist_telefone, motorist_endereco, motorist_filiacao, motorist_estado_civil, motorist_filhos, 
                                 motorist_cargo, motorist_empresa, new_motorist.status, motorist_conf_jornada, motorist_conf_fecham, 
                                 motorist_email])

        try:
            routes_logger.print(f"Tentando criar motorista: {new_motorist.nome}")
            
            motorist_driver.create_motorist(new_motorist.nome, new_motorist.data_admissao,
                                           new_motorist.cpf, new_motorist.cnh, new_motorist.rg, new_motorist.codigo_sap,
                                           new_motorist.operacao, new_motorist.ctps, new_motorist.serie, new_motorist.data_nascimento, 
                                           new_motorist.primeira_cnh, new_motorist.data_expedicao, new_motorist.vencimento_cnh, 
                                           new_motorist.done_mopp, new_motorist.vencimento_mopp, new_motorist.done_toxicologico_clt,
                                                                                        new_motorist.vencimento_toxicologico_clt, new_motorist.done_aso_semestral,
                                           new_motorist.vencimento_aso_semestral, new_motorist.done_aso_periodico,
                                           new_motorist.vencimento_aso_periodico, new_motorist.done_buonny, new_motorist.vencimento_buonny,
                                           new_motorist.telefone, new_motorist.endereco, new_motorist.filiacao, new_motorist.estado_civil,
                                           new_motorist.filhos, new_motorist.cargo, new_motorist.empresa, new_motorist.status,
                                           new_motorist.conf_jornada, new_motorist.conf_fecham, new_motorist.email)

            routes_logger.print("Motorista criado com sucesso!")
            flash('Motorista cadastrado com sucesso!', 'success')
            return redirect(url_for('config.manage_motorists'))  # Redireciona para a mesma página
            
        except ValueError as e:
            routes_logger.print(f"Erro de validação: {str(e)}")
            flash(str(e), 'error')
            return redirect(url_for('config.manage_motorists'))
        except Exception as e:
            routes_logger.print(f"Erro ao criar motorista: {str(e)}")
            flash('Erro ao cadastrar motorista. Tente novamente.', 'error')
            return redirect(url_for('config.manage_motorists'))

    elif request.method == 'PUT':
        # Edita um motorista existente
        id = request.form['_id']

        new_motorist_nome = request.form['nome']
        new_motorist_data_admissao = request.form['data_admissao']
        new_motorist_cpf = request.form['cpf']
        new_motorist_cnh = request.form['cnh']
        new_motorist_rg = request.form['rg']
        new_motorist_codigo_sap = request.form['codigo_sap']
        new_motorist_operacao = request.form['operacao']
        new_motorist_ctps = request.form['ctps']
        new_motorist_serie = request.form['serie']
        new_motorist_data_nascimento = request.form['data_nascimento']
        new_motorist_primeira_cnh = request.form['primeira_cnh']
        new_motorist_vencimento_cnh = request.form['vencimento_cnh']
        new_motorist_done_mopp = request.form['done_mopp']
        new_motorist_data_expedicao = request.form['data_expedicao']
        new_motorist_vencimento_mopp = request.form['vencimento_mopp']
        new_motorist_done_toxicologico_clt = request.form['done_toxicologico_clt']
        new_motorist_vencimento_toxicologico_clt = request.form['vencimento_toxicologico_clt']
        new_motorist_done_aso_semestral = request.form['done_aso_semestral']
        new_motorist_vencimento_aso_semestral = request.form['vencimento_aso_semestral']
        new_motorist_done_aso_periodico = request.form['done_aso_periodico']
        new_motorist_vencimento_aso_periodico = request.form['vencimento_aso_periodico']
        new_motorist_done_buonny = request.form['done_buonny']
        new_motorist_vencimento_buonny = request.form['vencimento_buonny']
        new_motorist_conf_jornada = request.form['conf_jornada']
        new_motorist_conf_fecham = request.form['conf_fecham']
        new_motorist_telefone = request.form['telefone']
        new_motorist_endereco = request.form['endereco']
        new_motorist_filiacao = request.form['filiacao']
        new_motorist_estado_civil = request.form['estado_civil']
        new_motorist_filhos = request.form['filhos']
        new_motorist_cargo = request.form['cargo']
        new_motorist_empresa = request.form['empresa']
        new_motorist_status = request.form['status']

        rows = motorist_driver.update_motorist(
            set_columns=['nome', 'data_admissao', 'cpf', 'cnh', 'rg', 'codigo_sap', 'operacao', 'ctps', 'serie',
                         'data_nascimento', 'primeira_cnh', 'vencimento_cnh', 'data_expedicao', 'vencimento_mopp',
                         'done_mopp', 'vencimento_mopp', 'done_toxicologico_clt', 'vencimento_toxicologico_clt', 
                         'done_aso_semestral', 'vencimento_aso_semestral', 'done_aso_periodico', 'vencimento_aso_periodico',
                         'done_buoony', 'vencimento_buonny', 'telefone', 'endereco',
                         'filiacao', 'estado_civil', 'filhos', 'cargo', 'empresa', 'status', 'conf_jornada', 'conf_fecham'],
            set_values=(new_motorist_nome, new_motorist_data_admissao, new_motorist_cpf, new_motorist_cnh,
                        new_motorist_rg, new_motorist_codigo_sap, new_motorist_operacao, new_motorist_ctps, new_motorist_serie, 
                        new_motorist_data_nascimento, new_motorist_primeira_cnh, new_motorist_vencimento_cnh, new_motorist_data_expedicao, 
                        new_motorist_vencimento_mopp, new_motorist_done_mopp, new_motorist_done_toxicologico_clt, 
                         new_motorist_vencimento_toxicologico_clt, new_motorist_done_aso_semestral, new_motorist_vencimento_aso_semestral, 
                        new_motorist_done_aso_periodico, new_motorist_vencimento_aso_periodico, new_motorist_done_buonny, 
                        new_motorist_vencimento_buonny, new_motorist_telefone, new_motorist_endereco, new_motorist_filiacao, 
                        new_motorist_estado_civil, new_motorist_filhos, new_motorist_cargo, new_motorist_empresa, new_motorist_status,
                        new_motorist_conf_jornada, new_motorist_conf_fecham),
            where_columns=['id'],
            where_values=(id,)
        )

        if rows == 0:
            return abort(403)

        return redirect(url_for('config.manage_motorists'))  # Redireciona para a mesma página


@config_bp.route('/former-motorists')
@route_access_required
def former_motorists():
    """Página de motoristas antigos"""
    # TODO: Implementar busca de motoristas antigos no banco de dados
    return render_template('former_motorists.html', 
                         motorists=[], 
                         operacoes_summary=[])


# ============================================================================
# NOVAS ROTAS PARA ESTRUTURA REORGANIZADA DE CONFIGURAÇÕES
# ============================================================================

@config_bp.route('/config')
@route_access_required
def config_main():
    """Página principal de configurações"""
    return render_template('config_main.html')




@config_bp.route('/config/vehicles')
@route_access_required
def config_vehicles():
    """Página de configuração de veículos"""
    all_trucks = truck_driver.retrieve_all_trucks()
    all_trucks = [Truck(truck) for truck in all_trucks]
    return render_template('truck_config.html', trucks=all_trucks)


@config_bp.route('/config/employees')
@route_access_required
def config_employees():
    """Página de configuração de funcionários"""
    return render_template('config_employees.html')


@config_bp.route('/config/employees/administrative')
@route_access_required
def config_employees_administrative():
    """Página de configuração de funcionários administrativos"""
    # TODO: Implementar lógica para funcionários administrativos
    return render_template('config_employees_administrative.html')


@config_bp.route('/config/employees/drivers')
@route_access_required
def config_employees_drivers():
    """Página de configuração de motoristas"""
    # Buscar todos os motoristas do banco
    all_motorists = motorist_driver.retrieve_all_motorists()
    print(f"DEBUG: Total de motoristas encontrados: {len(all_motorists)}")
    
    # Filtrar apenas motoristas ativos (case insensitive) e calcular status
    active_motorists = []
    for motorist_data in all_motorists:
        motorist = Motorist(motorist_data)
        print(f"DEBUG: Processando motorista: {motorist.nome}, Status: {motorist.status}")
        
        if motorist.status and 'ativo' in motorist.status.lower():
            print(f"DEBUG: Motorista ativo encontrado: {motorist.nome}")
            # Calcular status do motorista
            status_info = calculate_motorist_status(motorist)
            
            motorist_dict = {
                "id": motorist.id,
                "nome": motorist.nome,
                "cpf": motorist.cpf,
                "cnh": motorist.cnh,
                "operacao": motorist.operacao,
                "empresa": motorist.empresa,
                "status_type": status_info["type"],
                "status_text": status_info["text"]
            }
            print(f"DEBUG: Status calculado para {motorist.nome}: {status_info}")
            print(f"DEBUG: Dicionário criado: {motorist_dict}")
            active_motorists.append(motorist_dict)
            
            print(f"DEBUG: Total de motoristas ativos até agora: {len(active_motorists)}")
    
    # Ordenar por nome
    active_motorists.sort(key=lambda x: x["nome"].upper() if x["nome"] else '')
    
    # Debug final antes de passar para o template
    print(f"DEBUG: Dados finais que serão passados para o template:")
    for i, motorist in enumerate(active_motorists[:3]):
        print(f"  Motorista {i+1}: {motorist}")
    
    # Debug: verificar dados que serão passados para o template
    routes_logger.register_log("DEBUG_TEMPLATE_DATA", f"Total de motoristas ativos: {len(active_motorists)}")
    for i, motorist in enumerate(active_motorists[:3]):  # Log dos primeiros 3 motoristas
        routes_logger.register_log("DEBUG_TEMPLATE_DATA", f"Motorista {i+1}: {motorist}")
    
    # Contar por operação
    operacoes_count = {}
    for motorist in active_motorists:
        operacao = motorist["operacao"] if motorist["operacao"] else 'Sem Operação'
        operacoes_count[operacao] = operacoes_count.get(operacao, 0) + 1
    
    # Preparar dados de resumo por operação
    operacoes_summary = [(operacao, count) for operacao, count in operacoes_count.items()]
    operacoes_summary.sort(key=lambda x: x[0])
    
    return render_template('motorist_config.html', 
                        motorists=active_motorists, 
                        operacoes_summary=operacoes_summary)


@config_bp.route('/config/employees/mechanics')
@route_access_required
def config_employees_mechanics():
    """Página de configuração de mecânica e portaria"""
    # TODO: Implementar lógica para funcionários de mecânica e portaria
    return render_template('config_employees_mechanics.html')


@config_bp.route('/config/users')
@route_access_required
def config_users():
    """Página de configuração de usuários"""
    all_users = user_driver.retrieve_all_users()
    all_users = [User(user) for user in all_users]
    
    # Obter todas as rotas disponíveis organizadas por categoria
    try:
        from controller.route_utils import get_routes_sectors
        routes_sectors = get_routes_sectors()
    except Exception as e:
        routes_logger.register_log("Erro ao obter rotas", str(e))
        routes_sectors = set()
    
    return render_template('user_config.html', 
                           users=all_users, 
                           routes_sectors=routes_sectors)

# ===== API ROUTES =====

@config_bp.route('/api/motorists', methods=['POST'])
@route_access_required
def api_create_motorist():
    """API para criar novo motorista com validações completas"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        # ===== 1. VERIFICAR DUPLICIDADE =====
        cpf_original = data.get('cpf', '')
        nome_limpo = data.get('nome', '').strip().upper()
        
        # Verificar se CPF já existe (com formatação)
        existing_cpf = motorist_driver.retrieve_motorist(['cpf'], (cpf_original,))
        if existing_cpf:
            return jsonify({
                'success': False, 
                'message': 'Já existe um motorista cadastrado com este CPF'
            }), 400
        
        # Verificar se nome já existe
        existing_nome = motorist_driver.retrieve_motorist(['nome'], (nome_limpo,))
        if existing_nome:
            return jsonify({
                'success': False, 
                'message': 'Já existe um motorista cadastrado com este nome'
            }), 400
        
        # ===== 2. GERAR NOVO ID =====
        all_motorists = motorist_driver.retrieve_all_motorists()
        if all_motorists:
            max_id = max(motorist[0] for motorist in all_motorists)
            new_id = max_id + 1
        else:
            new_id = 1
        
        # ===== 3. VALIDAR CAMPOS OBRIGATÓRIOS =====
        required_fields = [
            'nome', 'data_admissao', 'cpf', 'cnh', 'rg', 'operacao', 
            'ctps', 'serie', 'data_nascimento', 'primeira_cnh', 
            'data_expedicao', 'vencimento_cnh', 'telefone', 'endereco', 
            'filiacao', 'estado_civil', 'filhos', 'cargo', 'empresa'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return jsonify({
                'success': False, 
                'message': f'Campos obrigatórios não preenchidos: {", ".join(missing_fields)}'
            }), 400
        
        # ===== 4. VALIDAR FORMATOS ESPECÍFICOS =====
        # Validar CPF (11 dígitos, removendo formatação apenas para validação)
        cpf_limpo_validacao = cpf_original.replace('.', '').replace('-', '')
        if len(cpf_limpo_validacao) != 11:
            return jsonify({
                'success': False, 
                'message': 'CPF deve conter exatamente 11 dígitos'
            }), 400
        
        # Validar CNH (11 dígitos)
        cnh_limpo = data.get('cnh', '').replace('.', '').replace('-', '')
        if len(cnh_limpo) != 11:
            return jsonify({
                'success': False, 
                'message': 'CNH deve conter exatamente 11 dígitos'
            }), 400
        
        # Validar telefone (11 dígitos)
        telefone_limpo = data.get('telefone', '').replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
        if len(telefone_limpo) != 11:
            return jsonify({
                'success': False, 
                'message': 'Telefone deve conter exatamente 11 dígitos'
            }), 400
        
        # Validar operação
        operacoes_validas = ['VIBRA', 'ALE', 'SADA', 'ESCURO']
        if data.get('operacao') not in operacoes_validas:
            return jsonify({
                'success': False, 
                'message': 'Operação deve ser VIBRA, ALE, SADA ou ESCURO'
            }), 400
        
        # Validar estado civil
        estados_validos = ['CASADO', 'SOLTEIRO', 'AMASIADO', 'UNIÃO ESTÁVEL', 'DIVORCIADO']
        if data.get('estado_civil') not in estados_validos:
            return jsonify({
                'success': False, 
                'message': 'Estado civil deve ser CASADO, SOLTEIRO, AMASIADO, UNIÃO ESTÁVEL ou DIVORCIADO'
            }), 400
        
        # Validar filhos (0-10)
        try:
            filhos = int(data.get('filhos', 0))
            if filhos < 0 or filhos > 10:
                return jsonify({
                    'success': False, 
                    'message': 'Número de filhos deve ser entre 0 e 10'
                }), 400
        except ValueError:
            return jsonify({
                'success': False, 
                'message': 'Número de filhos deve ser um número válido'
            }), 400
        
        # Validar cargo
        cargos_validos = ['MOTORISTA DE CAMINHÃO TRUCK', 'MOTORISTA DE CARRETA', 'MOTORISTA DE BITREM']
        if data.get('cargo') not in cargos_validos:
            return jsonify({
                'success': False, 
                'message': 'Cargo deve ser MOTORISTA DE CAMINHÃO TRUCK, MOTORISTA DE CARRETA ou MOTORISTA DE BITREM'
            }), 400
        
        # ===== 5. PREPARAR DADOS PARA INSERÇÃO =====
        # Manter datas no formato dd/mm/aaaa
        def convert_date(date_str):
            # Manter o formato original dd/mm/aaaa
            return date_str if date_str else ''
        
        # Converter checkboxes para valores apropriados
        conf_jornada = 'Ativo' if data.get('conf_jornada') == '1' else 'Inativo'
        conf_fecham = 'Ativo' if data.get('conf_fecham') == '1' else 'Inativo'
        
        motorist_data = {
            'id': new_id,  # ID gerado automaticamente
            'nome': nome_limpo,  # Nome em maiúsculas
            'data_admissao': convert_date(data.get('data_admissao', '')),
            'cpf': data.get('cpf', ''),  # CPF com formatação (pontos e hífens)
            'cnh': cnh_limpo,  # CNH limpa (apenas números)
            'rg': data.get('rg', '').replace('.', '').replace('-', ''),  # RG limpo
            'codigo_sap': data.get('codigo_sap', '').replace('.', '').replace('-', '')[:9],  # Máximo 9 dígitos
            'operacao': data.get('operacao', ''),
            'ctps': data.get('ctps', '').replace('.', '').replace('-', '')[:10],  # Máximo 10 dígitos
            'serie': data.get('serie', ''),  # Preservar zeros à esquerda
            'data_nascimento': convert_date(data.get('data_nascimento', '')),
            'primeira_cnh': convert_date(data.get('primeira_cnh', '')),
            'data_expedicao': convert_date(data.get('data_expedicao', '')),
            'vencimento_cnh': convert_date(data.get('vencimento_cnh', '')),
            'done_mopp': convert_date(data.get('done_mopp', '')),
            'vencimento_mopp': convert_date(data.get('vencimento_mopp', '')),
            'done_toxicologico_clt': convert_date(data.get('done_toxicologico_clt', '')),
            'vencimento_toxicologico_clt': convert_date(data.get('vencimento_toxicologico_clt', '')),
            'done_aso_semestral': convert_date(data.get('done_aso_semestral', '')),
            'vencimento_aso_semestral': convert_date(data.get('vencimento_aso_semestral', '')),
            'done_aso_periodico': convert_date(data.get('done_aso_periodico', '')),
            'vencimento_aso_periodico': convert_date(data.get('vencimento_aso_periodico', '')),
            'done_buonny': convert_date(data.get('done_buonny', '')),
            'vencimento_buonny': convert_date(data.get('vencimento_buonny', '')),
            'telefone': data.get('telefone', ''),  # Manter formato (##) #####-####
            'endereco': data.get('endereco', ''),
            'filiacao': data.get('filiacao', ''),
            'estado_civil': data.get('estado_civil', ''),
            'filhos': str(filhos),  # Converter para string
            'cargo': data.get('cargo', ''),
            'empresa': data.get('empresa', ''),
            'status': 'Ativo',  # Padrão para novos cadastros
            'conf_jornada': conf_jornada,
            'conf_fecham': conf_fecham,
            'done_toxicologico_cnh': convert_date(data.get('done_toxicologico_cnh', '')),
            'vencimento_toxicologico_cnh': convert_date(data.get('vencimento_toxicologico_cnh', '')),
            'email': data.get('email', '').strip()
        }
        
        # ===== 6. INSERIR NO BANCO DE DADOS =====
        motorist_id = motorist_driver.create_motorist_with_id(**motorist_data)
        
        if motorist_id:
            routes_logger.register_log(
                "Motorista criado via API", 
                f"ID: {motorist_id}, Nome: {motorist_data['nome']}, CPF: {motorist_data['cpf']}"
            )
            
            # ===== 7. INTEGRAÇÃO COM GOOGLE =====
            try:
                # Inicializar integração com Google se necessário
                global google_integration
                if google_integration is None:
                    try:
                        google_integration = GoogleIntegration()
                    except Exception as e:
                        routes_logger.register_log(
                            "Integração Google", 
                            f"ERRO ao inicializar integração Google: {str(e)}"
                        )
                        google_integration = None
                
                if google_integration is not None:
                    # Adicionar timeout para evitar travamento
                    import threading
                    import time
                    
                    google_result = {'success': False, 'error': None}
                    
                    def google_integration_thread():
                        try:
                            google_result['success'] = google_integration.process_new_motorist(motorist_data)
                        except Exception as e:
                            google_result['error'] = str(e)
                    
                    # Executar integração em thread separada com timeout
                    thread = threading.Thread(target=google_integration_thread)
                    thread.daemon = True
                    thread.start()
                    
                    # Aguardar máximo 30 segundos
                    thread.join(timeout=30)
                    
                    if thread.is_alive():
                        routes_logger.register_log(
                            "Integração Google", 
                            f"TIMEOUT: Integração com Google demorou mais de 30 segundos para motorista {motorist_data['nome']}"
                        )
                        # Continuar mesmo com timeout - motorista já foi salvo no BD
                    elif google_result['error']:
                        routes_logger.register_log(
                            "Integração Google", 
                            f"ERRO: {google_result['error']} para motorista {motorist_data['nome']}"
                        )
                    elif google_result['success']:
                        routes_logger.register_log(
                            "Integração Google", 
                            f"Motorista {motorist_data['nome']} processado com sucesso no Google Sheets e Forms"
                        )
                    else:
                        routes_logger.register_log(
                            "Integração Google", 
                            f"ERRO: Falha ao processar motorista {motorist_data['nome']} no Google"
                        )
                else:
                    routes_logger.register_log(
                        "Integração Google", 
                        f"AVISO: Integração com Google não disponível para motorista {motorist_data['nome']}"
                    )
                    
            except Exception as e:
                routes_logger.register_log(
                    "Integração Google", 
                    f"ERRO na integração Google: {str(e)}"
                )
            
            return jsonify({
                'success': True, 
                'message': 'Motorista cadastrado com sucesso',
                'motorist_id': motorist_id
            }), 201
        else:
            return jsonify({
                'success': False, 
                'message': 'Erro ao criar motorista no banco de dados'
            }), 500
            
    except Exception as e:
        routes_logger.register_log("Erro na API de criação de motorista", str(e))
        return jsonify({
            'success': False, 
            'message': f'Erro interno do servidor: {str(e)}'
        }), 500
            

# ========================================
# ROTAS PARA EMPRESAS
# ========================================

@config_bp.route('/company_config')
@route_access_required
def company_config():
    """Página de configuração de empresas"""
    all_companies = company_driver.retrieve_all_companies()
    all_companies = [Company(company) for company in all_companies]
    return render_template('company_config.html', companies=all_companies)


@config_bp.route('/companies', methods=['GET', 'POST'])
@route_access_required
def manage_companies():
    """Gerencia empresas (criar, editar, excluir)"""
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            # Criar nova empresa
            enterprise = request.form.get('enterprise', '').strip()
            cnpj = request.form.get('cnpj', '').strip()
            
            if not enterprise:
                flash('Nome da empresa é obrigatório!', 'error')
                return redirect(url_for('config.company_config'))
            
            if not cnpj:
                flash('CNPJ é obrigatório!', 'error')
                return redirect(url_for('config.company_config'))
            
            try:
                # Formatar CNPJ se necessário
                if len(cnpj.replace('.', '').replace('/', '').replace('-', '')) == 14:
                    cnpj = company_driver.format_cnpj(cnpj)
                
                company_id = company_driver.create_company(enterprise, cnpj)
                flash(f'Empresa "{enterprise}" criada com sucesso!', 'success')
                
            except ValueError as e:
                flash(f'Erro de validação: {str(e)}', 'error')
            except Exception as e:
                flash(f'Erro ao criar empresa: {str(e)}', 'error')
                
        elif action == 'update':
            # Atualizar empresa
            company_id = request.form.get('company_id')
            enterprise = request.form.get('enterprise', '').strip()
            cnpj = request.form.get('cnpj', '').strip()
            
            if not enterprise or not cnpj:
                flash('Todos os campos são obrigatórios!', 'error')
                return redirect(url_for('config.company_config'))
            
            try:
                # Formatar CNPJ se necessário
                if len(cnpj.replace('.', '').replace('/', '').replace('-', '')) == 14:
                    cnpj = company_driver.format_cnpj(cnpj)
                
                affected = company_driver.update_company(
                    set_columns=['enterprise', 'cnpj'],
                    set_values=(enterprise, cnpj),
                    where_columns=['id'],
                    where_values=(company_id,)
                )
                
                if affected > 0:
                    flash(f'Empresa "{enterprise}" atualizada com sucesso!', 'success')
                else:
                    flash('Empresa não encontrada!', 'error')
                    
            except ValueError as e:
                flash(f'Erro de validação: {str(e)}', 'error')
            except Exception as e:
                flash(f'Erro ao atualizar empresa: {str(e)}', 'error')
                
        elif action == 'delete':
            # Excluir empresa
            company_id = request.form.get('company_id')
            
            try:
                # Verificar se a empresa está sendo usada por motoristas
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM motorists WHERE empresa = (SELECT enterprise FROM companies WHERE id = ?)", (company_id,))
                count = cursor.fetchone()[0]
                conn.close()
                
                if count > 0:
                    flash('Não é possível excluir a empresa pois existem motoristas vinculados a ela!', 'error')
                else:
                    affected = company_driver.delete_company(['id'], (company_id,))
                    if affected > 0:
                        flash('Empresa excluída com sucesso!', 'success')
                    else:
                        flash('Empresa não encontrada!', 'error')
                        
            except Exception as e:
                flash(f'Erro ao excluir empresa: {str(e)}', 'error')
    
    return redirect(url_for('config.company_config'))


@config_bp.route('/api/companies', methods=['POST'])
@route_access_required
def api_create_company():
    """API para criar empresa via AJAX"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False, 
                'message': 'Dados não fornecidos'
            }), 400
        
        enterprise = data.get('enterprise', '').strip()
        cnpj = data.get('cnpj', '').strip()
        
        # Validações
        if not enterprise:
            return jsonify({
                'success': False, 
                'message': 'Nome da empresa é obrigatório'
            }), 400
        
        if not cnpj:
            return jsonify({
                'success': False, 
                'message': 'CNPJ é obrigatório'
            }), 400
        
        # Formatar CNPJ se necessário
        if len(cnpj.replace('.', '').replace('/', '').replace('-', '')) == 14:
            cnpj = company_driver.format_cnpj(cnpj)
        
        # Criar empresa
        company_id = company_driver.create_company(enterprise, cnpj)
        
        if company_id:
            routes_logger.register_log(
                "Empresa criada via API", 
                f"ID: {company_id}, Nome: {enterprise}, CNPJ: {cnpj}"
            )
            return jsonify({
                'success': True, 
                'message': 'Empresa cadastrada com sucesso',
                'company_id': company_id
            }), 201
        else:
            return jsonify({
                'success': False, 
                'message': 'Erro ao criar empresa no banco de dados'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False, 
            'message': f'Erro de validação: {str(e)}'
        }), 400
    except Exception as e:
        routes_logger.register_log("Erro na API de criação de empresa", str(e))
        return jsonify({
            'success': False, 
            'message': f'Erro interno do servidor: {str(e)}'
        }), 500


@config_bp.route('/motorist_details/<int:motorist_id>')
@route_access_required
def motorist_details(motorist_id):
    """Exibe os detalhes completos de um motorista específico"""
    try:
        # Buscar motorista por ID
        motorist_data = motorist_driver.retrieve_motorist(['id'], (motorist_id,))
        
        if not motorist_data:
            flash('Motorista não encontrado!', 'error')
            return redirect(url_for('config.motorist_config'))
        
        # Criar objeto Motorist com os dados
        motorist = Motorist(motorist_data)
        
        return render_template('motorist_details.html', motorist=motorist)
        
    except Exception as e:
        routes_logger.register_log("Erro ao buscar detalhes do motorista", str(e))
        flash(f'Erro ao carregar detalhes do motorista: {str(e)}', 'error')
        return redirect(url_for('config.motorist_config'))


@config_bp.route('/api/update_motorist_card', methods=['POST'])
@route_access_required
def api_update_motorist_card():
    """API para atualizar dados de um card específico do motorista"""
    try:
        motorist_id = request.form.get('motorist_id')
        card_type = request.form.get('card_type')
        
        if not motorist_id or not card_type:
            return jsonify({
                'success': False,
                'message': 'ID do motorista e tipo do card são obrigatórios'
            }), 400
        
        try:
            motorist_id = int(motorist_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'ID do motorista deve ser um número válido'
            }), 400
        
        # Verificar se o motorista existe
        motorist_data = motorist_driver.retrieve_motorist(['id'], (motorist_id,))
        if not motorist_data:
            return jsonify({
                'success': False,
                'message': 'Motorista não encontrado'
            }), 404
        
        # Preparar dados para atualização baseado no tipo do card
        update_data = {}
        
        if card_type == 'personal':
            # Informações pessoais
            fields = ['nome', 'cpf', 'rg', 'data_nascimento', 'estado_civil', 'filiacao', 'filhos']
            for field in fields:
                value = request.form.get(field, '').strip()
                if value:  # Só atualiza se o valor não estiver vazio
                    update_data[field] = value
        
        elif card_type == 'professional':
            # Informações profissionais
            fields = ['cargo', 'empresa', 'operacao', 'data_admissao', 'codigo_sap', 'ctps', 'serie']
            for field in fields:
                value = request.form.get(field, '').strip()
                if value:  # Só atualiza se o valor não estiver vazio
                    update_data[field] = value
        
        elif card_type == 'documents':
            # Documentos de habilitação
            fields = ['cnh', 'primeira_cnh', 'data_expedicao', 'vencimento_cnh', 'done_mopp', 'vencimento_mopp']
            for field in fields:
                value = request.form.get(field, '').strip()
                if value:  # Só atualiza se o valor não estiver vazio
                    update_data[field] = value
        
        elif card_type == 'medical':
            # Exames médicos
            fields = ['done_toxicologico_clt', 'vencimento_toxicologico_clt', 'done_toxicologico_cnh', 
                     'vencimento_toxicologico_cnh', 'done_aso_semestral', 'vencimento_aso_semestral',
                     'done_aso_periodico', 'vencimento_aso_periodico']
            for field in fields:
                value = request.form.get(field, '').strip()
                if value:  # Só atualiza se o valor não estiver vazio
                    update_data[field] = value
        
        elif card_type == 'other':
            # Outros documentos
            fields = ['done_buonny', 'vencimento_buonny', 'telefone', 'email', 'endereco']
            for field in fields:
                value = request.form.get(field, '').strip()
                if value:  # Só atualiza se o valor não estiver vazio
                    update_data[field] = value
        
        elif card_type == 'verification-jornada':
            # Verificação de Jornada
            value = request.form.get('conf_jornada', '').strip()
            if value:  # Só atualiza se o valor não estiver vazio
                update_data['conf_jornada'] = value
        
        elif card_type == 'verification-fechamento':
            # Verificação de Fechamento
            value = request.form.get('conf_fecham', '').strip()
            if value:  # Só atualiza se o valor não estiver vazio
                update_data['conf_fecham'] = value
        
        else:
            return jsonify({
                'success': False,
                'message': 'Tipo de card inválido'
            }), 400
        
        if not update_data:
            return jsonify({
                'success': False,
                'message': 'Nenhum dado válido para atualizar'
            }), 400
        
        # Atualizar motorista no banco de dados
        set_columns = list(update_data.keys())
        set_values = tuple(update_data.values())
        
        try:
            affected = motorist_driver.update_motorist(set_columns, set_values, ['id'], (motorist_id,))
            
            # Garantir que affected seja um inteiro
            if affected is None:
                affected = 0
            elif not isinstance(affected, int):
                affected = 0
            
            if affected > 0:
                routes_logger.register_log(
                    "Motorista atualizado via API", 
                    f"ID: {motorist_id}, Card: {card_type}, Campos: {list(update_data.keys())}"
                )
                return jsonify({
                    'success': True,
                    'message': 'Dados atualizados com sucesso'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Nenhum dado foi atualizado. Verifique se os dados são diferentes dos atuais.'
                }), 400
                
        except Exception as e:
            routes_logger.register_log("Erro na atualização de motorista", str(e))
            return jsonify({
                'success': False,
                'message': f'Erro ao atualizar dados: {str(e)}'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Erro de validação: {str(e)}'
        }), 400
    except Exception as e:
        routes_logger.register_log("Erro na API de atualização de motorista", str(e))
        return jsonify({
            'success': False,
            'message': f'Erro interno do servidor: {str(e)}'
        }), 500

@config_bp.route('/api/disable_motorist', methods=['POST'])
@route_access_required
def api_disable_motorist():
    """API para desligar um motorista (alterar status para Desligado)"""
    try:
        motorist_id = request.form.get('motorist_id')
        
        if not motorist_id:
            return jsonify({
                'success': False,
                'message': 'ID do motorista é obrigatório'
            }), 400
        
        motorist_id = int(motorist_id)
        
        # Verificar se o motorista existe
        motorist_data = motorist_driver.retrieve_motorist(['id'], (motorist_id,))
        if not motorist_data:
            return jsonify({
                'success': False,
                'message': 'Motorista não encontrado'
            }), 404
        
        # Atualizar o motorista com os novos valores
        set_columns = ['status', 'conf_jornada', 'conf_fecham']
        set_values = ('Desligado', 'Inativo', 'Inativo')
        
        affected = motorist_driver.update_motorist(set_columns, set_values, ['id'], (motorist_id,))
        
        if affected > 0:
            routes_logger.register_log(
                "Motorista desligado",
                f"ID: {motorist_id}, Status alterado para Desligado"
            )
            return jsonify({
                'success': True,
                'message': 'Motorista desligado com sucesso'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhuma alteração foi realizada'
            }), 400
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Erro de validação: {str(e)}'
        }), 400
    except Exception as e:
        routes_logger.register_log("Erro na API de desligamento de motorista", str(e))
        return jsonify({
            'success': False,
            'message': f'Erro interno do servidor: {str(e)}'
        }), 500

