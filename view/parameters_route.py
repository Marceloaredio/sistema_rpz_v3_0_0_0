from flask import Blueprint, request, jsonify
from controller.decorators import route_access_required
from controller.utils import CustomLogger
from global_vars import DEBUG, DB_PATH

params_bp = Blueprint('parametros', __name__)

params_logger = CustomLogger(source="PARAMS", debug=DEBUG)

@params_bp.route('/api/params/update', methods=['POST'])
@route_access_required
def atualizar_parametros():
    """
    Atualiza os parâmetros principais (diária padrão e ajuda alimentação).
    """
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        
        data = request.get_json()
        diaria_padrao = data.get('diaria_padrao')
        ajuda_alimentacao = data.get('ajuda_alimentacao')
        
        if diaria_padrao is None or ajuda_alimentacao is None:
            return jsonify({"mensagem": "Valores obrigatórios não fornecidos"}), 400
        
        parameters_driver = ParametersDriver(logger=params_logger, db_path=DB_PATH)
        
        # Atualizar diária padrão
        result1 = parameters_driver.update_parameter('diaria_padrao', str(diaria_padrao))
        
        # Atualizar ajuda alimentação
        result2 = parameters_driver.update_parameter('ajuda_alimentacao', str(ajuda_alimentacao))
        
        if result1 > 0 or result2 > 0:
            return jsonify({"mensagem": "Parâmetros atualizados com sucesso"})
        else:
            return jsonify({"mensagem": "Nenhum parâmetro foi atualizado"}), 400
            
    except Exception as e:
        params_logger.register_log(f"Erro ao atualizar parâmetros: {e}")
        return jsonify({"mensagem": f"Erro ao atualizar parâmetros: {str(e)}"}), 500


@params_bp.route('/api/params/criteria/add', methods=['POST'])
@route_access_required
def adicionar_criterio():
    """
    Adiciona um novo critério especial para diária.
    """
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        
        data = request.get_json()
        if not data:
            return jsonify({"mensagem": "Dados não fornecidos"}), 400
            
        valor_filtro = data.get('valor_filtro')
        valor_diaria = data.get('valor_diaria')
        valor_ajuda_alimentacao = data.get('valor_ajuda_alimentacao')
        descricao = data.get('descricao')
        carga_horaria_especial = data.get('carga_horaria_especial', 'Padrão')
        
        params_logger.print(f"Dados recebidos: valor_filtro={valor_filtro}, valor_diaria={valor_diaria}, valor_ajuda_alimentacao={valor_ajuda_alimentacao}, descricao={descricao}, carga_horaria_especial={carga_horaria_especial}")
        
        if not all([valor_filtro, valor_diaria is not None, valor_ajuda_alimentacao is not None]):
            return jsonify({"mensagem": "Todos os campos obrigatórios devem ser preenchidos"}), 400
        
        parameters_driver = ParametersDriver(logger=params_logger, db_path=DB_PATH)
        criterio_id = parameters_driver.add_criterio_diaria(valor_filtro, float(valor_diaria), float(valor_ajuda_alimentacao), descricao, carga_horaria_especial)
        
        params_logger.print(f"ID do critério retornado: {criterio_id}")
        
        if criterio_id > 0:
            # Buscar o critério recém-criado para retornar ao frontend
            try:
                # Query para buscar o critério sem considerar campo ativo
                query = '''
                SELECT id, tipo_filtro, valor_filtro, valor_diaria, valor_ajuda_alimentacao, descricao, carga_horaria_especial
                FROM criterios_diaria 
                WHERE id = ?
                '''
                criterio_result = parameters_driver.exec_query(query, params=(criterio_id,), fetchone=True)
                params_logger.print(f"Resultado da busca do critério: {criterio_result}")
                
                if criterio_result and isinstance(criterio_result, (list, tuple)) and len(criterio_result) >= 7:
                    criterio = {
                        'id': criterio_result[0],
                        'tipo_filtro': criterio_result[1],
                        'valor_filtro': criterio_result[2],
                        'valor_diaria': criterio_result[3],
                        'valor_ajuda_alimentacao': criterio_result[4],
                        'descricao': criterio_result[5],
                        'carga_horaria_especial': criterio_result[6]
                    }
                    params_logger.print(f"Critério encontrado: {criterio}")
                    return jsonify({
                        "mensagem": "Critério adicionado com sucesso",
                        "criterio": criterio
                    })
                else:
                    # Se não conseguiu buscar o critério, recarregar a página
                    params_logger.print("Não conseguiu buscar o critério, retornando reload=True")
                    return jsonify({"mensagem": "Critério adicionado com sucesso", "reload": True})
            except Exception as e:
                params_logger.register_log(f"Erro ao buscar critério criado: {e}")
                return jsonify({"mensagem": "Critério adicionado com sucesso", "reload": True})
        else:
            params_logger.print(f"Erro: criterio_id = {criterio_id}")
            return jsonify({"mensagem": "Erro ao adicionar critério"}), 400
            
    except Exception as e:
        params_logger.register_log(f"Erro ao adicionar critério: {e}")
        return jsonify({"mensagem": f"Erro ao adicionar critério: {str(e)}"}), 500


@params_bp.route('/api/params/criteria/update', methods=['POST'])
@route_access_required
def update_criteria():
    """
    Atualiza um critério existente.
    """
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        
        data = request.get_json()
        criterio_id = data.get('criterio_id')
        valor_filtro = data.get('valor_filtro')
        valor_diaria = data.get('valor_diaria')
        valor_ajuda_alimentacao = data.get('valor_ajuda_alimentacao')
        descricao = data.get('descricao')
        carga_horaria_especial = data.get('carga_horaria_especial', 'Padrão')
        
        if not all([criterio_id, valor_filtro, valor_diaria is not None, valor_ajuda_alimentacao is not None]):
            return jsonify({"mensagem": "Todos os campos obrigatórios devem ser preenchidos"}), 400
        
        parameters_driver = ParametersDriver(logger=params_logger, db_path=DB_PATH)
        result = parameters_driver.update_criterio_diaria(criterio_id, valor_filtro, float(valor_diaria), float(valor_ajuda_alimentacao), descricao, carga_horaria_especial)
        
        if result > 0:
            return jsonify({"mensagem": "Critério atualizado com sucesso"})
        else:
            return jsonify({"mensagem": "Erro ao atualizar critério"}), 400
            
    except Exception as e:
        params_logger.register_log(f"Erro ao atualizar critério: {e}")
        return jsonify({"mensagem": f"Erro ao atualizar critério: {str(e)}"}), 500


@params_bp.route('/api/params/criteria/delete', methods=['POST'])
@route_access_required
def delete_criteria():
    """
    Remove um critério de diária.
    """
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        
        data = request.get_json()
        criterio_id = data.get('criterio_id')
        
        if not criterio_id:
            return jsonify({"mensagem": "ID do critério não fornecido"}), 400
        
        parameters_driver = ParametersDriver(logger=params_logger, db_path=DB_PATH)
        result = parameters_driver.delete_criterio_diaria(criterio_id)
        
        if result > 0:
            return jsonify({"mensagem": "Critério excluído com sucesso"})
        else:
            return jsonify({"mensagem": "Erro ao excluir critério"}), 400
            
    except Exception as e:
        params_logger.register_log(f"Erro ao excluir critério: {e}")
        return jsonify({"mensagem": f"Erro ao excluir critério: {str(e)}"}), 500


@params_bp.route('/api/params/holidays/get', methods=['GET'])
@route_access_required
def listar_feriados():
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        from datetime import datetime
        ano = request.args.get('ano', type=int)
        if not ano:
            ano = datetime.now().year
        parameters_driver = ParametersDriver(logger=params_logger, db_path=DB_PATH)
        params = parameters_driver.get_all_parameters(ano_busca=ano)
        feriados = params.get('feriados', [])
        return jsonify({'feriados': feriados})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@params_bp.route('/api/params/holidays/add', methods=['POST'])
@route_access_required
def add_holiday():
    """
    Adiciona um novo feriado.
    """
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        data = request.get_json()
        data_feriado = data.get('data')
        descricao = data.get('descricao')
        tipo = data.get('tipo', 'regional')
        ano = data.get('ano')
        if not all([data_feriado, descricao]):
            return jsonify({"mensagem": "Data e descrição são obrigatórias"}), 400
        parameters_driver = ParametersDriver(logger=params_logger, db_path=DB_PATH)
        result = parameters_driver.add_feriado(data_feriado, descricao, tipo, ano)
        if result > 0:
            return jsonify({"mensagem": "Feriado adicionado com sucesso"})
        else:
            return jsonify({"mensagem": "Erro ao adicionar feriado"}), 400
    except Exception as e:
        params_logger.register_log(f"Erro ao adicionar feriado: {e}")
        return jsonify({"mensagem": f"Erro ao adicionar feriado: {str(e)}"}), 500


@params_bp.route('/api/params/holidays/delete', methods=['POST'])
@route_access_required
def delete_holiday():
    """
    Remove um feriado.
    """
    try:
        from model.drivers.parameters_driver import ParametersDriver
        from global_vars import DB_PATH
        data = request.get_json()
        feriado_id = data.get('feriado_id')
        ano = data.get('ano')
        if not feriado_id:
            return jsonify({"mensagem": "ID do feriado não fornecido"}), 400
        parameters_driver = ParametersDriver(logger=params_logger, db_path=DB_PATH)
        result = parameters_driver.delete_feriado(feriado_id)
        if result > 0:
            return jsonify({"mensagem": "Feriado excluído com sucesso"})
        else:
            return jsonify({"mensagem": "Erro ao excluir feriado"}), 400
    except Exception as e:
        params_logger.register_log(f"Erro ao excluir feriado: {e}")
        return jsonify({"mensagem": f"Erro ao excluir feriado: {str(e)}"}), 500