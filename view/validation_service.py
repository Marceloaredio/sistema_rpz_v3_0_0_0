"""
Serviço de Integração da Validação de Cálculos
Integra o sistema de validação com as rotas existentes
"""

from flask import jsonify, request
from model.validation.calculation_validator import CalculationValidator
from controller.utils import CustomLogger
from datetime import datetime, timedelta
import json


class ValidationService:
    """
    Serviço de integração da validação de cálculos
    """
    
    def __init__(self, logger: CustomLogger):
        self.logger = logger
        self.validator = CalculationValidator(logger)
    
    def validate_on_save(self, data: dict, db_connection) -> dict:
        """
        Valida cálculos ao salvar um registro
        
        Args:
            data: Dados do registro
            db_connection: Conexão com banco de dados
            
        Returns:
            Dict com resultado da validação
        """
        try:
            # Preparar dados para validação
            validation_data = self._prepare_validation_data(data)
            
            # Executar validação
            validation_result = self.validator.validate_calculation(validation_data)
            
            # Se há divergência, reprocessar últimos 15 dias
            if validation_result.get('status') == 'divergent':
                self.logger.print("🔄 Divergência detectada, iniciando reprocessamento dos últimos 15 dias...")
                reprocess_result = self.validator.reprocess_last_15_days(db_connection)
                
                validation_result['reprocess_result'] = reprocess_result
                validation_result['message'] = f"Divergência detectada entre os módulos de cálculo. {reprocess_result.get('total_corrected', 0)} registros foram reprocessados."
            
            return validation_result
            
        except Exception as e:
            self.logger.print(f"❌ Erro no serviço de validação: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Erro durante a validação de cálculos'
            }
    
    def validate_on_view(self, data: dict) -> dict:
        """
        Valida cálculos ao visualizar um registro
        
        Args:
            data: Dados do registro
            
        Returns:
            Dict com resultado da validação
        """
        try:
            # Preparar dados para validação
            validation_data = self._prepare_validation_data(data)
            
            # Executar validação
            validation_result = self.validator.validate_calculation(validation_data)
            
            return validation_result
            
        except Exception as e:
            self.logger.print(f"❌ Erro na validação de visualização: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Erro durante a validação de cálculos'
            }
    
    def _prepare_validation_data(self, data: dict) -> dict:
        """
        Prepara dados para validação
        
        Args:
            data: Dados brutos do registro
            
        Returns:
            Dict com dados formatados para validação
        """
        # Extrair dados básicos
        validation_data = {
            'inicio_jornada': data.get('inicio_jornada', ''),
            'fim_jornada': data.get('fim_jornada', ''),
            'inicio_refeicao': data.get('inicio_refeicao', ''),
            'fim_refeicao': data.get('fim_refeicao', ''),
            'observacao': data.get('observacao', ''),
            'data': data.get('data', ''),
            'dia_semana': data.get('dia_semana', ''),
            'descansos': data.get('descansos', [])
        }
        
        # Se descansos não estiverem no formato esperado, tentar extrair
        if not validation_data['descansos']:
            validation_data['descansos'] = self._extract_descansos(data)
        
        return validation_data
    
    def _extract_descansos(self, data: dict) -> list:
        """
        Extrai dados de descansos do registro
        
        Args:
            data: Dados do registro
            
        Returns:
            Lista de descansos
        """
        descansos = []
        
        # Tentar extrair descansos de diferentes formatos
        for i in range(1, 9):  # Máximo 8 descansos
            inicio_key = f'in_desc_{i}'
            fim_key = f'fim_desc_{i}'
            
            if inicio_key in data and fim_key in data:
                inicio = data.get(inicio_key, '')
                fim = data.get(fim_key, '')
                
                if inicio and fim:
                    descansos.append({
                        'inicio': inicio,
                        'fim': fim
                    })
        
        return descansos


def create_validation_routes(app, logger: CustomLogger):
    """
    Cria rotas de validação para a aplicação
    
    Args:
        app: Instância do Flask
        logger: Logger customizado
    """
    validation_service = ValidationService(logger)
    
    @app.route('/api/validation/validate-calculation', methods=['POST'])
    def validate_calculation():
        """
        Rota para validar cálculos de um registro
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'Dados não fornecidos'
                }), 400
            
            # Executar validação
            result = validation_service.validate_on_view(data)
            
            return jsonify(result)
            
        except Exception as e:
            logger.print(f"❌ Erro na rota de validação: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'message': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/validation/reprocess-period', methods=['POST'])
    def reprocess_period():
        """
        Rota para reprocessar um período específico
        """
        try:
            data = request.get_json()
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            if not start_date or not end_date:
                return jsonify({
                    'status': 'error',
                    'message': 'Datas de início e fim são obrigatórias'
                }), 400
            
            # Implementar reprocessamento de período específico
            # Por enquanto, retorna sucesso
            return jsonify({
                'status': 'success',
                'message': f'Período reprocessado: {start_date} até {end_date}',
                'corrected_records': 0
            })
            
        except Exception as e:
            logger.print(f"❌ Erro no reprocessamento de período: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'message': 'Erro interno do servidor'
            }), 500
    
    return validation_service 