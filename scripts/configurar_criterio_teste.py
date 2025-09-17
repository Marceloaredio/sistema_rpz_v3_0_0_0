#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: Configurar Critério de Teste
Módulo Fechamento de Ponto - Sistema RPZ v3.0.0.0

Este script configura o critério FOLGA com carga horária especial para teste.
"""

import sqlite3
import os

def configurar_criterio_teste():
    """Configura o critério FOLGA com carga horária especial"""
    
    db_path = "dbs/db_app.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Configurando critério FOLGA para teste...")
        
        # Atualizar critério FOLGA para ter carga horária especial
        cursor.execute("""
            UPDATE criterios_diaria 
            SET carga_horaria_especial = '04:00' 
            WHERE valor_filtro = 'FOLGA'
        """)
        
        if cursor.rowcount > 0:
            print("✅ Critério FOLGA atualizado para carga horária 04:00")
            
            # Verificar a atualização
            cursor.execute("""
                SELECT valor_filtro, carga_horaria_especial 
                FROM criterios_diaria 
                WHERE valor_filtro = 'FOLGA'
            """)
            
            resultado = cursor.fetchone()
            if resultado:
                print(f"🔍 Verificação: {resultado[0]} -> {resultado[1]}")
            
            conn.commit()
            return True
        else:
            print("⚠️ Critério FOLGA não encontrado para atualização")
            return False
        
    except Exception as e:
        print(f"❌ Erro ao configurar critério: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Função principal"""
    print("🧪 Script: Configurar Critério de Teste")
    print("=" * 50)
    
    sucesso = configurar_criterio_teste()
    
    if sucesso:
        print("\n✅ Configuração concluída com sucesso!")
        print("🎯 Agora o critério FOLGA tem carga horária especial 04:00")
        print("📝 Teste novamente a funcionalidade no sistema")
    else:
        print("\n❌ Configuração falhou!")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
