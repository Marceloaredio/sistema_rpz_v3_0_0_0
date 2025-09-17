from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
import pandas as pd
import sqlite3
from typing import List, Tuple, Optional

class UploadedDataDriver(GeneralDriver):
    def __init__(self, logger: CustomLogger, db_path: str, table: str = 'vehicle_data'):
        """
        Inicializa a classe UploadedDataDriver.

        :param logger: Instância de um logger customizado para registrar logs.
        :param db_path: Caminho para o banco de dados.
        :param table: Nome da tabela de destino (padrão: 'vehicle_data').
        """
        super().__init__(logger=logger, db_path=db_path)
        self.table = table
        self.columns = ["truck_id", "data_iso", "vel", "latitude", "longitude", "uf", "cidade", "rua", "ignicao"]
        self.create_table()

    def create_table(self):
        """
        Cria a tabela 'data' no banco de dados, se ela não existir.
        A tabela armazena as informações: placa, data, hora, vel, latitude,
        longitude, uf, cidade, rua e ignicao.
        """
        self.logger.print("Criando tabela 'data'.")

        query = f'''
            CREATE TABLE IF NOT EXISTS {self.table} (
                truck_id INTEGER NOT NULL,
                data_iso TEXT NOT NULL,
                vel REAL NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                uf TEXT,
                cidade TEXT,
                rua TEXT,
                ignicao INTEGER NOT NULL CHECK(ignicao in ('Ligada', 'Desligada')),
                PRIMARY KEY (truck_id, data_iso),
                FOREIGN KEY (truck_id) REFERENCES trucks(id) ON DELETE CASCADE
            )
        '''
        self.exec_query(query, log_success=False)
        self.logger.print("Tabela 'data' criada com sucesso.")

    def get_unique_truck_ids_and_plates(self):
        """
        Retorna os valores únicos de 'id' e 'placa' da tabela 'trucks', associando com a chave estrangeira 'truck_id'.

        :return: Uma lista de tuplas contendo o id e a placa únicos.
        """
        query = f'''
            SELECT DISTINCT t.id, t.placa
            FROM {self.table} AS td
            JOIN trucks AS t ON td.truck_id = t.id
        '''

        # Executando a consulta no banco de dados
        result = self.exec_query(query, fetchone=False)  # fetchone=False retorna todas as linhas

        return result  # Retorna uma lista de tuplas (id, placa) únicas

    def insert_record(self, truck_id: str, data: str, vel: float,
                      latitude: float, longitude: float, uf: str,
                      cidade: str, rua: str, ignicao: int) -> int:
        """
        Insere um novo registro de localização e estado do veículo na tabela 'data'.

        Parâmetros:
            truck_id (str): Identificador do caminhão.
            data (str): Data e hora do registro (formato: 'YYYY-MM-DD HH:MM:SS').
            vel (float): Velocidade do veículo no momento do registro.
            latitude (float): Latitude da localização registrada.
            longitude (float): Longitude da localização registrada.
            uf (str): Unidade federativa (estado) da localização.
            cidade (str): Nome da cidade correspondente à localização.
            rua (str): Nome da rua correspondente à localização.
            ignicao (int): Estado da ignição (1 para ligada, 0 para desligada).

        Retorno:
            int: Número de linhas afetadas pela inserção (geralmente 1).

        Efeitos colaterais:
            - Insere os dados na tabela `data`.
            - Pode registrar logs internos, se implementado.
        """
        self.logger.print(f"Inserindo registro na tabela '{self.table}'.")

        query = f'''
            INSERT OR IGNORE INTO {self.table} (truck_id, data_iso, vel, latitude, longitude, uf, cidade, rua, ignicao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (truck_id, data, vel, latitude, longitude, uf, cidade, rua, ignicao)

        row_count = self.exec_query(query=query, params=params)

        self.logger.print(f"{row_count} linha(s) afetada(s) ao inserir o registro.")
        return row_count

    def insert_from_dataframe(self, df: pd.DataFrame, force_table: str = None) -> int:
        """
        Insere múltiplos registros a partir de um DataFrame pandas usando uma única conexão.
        :param df: DataFrame contendo colunas compatíveis com a tabela.
        :type df: pandas.DataFrame
        :param force_table: Se fornecido, força o nome da tabela a ser usado na query.
        :return: Número de linhas inseridas com sucesso.
        :rtype: int
        """
        table_name = force_table if force_table else self.table
        self.logger.print(f"Iniciando inserção de dados a partir de DataFrame (conexão única) na tabela '{table_name}'.")

        if not all(col in df.columns for col in self.columns):
            raise ValueError(f"O DataFrame deve conter exatamente as colunas: {self.columns}")

        query = f'''
            INSERT OR IGNORE INTO {table_name} ({", ".join(self.columns)})
            VALUES ({", ".join(["?" for _ in self.columns])})
        '''

        data_tuples = [tuple(row[col] for col in self.columns) for _, row in df.iterrows()]

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(query, data_tuples)
                conn.commit()
        except Exception as e:
            self.logger.register_log(f"Erro ao inserir dados do DataFrame.", f'Erro: {e}')
            raise

        self.logger.print(f"Inserção concluída. Total de linhas inseridas: {len(data_tuples)} na tabela '{table_name}'.")
        return len(data_tuples)

    def delete_record(self, where_columns: list, where_values: tuple) -> int:
        """
        Deleta registros da tabela 'data' com base nas colunas e valores informados.

        :param where_columns: Lista de colunas para filtragem.
        :param where_values: Valores correspondentes às colunas.
        :return: Quantidade de linhas afetadas.
        """
        self.logger.register_log(
            f"Deletando registro(s) da tabela '{self.table}' com {where_values} nas colunas {where_columns}.")

        where_clause = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"DELETE FROM {self.table} WHERE {where_clause}"

        row_count = self.exec_query(query=query, params=where_values)
        self.logger.print(f"{row_count} linha(s) afetada(s) na exclusão do registro.")

        return row_count

    def update_record(self, set_columns: list, set_values: tuple,
                      where_columns: list, where_values: tuple) -> int:
        """
        Atualiza informações de um registro na tabela 'data'.

        :param set_columns: Lista de colunas a serem atualizadas.
        :param set_values: Valores correspondentes às colunas a serem atualizadas.
        :param where_columns: Lista de colunas utilizadas para encontrar o registro.
        :param where_values: Valores correspondentes aos filtros.
        :return: Quantidade de linhas afetadas.
        """
        if not set_columns or not set_values or len(set_columns) != len(set_values):
            raise ValueError(
                "Os parâmetros 'set_columns' e 'set_values' devem ter o mesmo tamanho e não podem ser vazios.")
        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        set_clause = ", ".join([f"{col}=?" for col in set_columns])
        where_clause = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"UPDATE {self.table} SET {set_clause} WHERE {where_clause}"

        row_count = self.exec_query(query=query, params=set_values + where_values,
                                    fetchone=False, log_success=True)
        return row_count

    def retrieve_record(self, where_columns: List[str], where_values: Tuple) -> Optional[Tuple]:
        """
        Consulta um registro na tabela 'data' com base nos filtros fornecidos.

        :param where_columns: Lista de colunas para filtragem.
        :param where_values: Valores correspondentes às colunas.
        :return: Registro encontrado (tuple) ou None se não existir.
        """
        self.logger.print(
            f"Consultando registro(s) na tabela '{self.table}' com dados {where_values} nas colunas {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        conditions = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"SELECT truck_id, data_iso, vel, latitude, longitude, uf, cidade, rua, ignicao " \
                f"FROM {self.table} WHERE {conditions}"

        record = self.exec_query(query=query, params=where_values, fetchone=True, log_success=False)
        return record

    def retrieve_by_datetime_range(
            self,
            start_datetime: str,
            end_datetime: str,
            where_columns: list = None,
            where_values: tuple = ()
    ) -> list:
        """
        Consulta registros na tabela com base em um intervalo de data e hora,
        e outras condições opcionais.

        :param start_datetime: Data e hora inicial no formato 'YYYY-MM-DD HH:MM:SS'.
        :param end_datetime: Data e hora final no formato 'YYYY-MM-DD HH:MM:SS'.
        :param where_columns: Lista opcional de colunas para filtragem adicional.
        :param where_values: Valores correspondentes às colunas adicionais.
        :return: Lista de registros encontrados ou lista vazia.
        """
        self.logger.print(
            f"Consultando registros entre '{start_datetime}' e '{end_datetime}' "
            f"com condições extras {where_columns}={where_values} na tabela '{self.table}'."
        )

        # Condição do intervalo de data
        conditions = ["data_iso BETWEEN ? AND ?"]
        params = [start_datetime, end_datetime]

        # Adiciona filtros adicionais, se existirem
        if where_columns and where_values:
            if len(where_columns) != len(where_values):
                raise ValueError("where_columns e where_values devem ter o mesmo tamanho.")
            conditions.extend([f"{col}=?" for col in where_columns])
            params.extend(where_values)

        condition_str = " AND ".join(conditions)

        query = (
            f"SELECT truck_id, data_iso, vel, latitude, longitude, uf, cidade, rua, ignicao "
            f"FROM {self.table} WHERE {condition_str}"
        )

        return self.exec_query(query=query, params=tuple(params), fetchone=False, log_success=False)

    def retrieve_all_records(self) -> list:
        """
        Retorna todos os registros da tabela 'data'.

        :return: Lista de registros (cada registro como tuple).
        """
        self.logger.print(f"Consultando todos os registros da tabela '{self.table}'.")

        query = f"SELECT truck_id, data_iso, vel, latitude, longitude, uf, cidade, rua, ignicao FROM {self.table}"
        records = self.exec_query(query=query, fetchone=False, log_success=False)

        return records

    def retrieve_all_records_by_condition(self, where_columns: list, where_values: tuple) -> list[tuple]:
        """
        Consulta todos os registros na tabela 'data' com base nos filtros fornecidos.

        :param where_columns: Lista de colunas para filtragem.
        :param where_values: Valores correspondentes às colunas.
        :return: Lista de registros encontrados (list[tuple]) ou lista vazia se nenhum for encontrado.
        """
        self.logger.print(
            f"Consultando todos os registros na tabela '{self.table}' com dados {where_values} nas colunas {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        conditions = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"SELECT truck_id, data_iso, vel, latitude, longitude, uf, cidade, rua, ignicao " \
                f"FROM {self.table} WHERE {conditions}"

        records = self.exec_query(query=query, params=where_values, fetchone=False, log_success=False)
        return records