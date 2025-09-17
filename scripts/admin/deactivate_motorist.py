#!/usr/bin/env python3
import sqlite3
import sys

def deactivate_motorist(motorist_id):
    """Desativa um motorista alterando seu status para 'Inativo'"""
    
    db_path = 'dbs/db_app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🚫 Desativando motorista ID: {motorist_id}")
        print("=" * 50)
        
        # Verificar se o motorista existe
        cursor.execute("SELECT nome, status FROM motorists WHERE id = ?", (motorist_id,))
        motorist = cursor.fetchone()
        
        if not motorist:
            print(f"❌ Motorista ID {motorist_id} não encontrado!")
            return
        
        motorist_name, current_status = motorist
        print(f"📋 Motorista: {motorist_name}")
        print(f"📊 Status atual: {current_status}")
        
        if current_status == 'Inativo':
            print("ℹ️  Motorista já está inativo!")
            return
        
        # Atualizar status para 'Inativo'
        try:
            cursor.execute("UPDATE motorists SET status = 'Inativo' WHERE id = ?", (motorist_id,))
            if cursor.rowcount > 0:
                print(f"✅ Motorista desativado com sucesso!")
                print(f"📊 Novo status: Inativo")
            else:
                print(f"❌ Erro ao desativar motorista")
                
        except Exception as e:
            print(f"❌ Erro ao desativar motorista: {e}")
        
        # Commit das alterações
        conn.commit()
        conn.close()
        
        print("✅ Desativação concluída com sucesso!")
        print("💡 Os dados históricos foram preservados.")
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        motorist_id = int(sys.argv[1])
    else:
        motorist_id = 72  # ID padrão
    
    # Confirmação
    print(f"⚠️  ATENÇÃO: Esta operação irá desativar o motorista ID {motorist_id}!")
    print("O motorista será marcado como 'Inativo' mas os dados históricos serão preservados.")
    
    confirm = input("Deseja continuar? (s/N): ").lower()
    if confirm in ['s', 'sim', 'y', 'yes']:
        deactivate_motorist(motorist_id)
    else:
        print("❌ Operação cancelada!") 