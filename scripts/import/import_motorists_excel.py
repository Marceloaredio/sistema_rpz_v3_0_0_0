#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para importar dados do Excel "Novos dados motorists" para a tabela motorists
"""

import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime
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

def validate_required_fields(row):
    """Valida campos obrigatórios"""
    required_fields = {
        'nome': 'Nome',
        'cpf': 'CPF',
        'cnh': 'CNH',
        'rg': 'RG',
        'operacao': 'Operação',
        'ctps': 'CTPS',
        'serie': 'Série',
        'data_nascimento': 'Data de Nascimento',
        'primeira_cnh': 'Primeira CNH',
        'data_expedicao': 'Data da Expedição',
        'vencimento_cnh': 'Vencimento CNH',
        'telefone': 'Telefone',
        'endereco': 'Endereço',
        'filiacao': 'Filiação',
        'estado_civil': 'Estado Civil',
        'filhos': 'Filhos',
        'cargo': 'Cargo',
        'empresa': 'Empresa'
    }
    
    missing_fields = []
    for field, display_name in required_fields.items():
        if pd.isna(row.get(field)) or str(row.get(field)).strip() == '':
            missing_fields.append(display_name)
    
    return missing_fields

def get_next_id(cursor):
    """Obtém o próximo ID disponível"""
    cursor.execute("SELECT MAX(id) FROM motorists")
    result = cursor.fetchone()
    max_id = result[0] if result[0] else 0
    return max_id + 1

def check_duplicates(cursor, cpf, nome):
    """Verifica duplicatas por CPF e nome"""
    duplicates = []
    
    if cpf:
        cursor.execute("SELECT id, nome FROM motorists WHERE cpf = ?", (cpf,))
        existing = cursor.fetchone()
        if existing:
            duplicates.append(f"CPF já existe (ID: {existing[0]}, Nome: {existing[1]})")
    
    if nome:
        cursor.execute("SELECT id, cpf FROM motorists WHERE nome = ?", (nome,))
        existing = cursor.fetchone()
        if existing:
            duplicates.append(f"Nome já existe (ID: {existing[0]}, CPF: {existing[1]})")
    
    return duplicates

def import_excel_to_database(excel_file_path, db_path):
    """Importa dados do Excel para o banco de dados"""
    
    print(f"🚀 Iniciando importação do arquivo: {excel_file_path}")
    print(f"📊 Banco de dados: {db_path}")
    
    # Verificar se o arquivo Excel existe
    if not os.path.exists(excel_file_path):
        print(f"❌ Arquivo não encontrado: {excel_file_path}")
        return False
    
    # Verificar se o banco de dados existe
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Ler o arquivo Excel
        print("📖 Lendo arquivo Excel...")
        df = pd.read_excel(excel_file_path)
        
        print(f"✅ Arquivo lido com sucesso! Encontradas {len(df)} linhas")
        print(f"📋 Colunas encontradas: {list(df.columns)}")
        
        # Conectar ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contadores
        total_rows = len(df)
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔄 Processando {total_rows} registros...")
        
        for index, row in df.iterrows():
            try:
                print(f"\n--- Processando linha {index + 1}/{total_rows} ---")
                
                # Validar campos obrigatórios
                missing_fields = validate_required_fields(row)
                if missing_fields:
                    print(f"⚠️  Campos obrigatórios faltando: {', '.join(missing_fields)}")
                    skipped_count += 1
                    continue
                
                # Limpar e processar dados
                nome = str(row.get('nome', '')).strip().upper()
                cpf = clean_cpf_cnh(row.get('cpf'))
                cnh = clean_cpf_cnh(row.get('cnh'))
                rg = clean_rg(row.get('rg'))
                codigo_sap = clean_cpf_cnh(row.get('codigo_sap'))
                operacao = str(row.get('operacao', '')).strip().upper()
                ctps = str(row.get('ctps', '')).strip()
                if ctps.endswith('.0'):
                    ctps = ctps[:-2]
                serie = str(row.get('serie', '')).strip()
                telefone = clean_phone(row.get('telefone'))
                endereco = str(row.get('endereco', '')).strip()
                filiacao = str(row.get('filiacao', '')).strip()
                estado_civil = str(row.get('estado_civil', '')).strip().upper()
                filhos = str(row.get('filhos', '0')).strip()
                if filhos.endswith('.0'):
                    filhos = filhos[:-2]
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
                vencimento_toxicologico_clt = convert_date(row.get('vencimento_toxicologico_clt'))
                done_aso_semestral = convert_date(row.get('done_aso_semestral'))
                vencimento_aso_semestral = convert_date(row.get('vencimento_aso_semestral'))
                done_aso_periodico = convert_date(row.get('done_aso_periodico'))
                vencimento_aso_periodico = convert_date(row.get('vencimento_aso_periodico'))
                done_buoony = convert_date(row.get('done_buoony'))
                vencimento_buonny = convert_date(row.get('vencimento_buonny'))
                done_toxicologico_cnh = convert_date(row.get('done_toxicologico_cnh'))
                vencimento_toxicologico_cnh = convert_date(row.get('vencimento_toxicologico_cnh'))
                
                # Validações específicas
                if cpf and len(cpf) != 11:
                    print(f"⚠️  CPF inválido: {cpf} (deve ter 11 dígitos)")
                    skipped_count += 1
                    continue
                
                if cnh and len(cnh) != 11:
                    print(f"⚠️  CNH inválida: {cnh} (deve ter 11 dígitos)")
                    skipped_count += 1
                    continue
                
                # Verificar se o ID já existe
                cursor.execute("SELECT nome FROM motorists WHERE id = ?", (motorist_id,))
                existing_motorist = cursor.fetchone()
                if existing_motorist:
                    print(f"⚠️  ID {motorist_id} já existe (Nome: {existing_motorist[0]})")
                    skipped_count += 1
                    continue
                
                # Verificar duplicatas
                duplicates = check_duplicates(cursor, cpf, nome)
                if duplicates:
                    print(f"⚠️  Duplicatas encontradas: {'; '.join(duplicates)}")
                    skipped_count += 1
                    continue
                
                # Usar o ID da planilha
                motorist_id = int(row.get('id', 0))
                if motorist_id == 0:
                    print(f"⚠️  ID inválido na linha {index + 1}")
                    skipped_count += 1
                    continue
                
                # Preparar dados para inserção
                motorist_data = (
                    motorist_id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie,
                    data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp,
                    vencimento_mopp, done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral,
                    vencimento_aso_semestral, done_aso_periodico, vencimento_aso_periodico,
                    done_buoony, vencimento_buonny, telefone, endereco, filiacao, estado_civil,
                    filhos, cargo, empresa, 'Ativo', 'Inativo', 'Inativo', done_toxicologico_cnh,
                    vencimento_toxicologico_cnh, email
                )
                
                # Inserir no banco
                query = """INSERT INTO motorists (
                    id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                    data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, 
                    vencimento_mopp, done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral, 
                    vencimento_aso_semestral, done_aso_periodico, vencimento_aso_periodico, 
                    done_buoony, vencimento_buonny, telefone, endereco, filiacao, estado_civil, 
                    filhos, cargo, empresa, status, conf_jornada, conf_fecham, done_toxicologico_cnh,
                    vencimento_toxicologico_cnh, email
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                
                cursor.execute(query, motorist_data)
                conn.commit()
                
                print(f"✅ Motorista importado com sucesso! ID: {motorist_id}, Nome: {nome}")
                imported_count += 1
                
            except Exception as e:
                print(f"❌ Erro ao processar linha {index + 1}: {str(e)}")
                error_count += 1
        
        # Fechar conexão
        conn.close()
        
        # Relatório final
        print(f"\n📊 RELATÓRIO FINAL:")
        print(f"✅ Importados com sucesso: {imported_count}")
        print(f"⚠️  Ignorados (duplicatas/erros): {skipped_count}")
        print(f"❌ Erros: {error_count}")
        print(f"📋 Total processado: {total_rows}")
        
        if imported_count > 0:
            print(f"\n🎉 Importação concluída com sucesso! {imported_count} motoristas foram adicionados ao banco de dados.")
            return True
        else:
            print(f"\n⚠️  Nenhum motorista foi importado. Verifique os dados do Excel.")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante a importação: {str(e)}")
        return False

def main():
    """Função principal"""
    print("🚀 IMPORTADOR DE MOTORISTAS - EXCEL PARA BANCO DE DADOS")
    print("=" * 60)
    
    # Configurar caminhos
    excel_file = "Novos dados motorists.xlsx"
    db_file = "dbs/db_app.db"
    
    # Verificar se o arquivo Excel existe
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo Excel não encontrado: {excel_file}")
        print("📁 Certifique-se de que o arquivo 'Novos dados motorists.xlsx' está na mesma pasta deste script.")
        return
    
    # Verificar se o banco de dados existe
    if not os.path.exists(db_file):
        print(f"❌ Banco de dados não encontrado: {db_file}")
        print("📁 Certifique-se de que o arquivo db_app.db está na pasta dbs/")
        return
    
    # Confirmar importação
    print(f"📋 Arquivo Excel: {excel_file}")
    print(f"🗄️  Banco de dados: {db_file}")
    print("\n⚠️  ATENÇÃO: Esta operação irá adicionar novos motoristas ao banco de dados.")
    print("   Duplicatas por CPF ou nome serão ignoradas.")
    
    response = input("\n🤔 Deseja continuar? (s/n): ").lower().strip()
    if response not in ['s', 'sim', 'y', 'yes']:
        print("❌ Importação cancelada pelo usuário.")
        return
    
    # Executar importação
    success = import_excel_to_database(excel_file, db_file)
    
    if success:
        print("\n✅ Importação concluída com sucesso!")
    else:
        print("\n❌ Importação falhou. Verifique os logs acima.")

if __name__ == "__main__":
    main() 