#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar se o email está sendo salvo corretamente
"""

import sqlite3

def check_email_data():
    """Verifica os dados do email"""
    try:
        conn = sqlite3.connect('dbs/db_app.db')
        cursor = conn.cursor()
        
        # Verificar primeiros 5 registros
        cursor.execute("SELECT id, nome, email FROM motorists LIMIT 5")
        rows = cursor.fetchall()
        
        print("📧 VERIFICAÇÃO DOS DADOS DE EMAIL:")
        print("=" * 50)
        
        for row in rows:
            id_motorist, nome, email = row
            print(f"ID: {id_motorist}")
            print(f"Nome: {nome}")
            print(f"Email: '{email}' (tipo: {type(email)})")
            print("-" * 30)
        
        # Verificar se há emails não nulos
        cursor.execute("SELECT COUNT(*) FROM motorists WHERE email IS NOT NULL AND email != ''")
        count_with_email = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM motorists WHERE email IS NULL OR email = ''")
        count_without_email = cursor.fetchone()[0]
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"Motoristas com email: {count_with_email}")
        print(f"Motoristas sem email: {count_without_email}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    check_email_data() 