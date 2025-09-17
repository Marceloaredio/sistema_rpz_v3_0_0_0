#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
from controller.utils import CustomLogger

class GoogleIntegration:
    def __init__(self):
        self.logger = CustomLogger(source="GOOGLE_INTEGRATION", debug=True)
        self.log_file = "logs/verif_forms_google.txt"
        
        # Configurações do Google Sheets
        self.spreadsheet_id = "1NauRIwyzMaObJ46zNLj0c-1aS7pHzUwXWaM6DSiAjHs"
        self.sheet_name = "Motoristas"
        
        # Configurações dos Google Forms
        self.forms_config = [
            {"id": "1kHjVfLPHnHWaHgeWMa2JV_fAYflFa2P_y3pnqJWHfGI", "campo": "MOTORISTA:"},
            {"id": "1UXMvIgpMrc8adfNNeEOgaL02hHQpWdi1r9TTs1FvLVc", "campo": "MOTORISTA:"},
            {"id": "1ZZk78DbOOMMn_MO8RBPcPsE5juq51MxnOwdzHu2jLv8", "campo": "MOTORISTA:"},
            {"id": "1rU83EUmsEXPOGG-XHOmfJAztbYWVjqQNxPaGQNMX7D4", "campo": "Nome do Participante:"},
            {"id": "1FVyTkp70R3PIINfnlNQuUj3QvvJW5VOY9OsRonkyTaE", "campo": "Nome do Participante:"},
            {"id": "1pLmWsw7PdKUJt_cWeLCUET11TeDjsjG0FlZmN3pJad4", "campo": "Nome do Participante:"},
            {"id": "1AfrEwnT6k8uJ6fHyNRrAGDXrhvj_A1tkIoaPNVkw7iM", "campo": "Nome do Participante:"},
            {"id": "188ilDeyjtQmzuXIT4beXZBYnbPIgci0NjkuNQrTEv30", "campo": "Nome do Participante:"},
            {"id": "1htb51Sa5gMgZxbOgns6pavpV8gbRLaHShutgD5RQirs", "campo": "Nome do Participante:"}
        ]
        
        # Verificar se as dependências do Google estão disponíveis
        self.google_available = self._check_google_dependencies()
        
        if self.google_available:
            # Configurar credenciais
            self._setup_credentials()
        else:
            self._log("AVISO: Dependências do Google não encontradas. Integração desabilitada.")
            self._log("Para ativar: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client gspread")
    
    def _check_google_dependencies(self):
        """Verifica se as dependências do Google estão disponíveis"""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            self._log("Dependências do Google encontradas e importadas com sucesso")
            return True
        except ImportError as e:
            self._log(f"Erro ao importar dependências do Google: {str(e)}")
            return False
        except Exception as e:
            self._log(f"Erro inesperado ao verificar dependências: {str(e)}")
            return False
    
    def _setup_credentials(self):
        """Configura as credenciais do Google"""
        try:
            # Verificar se existe arquivo de credenciais
            creds_file = "credentials/credentials.json"
            if not os.path.exists(creds_file):
                self._log("ERRO: Arquivo de credenciais não encontrado: " + creds_file)
                self._log("Configure as credenciais conforme o arquivo GOOGLE_SETUP.md")
                return False
            
            # Importar dependências do Google
            import gspread
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            # Configurar escopo
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/forms'
            ]
            
            # Carregar credenciais
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            
            # Configurar cliente do Google Sheets
            self.gc = gspread.authorize(creds)
            
            # Configurar cliente do Google Forms
            self.forms_service = build('forms', 'v1', credentials=creds)
            
            self._log("Credenciais configuradas com sucesso")
            return True
            
        except Exception as e:
            self._log(f"ERRO ao configurar credenciais: {str(e)}")
            return False
    
    def _log(self, message):
        """Registra log no arquivo especificado"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            
            # Criar diretório logs se não existir
            os.makedirs("logs", exist_ok=True)
            
            # Escrever no arquivo de log
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message)
            
            # Também logar no sistema
            self.logger.register_log("GOOGLE_INTEGRATION", message)
            
        except Exception as e:
            print(f"ERRO ao escrever log: {str(e)}")
    
    def _retry_operation(self, operation, operation_name, max_retries=3, delay=2):
        """Executa uma operação com retry em caso de erro de quota"""
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                error_msg = str(e).lower()
                if ("quota" in error_msg or "limit" in error_msg or "429" in error_msg) and attempt < max_retries - 1:
                    self._log(f"Tentativa {attempt + 1} falhou por quota - aguardando {delay}s antes de tentar novamente")
                    time.sleep(delay)
                    delay *= 2  # Aumentar delay exponencialmente
                else:
                    self._log(f"ERRO na operação '{operation_name}': {str(e)}")
                    raise e
    
    def insert_motorist_to_sheet(self, motorist_data):
        """Insere dados do motorista na planilha do Google Sheets"""
        if not self.google_available:
            self._log("ERRO: Integração com Google não disponível")
            return False
            
        try:
            self._log("Iniciando inserção na planilha do Google Sheets")
            
            # Abrir planilha
            spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.sheet_name)
            
            # Preparar dados para inserção (37 colunas)
            row_data = [
                motorist_data.get('id', ''),
                motorist_data.get('nome', ''),
                motorist_data.get('data_admissao', ''),
                motorist_data.get('cpf', ''),
                motorist_data.get('cnh', ''),
                motorist_data.get('rg', ''),
                motorist_data.get('codigo_sap', ''),
                motorist_data.get('operacao', ''),
                motorist_data.get('ctps', ''),
                motorist_data.get('serie', ''),
                motorist_data.get('data_nascimento', ''),
                motorist_data.get('primeira_cnh', ''),
                motorist_data.get('data_expedicao', ''),
                motorist_data.get('vencimento_cnh', ''),
                motorist_data.get('done_mopp', ''),
                motorist_data.get('vencimento_mopp', ''),
                motorist_data.get('done_aso_semestral', ''),
                motorist_data.get('vencimento_aso_semestral', ''),
                motorist_data.get('done_aso_periodico', ''),
                motorist_data.get('vencimento_aso_periodico', ''),
                motorist_data.get('done_buonny', ''),
                motorist_data.get('vencimento_buonny', ''),
                motorist_data.get('telefone', ''),
                motorist_data.get('endereco', ''),
                motorist_data.get('filiacao', ''),
                motorist_data.get('estado_civil', ''),
                motorist_data.get('filhos', ''),
                motorist_data.get('cargo', ''),
                motorist_data.get('empresa', ''),
                motorist_data.get('status', ''),
                motorist_data.get('conf_jornada', ''),
                motorist_data.get('conf_fecham', ''),
                motorist_data.get('done_toxicologico_cnh', ''),
                motorist_data.get('vencimento_toxicologico_cnh', ''),
                motorist_data.get('email', ''),
                motorist_data.get('done_toxicologico_clt', ''),
                motorist_data.get('vencimento_toxicologico_clt', '')
            ]
            
            # Inserir na próxima linha disponível
            worksheet.append_row(row_data)
            self._log(f"Dados inseridos na planilha: {motorist_data.get('nome', '')}")
            
            # Ordenar planilha pela coluna B (nome)
            self._sort_sheet_by_name(worksheet)
            
            return True
            
        except Exception as e:
            self._log(f"ERRO ao inserir na planilha: {str(e)}")
            return False
    
    def _sort_sheet_by_name(self, worksheet):
        """Ordena a planilha pela coluna B (nome do motorista)"""
        try:
            self._log("Iniciando ordenação da planilha")
            
            # Obter todos os dados
            all_values = worksheet.get_all_values()
            
            if len(all_values) <= 1:  # Apenas cabeçalho ou vazio
                self._log("Planilha vazia ou apenas cabeçalho")
                return
            
            # Separar cabeçalho e dados
            header = all_values[0]
            data = all_values[1:]
            
            # Ordenar dados pela coluna B (índice 1)
            data.sort(key=lambda x: x[1].upper() if len(x) > 1 and x[1] else '')
            
            # Limpar planilha (exceto cabeçalho) com retry
            if len(data) > 0:
                self._retry_operation(lambda: worksheet.delete_rows(2, len(all_values)), "deletar linhas")
            
            # Reinserir dados ordenados com delay entre operações
            for i, row in enumerate(data):
                self._retry_operation(lambda: worksheet.append_row(row), f"inserir linha {i+1}")
                # Delay de 1 segundo entre inserções para evitar quota
                if i < len(data) - 1:  # Não fazer delay na última inserção
                    time.sleep(1)
            
            self._log("Planilha ordenada com sucesso")
            
        except Exception as e:
            self._log(f"ERRO ao ordenar planilha: {str(e)}")
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                self._log("Ordenação falhou - dados mantidos mas não ordenados")
                self._log("Os dados foram inseridos mas não ordenados devido ao limite de quota da API")
    
    def update_google_forms(self):
        """Atualiza todos os Google Forms com a lista de motoristas"""
        if not self.google_available:
            self._log("ERRO: Integração com Google não disponível")
            return False
            
        try:
            self._log("Iniciando atualização dos Google Forms")
            
            # Obter lista de motoristas da planilha
            motorists = self._get_motorists_from_sheet()
            
            if not motorists:
                self._log("Nenhum motorista encontrado na planilha")
                return False
            
            # Atualizar cada formulário com delay entre eles
            for i, form_config in enumerate(self.forms_config):
                self._update_single_form(form_config, motorists)
                # Delay de 2 segundos entre formulários para evitar quota
                if i < len(self.forms_config) - 1:  # Não fazer delay no último formulário
                    time.sleep(2)
            
            self._log("Atualização dos Google Forms concluída")
            return True
            
        except Exception as e:
            self._log(f"ERRO ao atualizar Google Forms: {str(e)}")
            return False
    
    def _get_motorists_from_sheet(self):
        """Obtém lista de motoristas da planilha"""
        try:
            spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.sheet_name)
            
            # Obter dados (a partir da linha 2)
            all_values = worksheet.get_all_values()
            
            if len(all_values) <= 1:
                return []
            
            # Extrair nomes dos motoristas (coluna B, índice 1)
            motorists = []
            for row in all_values[1:]:  # Pular cabeçalho
                if len(row) > 1 and row[1].strip():  # Verificar se tem nome
                    motorists.append(row[1].strip())
            
            # Ordenar alfabeticamente e remover duplicatas
            motorists = sorted(list(set(motorists)))
            
            self._log(f"Encontrados {len(motorists)} motoristas na planilha")
            return motorists
            
        except Exception as e:
            self._log(f"ERRO ao obter motoristas da planilha: {str(e)}")
            return []
    
    def _update_single_form(self, form_config, motorists):
        """Atualiza um formulário específico"""
        try:
            form_id = form_config["id"]
            field_name = form_config["campo"]
            
            self._log(f"Atualizando formulário {form_id}")
            
            # Obter informações do formulário com retry
            form = self._retry_operation(
                lambda: self.forms_service.forms().get(formId=form_id).execute(),
                f"obter formulário {form_id}"
            )
            
            # Encontrar o campo correto
            field_id = None
            for item in form.get('items', []):
                if 'title' in item and field_name in item['title']:
                    field_id = item['itemId']
                    break
            
            if not field_id:
                self._log(f"Campo '{field_name}' não encontrado no formulário {form_id}")
                return False
            
            # Preparar opções para o campo
            options = []
            for motorist in motorists:
                options.append({
                    "value": motorist,
                    "isCorrect": False
                })
            
            # Atualizar o campo
            update_request = {
                "updateFormInfo": {
                    "info": {
                        "title": form.get('info', {}).get('title', '')
                    }
                },
                "updateItem": {
                    "itemId": field_id,
                    "item": {
                        "title": field_name,
                        "questionItem": {
                            "question": {
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": options,
                                    "shuffle": False
                                }
                            }
                        }
                    }
                }
            }
            
            # Executar atualização com retry
            self._retry_operation(
                lambda: self.forms_service.forms().batchUpdate(
                    formId=form_id,
                    body={"requests": [update_request]}
                ).execute(),
                f"atualizar formulário {form_id}"
            )
            
            self._log(f"Formulário {form_id} atualizado com sucesso")
            return True
            
        except Exception as e:
            self._log(f"ERRO ao atualizar formulário {form_config['id']}: {str(e)}")
            return False
    
    def process_new_motorist(self, motorist_data):
        """Processa um novo motorista: insere na planilha e atualiza formulários"""
        try:
            self._log("=== INICIANDO PROCESSAMENTO DE NOVO MOTORISTA ===")
            self._log(f"Motorista: {motorist_data.get('nome', '')}")
            
            if not self.google_available:
                self._log("AVISO: Integração com Google não disponível")
                self._log("Motorista salvo apenas no banco de dados local")
                return True
            
            # 1. Inserir na planilha
            sheet_success = self.insert_motorist_to_sheet(motorist_data)
            if not sheet_success:
                self._log("ERRO: Falha ao inserir na planilha")
                return False
            
            # 2. Atualizar Google Forms
            forms_success = self.update_google_forms()
            if not forms_success:
                self._log("ERRO: Falha ao atualizar Google Forms")
                return False
            
            self._log("=== PROCESSAMENTO CONCLUÍDO COM SUCESSO ===")
            return True
            
        except Exception as e:
            self._log(f"ERRO no processamento: {str(e)}")
            return False 