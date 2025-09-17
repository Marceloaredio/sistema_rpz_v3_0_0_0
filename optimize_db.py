import sqlite3

def optimize_database():
    conn = sqlite3.connect('dbs/db_app.db')
    cursor = conn.cursor()
    
    print("=== OTIMIZAÇÃO DO BANCO DE DADOS ===")
    
    # Verificar índices existentes
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
    indexes = cursor.fetchall()
    
    print(f"Índices existentes: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx[0]} em {idx[1]}")
    
    # Verificar tamanho do banco antes
    import os
    db_size_before = os.path.getsize('dbs/db_app.db') / (1024*1024)  # MB
    print(f"\nTamanho do banco antes: {db_size_before:.2f} MB")
    
    # Executar ANALYZE para atualizar estatísticas
    try:
        cursor.execute("ANALYZE;")
        conn.commit()
        print("✅ Estatísticas atualizadas (ANALYZE executado)")
    except Exception as e:
        print(f"❌ Erro ao executar ANALYZE: {e}")
    
    # Executar VACUUM novamente para garantir otimização
    try:
        cursor.execute("VACUUM;")
        conn.commit()
        print("✅ Banco otimizado (VACUUM executado)")
    except Exception as e:
        print(f"❌ Erro ao executar VACUUM: {e}")
    
    # Verificar tamanho do banco depois
    db_size_after = os.path.getsize('dbs/db_app.db') / (1024*1024)  # MB
    print(f"Tamanho do banco depois: {db_size_after:.2f} MB")
    
    if db_size_after < db_size_before:
        saved = db_size_before - db_size_after
        print(f"💾 Espaço economizado: {saved:.2f} MB")
    else:
        print("ℹ️ Tamanho do banco mantido")
    
    conn.close()

if __name__ == "__main__":
    optimize_database()




