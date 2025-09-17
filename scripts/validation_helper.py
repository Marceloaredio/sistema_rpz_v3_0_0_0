#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação para o plano de limpeza do Sistema RPZ
Verifica se as funcionalidades estão funcionando após cada fase
"""

import os
import sys
import subprocess
import time
import requests
from datetime import datetime
from pathlib import Path

class ValidationHelper:
    def __init__(self):
        self.project_root = Path.cwd()
        self.log_file = self.project_root / "logs" / "validation.log"
        self.app_url = "http://localhost:5000"
        
    def log(self, message, level="INFO"):
        """Registra mensagem no log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Criar diretório de logs se não existir
        self.log_file.parent.mkdir(exist_ok=True)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def check_file_exists(self, file_path, required=True):
        """Verifica se um arquivo existe"""
        exists = os.path.exists(file_path)
        if required and not exists:
            self.log(f"❌ Arquivo obrigatório não encontrado: {file_path}", "ERROR")
            return False
        elif not required and exists:
            self.log(f"⚠️ Arquivo que deveria ter sido removido ainda existe: {file_path}", "WARNING")
            return False
        else:
            self.log(f"✅ Arquivo {file_path}: {'existe' if exists else 'não existe'}")
            return True
    
    def check_imports(self, file_path):
        """Verifica se os imports de um arquivo estão funcionando"""
        self.log(f"🔍 Verificando imports em: {file_path}")
        
        try:
            # Tentar importar o módulo
            result = subprocess.run([
                sys.executable, "-c", f"import sys; sys.path.append('.'); import {file_path.replace('/', '.').replace('.py', '')}"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log(f"✅ Imports funcionando em: {file_path}")
                return True
            else:
                self.log(f"❌ Erro nos imports de {file_path}: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ Timeout ao verificar imports de: {file_path}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Erro ao verificar imports de {file_path}: {e}", "ERROR")
            return False
    
    def check_database_connection(self):
        """Verifica se a conexão com o banco de dados está funcionando"""
        self.log("🔍 Verificando conexão com banco de dados...")
        
        try:
            import sqlite3
            db_path = self.project_root / "dbs" / "db_app.db"
            
            if not db_path.exists():
                self.log("❌ Arquivo de banco de dados não encontrado", "ERROR")
                return False
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Testar query simples
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            conn.close()
            
            self.log(f"✅ Conexão com banco OK. {len(tables)} tabelas encontradas")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro na conexão com banco: {e}", "ERROR")
            return False
    
    def check_web_application(self):
        """Verifica se a aplicação web está funcionando"""
        self.log("🔍 Verificando aplicação web...")
        
        try:
            # Tentar iniciar a aplicação em background
            process = subprocess.Popen([
                sys.executable, "app.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Aguardar um pouco para a aplicação inicializar
            time.sleep(5)
            
            # Verificar se está rodando
            try:
                response = requests.get(self.app_url, timeout=10)
                if response.status_code == 200:
                    self.log("✅ Aplicação web funcionando")
                    result = True
                else:
                    self.log(f"❌ Aplicação web retornou status {response.status_code}", "ERROR")
                    result = False
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Erro ao acessar aplicação web: {e}", "ERROR")
                result = False
            
            # Finalizar processo
            process.terminate()
            process.wait(timeout=10)
            
            return result
            
        except Exception as e:
            self.log(f"❌ Erro ao verificar aplicação web: {e}", "ERROR")
            return False
    
    def check_critical_files(self):
        """Verifica se os arquivos críticos estão presentes"""
        self.log("🔍 Verificando arquivos críticos...")
        
        critical_files = [
            "app.py",
            "global_vars.py",
            "requirements.txt",
            "dbs/db_app.db",
            "config/config.ini",
            "controller/utils.py",
            "model/db_model.py",
            "view/public_routes.py",
            "view/common_routes.py"
        ]
        
        all_good = True
        for file_path in critical_files:
            if not self.check_file_exists(file_path, required=True):
                all_good = False
        
        return all_good
    
    def check_removed_files(self, phase):
        """Verifica se os arquivos que deveriam ter sido removidos foram removidos"""
        self.log(f"🔍 Verificando arquivos removidos na Fase {phase}...")
        
        removed_files = {
            2: [  # Fase 2 - Remoção de arquivos desnecessários
                "requirements-minimal.txt",
                "docs/ajuste_de_telas_fase1.md",
                "docs/ajuste_de_telas_fase2.md",
                "docs/ajuste_de_telas.md",
                "docs/modal_inserir.md",
                "docs/soma_cards.md",
                "docs/CLEANUP_ANALYSIS.md",
                "scripts/investigar_dados_entrada.py",
                "scripts/reconfigurar_folga.py"
            ],
            3: [  # Fase 3 - Consolidação de código
                "model/user.py",
                "controller/google_integration.py",
                "controller/google_sheets.py"
            ],
            4: [  # Fase 4 - Consolidação de arquivos estáticos
                "static/css/style.css",
                "static/css/basic.css"
            ]
        }
        
        if phase not in removed_files:
            self.log(f"⚠️ Fase {phase} não tem arquivos para verificar")
            return True
        
        all_removed = True
        for file_path in removed_files[phase]:
            if not self.check_file_exists(file_path, required=False):
                all_removed = False
        
        return all_removed
    
    def check_pycache_removed(self):
        """Verifica se todas as pastas __pycache__ foram removidas"""
        self.log("🔍 Verificando remoção de __pycache__...")
        
        pycache_found = []
        for root, dirs, files in os.walk(self.project_root):
            if '__pycache__' in dirs:
                pycache_found.append(os.path.join(root, '__pycache__'))
        
        if pycache_found:
            self.log(f"❌ Pastas __pycache__ ainda existem: {pycache_found}", "ERROR")
            return False
        else:
            self.log("✅ Todas as pastas __pycache__ foram removidas")
            return True
    
    def check_consolidated_files(self):
        """Verifica se os arquivos consolidados estão funcionando"""
        self.log("🔍 Verificando arquivos consolidados...")
        
        # Verificar se os novos arquivos consolidados existem e funcionam
        consolidated_files = [
            "controller/google_manager.py",  # Se foi criado
            "controller/infractions_manager.py",  # Se foi criado
        ]
        
        all_good = True
        for file_path in consolidated_files:
            if os.path.exists(file_path):
                if not self.check_imports(file_path):
                    all_good = False
            # Se não existe, não é erro (pode não ter sido criado ainda)
        
        return all_good
    
    def run_phase_validation(self, phase):
        """Executa validação para uma fase específica"""
        self.log(f"🚀 Iniciando validação da Fase {phase}")
        
        all_passed = True
        
        # Verificações básicas sempre
        if not self.check_critical_files():
            all_passed = False
        
        if not self.check_database_connection():
            all_passed = False
        
        # Verificações específicas por fase
        if phase >= 2:
            if not self.check_removed_files(2):
                all_passed = False
            
            if not self.check_pycache_removed():
                all_passed = False
        
        if phase >= 3:
            if not self.check_removed_files(3):
                all_passed = False
            
            if not self.check_consolidated_files():
                all_passed = False
        
        if phase >= 4:
            if not self.check_removed_files(4):
                all_passed = False
        
        # Verificação da aplicação web (apenas nas fases finais)
        if phase >= 7:
            if not self.check_web_application():
                all_passed = False
        
        if all_passed:
            self.log(f"✅ Fase {phase} validada com sucesso!")
        else:
            self.log(f"❌ Fase {phase} falhou na validação!", "ERROR")
        
        return all_passed
    
    def run_full_validation(self):
        """Executa validação completa"""
        self.log("🚀 Iniciando validação completa do sistema...")
        
        phases = [2, 3, 4, 5, 6, 7, 8]
        results = {}
        
        for phase in phases:
            self.log(f"\n{'='*50}")
            self.log(f"Validando Fase {phase}")
            self.log(f"{'='*50}")
            
            results[phase] = self.run_phase_validation(phase)
        
        # Relatório final
        self.log(f"\n{'='*50}")
        self.log("RELATÓRIO FINAL DE VALIDAÇÃO")
        self.log(f"{'='*50}")
        
        passed_phases = sum(1 for result in results.values() if result)
        total_phases = len(phases)
        
        for phase, passed in results.items():
            status = "✅ PASSOU" if passed else "❌ FALHOU"
            self.log(f"Fase {phase}: {status}")
        
        self.log(f"\nTotal: {passed_phases}/{total_phases} fases passaram")
        
        if passed_phases == total_phases:
            self.log("🎉 VALIDAÇÃO COMPLETA: Todas as fases passaram!")
        else:
            self.log("⚠️ VALIDAÇÃO INCOMPLETA: Algumas fases falharam!")
        
        return passed_phases == total_phases

def main():
    """Função principal"""
    print("🧪 Sistema RPZ - Helper de Validação")
    print("=" * 50)
    
    helper = ValidationHelper()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "phase":
            if len(sys.argv) > 2:
                phase = int(sys.argv[2])
                helper.run_phase_validation(phase)
            else:
                print("❌ Especifique o número da fase: python validation_helper.py phase 2")
        elif command == "full":
            helper.run_full_validation()
        elif command == "critical":
            helper.check_critical_files()
        elif command == "database":
            helper.check_database_connection()
        elif command == "web":
            helper.check_web_application()
        else:
            print("❌ Comando não reconhecido")
            print("Comandos disponíveis: phase <número>, full, critical, database, web")
    else:
        # Executar validação completa por padrão
        helper.run_full_validation()

if __name__ == "__main__":
    main()

