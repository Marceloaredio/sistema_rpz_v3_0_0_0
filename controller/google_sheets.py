import gspread
from google.oauth2.service_account import Credentials
try:
    import pandas as pd
except ImportError:
    print("AVISO: pandas não disponível, usando stub")
    import pandas_stub as pd
from datetime import datetime
import configparser
import os
import hashlib
from controller.utils import CustomLogger

class GoogleSheetsManager:
    """
    Classe para gerenciar a integração com Google Sheets
    """
    
    def __init__(self, logger: CustomLogger):
        self.logger = logger
        self.config = configparser.ConfigParser()
        # Lê o config correto da pasta config/
        self.config.read('config/config.ini', encoding='utf-8')
        
        # Configurações do Google Sheets
        # Respeita o caminho definido no config.ini; se não houver, tenta defaults conhecidos
        self.credentials_file = self.config.get('GOOGLE_SHEETS', 'CREDENTIALS_FILE', fallback=None)
        if not self.credentials_file:
            # defaults conhecidos
            if os.path.exists('credentials/credentials.json'):
                self.credentials_file = 'credentials/credentials.json'
            elif os.path.exists('credentials/google_service_account.json'):
                self.credentials_file = 'credentials/google_service_account.json'
            else:
                # mantém um fallback para mensagem mais amigável adiante
                self.credentials_file = 'credentials/credentials.json'
        self.spreadsheet_name = self.config.get('GOOGLE_SHEETS', 'SPREADSHEET_NAME', fallback='RPZ_Dayoff_Export')
        self.spreadsheet_id = self.config.get('GOOGLE_SHEETS', 'SPREADSHEET_ID', fallback=None)
        self.worksheet_name = self.config.get('GOOGLE_SHEETS', 'WORKSHEET_NAME', fallback='Folgas')
        
        # Caminho do banco de dados
        from global_vars import DB_PATH
        self.db_path = DB_PATH
        
        # Mapeamento de motivos para abreviações
        self.motivo_mapping = {
            'folga': 'FO',
            'manutenção': 'MAN',
            'férias': 'FE',
            'carga e descarga': 'C/D',
            'at. médico': 'AT.M',
            'afastamento': 'AFS',
            'lic. óbito': 'L.OB',
            'lic. paternidade': 'L.PT'
        }
        
        self.client = None
        # Não fazer autenticação no construtor - será feita quando necessário
    
    def _generate_hash(self, data, motorista, motivo):
        """
        Gera uma hash baseada na data, motorista e motivo
        """
        combined = f"{data}{motorista}{motivo}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()[:8].upper()
    
    def _format_date(self, date_str):
        """
        Converte data do formato DD-MM-YYYY para DD/MM/AAAA
        """
        try:
            if '-' in date_str:
                day, month, year = date_str.split('-')
                return f"{day}/{month}/{year}"
            return date_str
        except:
            return date_str
    
    def _map_motivo(self, motivo):
        """
        Mapeia o motivo para a abreviação correspondente
        """
        motivo_lower = motivo.lower().strip()
        return self.motivo_mapping.get(motivo_lower, motivo.upper())
    
    def _authenticate(self):
        """
        Autentica com o Google Sheets usando credenciais de conta de serviço
        """
        try:
            # Verificar se o arquivo de credenciais existe
            if not os.path.exists(self.credentials_file):
                self.logger.register_log(f"Arquivo de credenciais não encontrado: {self.credentials_file}")
                raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {self.credentials_file}")
            
            # Configurar escopo
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Carregar credenciais
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scope
            )
            
            # Criar cliente
            self.client = gspread.authorize(credentials)
            self.logger.register_log("Autenticação com Google Sheets realizada com sucesso")
            
        except Exception as e:
            self.logger.register_log(f"Erro na autenticação com Google Sheets: {str(e)}")
            raise
    
    def create_or_get_spreadsheet(self):
        """
        Abre uma planilha existente pelo ID ou cria uma nova se o ID não for fornecido
        """
        try:
            if self.spreadsheet_id:
                # Abrir planilha existente pelo ID
                spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                self.logger.register_log(f"Planilha aberta pelo ID: {self.spreadsheet_id}")
            else:
                # Tentar abrir planilha existente pelo nome
                try:
                    spreadsheet = self.client.open(self.spreadsheet_name)
                    spreadsheet.share('rpztransportes4.0@gmail.com', perm_type='user', role='writer')
                    self.logger.register_log(f"Planilha existente encontrada pelo nome: {self.spreadsheet_name}")
                except gspread.SpreadsheetNotFound:
                    # Criar nova planilha
                    spreadsheet = self.client.create(self.spreadsheet_name)
                    spreadsheet.share('rpztransportes4.0@gmail.com', perm_type='user', role='writer')
                    self.logger.register_log(f"Nova planilha criada: {self.spreadsheet_name}")
            
            return spreadsheet
            
        except Exception as e:
            self.logger.register_log(f"Erro ao abrir/criar planilha: {str(e)}")
            raise
    
    def create_or_get_worksheet(self, spreadsheet):
        """
        Cria uma nova aba ou obtém uma existente
        """
        try:
            worksheet = spreadsheet.worksheet(self.worksheet_name)
            self.logger.register_log(f"Aba existente encontrada: {self.worksheet_name}")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows=1000, cols=10)
            self.logger.register_log(f"Nova aba criada: {self.worksheet_name}")
        
        return worksheet
    
    def export_dayoff_data(self, dayoff_data):
        """
        Exporta dados da tabela dayoff para o Google Sheets
        
        Args:
            dayoff_data: Lista de tuplas com dados de dayoff (motorist_id, data, motivo)
        
        Returns:
            dict: {'success': bool, 'link': str, 'error': str}
        """
        try:
            # Fazer autenticação se ainda não foi feita
            if not self.client:
                self._authenticate()
            
            # Importar motorist_driver para buscar nomes
            from model.drivers.motorist_driver import MotoristDriver
            motorist_driver = MotoristDriver(self.logger, self.db_path)
            
            # Criar ou obter planilha e aba
            spreadsheet = self.create_or_get_spreadsheet()
            worksheet = self.create_or_get_worksheet(spreadsheet)
            
            # Preparar dados para exportação
            headers = ['ID', 'Data', 'Motorista', 'Motivo']
            data_rows = []
            
            for row in dayoff_data:
                motorist_id, data, motivo = row
                
                try:
                    motorist_info = motorist_driver.retrieve_motorist(['id'], (motorist_id,))
                    motorist_name = motorist_info[1] if motorist_info and len(motorist_info) > 1 else f"ID {motorist_id}"
                except:
                    motorist_name = f"ID {motorist_id}"
                
                formatted_date = self._format_date(data)
                
                mapped_motivo = self._map_motivo(motivo)
                
                hash_id = self._generate_hash(formatted_date, motorist_name, mapped_motivo)
                
                data_rows.append([
                    hash_id,
                    formatted_date,
                    motorist_name,
                    mapped_motivo
                ])
            
            worksheet.clear()
            
            worksheet.update('A1:D1', [headers])
            
            if data_rows:
                worksheet.update(f'A2:D{len(data_rows)+1}', data_rows)
            
            worksheet.format('A1:D1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            worksheet.columns_auto_resize(0, 3)
            
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            self.logger.print(f"Link da planilha: {spreadsheet_url}")
            
            self.logger.register_log(f"Dados exportados com sucesso: {len(data_rows)} registros")
            
            return {
                'success': True,
                'link': spreadsheet_url,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"Erro ao exportar dados para Google Sheets: {str(e)}"
            self.logger.register_log(error_msg)
            return {
                'success': False,
                'link': None,
                'error': error_msg
            } 