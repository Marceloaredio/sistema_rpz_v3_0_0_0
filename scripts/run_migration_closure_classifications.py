#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migração para criar tabela closure_block_classifications
Sistema RPZ v3.0.0.0 - Fase 1: Modelo de dados e auditoria

Autor: Sistema RPZ
Data: 2025-01-27
"""

import sqlite3
import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from global_vars import DB_PATH

def run_migration():
    """
    Executa a migração para criar a tabela closure_block_classifications
    """
    print("🚀 Iniciando migração: closure_block_classifications")
    print(f"📁 Banco de dados: {DB_PATH}")
    
    # Verificar se o arquivo de banco existe
    if not os.path.exists(DB_PATH):
        print(f"❌ Erro: Banco de dados não encontrado em {DB_PATH}")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se as tabelas já existem
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='closure_block_classifications'
        """)
        
        if cursor.fetchone():
            print("⚠️  Tabela closure_block_classifications já existe. Pulando criação...")
            return True
        
        # Ler e executar o script SQL
        migration_file = os.path.join(os.path.dirname(__file__), 'migration_closure_block_classifications.sql')
        
        if not os.path.exists(migration_file):
            print(f"❌ Erro: Arquivo de migração não encontrado: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("📝 Executando script SQL...")
        
        # Executar o script SQL
        cursor.executescript(sql_script)
        
        # Verificar se as tabelas foram criadas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('closure_block_classifications', 'closure_block_classifications_audit')
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Tabelas criadas: {[table[0] for table in tables]}")
        
        # Verificar estrutura da tabela principal
        cursor.execute("PRAGMA table_info(closure_block_classifications)")
        columns = cursor.fetchall()
        print("📋 Estrutura da tabela closure_block_classifications:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        # Verificar índices
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_closure_%'
        """)
        indexes = cursor.fetchall()
        print(f"🔍 Índices criados: {[idx[0] for idx in indexes]}")
        
        # Verificar triggers
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger' AND name LIKE '%closure_classifications%'
        """)
        triggers = cursor.fetchall()
        print(f"⚡ Triggers criados: {[trg[0] for trg in triggers]}")
        
        # Commit das alterações
        conn.commit()
        
        print("✅ Migração executada com sucesso!")
        print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro SQLite: {e}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def verify_migration():
    """
    Verifica se a migração foi aplicada corretamente
    """
    print("\n🔍 Verificando migração...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('closure_block_classifications', 'closure_block_classifications_audit')
        """)
        tables = cursor.fetchall()
        
        if len(tables) == 2:
            print("✅ Ambas as tabelas existem")
        else:
            print(f"❌ Esperado 2 tabelas, encontrado {len(tables)}")
            return False
        
        # Verificar constraints
        cursor.execute("PRAGMA table_info(closure_block_classifications)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['id', 'motorist_id', 'data', 'classification', 'created_at', 'updated_at']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"❌ Colunas faltando: {missing_columns}")
            return False
        else:
            print("✅ Todas as colunas obrigatórias existem")
        
        # Verificar índices
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_closure_%'
        """)
        indexes = cursor.fetchall()
        
        if len(indexes) >= 4:  # Esperamos pelo menos 4 índices
            print(f"✅ {len(indexes)} índices criados")
        else:
            print(f"⚠️  Apenas {len(indexes)} índices encontrados")
        
        # Verificar triggers
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger' AND name LIKE '%closure_classifications%'
        """)
        triggers = cursor.fetchall()
        
        if len(triggers) >= 3:  # Esperamos pelo menos 3 triggers
            print(f"✅ {len(triggers)} triggers criados")
        else:
            print(f"⚠️  Apenas {len(triggers)} triggers encontrados")
        
        print("✅ Verificação concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA RPZ v3.0.0.0 - MIGRAÇÃO FASE 1")
    print("Tabela: closure_block_classifications")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        verify_migration()
        print("\n🎉 Fase 1 concluída com sucesso!")
        print("📋 Próximos passos:")
        print("   - Implementar APIs de leitura/escrita (Fase 2)")
        print("   - Adicionar UI no closure_analysis.html (Fase 3)")
    else:
        print("\n💥 Falha na migração!")
        print("🔧 Verifique os logs e tente novamente")
        sys.exit(1)

