from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import List, Tuple, Optional


class RemovedInfractionsDriver(GeneralDriver):
    def __init__(self, logger: CustomLogger, db_path: str):
        super().__init__(logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        """ Cria a tabela removed_infractions no banco de dados, caso não exista. """
        self.logger.print("Executando criação da tabela de infrações removidas")

        query = '''
        CREATE TABLE IF NOT EXISTS removed_infractions (
            hash TEXT PRIMARY KEY,
            motorist_id INTEGER NOT NULL,
            truck_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            duration TEXT,
            tipo_infracao INTEGER NOT NULL,
            desc_infracao TEXT NOT NULL,
            link_justification TEXT,
            data_remocao TEXT DEFAULT (strftime('%d-%m-%Y %H:%M:%S', 'now', 'localtime')),
            FOREIGN KEY (motorist_id) REFERENCES motorists(id),
            FOREIGN KEY (truck_id) REFERENCES trucks(id)
        );
        '''
        self.exec_query(query, log_success=False)
        self.logger.print("Tabela de infrações removidas criada com sucesso.")

    def add_removed_infraction(self, infraction_data: tuple) -> int:
        """
        Adiciona uma infração removida à tabela.
        
        :param infraction_data: Tupla com os dados da infração (hash, motorist_id, truck_id, data, hora, duration, tipo_infracao, desc_infracao, link_justification)
        :return: Número de linhas afetadas
        """
        query = """
            INSERT INTO removed_infractions (hash, motorist_id, truck_id, data, hora, duration, tipo_infracao, desc_infracao, link_justification)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.exec_query(query=query, params=infraction_data[:9])  # Pega os 9 primeiros campos

    def get_all_removed_infractions(self) -> list:
        """
        Retorna todas as infrações removidas com informações do motorista e veículo.
        
        :return: Lista de infrações removidas
        """
        query = """
            SELECT r.*, m.nome as motorista_nome, t.placa as placa
            FROM removed_infractions r
            JOIN motorists m ON r.motorist_id = m.id
            JOIN trucks t ON r.truck_id = t.id
            ORDER BY r.data_remocao DESC
        """
        return self.exec_query(query=query, fetchone=False)

    def get_removed_infraction(self, hash_value: str) -> Optional[tuple]:
        """
        Busca uma infração removida específica pelo hash.
        
        :param hash_value: Hash da infração
        :return: Dados da infração ou None se não encontrada
        """
        query = """
            SELECT r.*, m.nome as motorista_nome, t.placa as placa
            FROM removed_infractions r
            JOIN motorists m ON r.motorist_id = m.id
            JOIN trucks t ON r.truck_id = t.id
            WHERE r.hash = ?
        """
        return self.exec_query(query=query, params=(hash_value,), fetchone=True) 