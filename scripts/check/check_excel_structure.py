#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar a estrutura do arquivo Excel "Novos dados motorists.xlsx"
Especialmente a coluna A que deve conter os IDs
"""

import pandas as pd
import os

def check_excel_structure():
    """Verifica a estrutura do arquivo Excel"""
    
    excel_file = "Novos dados motorists.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo não encontrado: {excel_file}")
        return
    
    try:
        # Ler o arquivo Excel
        print(f"📖 Lendo arquivo: {excel_file}")
        df = pd.read_excel(excel_file)
        
        print(f"\n📊 INFORMAÇÕES GERAIS:")
        print(f"   Total de linhas: {len(df)}")
        print(f"   Total de colunas: {len(df.columns)}")
        
        print(f"\n📋 COLUNAS ENCONTRADAS:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. {col}")
        
        print(f"\n🔍 ANÁLISE DA COLUNA A (PRIMEIRA COLUNA):")
        first_col = df.columns[0]
        print(f"   Nome da coluna: '{first_col}'")
        print(f"   Tipo de dados: {df[first_col].dtype}")
        
        # Verificar se a primeira coluna parece ser ID
        sample_values = df[first_col].head(10).tolist()
        print(f"   Primeiros 10 valores: {sample_values}")
        
        # Verificar se são números
        numeric_count = 0
        for value in df[first_col]:
            if pd.notna(value) and str(value).isdigit():
                numeric_count += 1
        
        print(f"   Valores numéricos: {numeric_count}/{len(df)}")
        
        if numeric_count == len(df):
            print(f"   ✅ TODOS os valores são numéricos - provavelmente é a coluna de ID!")
        elif numeric_count > len(df) * 0.8:
            print(f"   ⚠️  A maioria dos valores são numéricos - pode ser a coluna de ID")
        else:
            print(f"   ❌ Poucos valores numéricos - provavelmente não é a coluna de ID")
        
        # Verificar se há valores únicos
        unique_values = df[first_col].nunique()
        print(f"   Valores únicos: {unique_values}")
        
        if unique_values == len(df):
            print(f"   ✅ Todos os valores são únicos - ideal para ID!")
        else:
            print(f"   ⚠️  Há valores duplicados na coluna")
        
        # Verificar se há valores nulos
        null_count = df[first_col].isnull().sum()
        print(f"   Valores nulos: {null_count}")
        
        if null_count == 0:
            print(f"   ✅ Nenhum valor nulo - coluna válida para ID!")
        else:
            print(f"   ⚠️  Há valores nulos na coluna")
        
        print(f"\n📝 AMOSTRA DE DADOS (primeiras 5 linhas):")
        print(df.head())
        
        print(f"\n🔍 VERIFICAÇÃO ESPECÍFICA PARA ID:")
        if numeric_count == len(df) and unique_values == len(df) and null_count == 0:
            print(f"   ✅ A coluna '{first_col}' é PERFEITA para ser usada como ID!")
            print(f"   💡 Recomendação: Use esta coluna como ID na importação")
        else:
            print(f"   ⚠️  A coluna '{first_col}' pode ter problemas para ser usada como ID")
            print(f"   💡 Verifique os dados antes de usar como ID")
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {str(e)}")

if __name__ == "__main__":
    print("🔍 VERIFICADOR DE ESTRUTURA DO EXCEL")
    print("=" * 50)
    check_excel_structure() 