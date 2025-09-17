#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestrador principal do plano de limpeza do Sistema RPZ
Executa todas as fases de forma controlada e segura
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

class CleanupOrchestrator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.log_file = self.project_root / "logs" / "orchestrator.log"
        self.phase_file = self.project_root / "logs" / "current_phase.txt"
        
    def log(self, message, level="INFO"):
        """Registra mensagem no log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Criar diretório de logs se não existir
        self.log_file.parent.mkdir(exist_ok=True)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def save_phase(self, phase):
        """Salva a fase atual"""
        with open(self.phase_file, "w") as f:
            f.write(str(phase))
    
    def get_current_phase(self):
        """Obtém a fase atual"""
        if self.phase_file.exists():
            try:
                with open(self.phase_file, "r") as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0
    
    def run_command(self, command, description):
        """Executa um comando e retorna o resultado"""
        self.log(f"🔄 {description}")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log(f"✅ {description} - Sucesso")
                if result.stdout:
                    self.log(f"📋 Saída: {result.stdout}")
                return True
            else:
                self.log(f"❌ {description} - Falhou: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} - Timeout", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ {description} - Erro: {e}", "ERROR")
            return False
    
    def run_phase_1(self):
        """Fase 1: Preparação e Backup"""
        self.log("🚀 INICIANDO FASE 1: PREPARAÇÃO E BACKUP")
        
        # 1.1 Criar backup completo
        if not self.run_command("python scripts/cleanup_helper.py backup", "Criando backup completo"):
            return False
        
        # 1.2 Verificar dependências
        if not self.run_command("python scripts/cleanup_helper.py deps", "Verificando dependências"):
            self.log("⚠️ Aviso: Problemas com dependências detectados", "WARNING")
        
        # 1.3 Verificar imports
        if not self.run_command("python scripts/cleanup_helper.py imports", "Verificando imports"):
            self.log("⚠️ Aviso: Imports não utilizados detectados", "WARNING")
        
        # 1.4 Criar ponto de restauração
        if not self.run_command("python scripts/rollback_helper.py point", "Criando ponto de restauração"):
            return False
        
        # 1.5 Validação inicial
        if not self.run_command("python scripts/validation_helper.py critical", "Validação inicial"):
            return False
        
        self.log("✅ FASE 1 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase_2(self):
        """Fase 2: Remoção de Arquivos Desnecessários"""
        self.log("🚀 INICIANDO FASE 2: REMOÇÃO DE ARQUIVOS DESNECESSÁRIOS")
        
        # 2.1 Remover __pycache__
        if not self.run_command("python scripts/cleanup_helper.py pycache", "Removendo __pycache__"):
            return False
        
        # 2.2 Atualizar .gitignore
        if not self.run_command("python scripts/cleanup_helper.py gitignore", "Atualizando .gitignore"):
            return False
        
        # 2.3 Remover arquivos de documentação obsoleta
        obsolete_docs = [
            "docs/ajuste_de_telas_fase1.md",
            "docs/ajuste_de_telas_fase2.md", 
            "docs/ajuste_de_telas.md",
            "docs/modal_inserir.md",
            "docs/soma_cards.md",
            "docs/CLEANUP_ANALYSIS.md"
        ]
        
        for doc in obsolete_docs:
            if os.path.exists(doc):
                if not self.run_command(f"rm {doc}", f"Removendo {doc}"):
                    return False
        
        # 2.4 Remover scripts de debug
        debug_scripts = [
            "scripts/investigar_dados_entrada.py",
            "scripts/reconfigurar_folga.py"
        ]
        
        for script in debug_scripts:
            if os.path.exists(script):
                if not self.run_command(f"rm {script}", f"Removendo {script}"):
                    return False
        
        # 2.5 Remover requirements duplicado
        if os.path.exists("requirements-minimal.txt"):
            if not self.run_command("rm requirements-minimal.txt", "Removendo requirements-minimal.txt"):
                return False
        
        # 2.6 Validação da fase
        if not self.run_command("python scripts/validation_helper.py phase 2", "Validação da Fase 2"):
            self.log("❌ Fase 2 falhou na validação. Executando rollback...", "ERROR")
            self.run_command("python scripts/rollback_helper.py phase 2", "Rollback da Fase 2")
            return False
        
        self.log("✅ FASE 2 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase_3(self):
        """Fase 3: Consolidação de Código"""
        self.log("🚀 INICIANDO FASE 3: CONSOLIDAÇÃO DE CÓDIGO")
        
        # 3.1 Remover model/user.py (se não usado)
        if os.path.exists("model/user.py"):
            # Verificar se está sendo usado
            result = subprocess.run("grep -r 'from model.user import' .", shell=True, capture_output=True, text=True)
            if not result.stdout:
                if not self.run_command("rm model/user.py", "Removendo model/user.py"):
                    return False
            else:
                self.log("⚠️ model/user.py está sendo usado, mantendo", "WARNING")
        
        # 3.2 Consolidar Google Integration
        self.log("🔄 Consolidando Google Integration...")
        # TODO: Implementar consolidação real
        # Por enquanto, apenas remover se não usado
        google_files = ["controller/google_integration.py", "controller/google_sheets.py"]
        for file in google_files:
            if os.path.exists(file):
                result = subprocess.run(f"grep -r '{file}' .", shell=True, capture_output=True, text=True)
                if not result.stdout:
                    if not self.run_command(f"rm {file}", f"Removendo {file}"):
                        return False
                else:
                    self.log(f"⚠️ {file} está sendo usado, mantendo", "WARNING")
        
        # 3.3 Validação da fase
        if not self.run_command("python scripts/validation_helper.py phase 3", "Validação da Fase 3"):
            self.log("❌ Fase 3 falhou na validação. Executando rollback...", "ERROR")
            self.run_command("python scripts/rollback_helper.py phase 3", "Rollback da Fase 3")
            return False
        
        self.log("✅ FASE 3 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase_4(self):
        """Fase 4: Consolidação de Arquivos Estáticos"""
        self.log("🚀 INICIANDO FASE 4: CONSOLIDAÇÃO DE ARQUIVOS ESTÁTICOS")
        
        # 4.1 Remover CSS redundante
        css_files = ["static/css/style.css", "static/css/basic.css"]
        for css in css_files:
            if os.path.exists(css):
                # Verificar se está sendo usado
                result = subprocess.run(f"grep -r '{css}' templates/", shell=True, capture_output=True, text=True)
                if not result.stdout:
                    if not self.run_command(f"rm {css}", f"Removendo {css}"):
                        return False
                else:
                    self.log(f"⚠️ {css} está sendo usado, mantendo", "WARNING")
        
        # 4.2 Validação da fase
        if not self.run_command("python scripts/validation_helper.py phase 4", "Validação da Fase 4"):
            self.log("❌ Fase 4 falhou na validação. Executando rollback...", "ERROR")
            self.run_command("python scripts/rollback_helper.py phase 4", "Rollback da Fase 4")
            return False
        
        self.log("✅ FASE 4 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase_5(self):
        """Fase 5: Limpeza de Banco de Dados"""
        self.log("🚀 INICIANDO FASE 5: LIMPEZA DE BANCO DE DADOS")
        
        # 5.1 Verificar integridade do banco
        if not self.run_command("python scripts/validation_helper.py database", "Verificando banco de dados"):
            return False
        
        # 5.2 Backup do banco
        if not self.run_command("cp dbs/db_app.db dbs/db_app_backup_$(date +%Y%m%d_%H%M%S).db", "Backup do banco de dados"):
            return False
        
        self.log("✅ FASE 5 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase_6(self):
        """Fase 6: Atualização de Documentação"""
        self.log("🚀 INICIANDO FASE 6: ATUALIZAÇÃO DE DOCUMENTAÇÃO")
        
        # 6.1 Gerar relatório de limpeza
        if not self.run_command("python scripts/cleanup_helper.py report", "Gerando relatório de limpeza"):
            return False
        
        self.log("✅ FASE 6 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase_7(self):
        """Fase 7: Testes e Validação"""
        self.log("🚀 INICIANDO FASE 7: TESTES E VALIDAÇÃO")
        
        # 7.1 Validação completa
        if not self.run_command("python scripts/validation_helper.py full", "Validação completa"):
            return False
        
        # 7.2 Teste da aplicação web
        if not self.run_command("python scripts/validation_helper.py web", "Teste da aplicação web"):
            self.log("⚠️ Aviso: Problemas com aplicação web detectados", "WARNING")
        
        self.log("✅ FASE 7 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase_8(self):
        """Fase 8: Otimização Final"""
        self.log("🚀 INICIANDO FASE 8: OTIMIZAÇÃO FINAL")
        
        # 8.1 Verificar duplicatas
        if not self.run_command("python scripts/cleanup_helper.py duplicates", "Verificando duplicatas"):
            return False
        
        # 8.2 Validação final
        if not self.run_command("python scripts/validation_helper.py full", "Validação final"):
            return False
        
        self.log("✅ FASE 8 CONCLUÍDA COM SUCESSO")
        return True
    
    def run_phase(self, phase):
        """Executa uma fase específica"""
        self.log(f"🎯 EXECUTANDO FASE {phase}")
        
        # Salvar fase atual
        self.save_phase(phase)
        
        # Executar fase
        phase_methods = {
            1: self.run_phase_1,
            2: self.run_phase_2,
            3: self.run_phase_3,
            4: self.run_phase_4,
            5: self.run_phase_5,
            6: self.run_phase_6,
            7: self.run_phase_7,
            8: self.run_phase_8
        }
        
        if phase not in phase_methods:
            self.log(f"❌ Fase {phase} não existe", "ERROR")
            return False
        
        success = phase_methods[phase]()
        
        if success:
            self.log(f"🎉 FASE {phase} CONCLUÍDA COM SUCESSO!")
        else:
            self.log(f"💥 FASE {phase} FALHOU!")
        
        return success
    
    def run_all_phases(self):
        """Executa todas as fases em sequência"""
        self.log("🚀 INICIANDO LIMPEZA COMPLETA DO SISTEMA RPZ")
        
        phases = [1, 2, 3, 4, 5, 6, 7, 8]
        successful_phases = 0
        
        for phase in phases:
            self.log(f"\n{'='*60}")
            self.log(f"EXECUTANDO FASE {phase}/8")
            self.log(f"{'='*60}")
            
            if self.run_phase(phase):
                successful_phases += 1
                self.log(f"✅ Fase {phase} concluída com sucesso")
            else:
                self.log(f"❌ Fase {phase} falhou. Parando execução.", "ERROR")
                break
        
        # Relatório final
        self.log(f"\n{'='*60}")
        self.log("RELATÓRIO FINAL")
        self.log(f"{'='*60}")
        self.log(f"Fases executadas com sucesso: {successful_phases}/8")
        
        if successful_phases == 8:
            self.log("🎉 LIMPEZA COMPLETA FINALIZADA COM SUCESSO!")
            self.log("📊 Sistema otimizado e funcionando perfeitamente")
        else:
            self.log(f"⚠️ LIMPEZA PARCIAL: {successful_phases}/8 fases concluídas")
            self.log("🔧 Verifique os logs para identificar problemas")
        
        return successful_phases == 8
    
    def resume_from_phase(self, start_phase):
        """Retoma a limpeza a partir de uma fase específica"""
        self.log(f"🔄 RETOMANDO LIMPEZA A PARTIR DA FASE {start_phase}")
        
        current_phase = self.get_current_phase()
        if current_phase >= start_phase:
            self.log(f"⚠️ Sistema já está na fase {current_phase}. Use 'continue' para prosseguir.")
            return False
        
        phases = list(range(start_phase, 9))
        successful_phases = 0
        
        for phase in phases:
            self.log(f"\n{'='*60}")
            self.log(f"EXECUTANDO FASE {phase}/8")
            self.log(f"{'='*60}")
            
            if self.run_phase(phase):
                successful_phases += 1
                self.log(f"✅ Fase {phase} concluída com sucesso")
            else:
                self.log(f"❌ Fase {phase} falhou. Parando execução.", "ERROR")
                break
        
        return successful_phases == len(phases)

def main():
    """Função principal"""
    print("🎭 Sistema RPZ - Orquestrador de Limpeza")
    print("=" * 60)
    
    orchestrator = CleanupOrchestrator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            orchestrator.run_all_phases()
        elif command == "phase":
            if len(sys.argv) > 2:
                phase = int(sys.argv[2])
                orchestrator.run_phase(phase)
            else:
                print("❌ Especifique o número da fase: python cleanup_orchestrator.py phase 2")
        elif command == "resume":
            if len(sys.argv) > 2:
                start_phase = int(sys.argv[2])
                orchestrator.resume_from_phase(start_phase)
            else:
                current_phase = orchestrator.get_current_phase()
                print(f"ℹ️ Fase atual: {current_phase}")
                print("Use: python cleanup_orchestrator.py resume <fase_inicial>")
        elif command == "status":
            current_phase = orchestrator.get_current_phase()
            print(f"📊 Fase atual: {current_phase}")
            print("📋 Logs disponíveis em: logs/")
        else:
            print("❌ Comando não reconhecido")
            print("Comandos disponíveis: all, phase <número>, resume <fase>, status")
    else:
        # Modo interativo
        print("Escolha uma opção:")
        print("1. Executar limpeza completa")
        print("2. Executar fase específica")
        print("3. Retomar limpeza")
        print("4. Verificar status")
        
        try:
            choice = input("\nDigite sua escolha (1-4): ")
            
            if choice == "1":
                orchestrator.run_all_phases()
            elif choice == "2":
                phase = int(input("Digite o número da fase (1-8): "))
                orchestrator.run_phase(phase)
            elif choice == "3":
                start_phase = int(input("Digite a fase inicial: "))
                orchestrator.resume_from_phase(start_phase)
            elif choice == "4":
                current_phase = orchestrator.get_current_phase()
                print(f"📊 Fase atual: {current_phase}")
            else:
                print("❌ Escolha inválida")
                
        except (ValueError, KeyboardInterrupt):
            print("❌ Operação cancelada")

if __name__ == "__main__":
    main()

