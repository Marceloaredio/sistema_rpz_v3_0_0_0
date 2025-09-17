#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Feature Flags - Sistema RPZ v3.0.0.0

Este módulo gerencia as funcionalidades que podem ser ativadas/desativadas
através de configurações, permitindo deploy gradual e rollback seguro.

Autor: Sistema RPZ
Data: 01/08/2025
Versão: 1.0
"""

import configparser
import os
from typing import Any, Optional
from pathlib import Path

class FeatureFlags:
    """
    Classe para gerenciar feature flags do sistema.
    """
    
    def __init__(self, config_path: str = "config/config.ini"):
        """
        Inicializa o gerenciador de feature flags.
        
        :param config_path: Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Carrega o arquivo de configuração."""
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
            else:
                raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            # Configurações padrão em caso de erro
            self._set_defaults()
    
    def _set_defaults(self):
        """Define configurações padrão em caso de erro."""
        self.config['FECHAMENTO'] = {
            'CARGA_HORARIA_ESPECIAL_ENABLED': 'false',
            'CARGA_HORARIA_MAX_HORAS': '12',
            'CARGA_HORARIA_FORMATO': 'HH:00'
        }
    
    def is_enabled(self, feature: str) -> bool:
        """
        Verifica se uma funcionalidade está habilitada.
        
        :param feature: Nome da funcionalidade (ex: 'CARGA_HORARIA_ESPECIAL_ENABLED')
        :return: True se habilitada, False caso contrário
        """
        try:
            # Extrair seção e chave da feature
            if '.' in feature:
                section, key = feature.split('.', 1)
            else:
                # Para compatibilidade, assumir seção FECHAMENTO
                section = 'FECHAMENTO'
                key = feature
            
            if section in self.config and key in self.config[section]:
                value = self.config[section][key].lower()
                return value in ['true', '1', 'yes', 'on']
            return False
            
        except Exception as e:
            print(f"Erro ao verificar feature flag '{feature}': {e}")
            return False
    
    def get_value(self, feature: str, default: Any = None) -> Any:
        """
        Obtém o valor de uma configuração.
        
        :param feature: Nome da configuração (ex: 'CARGA_HORARIA_MAX_HORAS')
        :param default: Valor padrão se não encontrado
        :return: Valor da configuração ou default
        """
        try:
            if '.' in feature:
                section, key = feature.split('.', 1)
            else:
                section = 'FECHAMENTO'
                key = feature
            
            if section in self.config and key in self.config[section]:
                value = self.config[section][key]
                
                # Tentar converter para tipos apropriados
                if value.lower() in ['true', 'false']:
                    return value.lower() == 'true'
                elif value.isdigit():
                    return int(value)
                elif value.replace('.', '').isdigit():
                    return float(value)
                else:
                    return value
            
            return default
            
        except Exception as e:
            print(f"Erro ao obter valor da configuração '{feature}': {e}")
            return default
    
    def set_value(self, feature: str, value: Any) -> bool:
        """
        Define o valor de uma configuração.
        
        :param feature: Nome da configuração
        :param value: Novo valor
        :return: True se bem-sucedido, False caso contrário
        """
        try:
            if '.' in feature:
                section, key = feature.split('.', 1)
            else:
                section = 'FECHAMENTO'
                key = feature
            
            # Criar seção se não existir
            if section not in self.config:
                self.config[section] = {}
            
            # Definir valor
            self.config[section][key] = str(value)
            
            # Salvar no arquivo
            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            
            return True
            
        except Exception as e:
            print(f"Erro ao definir configuração '{feature}': {e}")
            return False
    
    def reload(self):
        """Recarrega o arquivo de configuração."""
        self._load_config()
    
    def get_all_features(self) -> dict:
        """
        Retorna todas as configurações de feature flags.
        
        :return: Dicionário com todas as configurações
        """
        features = {}
        for section in self.config.sections():
            features[section] = {}
            for key, value in self.config[section].items():
                features[section][key] = value
        
        return features

# Instância global para uso em todo o sistema
feature_flags = FeatureFlags()

# Funções de conveniência para uso direto
def is_carga_horaria_especial_enabled() -> bool:
    """Verifica se a funcionalidade de carga horária especial está habilitada."""
    return feature_flags.is_enabled('CARGA_HORARIA_ESPECIAL_ENABLED')

def get_carga_horaria_max_horas() -> int:
    """Obtém o número máximo de horas permitido para carga horária especial."""
    return feature_flags.get_value('CARGA_HORARIA_MAX_HORAS', 12)

def get_carga_horaria_formato() -> str:
    """Obtém o formato esperado para carga horária especial."""
    return feature_flags.get_value('CARGA_HORARIA_FORMATO', 'HH:00')

# Exemplo de uso:
if __name__ == "__main__":
    print("🔧 Feature Flags - Sistema RPZ")
    print("=" * 40)
    
    print(f"Carga Horária Especial: {'✅ Ativa' if is_carga_horaria_especial_enabled() else '❌ Inativa'}")
    print(f"Máximo de Horas: {get_carga_horaria_max_horas()}")
    print(f"Formato: {get_carga_horaria_formato()}")
    
    print("\n📋 Todas as configurações:")
    for section, configs in feature_flags.get_all_features().items():
        print(f"\n[{section}]")
        for key, value in configs.items():
            print(f"  {key} = {value}")
