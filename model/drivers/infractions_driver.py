from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
import pandas as pd
import sqlite3
from typing import List, Tuple, Optional
import hashlib
from global_vars import INFRACTION_DICT

class InfractionsDriver(GeneralDriver):
    def __init__(self, logger: CustomLogger, db_path: str):
        super().__init__(logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        """ Cria a tabela infractions no banco de dados, caso não exista. """
        self.logger.print("Executando criação da tabela de infrações")

        query = '''
        CREATE TABLE IF NOT EXISTS infractions (
        hash TEXT PRIMARY KEY,
        motorist_id INTEGER NOT NULL,
        truck_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        hora TEXT NOT NULL,
        duration TEXT,
        tipo_infracao INTEGER NOT NULL,
        desc_infracao TEXT NOT NULL,
        lido INTEGER NOT NULL DEFAULT 0,
        link_tratativa TEXT,
        FOREIGN KEY (motorist_id) REFERENCES motorists(id),
        FOREIGN KEY (truck_id) REFERENCES trucks(id)
            );
        '''
        self.exec_query(query, log_success=False)
        self.logger.print("Tabela de infrações criada com sucesso.")

    def _build_where_clause(self, where_columns: List[str], where_values: Tuple[str]) -> str:
        """ Gera a cláusula WHERE com base nas colunas e valores fornecidos. """
        if len(where_columns) != len(where_values):
            raise ValueError("O número de colunas e valores deve ser igual.")
        return " AND ".join([f"{col}=?" for col in where_columns])

    def create_infraction(self, motorist_id: str, truck_id: int, data: str, hora: str, duration: str,
                          tipo_infracao: int) -> int:
        """
        Cria e insere um novo registro de infração no banco de dados.

        Gera um hash único com base no motorista, data, hora e tipo de infração para evitar duplicidades.
        Em seguida, insere os dados na tabela `infractions`, incluindo a descrição correspondente ao tipo de infração.

        Parâmetros:
            motorist_id (str): Identificador único do motorista.
            truck_id (int): Identificador do caminhão associado à infração.
            data (str): Data da infração (formato esperado: 'YYYY-MM-DD').
            hora (str): Hora da infração (formato esperado: 'HH:MM').
            duration (str): Duração da infração (formato livre, ex: '00:45').
            tipo_infracao (int): Código numérico representando o tipo de infração.

        Retorno:
            int: Número de linhas afetadas pela inserção (deve ser 1 em caso de sucesso).

        Efeitos colaterais:
            - Registra mensagens de log detalhadas sobre a operação realizada.
        """

        # Gerando um hash único para cada infração
        hash_value = hashlib.sha256(f"{motorist_id}{data}{hora}{tipo_infracao}".encode('utf-8')).hexdigest()

        self.logger.print(
            f"Adicionando infração: motorista={motorist_id}, data={data}, tipo_infracao={tipo_infracao}, hash={hash_value}")

        query = """
            INSERT OR REPLACE INTO infractions (hash, motorist_id, truck_id, data, hora, duration, tipo_infracao, desc_infracao, lido)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        desc_infracao = INFRACTION_DICT.get(tipo_infracao)
        params = (hash_value, motorist_id, truck_id, data, hora, duration, tipo_infracao, desc_infracao, 0)

        row_count = self.exec_query(query=query, params=params)
        self.logger.print(f"Linhas afetadas: {row_count}")
        return row_count

    def delete_infraction(self, where_columns: List[str], where_values: Tuple[str]) -> int:
        """
        Deleta um registro de infração no banco de dados com base nas condições fornecidas.

        :param where_columns: Lista de colunas usadas para filtrar a exclusão.
        :param where_values: Valores correspondentes às colunas de filtro.
        :return: Número de linhas afetadas.
        """
        where_clause = self._build_where_clause(where_columns, where_values)
        query = f"DELETE FROM infractions WHERE {where_clause}"

        row_count = self.exec_query(query=query, params=where_values)
        self.logger.print(f"{row_count} linhas afetadas ao excluir a infração com os dados {where_values}.")
        return row_count

    def update_infraction(self, set_columns: List[str], set_values: Tuple[str], where_columns: List[str],
                          where_values: Tuple[str]) -> int:
        """
        Atualiza informações de uma infração no banco de dados.

        :param set_columns: Lista de colunas a serem atualizadas.
        :param set_values: Valores correspondentes às colunas a serem atualizadas.
        :param where_columns: Lista de colunas usadas para encontrar a infração.
        :param where_values: Valores correspondentes às colunas de busca.
        :return: Número de linhas afetadas.
        """
        if len(set_columns) != len(set_values):
            raise ValueError("O número de colunas e valores deve ser igual")

        where_clause = self._build_where_clause(where_columns, where_values)
        set_clause = ", ".join([f"{col}=?" for col in set_columns])

        query = f"UPDATE infractions SET {set_clause} WHERE {where_clause}"

        row_count = self.exec_query(query=query, params=set_values + where_values)
        return row_count

    def retrieve_infraction(self, where_columns: List[str], where_values: Tuple[str]) -> Optional[
        Tuple[str, str, str, str, str]]:
        """
        Consulta uma infração no banco de dados. Se existir, retorna os dados completos da infração.

        :param where_columns: Lista de colunas para filtrar a busca.
        :param where_values: Valores correspondentes às colunas de filtro.
        :return: Dados da infração ou None caso não exista.
        """
        where_clause = self._build_where_clause(where_columns, where_values)
        query = f"SELECT hash, motorist_id, truck_id, data, hora, duration, tipo_infracao, desc_infracao, lido, link_tratativa FROM " \
                f"infractions WHERE {where_clause}"

        infraction_data = self.exec_query(query=query, params=where_values, fetchone=True, log_success=False)
        return infraction_data

    def retrieve_infractions(self, where_columns: List[str], where_values: Tuple[str]) -> Optional[
        Tuple[str, str, str, str, str]]:
        """
        Consulta uma infração no banco de dados. Se existir, retorna os dados completos da infração.

        :param where_columns: Lista de colunas para filtrar a busca.
        :param where_values: Valores correspondentes às colunas de filtro.
        :return: Dados da infração ou None caso não exista.
        """
        where_clause = self._build_where_clause(where_columns, where_values)
        query = f"SELECT hash, motorist_id, truck_id, data, hora, duration, tipo_infracao, desc_infracao, lido, link_tratativa FROM " \
                f"infractions WHERE {where_clause}"

        infraction_data = self.exec_query(query=query, params=where_values, fetchone=False, log_success=False)
        return infraction_data

    def retrieve_all_infractions(self) -> List[Tuple[str, str, str, str, str]]:
        """
        Retorna uma lista contendo todos os dados de todas as infrações.

        :return: Uma lista contendo todos os dados de todas as infrações.
        """
        self.logger.print("Consultando todas as infrações da tabela.")

        query = "SELECT hash, motorist_id, truck_id, data, hora, duration, tipo_infracao, desc_infracao, lido, link_tratativa FROM infractions " \
                "ORDER BY strftime('%Y-%m-%d', substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2)) DESC " \
                "LIMIT 100"
        infractions = self.exec_query(query=query, fetchone=False, log_success=False)

        return infractions

    def mark_as_read(self, infraction_hash: str) -> int:
        """
        Marca uma infração como lida.

        :param infraction_hash: O hash da infração a ser marcada como lida.
        :return: Número de linhas afetadas.
        """
        query = "UPDATE infractions SET lido = 1 WHERE hash = ?"
        row_count = self.exec_query(query=query, params=(infraction_hash,))
        return row_count

    def update_link_justification(self, infraction_hash: str, link: str) -> int:
        """
        Atualiza ou adiciona o link da justification para uma infração.

        :param infraction_hash: O hash da infração.
        :param link: O link do documento no Google Drive.
        :return: Número de linhas afetadas.
        """
        query = "UPDATE infractions SET link_tratativa = ? WHERE hash = ?"
        row_count = self.exec_query(query=query, params=(link, infraction_hash))
        return row_count

    def get_link_justification(self, infraction_hash: str) -> Optional[str]:
        """
        Retorna o link da justification de uma infração específica.

        :param infraction_hash: O hash da infração.
        :return: O link da justification ou None se não existir.
        """
        query = "SELECT link_tratativa FROM infractions WHERE hash = ?"
        result = self.exec_query(query=query, params=(infraction_hash,), fetchone=True)
        return result[0] if result else None