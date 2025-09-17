# Stub do pandas para quando a biblioteca não está disponível
# Este arquivo é usado como fallback quando pandas não pode ser importado

import sys
from datetime import datetime, timedelta

class DataFrame:
    """Stub da classe DataFrame do pandas"""
    def __init__(self, data=None, columns=None):
        self.data = data or []
        self.columns = columns or []
    
    def __getitem__(self, key):
        return self
    
    def __setitem__(self, key, value):
        pass
    
    def to_dict(self, orient='records'):
        return self.data
    
    def head(self, n=5):
        return self
    
    def tail(self, n=5):
        return self
    
    def shape(self):
        return (len(self.data), len(self.columns))
    
    def empty(self):
        return len(self.data) == 0

class Series:
    """Stub da classe Series do pandas"""
    def __init__(self, data=None):
        self.data = data or []
    
    def __getitem__(self, key):
        return self.data[key] if isinstance(key, int) else self
    
    def __setitem__(self, key, value):
        if isinstance(key, int) and key < len(self.data):
            self.data[key] = value
    
    def isna(self):
        return [False] * len(self.data)
    
    def notna(self):
        return [True] * len(self.data)
    
    def str(self):
        return self
    
    def extract(self, pattern):
        return self
    
    def dt(self):
        return self

class Timestamp:
    """Stub da classe Timestamp do pandas"""
    def __init__(self, value):
        self.value = value
    
    def strftime(self, format_str):
        return self.value.strftime(format_str)

def to_datetime(data, **kwargs):
    """Stub da função to_datetime do pandas"""
    if isinstance(data, str):
        try:
            return datetime.strptime(data, '%Y-%m-%d')
        except:
            return datetime.now()
    return data

def read_excel(file_path, **kwargs):
    """Stub da função read_excel do pandas"""
    return DataFrame()

def concat(dataframes, **kwargs):
    """Stub da função concat do pandas"""
    return DataFrame()

# Criar alias para compatibilidade
pd = sys.modules[__name__]






