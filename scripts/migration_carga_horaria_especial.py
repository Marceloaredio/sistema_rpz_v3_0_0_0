#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Migração: Carga Horária em Critérios Especiais
Módulo Fechamento de Ponto - Sistema RPZ v3.0.0.0

Este script adiciona as novas colunas necessárias para implementar
a funcionalidade de carga horária personalizada nos critérios especiais.

Autor: Sistema RPZ
Data: 01/08/2025
Versão: 1.0
"""

import sqlite3
import os
import sys
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/migration_carga_horaria.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def conectar_banco(db_path):
    """Conecta ao banco de dados SQLite."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        raise

def verificar_coluna_existe(conn, tabela, coluna):
    """Verifica se uma coluna já existe em uma tabela."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = cursor.fetchall()
        
        for col in colunas:
            if col['name'] == coluna:
                return True
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar coluna {coluna} na tabela {tabela}: {e}")
        return False

def adicionar_coluna_criterios_diaria(conn):
    """Adiciona coluna carga_horaria_especial na tabela criterios_diaria."""
    try:
        if not verificar_coluna_existe(conn, 'criterios_diaria', 'carga_horaria_especial'):
            logger.info("Adicionando coluna 'carga_horaria_especial' na tabela 'criterios_diaria'...")
            
            # SQLite não suporta ADD COLUMN com IF NOT EXISTS, então usamos try-catch
            cursor = conn.cursor()
            cursor.execute('''
                ALTER TABLE criterios_diaria 
                ADD COLUMN carga_horaria_especial TEXT DEFAULT 'Padrão'
            ''')
            
            # Atualizar registros existentes para 'Padrão'
            cursor.execute('''
                UPDATE criterios_diaria 
                SET carga_horaria_especial = 'Padrão' 
                WHERE carga_horaria_especial IS NULL
            ''')
            
            conn.commit()
            logger.info("✅ Coluna 'carga_horaria_especial' adicionada com sucesso!")
            return True
        else:
            logger.info("ℹ️ Coluna 'carga_horaria_especial' já existe na tabela 'criterios_diaria'")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar coluna 'carga_horaria_especial': {e}")
        conn.rollback()
        return False

def adicionar_colunas_dayoff_fecham(conn):
    """Adiciona colunas de carga horária especial na tabela dayoff_fecham."""
    try:
        colunas_para_adicionar = [
            ('carga_horaria_esp', 'TEXT DEFAULT ""'),
            ('hextra_50_esp', 'TEXT DEFAULT ""')
        ]
        
        for coluna, definicao in colunas_para_adicionar:
            if not verificar_coluna_existe(conn, 'dayoff_fecham', coluna):
                logger.info(f"Adicionando coluna '{coluna}' na tabela 'dayoff_fecham'...")
                
                cursor = conn.cursor()
                cursor.execute(f'''
                    ALTER TABLE dayoff_fecham 
                    ADD COLUMN {coluna} {definicao}
                ''')
                
                # Atualizar registros existentes para vazio
                cursor.execute(f'''
                    UPDATE dayoff_fecham 
                    SET {coluna} = '' 
                    WHERE {coluna} IS NULL
                ''')
                
                logger.info(f"✅ Coluna '{coluna}' adicionada com sucesso!")
            else:
                logger.info(f"ℹ️ Coluna '{coluna}' já existe na tabela 'dayoff_fecham'")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar colunas em 'dayoff_fecham': {e}")
        conn.rollback()
        return False

def verificar_criterios_especiais(conn):
    """Verifica se os critérios especiais GARAGEM e CARGA/DESCARGA existem."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT valor_filtro, carga_horaria_especial 
            FROM criterios_diaria 
            WHERE valor_filtro IN ('GARAGEM', 'CARGA/DESCARGA')
        ''')
        
        criterios = cursor.fetchall()
        logger.info(f"Critérios especiais encontrados: {len(criterios)}")
        
        for criterio in criterios:
            logger.info(f"  - {criterio['valor_filtro']}: {criterio['carga_horaria_especial']}")
            
        return criterios
        
    except Exception as e:
        logger.error(f"Erro ao verificar critérios especiais: {e}")
        return []

def validar_migracao(conn):
    """Valida se a migração foi executada corretamente."""
    try:
        # Verificar tabela criterios_diaria
        if not verificar_coluna_existe(conn, 'criterios_diaria', 'carga_horaria_especial'):
            logger.error("❌ Coluna 'carga_horaria_especial' não foi criada em 'criterios_diaria'")
            return False
            
        # Verificar tabela dayoff_fecham
        if not verificar_coluna_existe(conn, 'dayoff_fecham', 'carga_horaria_esp'):
            logger.error("❌ Coluna 'carga_horaria_esp' não foi criada em 'dayoff_fecham'")
            return False
            
        if not verificar_coluna_existe(conn, 'dayoff_fecham', 'hextra_50_esp'):
            logger.error("❌ Coluna 'hextra_50_esp' não foi criada em 'dayoff_fecham'")
            return False
            
        logger.info("✅ Validação da migração concluída com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        return False

def executar_migracao(db_path):
    """Executa a migração completa."""
    logger.info("🚀 INICIANDO MIGRAÇÃO: Carga Horária em Critérios Especiais")
    logger.info(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"🗄️ Banco: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = conectar_banco(db_path)
        logger.info("✅ Conexão com banco estabelecida")
        
        # Executar migrações
        sucesso_criterios = adicionar_coluna_criterios_diaria(conn)
        sucesso_dayoff = adicionar_colunas_dayoff_fecham(conn)
        
        if sucesso_criterios and sucesso_dayoff:
            # Validar migração
            if validar_migracao(conn):
                logger.info("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                
                # Verificar critérios especiais
                verificar_criterios_especiais(conn)
                
                return True
            else:
                logger.error("❌ Falha na validação da migração")
                return False
        else:
            logger.error("❌ Falha em uma ou mais etapas da migração")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro durante a migração: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("🔌 Conexão com banco fechada")

def main():
    """Função principal."""
    # Caminho do banco (ajustar conforme necessário)
    db_path = "dbs/db_app.db"
    
    print("=" * 60)
    print("MIGRAÇÃO: Carga Horária em Critérios Especiais")
    print("Sistema RPZ v3.0.0.0 - Módulo Fechamento de Ponto")
    print("=" * 60)
    
    # Confirmar execução
    resposta = input("\nDeseja executar a migração? (s/N): ").strip().lower()
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("❌ Migração cancelada pelo usuário")
        return
    
    # Executar migração
    sucesso = executar_migracao(db_path)
    
    if sucesso:
        print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("✅ Novas colunas adicionadas:")
        print("   - criterios_diaria.carga_horaria_especial")
        print("   - dayoff_fecham.carga_horaria_esp")
        print("   - dayoff_fecham.hextra_50_esp")
        print("\n📋 Próximos passos:")
        print("   1. Implementar feature flag")
        print("   2. Testar funcionalidade")
        print("   3. Ativar gradualmente")
    else:
        print("\n❌ MIGRAÇÃO FALHOU!")
        print("📋 Verifique os logs em 'logs/migration_carga_horaria.log'")
        print("🔄 Execute novamente ou contate o suporte")

if __name__ == "__main__":
    main()
