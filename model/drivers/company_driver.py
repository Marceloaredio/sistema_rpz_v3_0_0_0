from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import List, Tuple, Optional
import re


class CompanyDriver(GeneralDriver):

    def __init__(self, logger: CustomLogger, db_path: str):
        GeneralDriver.__init__(self, logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        self.logger.print("Executando create table para companies")

        query = """
                    CREATE TABLE IF NOT EXISTS companies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        enterprise TEXT NOT NULL,
                        cnpj TEXT UNIQUE NOT NULL
                    )
        """
        self.exec_query(query, log_success=False)
        self.logger.print("Create table companies executado com sucesso.")

    def create_company(self, enterprise: str, cnpj: str) -> int:
        """
        Cria uma nova empresa no banco de dados.
        
        Args:
            enterprise: Nome da empresa
            cnpj: CNPJ da empresa (formato: XX.XXX.XXX/XXXX-XX)
            
        Returns:
            int: ID da empresa criada
        """
        self.logger.print(f"Criando empresa: {enterprise}")

        # Validar formato do CNPJ
        if not self._validate_cnpj_format(cnpj):
            raise ValueError(f"Formato de CNPJ inválido: {cnpj}. Use o formato XX.XXX.XXX/XXXX-XX")

        query = """INSERT INTO companies (enterprise, cnpj) VALUES (?, ?)"""
        params = (enterprise.strip(), cnpj.strip())

        company_id = self.exec_query(query=query, params=params, log_success=False)
        self.logger.print(f"Empresa criada com sucesso. ID: {company_id}")
        return company_id

    def create_company_with_id(self, id: int, enterprise: str, cnpj: str) -> int:
        """
        Cria uma empresa com ID específico.
        
        Args:
            id: ID da empresa
            enterprise: Nome da empresa
            cnpj: CNPJ da empresa
            
        Returns:
            int: ID da empresa criada
        """
        self.logger.print(f"Criando empresa com ID {id}: {enterprise}")

        # Validar formato do CNPJ
        if not self._validate_cnpj_format(cnpj):
            raise ValueError(f"Formato de CNPJ inválido: {cnpj}. Use o formato XX.XXX.XXX/XXXX-XX")

        query = """INSERT INTO companies (id, enterprise, cnpj) VALUES (?, ?, ?)"""
        params = (id, enterprise.strip(), cnpj.strip())

        company_id = self.exec_query(query=query, params=params, log_success=False)
        self.logger.print(f"Empresa criada com sucesso. ID: {company_id}")
        return company_id

    def update_company(self, set_columns: list, set_values: tuple, where_columns: list, where_values: tuple) -> int:
        """
        Atualiza dados de uma empresa.
        
        Args:
            set_columns: Lista de colunas a serem atualizadas
            set_values: Valores para as colunas
            where_columns: Lista de colunas para condição WHERE
            where_values: Valores para as condições WHERE
            
        Returns:
            int: Número de linhas afetadas
        """
        self.logger.print(f"Atualizando empresa com condições: {where_columns}")

        set_clause = ", ".join([f"{col} = ?" for col in set_columns])
        where_clause = " AND ".join([f"{col} = ?" for col in where_columns])

        query = f"UPDATE companies SET {set_clause} WHERE {where_clause}"
        params = set_values + where_values

        affected_rows = self.exec_query(query=query, params=params, log_success=False)
        self.logger.print(f"Empresa atualizada. Linhas afetadas: {affected_rows}")
        return affected_rows

    def retrieve_company(self, where_columns: List[str], where_values: Tuple) -> Optional[Tuple]:
        """
        Busca uma empresa específica.
        
        Args:
            where_columns: Lista de colunas para condição WHERE
            where_values: Valores para as condições WHERE
            
        Returns:
            Optional[Tuple]: Dados da empresa ou None se não encontrada
        """
        where_clause = " AND ".join([f"{col} = ?" for col in where_columns])
        query = f"SELECT * FROM companies WHERE {where_clause}"

        result = self.exec_query(query=query, params=where_values, fetchone=True, log_success=False)
        return result

    def retrieve_all_companies(self) -> list:
        """
        Busca todas as empresas.
        
        Returns:
            list: Lista de todas as empresas
        """
        query = "SELECT * FROM companies ORDER BY enterprise"
        result = self.exec_query(query=query, fetchone=False, log_success=False)
        return result

    def get_company_name(self, company_id: int) -> Optional[str]:
        """
        Obtém o nome de uma empresa pelo ID.
        
        Args:
            company_id: ID da empresa
            
        Returns:
            Optional[str]: Nome da empresa ou None se não encontrada
        """
        result = self.retrieve_company(['id'], (company_id,))
        return result[1] if result else None

    def delete_company(self, where_columns: List[str], where_values: Tuple) -> int:
        """
        Remove uma empresa.
        
        Args:
            where_columns: Lista de colunas para condição WHERE
            where_values: Valores para as condições WHERE
            
        Returns:
            int: Número de linhas afetadas
        """
        self.logger.print(f"Removendo empresa com condições: {where_columns}")

        where_clause = " AND ".join([f"{col} = ?" for col in where_columns])
        query = f"DELETE FROM companies WHERE {where_clause}"

        affected_rows = self.exec_query(query=query, params=where_values, log_success=False)
        self.logger.print(f"Empresa removida. Linhas afetadas: {affected_rows}")
        return affected_rows

    def _validate_cnpj_format(self, cnpj: str) -> bool:
        """
        Valida o formato do CNPJ.
        
        Args:
            cnpj: CNPJ a ser validado
            
        Returns:
            bool: True se o formato estiver correto
        """
        # Padrão: XX.XXX.XXX/XXXX-XX
        pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'
        return bool(re.match(pattern, cnpj.strip()))

    def format_cnpj(self, cnpj: str) -> str:
        """
        Formata um CNPJ para o padrão XX.XXX.XXX/XXXX-XX.
        
        Args:
            cnpj: CNPJ sem formatação
            
        Returns:
            str: CNPJ formatado
        """
        # Remove caracteres não numéricos
        cnpj_clean = re.sub(r'[^\d]', '', cnpj)
        
        # Verifica se tem 14 dígitos
        if len(cnpj_clean) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos. Encontrados: {len(cnpj_clean)}")
        
        # Formata: XX.XXX.XXX/XXXX-XX
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}" 