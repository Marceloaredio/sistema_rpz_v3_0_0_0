#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de rollback para o plano de limpeza do Sistema RPZ
Permite reverter mudanças em caso de problemas
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

class RollbackHelper:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups"
        self.log_file = self.project_root / "logs" / "rollback.log"
        
    def log(self, message, level="INFO"):
        """Registra mensagem no log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Criar diretório de logs se não existir
        self.log_file.parent.mkdir(exist_ok=True)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def list_backups(self):
        """Lista todos os backups disponíveis"""
        self.log("📋 Listando backups disponíveis...")
        
        if not self.backup_dir.exists():
            self.log("❌ Diretório de backups não encontrado", "ERROR")
            return []
        
        backups = []
        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith("sistema_rpz_backup_"):
                backups.append(item)
        
        if not backups:
            self.log("❌ Nenhum backup encontrado", "ERROR")
            return []
        
        # Ordenar por data de criação (mais recente primeiro)
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        self.log(f"✅ {len(backups)} backups encontrados:")
        for i, backup in enumerate(backups):
            mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
            self.log(f"  {i+1}. {backup.name} (criado em {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        return backups
    
    def restore_backup(self, backup_path):
        """Restaura um backup específico"""
        self.log(f"🔄 Restaurando backup: {backup_path}")
        
        if not backup_path.exists():
            self.log(f"❌ Backup não encontrado: {backup_path}", "ERROR")
            return False
        
        try:
            # Criar backup do estado atual antes de restaurar
            current_backup = self.backup_dir / f"current_state_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.log(f"📦 Criando backup do estado atual: {current_backup}")
            shutil.copytree(self.project_root, current_backup, 
                          ignore=shutil.ignore_patterns('backups', '__pycache__', '*.pyc', '.git'))
            
            # Remover arquivos atuais (exceto backups e logs)
            self.log("🗑️ Removendo arquivos atuais...")
            for item in self.project_root.iterdir():
                if item.name not in ['backups', 'logs', '.git']:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            
            # Restaurar arquivos do backup
            self.log("📥 Restaurando arquivos do backup...")
            for item in backup_path.iterdir():
                if item.name not in ['backups', 'logs']:  # Não restaurar backups e logs do backup
                    dest = self.project_root / item.name
                    if item.is_file():
                        shutil.copy2(item, dest)
                    elif item.is_dir():
                        shutil.copytree(item, dest)
            
            self.log("✅ Backup restaurado com sucesso!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao restaurar backup: {e}", "ERROR")
            return False
    
    def restore_specific_files(self, file_list, backup_path):
        """Restaura arquivos específicos de um backup"""
        self.log(f"🔄 Restaurando arquivos específicos do backup: {backup_path}")
        
        if not backup_path.exists():
            self.log(f"❌ Backup não encontrado: {backup_path}", "ERROR")
            return False
        
        restored_count = 0
        for file_path in file_list:
            source_file = backup_path / file_path
            dest_file = self.project_root / file_path
            
            if source_file.exists():
                try:
                    # Criar diretório de destino se necessário
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    if source_file.is_file():
                        shutil.copy2(source_file, dest_file)
                    elif source_file.is_dir():
                        if dest_file.exists():
                            shutil.rmtree(dest_file)
                        shutil.copytree(source_file, dest_file)
                    
                    self.log(f"✅ Restaurado: {file_path}")
                    restored_count += 1
                    
                except Exception as e:
                    self.log(f"❌ Erro ao restaurar {file_path}: {e}", "ERROR")
            else:
                self.log(f"⚠️ Arquivo não encontrado no backup: {file_path}", "WARNING")
        
        self.log(f"✅ {restored_count}/{len(file_list)} arquivos restaurados")
        return restored_count > 0
    
    def rollback_phase(self, phase):
        """Reverte mudanças de uma fase específica"""
        self.log(f"🔄 Revertendo mudanças da Fase {phase}")
        
        # Listar backups disponíveis
        backups = self.list_backups()
        if not backups:
            return False
        
        # Usar o backup mais recente
        latest_backup = backups[0]
        self.log(f"📦 Usando backup: {latest_backup.name}")
        
        # Arquivos específicos por fase
        phase_files = {
            2: [  # Fase 2 - Arquivos removidos
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
            3: [  # Fase 3 - Arquivos consolidados
                "model/user.py",
                "controller/google_integration.py",
                "controller/google_sheets.py"
            ],
            4: [  # Fase 4 - Arquivos CSS
                "static/css/style.css",
                "static/css/basic.css"
            ]
        }
        
        if phase not in phase_files:
            self.log(f"⚠️ Fase {phase} não tem arquivos para reverter")
            return True
        
        return self.restore_specific_files(phase_files[phase], latest_backup)
    
    def emergency_restore(self):
        """Restauração de emergência - restaura backup completo"""
        self.log("🚨 INICIANDO RESTAURAÇÃO DE EMERGÊNCIA")
        
        backups = self.list_backups()
        if not backups:
            self.log("❌ Nenhum backup disponível para restauração de emergência", "ERROR")
            return False
        
        # Usar o backup mais recente
        latest_backup = backups[0]
        self.log(f"📦 Restaurando backup completo: {latest_backup.name}")
        
        return self.restore_backup(latest_backup)
    
    def create_restore_point(self):
        """Cria um ponto de restauração antes de fazer mudanças"""
        self.log("📦 Criando ponto de restauração...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        restore_point = self.backup_dir / f"restore_point_{timestamp}"
        
        try:
            shutil.copytree(self.project_root, restore_point, 
                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            
            self.log(f"✅ Ponto de restauração criado: {restore_point.name}")
            return restore_point
            
        except Exception as e:
            self.log(f"❌ Erro ao criar ponto de restauração: {e}", "ERROR")
            return None
    
    def interactive_restore(self):
        """Modo interativo para seleção de backup"""
        self.log("🔄 Modo interativo de restauração")
        
        backups = self.list_backups()
        if not backups:
            return False
        
        print("\nSelecione o backup para restaurar:")
        for i, backup in enumerate(backups):
            mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i+1}. {backup.name} (criado em {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            choice = int(input("\nDigite o número do backup: ")) - 1
            if 0 <= choice < len(backups):
                selected_backup = backups[choice]
                self.log(f"📦 Backup selecionado: {selected_backup.name}")
                
                confirm = input("Tem certeza que deseja restaurar este backup? (s/N): ")
                if confirm.lower() in ['s', 'sim', 'y', 'yes']:
                    return self.restore_backup(selected_backup)
                else:
                    self.log("❌ Restauração cancelada pelo usuário")
                    return False
            else:
                self.log("❌ Escolha inválida", "ERROR")
                return False
                
        except (ValueError, KeyboardInterrupt):
            self.log("❌ Operação cancelada", "ERROR")
            return False

def main():
    """Função principal"""
    print("🔄 Sistema RPZ - Helper de Rollback")
    print("=" * 50)
    
    helper = RollbackHelper()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            helper.list_backups()
        elif command == "restore":
            if len(sys.argv) > 2:
                backup_name = sys.argv[2]
                backup_path = helper.backup_dir / backup_name
                helper.restore_backup(backup_path)
            else:
                helper.interactive_restore()
        elif command == "phase":
            if len(sys.argv) > 2:
                phase = int(sys.argv[2])
                helper.rollback_phase(phase)
            else:
                print("❌ Especifique o número da fase: python rollback_helper.py phase 2")
        elif command == "emergency":
            helper.emergency_restore()
        elif command == "point":
            helper.create_restore_point()
        elif command == "interactive":
            helper.interactive_restore()
        else:
            print("❌ Comando não reconhecido")
            print("Comandos disponíveis: list, restore [backup_name], phase <número>, emergency, point, interactive")
    else:
        # Modo interativo por padrão
        helper.interactive_restore()

if __name__ == "__main__":
    main()

