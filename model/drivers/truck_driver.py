from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import Optional, Tuple
import re


class TruckDriver(GeneralDriver):

    def __init__(self, logger: CustomLogger, db_path: str):
        GeneralDriver.__init__(self, logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        self.logger.print("Executando create table")

        query = '''
                    CREATE TABLE IF NOT EXISTS trucks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        placa TEXT NOT NULL UNIQUE,
                        identificacao TEXT,
                        ano INTEGER,
                        modelo TEXT,
                        vencimento_aet_dnit TEXT,
                        vencimento_aet_mg TEXT,
                        vencimento_aet_sp TEXT,
                        vencimento_aet_go TEXT,
                        vencimento_civ_cipp TEXT,
                        vencimento_cronotografo TEXT,
                        exercicio_crlv INTEGER,
                        peso_tara REAL,
                        link_documentacao TEXT,
                        status TEXT
                    )
        '''
        self.exec_query(query, log_success=False)
        self.logger.print("Create table executado com sucesso.")

    import re

    def create_truck(self, placa: Optional[str] = None, identificacao: Optional[str] = None,
                     ano: Optional[int] = None, modelo: Optional[str] = None,
                     vencimento_aet_dnit: Optional[str] = None, vencimento_aet_mg: Optional[str] = None,
                     vencimento_aet_sp: Optional[str] = None, vencimento_aet_go: Optional[str] = None,
                     vencimento_civ_cipp: Optional[str] = None, vencimento_cronotografo: Optional[str] = None,
                     exercicio_crlv: Optional[int] = None, peso_tara: Optional[float] = None,
                     link_documentacao: Optional[str] = None, status: Optional[str] = None):

        self.logger.print(f"Adicionando caminhão: placa: {placa}.")

        def upper_if_contains_letter(value):
            return value.upper() if isinstance(value, str) and re.search(r'[a-zA-Z]', value) else value

        # Aplica upper() onde necessário
        placa = upper_if_contains_letter(placa)
        identificacao = upper_if_contains_letter(identificacao)
        modelo = upper_if_contains_letter(modelo)
        link_documentacao = upper_if_contains_letter(link_documentacao)
        status = upper_if_contains_letter(status)

        query = """
                    INSERT INTO trucks (placa, identificacao, ano, modelo, vencimento_aet_dnit, vencimento_aet_mg,
                    vencimento_aet_sp, vencimento_aet_go, vencimento_civ_cipp, vencimento_cronotografo, exercicio_crlv,
                    peso_tara, link_documentacao, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

        params = (placa, identificacao, ano, modelo, vencimento_aet_dnit, vencimento_aet_mg, vencimento_aet_sp,
                  vencimento_aet_go, vencimento_civ_cipp, vencimento_cronotografo, exercicio_crlv, peso_tara,
                  link_documentacao, status)

        row_count = self.exec_query(query=query, params=params)

        self.logger.print(f"Linhas afetadas: {row_count}")

        return row_count

    def delete_truck(self, where_columns: list, where_values: tuple) -> int:
        self.logger.register_log(f"Deletando caminhão da tabela com dado(s) '{where_values}' "
                                 f"na(s) coluna(s) '{where_columns}'.")

        where_clause = " AND ".join([f"{col}=?" for col in where_columns])

        query = f"DELETE FROM trucks WHERE {where_clause}"

        delete_data = ", ".join([f"{where_columns[i]}: {where_values[i]}" for i in range(len(where_values))])

        row_count = self.exec_query(query=query, params=where_values)

        self.logger.print(f"{row_count} linhas afetadas ao excluir o caminhão com os dados {delete_data}.")

        return row_count

    def update_truck(self, set_columns: list, set_values: tuple, where_columns: list, where_values: tuple) -> int:
        if not set_columns or not set_values or len(set_columns) != len(set_values):
            raise ValueError(
                "Os parâmetros 'set_columns' e 'set_values' devem ter o mesmo tamanho e não podem ser vazios.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        def upper_if_contains_letter(value):
            return value.upper() if isinstance(value, str) and re.search(r'[a-zA-Z]', value) else value

        # Aplica upper() aos valores de set_values conforme necessário
        set_values = tuple(upper_if_contains_letter(val) for val in set_values)

        set_clause = ", ".join([f"{col}=?" for col in set_columns])
        where_clause = " AND ".join([f"{col}=?" for col in where_columns])

        query = f"UPDATE trucks SET {set_clause} WHERE {where_clause}"

        row_count = self.exec_query(query=query, params=set_values + where_values, fetchone=False, log_success=True)

        return row_count

    def retrieve_truck(self, where_columns, where_values) -> Optional[Tuple]:
        self.logger.print(f"Consultando no BD por caminhão com dado(s) {where_values} na(s) coluna(s) {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        conditions = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"SELECT id, placa, identificacao, ano, modelo, vencimento_aet_dnit, vencimento_aet_mg, \
                    vencimento_aet_sp, vencimento_aet_go, vencimento_civ_cipp, vencimento_cronotografo, exercicio_crlv, \
                    peso_tara, link_documentacao, status FROM trucks WHERE {conditions}"

        truck = self.exec_query(query=query, params=where_values, fetchone=True, log_success=False)

        return truck

    def get_plate_by_id(self, truck_id: int) -> str:
        """
        Busca a placa de um caminhão pelo ID.
        
        :param truck_id: ID do caminhão
        :return: Placa do caminhão ou string de erro
        """
        try:
            query = "SELECT placa FROM trucks WHERE id = ?"
            result = self.exec_query(query=query, params=(truck_id,), fetchone=True)
            if result and len(result) > 0:
                return result[0]
            else:
                return f"ID {truck_id} (não encontrado)"
        except Exception as e:
            self.logger.register_log(f"Erro ao buscar placa do caminhão {truck_id}: {e}")
            return f"ID {truck_id} (erro)"

    def retrieve_all_trucks(self) -> list:
        self.logger.print("Consultando todos os caminhões da tabela.")

        query = "SELECT id, placa, identificacao, ano, modelo, vencimento_aet_dnit, " \
                "vencimento_aet_mg, vencimento_aet_sp, vencimento_aet_go, vencimento_civ_cipp, " \
                "vencimento_cronotografo, exercicio_crlv, peso_tara, link_documentacao, status FROM trucks"

        trucks = self.exec_query(query=query, fetchone=False, log_success=False)

        return trucks
