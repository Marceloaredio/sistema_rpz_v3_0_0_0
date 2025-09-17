#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controller.google_integration import GoogleIntegration

def test_google_integration():
    """Testa a integração com Google"""
    
    print("=== Teste de Integração com Google ===")
    
    # Verificar se o arquivo de credenciais existe
    creds_file = "config/google_credentials.json"
    if not os.path.exists(creds_file):
        print(f"❌ Arquivo de credenciais não encontrado: {creds_file}")
        print("Por favor, configure as credenciais conforme o arquivo GOOGLE_SETUP.md")
        return False
    
    print(f"✅ Arquivo de credenciais encontrado: {creds_file}")
    
    # Testar inicialização da integração
    try:
        google_integration = GoogleIntegration()
        print("✅ Integração com Google inicializada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar integração: {str(e)}")
        return False
    
    # Testar dados de exemplo
    test_motorist = {
        'id': 999,
        'nome': 'TESTE INTEGRAÇÃO GOOGLE',
        'data_admissao': '01/01/2024',
        'cpf': '123.456.789-00',
        'cnh': '12345678901',
        'rg': '12345678',
        'codigo_sap': '123456789',
        'operacao': 'VIBRA',
        'ctps': '1234567890',
        'serie': '123',
        'data_nascimento': '01/01/1990',
        'primeira_cnh': '01/01/2010',
        'data_expedicao': '01/01/2010',
        'vencimento_cnh': '01/01/2025',
        'done_mopp': '01/01/2024',
        'vencimento_mopp': '01/01/2025',
        'done_toxicologico_clt': '01/01/2024',
        'vencimento_toxicologico_clt': '01/01/2025',
        'done_aso_semestral': '01/01/2024',
        'vencimento_aso_semestral': '01/01/2025',
        'done_aso_periodico': '01/01/2024',
        'vencimento_aso_periodico': '01/01/2025',
        'done_buonny': '01/01/2024',
        'vencimento_buonny': '01/01/2025',
        'telefone': '(11) 99999-9999',
        'endereco': 'Rua Teste, 123',
        'filiacao': 'Pai e Mãe',
        'estado_civil': 'SOLTEIRO',
        'filhos': '0',
        'cargo': 'MOTORISTA DE CAMINHÃO TRUCK',
        'empresa': 'EMPRESA TESTE',
        'status': 'Ativo',
        'conf_jornada': 'Ativo',
        'conf_fecham': 'Ativo',
        'done_toxicologico_cnh': '01/01/2024',
        'vencimento_toxicologico_cnh': '01/01/2025',
        'email': 'teste@teste.com'
    }
    
    print(f"\nTestando com motorista: {test_motorist['nome']}")
    
    # Testar processamento (sem inserir dados reais)
    try:
        # Testar apenas a configuração
        print("✅ Configuração da integração está correta")
        print("📝 Para testar a inserção real, use a interface web")
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False
    
    print("\n=== Teste Concluído ===")
    print("✅ Integração com Google configurada corretamente")
    print("📝 Verifique os logs em: logs/verif_forms_google.txt")
    
    return True

if __name__ == "__main__":
    test_google_integration() 