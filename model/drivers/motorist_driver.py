from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import List, Tuple, Optional
import re


class MotoristDriver(GeneralDriver):

    def __init__(self, logger: CustomLogger, db_path: str):
        GeneralDriver.__init__(self, logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        self.logger.print("Executando create table")

        query = """
                    CREATE TABLE IF NOT EXISTS motorists (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        data_admissao TEXT,
                        cpf TEXT,
                        cnh TEXT,
                        rg TEXT,
                        codigo_sap TEXT,
                        operacao TEXT,
                        ctps TEXT,
                        serie TEXT,
                        data_nascimento TEXT,
                        primeira_cnh TEXT,
                        data_expedicao TEXT,
                        vencimento_cnh TEXT,
                        done_mopp TEXT,
                        vencimento_mopp TEXT,
                        done_toxicologico_clt TEXT,
                        vencimento_toxicologico_clt TEXT,
                        done_aso_semestral TEXT,
                        vencimento_aso_semestral TEXT,
                        done_aso_periodico TEXT,
                        vencimento_aso_periodico TEXT,
                        done_buonny TEXT,
                        vencimento_buonny TEXT,
                        telefone TEXT,
                        endereco TEXT,
                        filiacao TEXT,
                        estado_civil TEXT,
                        filhos TEXT,
                        cargo TEXT,
                        empresa TEXT,
                        status TEXT,
                        conf_jornada TEXT,
                        conf_fecham TEXT,
                        done_toxicologico_cnh TEXT,
                        vencimento_toxicologico_cnh TEXT,
                        email TEXT
                    )
        """
        self.exec_query(query, log_success=False)
        self.logger.print("Create table executado com sucesso.")

    def check_duplicate_motorist(self, cpf: str, nome: str) -> bool:
        """
        Verifica se já existe um motorista com o mesmo CPF ou nome.
        
        Args:
            cpf: CPF do motorista
            nome: Nome do motorista
            
        Returns:
            bool: True se já existe, False caso contrário
        """
        self.logger.print(f"Verificando duplicidade para CPF: {cpf}, Nome: {nome}")
        
        # Verificar por CPF (mantendo formatação original)
        if cpf:
            query_cpf = "SELECT COUNT(*) FROM motorists WHERE cpf = ?"
            result_cpf = self.exec_query(query=query_cpf, params=(cpf,), fetchone=True, log_success=False)
            self.logger.print(f"Resultado verificação CPF: {result_cpf}")
            if result_cpf and result_cpf[0] > 0:
                self.logger.print("CPF duplicado encontrado!")
                return True
        
        # Verificar por nome (ignorando maiúsculas/minúsculas)
        if nome:
            query_nome = "SELECT COUNT(*) FROM motorists WHERE UPPER(nome) = UPPER(?)"
            result_nome = self.exec_query(query=query_nome, params=(nome,), fetchone=True, log_success=False)
            self.logger.print(f"Resultado verificação nome: {result_nome}")
            if result_nome and result_nome[0] > 0:
                self.logger.print("Nome duplicado encontrado!")
                return True
        
        self.logger.print("Nenhuma duplicidade encontrada")
        return False



    def get_next_id(self) -> int:
        """
        Obtém o próximo ID disponível para um novo motorista.
        
        Returns:
            int: Próximo ID disponível
        """
        query = "SELECT COALESCE(MAX(id), 0) + 1 FROM motorists"
        result = self.exec_query(query=query, fetchone=True, log_success=False)
        return result[0] if result else 1

    def create_motorist(self, nome: str, data_admissao: Optional[str] = None,
                        cpf: Optional[str] = None, cnh: Optional[str] = None, 
                        rg: Optional[str] = None, codigo_sap: Optional[str] = None,
                        operacao: Optional[str] = None, ctps: Optional[str] = None,
                        serie: Optional[str] = None, data_nascimento: Optional[str] = None,
                        primeira_cnh: Optional[str] = None, data_expedicao: Optional[str] = None,
                        vencimento_cnh: Optional[str] = None, done_mopp: Optional[str] = None,
                                                 vencimento_mopp: Optional[str] = None, done_toxicologico_clt: Optional[str] = None,
                         vencimento_toxicologico_clt: Optional[str] = None, done_aso_semestral: Optional[str] = None,
                        vencimento_aso_semestral: Optional[str] = None, done_aso_periodico: Optional[str] = None,
                        vencimento_aso_periodico: Optional[str] = None, done_buonny: Optional[str] = None,
                        vencimento_buonny: Optional[str] = None, telefone: Optional[str] = None,
                        endereco: Optional[str] = None, filiacao: Optional[str] = None, 
                        estado_civil: Optional[str] = None, filhos: Optional[str] = None,
                        cargo: Optional[str] = None, empresa: Optional[str] = None, 
                        status: Optional[str] = None, conf_jornada: Optional[str] = None,
                        conf_fecham: Optional[str] = None, done_toxicologico_cnh: Optional[str] = None,
                        vencimento_toxicologico_cnh: Optional[str] = None, email: Optional[str] = None):

        self.logger.print(f"Criando motorista com nome: {nome}")

        # Verificar duplicidade
        self.logger.print(f"Verificando duplicidade antes de criar motorista")
        is_duplicate = self.check_duplicate_motorist(cpf, nome)
        self.logger.print(f"Resultado da verificação de duplicidade: {is_duplicate}")
        
        if is_duplicate:
            self.logger.print("Duplicidade detectada! Lançando erro...")
            raise ValueError("Já existe um motorista cadastrado com este CPF ou nome.")

        # Obter próximo ID
        next_id = self.get_next_id()
        
        # Converter nome para maiúsculas
        nome_upper = nome.upper() if nome else None
        
        # Processar campos de checkbox
        conf_jornada_value = "Ativo" if conf_jornada == "1" else "Inativo"
        conf_fecham_value = "Ativo" if conf_fecham == "1" else "Inativo"
        
        # Definir status padrão como "Ativo" (não vem do frontend)
        status_value = "Ativo"

        query = """INSERT INTO motorists (
                        id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                        data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, 
                        vencimento_mopp, done_aso_semestral, vencimento_aso_semestral, done_aso_periodico, 
                        vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, endereco, filiacao, 
                        estado_civil, filhos, cargo, empresa, status, conf_jornada, conf_fecham, done_toxicologico_cnh,
                        vencimento_toxicologico_cnh, email, done_toxicologico_clt, vencimento_toxicologico_clt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        params = (next_id, nome_upper, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie,
                  data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp,
                  vencimento_mopp, done_aso_semestral, vencimento_aso_semestral, done_aso_periodico,
                  vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, endereco, filiacao,
                  estado_civil, filhos, cargo, empresa, status_value, conf_jornada_value, conf_fecham_value, done_toxicologico_cnh,
                  vencimento_toxicologico_cnh, email, done_toxicologico_clt, vencimento_toxicologico_clt)

        motorist_id = self.exec_query(query=query, params=params, log_success=False)
        self.logger.print(f"Motorista criado com sucesso. ID: {motorist_id}")

        return motorist_id

    def create_motorist_with_id(self, id: int, nome: str, data_admissao: Optional[str] = None,
                        cpf: Optional[str] = None, cnh: Optional[str] = None, 
                        rg: Optional[str] = None, codigo_sap: Optional[str] = None,
                        operacao: Optional[str] = None, ctps: Optional[str] = None,
                        serie: Optional[str] = None, data_nascimento: Optional[str] = None,
                        primeira_cnh: Optional[str] = None, data_expedicao: Optional[str] = None,
                        vencimento_cnh: Optional[str] = None, done_mopp: Optional[str] = None,
                                                 vencimento_mopp: Optional[str] = None, done_toxicologico_clt: Optional[str] = None,
                         vencimento_toxicologico_clt: Optional[str] = None, done_aso_semestral: Optional[str] = None,
                        vencimento_aso_semestral: Optional[str] = None, done_aso_periodico: Optional[str] = None,
                        vencimento_aso_periodico: Optional[str] = None, done_buonny: Optional[str] = None,
                        vencimento_buonny: Optional[str] = None, telefone: Optional[str] = None,
                        endereco: Optional[str] = None, filiacao: Optional[str] = None, 
                        estado_civil: Optional[str] = None, filhos: Optional[str] = None,
                        cargo: Optional[str] = None, empresa: Optional[str] = None, 
                        status: Optional[str] = None, conf_jornada: Optional[str] = None,
                        conf_fecham: Optional[str] = None, done_toxicologico_cnh: Optional[str] = None,
                        vencimento_toxicologico_cnh: Optional[str] = None, email: Optional[str] = None):

        self.logger.print(f"Criando motorista com ID customizado: {id}, nome: {nome}")

        query = """INSERT INTO motorists (
                        id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                        data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, 
                        vencimento_mopp, done_aso_semestral, vencimento_aso_semestral, done_aso_periodico, 
                        vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, endereco, filiacao, 
                        estado_civil, filhos, cargo, empresa, status, conf_jornada, conf_fecham, done_toxicologico_cnh,
                        vencimento_toxicologico_cnh, email, done_toxicologico_clt, vencimento_toxicologico_clt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        params = (id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie,
                  data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp,
                  vencimento_mopp, done_aso_semestral, vencimento_aso_semestral, done_aso_periodico,
                  vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, endereco, filiacao,
                  estado_civil, filhos, cargo, empresa, status, conf_jornada, conf_fecham, done_toxicologico_cnh,
                  vencimento_toxicologico_cnh, email, done_toxicologico_clt, vencimento_toxicologico_clt)

        motorist_id = self.exec_query(query=query, params=params, log_success=False)
        self.logger.print(f"Motorista criado com sucesso. ID: {motorist_id}")

        return motorist_id

    def update_motorist(self, set_columns: list, set_values: tuple, where_columns: list, where_values: tuple) -> int:
        self.logger.print(f"Atualizando motorista com dados {set_values} nas colunas {set_columns}.")

        if not set_columns or not set_values or len(set_columns) != len(set_values):
            raise ValueError(
                "Os parâmetros 'set_columns' e 'set_values' devem ter o mesmo tamanho e não podem ser vazios.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        set_clause = ", ".join([f"{col}=?" for col in set_columns])
        where_clause = " AND ".join([f"{col}=?" for col in where_columns])

        query = f"UPDATE motorists SET {set_clause} WHERE {where_clause}"

        all_params = set_values + where_values
        
        try:
            row_count = self.exec_query(query=query, params=all_params, log_success=False)
            
            # Garantir que row_count seja um inteiro
            if row_count is None:
                row_count = 0
            elif not isinstance(row_count, int):
                row_count = 0
                
            self.logger.print(f"Motorista atualizado com sucesso. Linhas afetadas: {row_count}")
            return row_count
            
        except Exception as e:
            self.logger.register_log(f"Erro ao atualizar motorista: {str(e)}")
            return 0

    def retrieve_motorist(self, where_columns: List[str], where_values: Tuple) -> Optional[Tuple]:
        self.logger.print(f"Consultando no BD por motorista com dado(s) {where_values} na(s) coluna(s) {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        conditions = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"""SELECT id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, vencimento_mopp, 
                done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral, vencimento_aso_semestral, 
                done_aso_periodico, vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, 
                endereco, filiacao, estado_civil, filhos, cargo, empresa, status, conf_jornada, conf_fecham,
                done_toxicologico_cnh, vencimento_toxicologico_cnh, email 
                FROM motorists WHERE {conditions}"""

        motorist = self.exec_query(query=query, params=where_values, fetchone=True, log_success=False)

        return motorist

    def retrieve_all_motorists(self) -> list:
        self.logger.print("Consultando todos os motoristas da tabela.")

        query = f"""SELECT id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, vencimento_mopp, 
                done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral, vencimento_aso_semestral, 
                done_aso_periodico, vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, 
                endereco, filiacao, estado_civil, filhos, cargo, empresa, status, conf_jornada, conf_fecham,
                done_toxicologico_cnh, vencimento_toxicologico_cnh, email FROM motorists"""

        motorists = self.exec_query(query=query, fetchone=False, log_success=False)

        return motorists

    def retrieve_active_motorists_for_journey(self) -> list:
        """Retorna apenas motoristas ativos para o módulo de jornada"""
        self.logger.print("Consultando motoristas ativos para jornada.")

        query = f"""SELECT id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, vencimento_mopp, 
                done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral, vencimento_aso_semestral, 
                done_aso_periodico, vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, 
                endereco, filiacao, estado_civil, filhos, cargo, empresa, status, conf_jornada, conf_fecham,
                done_toxicologico_cnh, vencimento_toxicologico_cnh, email 
                FROM motorists 
                WHERE status = 'Ativo' AND conf_jornada = 'Ativo'"""

        motorists = self.exec_query(query=query, fetchone=False, log_success=False)

        return motorists

    def retrieve_active_motorists_for_closure(self) -> list:
        """Retorna apenas motoristas ativos para o módulo de fechamento"""
        self.logger.print("Consultando motoristas ativos para fechamento.")

        query = f"""SELECT id, nome, data_admissao, cpf, cnh, rg, codigo_sap, operacao, ctps, serie, 
                data_nascimento, primeira_cnh, data_expedicao, vencimento_cnh, done_mopp, vencimento_mopp, 
                done_toxicologico_clt, vencimento_toxicologico_clt, done_aso_semestral, vencimento_aso_semestral, 
                done_aso_periodico, vencimento_aso_periodico, done_buonny, vencimento_buonny, telefone, 
                endereco, filiacao, estado_civil, filhos, cargo, empresa, status, conf_jornada, conf_fecham,
                done_toxicologico_cnh, vencimento_toxicologico_cnh, email 
                FROM motorists 
                WHERE status = 'Ativo' AND conf_fecham = 'Ativo'"""

        motorists = self.exec_query(query=query, fetchone=False, log_success=False)

        return motorists

    def get_motorist_name(self, motorist_id):
        """
        Retorna o nome do motorista baseado no ID
        """
        motorist = self.retrieve_motorist(["id"], (motorist_id,))
        if motorist:
            return motorist[1]  # nome está na posição 1
        return None

    def delete_motorist(self, where_columns: List[str], where_values: Tuple) -> int:
        self.logger.print(f"Deletando motorista com dados {where_values} nas colunas {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        where_clause = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"DELETE FROM motorists WHERE {where_clause}"

        row_count = self.exec_query(query=query, params=where_values, log_success=False)

        self.logger.print(f"Motorista deletado com sucesso. Linhas afetadas: {row_count}")

        return row_count
