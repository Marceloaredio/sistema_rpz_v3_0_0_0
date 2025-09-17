#!/usr/bin/env python3
import sqlite3
import sys

def delete_motorist_cascade(motorist_id):
    """Exclui um motorista e todos os seus registros relacionados"""
    
    db_path = 'dbs/db_app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🗑️  Excluindo motorista ID: {motorist_id}")
        print("=" * 50)
        
        # Verificar se o motorista existe
        cursor.execute("SELECT nome FROM motorists WHERE id = ?", (motorist_id,))
        motorist = cursor.fetchone()
        
        if not motorist:
            print(f"❌ Motorista ID {motorist_id} não encontrado!")
            return
        
        motorist_name = motorist[0]
        print(f"📋 Motorista: {motorist_name}")
        
        # Lista de tabelas para excluir registros relacionados
        tables_to_clean = [
            ('perm_data', 'motorist_id'),
            ('removed_infractions', 'motorist_id'),
            ('dayoff', 'motorist_id'),
            ('perm_data_fecham', 'motorist_id'),
            ('dayoff_fecham', 'motorist_id'),
            ('infractions', 'motorist_id'),
            ('infractions_old', 'motorist_id')
        ]
        
        total_deleted = 0
        
        # Excluir registros relacionados
        for table, column in tables_to_clean:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (motorist_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    cursor.execute(f"DELETE FROM {table} WHERE {column} = ?", (motorist_id,))
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    print(f"✅ {table}: {deleted} registro(s) excluído(s)")
                else:
                    print(f"ℹ️  {table}: Nenhum registro encontrado")
                    
            except Exception as e:
                print(f"❌ Erro ao excluir de {table}: {e}")
        
        # Finalmente, excluir o motorista
        try:
            cursor.execute("DELETE FROM motorists WHERE id = ?", (motorist_id,))
            if cursor.rowcount > 0:
                print(f"✅ Motorista excluído com sucesso!")
                total_deleted += 1
            else:
                print(f"❌ Erro ao excluir motorista")
                
        except Exception as e:
            print(f"❌ Erro ao excluir motorista: {e}")
        
        # Commit das alterações
        conn.commit()
        conn.close()
        
        print(f"\n🎯 Total de registros excluídos: {total_deleted}")
        print("✅ Exclusão concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        motorist_id = int(sys.argv[1])
    else:
        motorist_id = 72  # ID padrão
    
    # Confirmação
    print(f"⚠️  ATENÇÃO: Esta operação irá excluir o motorista ID {motorist_id} e TODOS os seus registros relacionados!")
    print("Isso inclui dados de ponto, infrações, folgas, etc.")
    
    confirm = input("Deseja continuar? (s/N): ").lower()
    if confirm in ['s', 'sim', 'y', 'yes']:
        delete_motorist_cascade(motorist_id)
    else:
        print("❌ Operação cancelada!") 