#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Simples de Validação da Migração
Módulo Fechamento de Ponto - Sistema RPZ v3.0.0.0
"""

import sqlite3
import os
from datetime import datetime

def validar_migracao():
    """Valida se a migração foi executada corretamente."""
    db_path = "dbs/db_app.db"
    
    print("VALIDACAO DA MIGRACAO - CARGA HORARIA ESPECIAL")
    print("=" * 50)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    if not os.path.exists(db_path):
        print(f"ERRO: Banco nao encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Conexao com banco estabelecida")
        
        # Teste 1: Verificar coluna em criterios_diaria
        print("\n1. Verificando tabela criterios_diaria...")
        cursor.execute("PRAGMA table_info(criterios_diaria)")
        colunas = cursor.fetchall()
        
        coluna_encontrada = False
        for coluna in colunas:
            if coluna[1] == 'carga_horaria_especial':
                coluna_encontrada = True
                print(f"   OK: Coluna 'carga_horaria_especial' encontrada")
                print(f"       Tipo: {coluna[2]}, Default: {coluna[4]}")
                break
        
        if not coluna_encontrada:
            print("   ERRO: Coluna 'carga_horaria_especial' nao encontrada")
            return False
        
        # Teste 2: Verificar colunas em dayoff_fecham
        print("\n2. Verificando tabela dayoff_fecham...")
        cursor.execute("PRAGMA table_info(dayoff_fecham)")
        colunas = cursor.fetchall()
        
        colunas_encontradas = []
        for coluna in colunas:
            if coluna[1] in ['carga_horaria_esp', 'hextra_50_esp']:
                colunas_encontradas.append(coluna[1])
                print(f"   OK: Coluna '{coluna[1]}' encontrada")
        
        if len(colunas_encontradas) != 2:
            print(f"   ERRO: Esperadas 2 colunas, encontradas {len(colunas_encontradas)}")
            return False
        
        # Teste 3: Verificar dados existentes
        print("\n3. Verificando dados existentes...")
        cursor.execute("SELECT COUNT(*) FROM criterios_diaria")
        total_criterios = cursor.fetchone()[0]
        print(f"   Total de criterios: {total_criterios}")
        
        cursor.execute("SELECT COUNT(*) FROM criterios_diaria WHERE carga_horaria_especial = 'Padrao'")
        criterios_padrao = cursor.fetchone()[0]
        print(f"   Criterios com valor 'Padrao': {criterios_padrao}")
        
        if criterios_padrao != total_criterios:
            print(f"   AVISO: Nem todos os criterios tem valor 'Padrao'")
        
        # Teste 4: Verificar critérios especiais
        print("\n4. Verificando criterios especiais...")
        cursor.execute("""
            SELECT valor_filtro, carga_horaria_especial 
            FROM criterios_diaria 
            WHERE valor_filtro IN ('GARAGEM', 'CARGA/DESCARGA')
        """)
        
        criterios_especiais = cursor.fetchall()
        print(f"   Criterios especiais encontrados: {len(criterios_especiais)}")
        
        for criterio in criterios_especiais:
            print(f"     - {criterio[0]}: {criterio[1]}")
        
        # Teste 5: Verificar se pode inserir novos valores
        print("\n5. Testando insercao de valores...")
        try:
            cursor.execute("""
                INSERT INTO criterios_diaria 
                (tipo_filtro, valor_filtro, valor_diaria, valor_ajuda_alimentacao, carga_horaria_especial)
                VALUES ('TESTE', 'TESTE', 0.0, 0.0, '08:00')
            """)
            
            # Verificar se foi inserido
            cursor.execute("SELECT carga_horaria_especial FROM criterios_diaria WHERE tipo_filtro = 'TESTE'")
            resultado = cursor.fetchone()
            
            if resultado and resultado[0] == '08:00':
                print("   OK: Valor '08:00' foi inserido corretamente")
            else:
                print("   ERRO: Valor nao foi inserido corretamente")
                return False
            
            # Remover registro de teste
            cursor.execute("DELETE FROM criterios_diaria WHERE tipo_filtro = 'TESTE'")
            print("   OK: Registro de teste removido")
            
        except Exception as e:
            print(f"   ERRO ao testar insercao: {e}")
            return False
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 50)
        print("RESULTADO: TODOS OS TESTES PASSARAM!")
        print("A migracao foi executada com sucesso.")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"ERRO durante a validacao: {e}")
        return False

if __name__ == "__main__":
    validar_migracao()
