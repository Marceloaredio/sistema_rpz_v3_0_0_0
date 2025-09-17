import sqlite3

def clean_database():
    conn = sqlite3.connect('dbs/db_app.db')
    cursor = conn.cursor()
    
    print("=== LIMPEZA DO BANCO DE DADOS ===")
    
    # Remover tabela vazia
    try:
        cursor.execute("DROP TABLE IF EXISTS analyzed_closures;")
        conn.commit()
        print("✅ Tabela 'analyzed_closures' removida (estava vazia)")
    except Exception as e:
        print(f"❌ Erro ao remover tabela: {e}")
    
    # Verificar se ainda existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analyzed_closures';")
    if cursor.fetchone():
        print("⚠️ Tabela ainda existe")
    else:
        print("✅ Tabela removida com sucesso")
    
    # Otimizar banco
    try:
        cursor.execute("VACUUM;")
        conn.commit()
        print("✅ Banco otimizado (VACUUM executado)")
    except Exception as e:
        print(f"❌ Erro ao otimizar banco: {e}")
    
    # Verificar tamanho final
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
    table_count = cursor.fetchone()[0]
    print(f"📊 Total de tabelas após limpeza: {table_count}")
    
    conn.close()

if __name__ == "__main__":
    clean_database()




