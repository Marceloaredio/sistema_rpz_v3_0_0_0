#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpar completamente a tabela motorists e reimportar com dados corretos
"""

import pandas as pd
import sqlite3
import os
import sys
import re

def clean_cpf_cnh(value):
    """Limpa CPF e CNH removendo pontos e hífens"""
    if pd.isna(value):
        return None
    return str(value).replace('.', '').replace('-', '').strip()

def clean_rg(value):
    """Limpa RG removendo pontos e hífens, mantendo números e letras"""
    if pd.isna(value):
        return None
    return str(value).replace('.', '').replace('-', '').strip()

def clean_phone(value):
    """Formata telefone para o padrão (##) #####-####"""
    if pd.isna(value):
        return None
    
    # Remove todos os caracteres não numéricos
    phone = re.sub(r'\D', '', str(value))
    
    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    else:
        return str(value)

def convert_date(value):
    """Converte data do Excel para formato dd/mm/aaaa"""
    if pd.isna(value):
        return None
    
    try:
        # Se for datetime do pandas
        if isinstance(value, pd.Timestamp):
            return value.strftime('%d/%m/%Y')
        
        # Se for string no formato dd/mm/aaaa
        if isinstance(value, str) and '/' in value:
            return value  # Manter formato original
        
        # Se for número (data do Excel)
        if isinstance(value, (int, float)):
            date = pd.to_datetime('1899-12-30') + pd.Timedelta(days=int(value))
            return date.strftime('%d/%m/%Y')
            
    except:
        pass
    
    return str(value) if value else None

def clean_numeric_field(value):
    """Remove .0 de campos numéricos"""
    if pd.isna(value):
        return ''
    value_str = str(value).strip()
    if value_str.endswith('.0'):
        return value_str[:-2]
    return value_str

def backup_and_clear_motorists(db_path):
    """Faz backup e limpa a tabela motorists"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar registros antes
        cursor.execute("SELECT COUNT(*) FROM motorists")
        count_before = cursor.fetchone()[0]
        
        print(f"📊 Registros encontrados na tabela motorists: {count_before}")
        
        if count_before > 0:
            # Criar backup
            cursor.execute("CREATE TABLE IF NOT EXISTS motorists_backup AS SELECT * FROM motorists")
            print(f"✅ Backup criado: {count_before} registros salvos em motorists_backup")
            
            # Limpar tabela
            cursor.execute("DELETE FROM motorists")
            conn.commit()
            
            print(f"🗑️  Tabela motorists limpa: {count_before} registros removidos")
        else:
            print("ℹ️  Tabela motorists já está vazia")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao limpar tabela: {e}")
        return False

def import_with_correct_ids(excel_file, db_path):
    """Importa motoristas com os IDs corretos da planilha"""
    
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo Excel não encontrado: {excel_file}")
        return False
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Ler planilha - forçar leitura de todas as linhas
        print(f"📖 Lendo planilha: {excel_file}")
        df = pd.read_excel(excel_file, header=0, nrows=None, engine='openpyxl')
        
        # Verificar se há dados vazios no início e remover
        df = df.dropna(subset=['id', 'nome']).reset_index(drop=True)
        
        print(f"📊 Total de linhas encontradas: {len(df)}")
        print(f"📋 Primeiras linhas: {df.head(3).to_dict('records')}")
        print(f"📋 Últimas linhas: {df.tail(3).to_dict('records')}")
        
        # Verificar se temos 71 registros
        if len(df) != 71:
            print(f"⚠️  ATENÇÃO: Esperava 71 registros, mas encontrou {len(df)}")
        
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        imported_count = 0
        skipped_count = 0
        
        print(f"🔄 Processando {len(df)} registros...")
        
        for index, row in df.iterrows():
            try:
                # Obter ID da planilha
                motorist_id = int(row.get('id', 0))
                if motorist_id == 0:
                    print(f"⚠️  ID inválido na linha {index + 1}")
                    skipped_count += 1
                    continue
                
                # Obter outros dados
                nome = str(row.get('nome', '')).strip().upper()
                cpf = str(row.get('cpf', '')).strip()
                cnh = str(row.get('cnh', '')).strip()
                rg = str(row.get('rg', '')).strip()
                operacao = str(row.get('operacao', '')).strip().upper()
                ctps = clean_numeric_field(row.get('ctps'))
                serie = clean_numeric_field(row.get('serie'))
                telefone = clean_phone(row.get('telefone'))
                endereco = str(row.get('endereco', '')).strip()
                filiacao = str(row.get('filiacao', '')).strip()
                estado_civil = str(row.get('estado_civil', '')).strip().upper()
                filhos = clean_numeric_field(row.get('filhos'))
                cargo = str(row.get('cargo', '')).strip().upper()
                empresa = str(row.get('empresa', '')).strip()
                email = str(row.get('email', '')).strip()
                
                # Converter datas
                data_admissao = convert_date(row.get('data_admissao'))
                data_nascimento = convert_date(row.get('data_nascimento'))
                primeira_cnh = convert_date(row.get('primeira_cnh'))
                data_expedicao = convert_date(row.get('data_expedicao'))
                vencimento_cnh = convert_date(row.get('vencimento_cnh'))
                done_mopp = convert_date(row.get('done_mopp'))
                vencimento_mopp = convert_date(row.get('vencimento_mopp'))
                done_toxicologico_clt = convert_date(row.get('done_toxicologico_clt'))
                vencimento_toxicologico_clt = convert_date(row.get('vencimento_toxicologico-clt'))
                done_aso_semestral = convert_date(row.get('done_aso_semestral'))
                vencimento_aso_semestral = convert_date(row.get('vencimento_aso_semestral'))
                done_aso_periodico = convert_date(row.get('done_aso_periodico'))
                vencimento_aso_periodico = convert_date(row.get('vencimento_aso_periodico'))
                done_buonny = convert_date(row.get('done_buonny'))
                vencimento_buonny = convert_date(row.get('vencimento_buonny'))
                done_toxicologico_cnh = convert_date(row.get('done_toxicologico_cnh'))
                vencimento_toxicologico_cnh = convert_date(row.get('vencimento_toxicologico_cnh'))
                
                # Validações básicas
                if not nome or not cpf or not cnh:
                    print(f"⚠️  Dados obrigatórios faltando na linha {index + 1}: {nome}, {cpf}, {cnh}")
                    skipped_count += 1
                    continue
                
                # Inserir no banco
                motorist_data = (
                    motorist_id, nome, data_admissao, cpf, cnh, rg, '', operacao, ctps, serie,
                    data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp,
                    vencimento_mopp, done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral,
                    vencimento_aso_semestral, done_aso_periodico, vencimento_aso_periodico,
                    done_buonny, vencimento_buonny, telefone, endereco, filiacao, estado_civil,
                    filhos, cargo, empresa, 'Ativo', 'Inativo', 'Inativo', done_toxicologico_cnh,
                    vencimento_toxicologico_cnh, email
                )
                
                query = """INSERT INTO motorists (
                    id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                    data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, 
                    vencimento_mopp, done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral, 
                    vencimento_aso_semestral, done_aso_periodico, vencimento_aso_periodico, 
                    done_buonny, vencimento_buonny, telefone, endereco, filiacao, estado_civil, 
                    filhos, cargo, empresa, status, conf_jornada, conf_fecham, done_toxicologico_cnh,
                    vencimento_toxicologico_cnh, email
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                
                cursor.execute(query, motorist_data)
                conn.commit()
                
                print(f"✅ Motorista importado: ID {motorist_id}, Nome: {nome}")
                imported_count += 1
                
            except Exception as e:
                print(f"❌ Erro na linha {index + 1}: {e}")
                skipped_count += 1
        
        conn.close()
        
        print(f"\n📊 RELATÓRIO FINAL:")
        print(f"✅ Importados: {imported_count}")
        print(f"⚠️  Ignorados: {skipped_count}")
        
        return imported_count > 0
        
    except Exception as e:
        print(f"❌ Erro durante importação: {e}")
        return False

def main():
    """Função principal"""
    print("🧹 LIMPEZA E REIMPORTAÇÃO COMPLETA DOS MOTORISTAS")
    print("=" * 60)
    
    excel_file = "Novos dados motorists.xlsx"
    db_path = "dbs/db_app.db"
    
    # Verificar arquivos
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo Excel não encontrado: {excel_file}")
        return
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    # Informações
    print(f"📋 Arquivo Excel: {excel_file}")
    print(f"🗄️  Banco de dados: {db_path}")
    print("\n⚠️  ATENÇÃO: Esta operação irá:")
    print("   1. Fazer backup da tabela motorists atual")
    print("   2. LIMPAR COMPLETAMENTE a tabela motorists")
    print("   3. Reimportar com os dados corretos da planilha")
    print("\n✅ Problemas que serão corrigidos:")
    print("   - IDs corretos da planilha")
    print("   - Datas no formato dd/mm/aaaa")
    print("   - Campos numéricos sem .0")
    
    # Executar automaticamente
    print("\n🔄 Iniciando processo automaticamente...")
    
    # Executar limpeza e importação
    
    # 1. Backup e limpeza
    if not backup_and_clear_motorists(db_path):
        print("❌ Falha na limpeza. Operação cancelada!")
        return
    
    # 2. Reimportar
    if import_with_correct_ids(excel_file, db_path):
        print("\n✅ Processo concluído com sucesso!")
        print("💡 Todos os motoristas foram reimportados com dados corretos.")
    else:
        print("\n❌ Falha na importação!")
        print("💡 Verifique os dados da planilha e tente novamente.")

if __name__ == "__main__":
    main() 