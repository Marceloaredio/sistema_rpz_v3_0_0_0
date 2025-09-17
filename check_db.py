import sqlite3

# Verificar database.db
try:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tabelas em database.db: {len(tables)}")
    if tables:
        print("Tabelas:", [table[0] for table in tables])
    conn.close()
except Exception as e:
    print(f"Erro ao verificar database.db: {e}")

# Verificar dbs/db_app.db
try:
    conn = sqlite3.connect('dbs/db_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tabelas em dbs/db_app.db: {len(tables)}")
    conn.close()
except Exception as e:
    print(f"Erro ao verificar dbs/db_app.db: {e}")

