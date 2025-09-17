#!/usr/bin/env python3
import sqlite3
import sys

def check_motorist_dependencies(motorist_id):
    """Verifica quais tabelas estão referenciando um motorista específico"""
    
    db_path = 'dbs/db_app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obter todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"🔍 Verificando dependências do motorista ID: {motorist_id}")
        print("=" * 50)
        
        # Verificar cada tabela por referências ao motorista
        for table in tables:
            try:
                # Obter estrutura da tabela
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                # Procurar por colunas que podem referenciar motoristas
                motorist_columns = []
                for col in columns:
                    col_name = col[1].lower()
                    if 'motorist' in col_name or 'motorista' in col_name or 'id_motorist' in col_name:
                        motorist_columns.append(col[1])
                
                if motorist_columns:
                    print(f"\n📋 Tabela: {table}")
                    print(f"   Colunas relacionadas: {', '.join(motorist_columns)}")
                    
                    # Verificar se há registros referenciando o motorista
                    for col in motorist_columns:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = ?", (motorist_id,))
                            count = cursor.fetchone()[0]
                            if count > 0:
                                print(f"   ⚠️  {col}: {count} registro(s) encontrado(s)")
                                
                                # Mostrar alguns exemplos
                                cursor.execute(f"SELECT * FROM {table} WHERE {col} = ? LIMIT 3", (motorist_id,))
                                examples = cursor.fetchall()
                                if examples:
                                    print(f"   📝 Exemplos de registros:")
                                    for i, example in enumerate(examples, 1):
                                        print(f"      {i}. {example}")
                        except Exception as e:
                            print(f"   ❌ Erro ao verificar {col}: {e}")
                            
            except Exception as e:
                print(f"❌ Erro ao verificar tabela {table}: {e}")
        
        # Verificar também por nome do motorista
        cursor.execute("SELECT nome FROM motorists WHERE id = ?", (motorist_id,))
        motorist_name = cursor.fetchone()
        if motorist_name:
            motorist_name = motorist_name[0]
            print(f"\n🔍 Verificando por nome: {motorist_name}")
            
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    name_columns = []
                    for col in columns:
                        col_name = col[1].lower()
                        if 'nome' in col_name or 'name' in col_name:
                            name_columns.append(col[1])
                    
                    if name_columns:
                        for col in name_columns:
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?", (f'%{motorist_name}%',))
                                count = cursor.fetchone()[0]
                                if count > 0:
                                    print(f"   📋 {table}.{col}: {count} registro(s) com nome similar")
                            except:
                                pass
                except:
                    pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")

if __name__ == "__main__":
    motorist_id = 72  # ID do motorista que você está tentando excluir
    check_motorist_dependencies(motorist_id) 