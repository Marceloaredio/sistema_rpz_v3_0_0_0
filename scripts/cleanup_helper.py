#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script auxiliar para limpeza do Sistema RPZ
Executa verificações e preparações para o plano de limpeza
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class CleanupHelper:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups"
        self.log_file = self.project_root / "logs" / "cleanup.log"
        
    def log(self, message):
        """Registra mensagem no log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # Criar diretório de logs se não existir
        self.log_file.parent.mkdir(exist_ok=True)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def create_backup(self):
        """Cria backup completo do sistema"""
        self.log("🔄 Iniciando backup completo do sistema...")
        
        try:
            # Criar diretório de backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"sistema_rpz_backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copiar projeto inteiro
            shutil.copytree(self.project_root, backup_path, 
                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            
            self.log(f"✅ Backup criado em: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.log(f"❌ Erro ao criar backup: {e}")
            return None
    
    def check_dependencies(self):
        """Verifica dependências não utilizadas"""
        self.log("🔍 Verificando dependências não utilizadas...")
        
        try:
            # Verificar se pip-autoremove está instalado
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True)
            
            if "pip-autoremove" not in result.stdout:
                self.log("⚠️ pip-autoremove não instalado. Instalando...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pip-autoremove"])
            
            # Verificar dependências não utilizadas
            result = subprocess.run([sys.executable, "-m", "pip_autoremove", 
                                   "-r", "requirements.txt", "--dry-run"], 
                                  capture_output=True, text=True)
            
            if result.stdout:
                self.log("📋 Dependências que podem ser removidas:")
                self.log(result.stdout)
            else:
                self.log("✅ Todas as dependências estão sendo utilizadas")
                
        except Exception as e:
            self.log(f"❌ Erro ao verificar dependências: {e}")
    
    def check_unused_imports(self):
        """Verifica imports não utilizados"""
        self.log("🔍 Verificando imports não utilizados...")
        
        try:
            # Verificar se unimport está instalado
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True)
            
            if "unimport" not in result.stdout:
                self.log("⚠️ unimport não instalado. Instalando...")
                subprocess.run([sys.executable, "-m", "pip", "install", "unimport"])
            
            # Verificar imports não utilizados
            result = subprocess.run([sys.executable, "-m", "unimport", "--check", "."], 
                                  capture_output=True, text=True)
            
            if result.stdout:
                self.log("📋 Imports não utilizados encontrados:")
                self.log(result.stdout)
            else:
                self.log("✅ Todos os imports estão sendo utilizados")
                
        except Exception as e:
            self.log(f"❌ Erro ao verificar imports: {e}")
    
    def find_duplicate_files(self):
        """Encontra arquivos duplicados"""
        self.log("🔍 Procurando arquivos duplicados...")
        
        duplicates = []
        file_hashes = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # Pular diretórios de backup e cache
            if any(skip in root for skip in ['backups', '__pycache__', '.git']):
                continue
                
            for file in files:
                if file.endswith(('.py', '.css', '.js', '.md')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hash(f.read())
                        
                        if file_hash in file_hashes:
                            duplicates.append((file_hashes[file_hash], file_path))
                        else:
                            file_hashes[file_hash] = file_path
                    except Exception:
                        continue
        
        if duplicates:
            self.log("📋 Arquivos duplicados encontrados:")
            for original, duplicate in duplicates:
                self.log(f"  - {original} <-> {duplicate}")
        else:
            self.log("✅ Nenhum arquivo duplicado encontrado")
    
    def check_file_usage(self, file_path):
        """Verifica se um arquivo está sendo usado"""
        self.log(f"🔍 Verificando uso do arquivo: {file_path}")
        
        if not os.path.exists(file_path):
            self.log(f"❌ Arquivo não encontrado: {file_path}")
            return False
        
        # Procurar referências ao arquivo
        references = []
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(('.py', '.html', '.js', '.css', '.md')):
                    file_path_check = Path(root) / file
                    try:
                        with open(file_path_check, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if os.path.basename(file_path) in content:
                                references.append(file_path_check)
                    except Exception:
                        continue
        
        if references:
            self.log(f"✅ Arquivo está sendo usado em {len(references)} lugares:")
            for ref in references:
                self.log(f"  - {ref}")
            return True
        else:
            self.log(f"❌ Arquivo não está sendo usado")
            return False
    
    def remove_pycache(self):
        """Remove todas as pastas __pycache__"""
        self.log("🗑️ Removendo pastas __pycache__...")
        
        removed_count = 0
        for root, dirs, files in os.walk(self.project_root):
            if '__pycache__' in dirs:
                pycache_path = Path(root) / '__pycache__'
                try:
                    shutil.rmtree(pycache_path)
                    removed_count += 1
                    self.log(f"  ✅ Removido: {pycache_path}")
                except Exception as e:
                    self.log(f"  ❌ Erro ao remover {pycache_path}: {e}")
        
        self.log(f"✅ Total de pastas __pycache__ removidas: {removed_count}")
    
    def update_gitignore(self):
        """Atualiza .gitignore para ignorar arquivos desnecessários"""
        self.log("📝 Atualizando .gitignore...")
        
        gitignore_path = self.project_root / ".gitignore"
        ignore_patterns = [
            "# Python cache files",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "*.so",
            "",
            "# Backup files",
            "backups/",
            "",
            "# Log files",
            "logs/*.log",
            "",
            "# IDE files",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# OS files",
            ".DS_Store",
            "Thumbs.db"
        ]
        
        try:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write("\n" + "\n".join(ignore_patterns))
            self.log("✅ .gitignore atualizado")
        except Exception as e:
            self.log(f"❌ Erro ao atualizar .gitignore: {e}")
    
    def generate_cleanup_report(self):
        """Gera relatório de limpeza"""
        self.log("📊 Gerando relatório de limpeza...")
        
        report_path = self.project_root / "docs" / "RELATORIO_LIMPEZA.md"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# 📊 Relatório de Limpeza do Sistema RPZ\n\n")
                f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Contar arquivos por tipo
                file_counts = {}
                total_files = 0
                
                for root, dirs, files in os.walk(self.project_root):
                    if any(skip in root for skip in ['backups', '__pycache__', '.git']):
                        continue
                        
                    for file in files:
                        ext = Path(file).suffix
                        file_counts[ext] = file_counts.get(ext, 0) + 1
                        total_files += 1
                
                f.write("## 📈 Estatísticas do Projeto\n\n")
                f.write(f"- **Total de arquivos:** {total_files}\n")
                f.write("- **Arquivos por tipo:**\n")
                
                for ext, count in sorted(file_counts.items()):
                    f.write(f"  - `{ext or 'sem extensão'}`: {count}\n")
                
                f.write("\n## 🎯 Próximos Passos\n\n")
                f.write("1. Executar Fase 1 do plano de limpeza\n")
                f.write("2. Fazer backup completo\n")
                f.write("3. Iniciar remoção de arquivos desnecessários\n")
                f.write("4. Consolidar código duplicado\n")
                f.write("5. Otimizar arquivos estáticos\n")
            
            self.log(f"✅ Relatório gerado em: {report_path}")
            
        except Exception as e:
            self.log(f"❌ Erro ao gerar relatório: {e}")
    
    def run_full_analysis(self):
        """Executa análise completa"""
        self.log("🚀 Iniciando análise completa do sistema...")
        
        # Criar backup
        backup_path = self.create_backup()
        if not backup_path:
            self.log("❌ Falha ao criar backup. Abortando análise.")
            return
        
        # Verificar dependências
        self.check_dependencies()
        
        # Verificar imports
        self.check_unused_imports()
        
        # Procurar duplicatas
        self.find_duplicate_files()
        
        # Remover __pycache__
        self.remove_pycache()
        
        # Atualizar .gitignore
        self.update_gitignore()
        
        # Gerar relatório
        self.generate_cleanup_report()
        
        self.log("✅ Análise completa finalizada!")
        self.log(f"📁 Backup disponível em: {backup_path}")
        self.log("📋 Consulte o relatório em: docs/RELATORIO_LIMPEZA.md")
        self.log("📖 Siga o plano em: docs/PLANO_LIMPEZA_SISTEMA.md")

def main():
    """Função principal"""
    print("🧹 Sistema RPZ - Helper de Limpeza")
    print("=" * 50)
    
    helper = CleanupHelper()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            helper.create_backup()
        elif command == "deps":
            helper.check_dependencies()
        elif command == "imports":
            helper.check_unused_imports()
        elif command == "duplicates":
            helper.find_duplicate_files()
        elif command == "pycache":
            helper.remove_pycache()
        elif command == "gitignore":
            helper.update_gitignore()
        elif command == "report":
            helper.generate_cleanup_report()
        elif command == "full":
            helper.run_full_analysis()
        else:
            print("❌ Comando não reconhecido")
            print("Comandos disponíveis: backup, deps, imports, duplicates, pycache, gitignore, report, full")
    else:
        # Executar análise completa por padrão
        helper.run_full_analysis()

if __name__ == "__main__":
    main()

