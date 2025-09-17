from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import List, Tuple, Optional
import re
from datetime import datetime


class FormerMotoristDriver(GeneralDriver):

    def __init__(self, logger: CustomLogger, db_path: str):
        GeneralDriver.__init__(self, logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        self.logger.print("Executando create table para former_motorists")

        query = '''
                    CREATE TABLE IF NOT EXISTS former_motorists (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_id INTEGER,
                        nome TEXT NOT NULL,
                        
                        data_admissao TEXT,
                        data_demissao TEXT,
                        cpf TEXT,
                        cnh TEXT,
                        rg TEXT,
                        ctps TEXT,
                        serie TEXT,
                        data_nascimento TEXT,
                        primeira_cnh TEXT,
                        vencimento_cnh TEXT,
                        data_expedicao TEXT,
                        vencimento_mopp TEXT,
                        vencimento_toxicologico TEXT,
                        vencimento_aso_semestral TEXT,
                        vencimento_aso_periodico TEXT,
                        vencimento_buonny TEXT,
                        
                        
                        
                        
                        telefone TEXT,
                        endereco TEXT,
                        filiacao TEXT,
                        estado_civil TEXT,
                        filhos TEXT,
                        cargo TEXT,
                        empresa TEXT,
                        
                        status TEXT
                    )
        '''
        self.exec_query(query, log_success=False)
        self.logger.print("Create table executado com sucesso.")

    def add_former_motorist(self, original_id: int, nome: str, identificacao: Optional[str] = None,
                          data_admissao: Optional[str] = None, cpf: Optional[str] = None,
                          cnh: Optional[str] = None, rg: Optional[str] = None, ctps: Optional[str] = None,
                          serie: Optional[str] = None, data_nascimento: Optional[str] = None,
                          primeira_cnh: Optional[str] = None, vencimento_cnh: Optional[str] = None,
                          data_expedicao: Optional[str] = None, vencimento_mopp: Optional[str] = None,
                          vencimento_toxicologico: Optional[str] = None, vencimento_aso_semestral: Optional[str] = None,
                          vencimento_aso_periodico: Optional[str] = None, vencimento_buonny: Optional[str] = None,
                          nr_20: Optional[str] = None, nr_35: Optional[str] = None, nr_6: Optional[str] = None,
                          telefone: Optional[str] = None,
                          endereco: Optional[str] = None,
                          filiacao: Optional[str] = None, estado_civil: Optional[str] = None,
                          filhos: Optional[str] = None,
                          cargo: Optional[str] = None, empresa: Optional[str] = None,
                          status: Optional[str] = None):

        self.logger.print(f"Adicionando ex-motorista: nome: {nome}.")

        data_demissao = datetime.now().strftime("%d/%m/%Y")

        def upper_if_contains_letter(value):
            return value.upper() if isinstance(value, str) and re.search(r'[a-zA-Z]', value) else value

        # Aplica upper() onde necessário
        nome = upper_if_contains_letter(nome)
        
        cpf = upper_if_contains_letter(cpf)
        cnh = upper_if_contains_letter(cnh)
        rg = upper_if_contains_letter(rg)
        ctps = upper_if_contains_letter(ctps)
        serie = upper_if_contains_letter(serie)
        
        telefone = upper_if_contains_letter(telefone)
        endereco = upper_if_contains_letter(endereco)
        filiacao = upper_if_contains_letter(filiacao)
        estado_civil = upper_if_contains_letter(estado_civil)
        filhos = upper_if_contains_letter(filhos)
        cargo = upper_if_contains_letter(cargo)
        empresa = upper_if_contains_letter(empresa)
        
        status = upper_if_contains_letter(status)

        query = """
                    INSERT INTO former_motorists (original_id, nome, data_admissao, data_demissao, 
                    cpf, cnh, rg, ctps, serie, data_nascimento, primeira_cnh, vencimento_cnh, data_expedicao, 
                    vencimento_mopp, vencimento_toxicologico, vencimento_aso_semestral, vencimento_aso_periodico, 
                    vencimento_buonny, telefone, endereco, filiacao, estado_civil, 
                    filhos, cargo, empresa, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

        params = (original_id, nome, data_admissao, data_demissao, cpf, cnh, rg, ctps, serie, 
                 data_nascimento, primeira_cnh, vencimento_cnh, data_expedicao, vencimento_mopp, 
                 vencimento_toxicologico, vencimento_aso_semestral, vencimento_aso_periodico, vencimento_buonny, 
                 telefone, endereco, filiacao, estado_civil, filhos, cargo, 
                 empresa, status)

        row_count = self.exec_query(query=query, params=params)

        self.logger.print(f"Linhas afetadas: {row_count}")

        return row_count

    def retrieve_former_motorist(self, where_columns: List[str], where_values: Tuple) -> Optional[Tuple]:
        self.logger.print(f"Consultando no BD por ex-motorista com dado(s) {where_values} na(s) coluna(s) {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        conditions = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"""SELECT id, original_id, nome, data_admissao, data_demissao, cpf, cnh, rg, ctps, 
                serie, data_nascimento, primeira_cnh, vencimento_cnh, data_expedicao, vencimento_mopp, 
                vencimento_toxicologico, vencimento_aso_semestral, vencimento_aso_periodico, vencimento_buonny, 
                telefone, endereco, filiacao, estado_civil, filhos, cargo, 
                empresa, status FROM former_motorists WHERE {conditions}"""

        motorist = self.exec_query(query=query, params=where_values, fetchone=True, log_success=False)

        return motorist

    def retrieve_all_former_motorists(self) -> list:
        self.logger.print("Consultando todos os ex-motoristas da tabela.")

        query = """SELECT id, original_id, nome, data_admissao, data_demissao, cpf, cnh, rg, ctps, 
                serie, data_nascimento, primeira_cnh, vencimento_cnh, data_expedicao, vencimento_mopp, 
                vencimento_toxicologico, vencimento_aso_semestral, vencimento_aso_periodico, vencimento_buonny, 
                telefone, endereco, filiacao, estado_civil, filhos, cargo, 
                empresa, status FROM former_motorists"""

        motorists = self.exec_query(query=query, fetchone=False, log_success=False)

        return motorists 