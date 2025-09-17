from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import Optional, Tuple, Dict
import pandas as pd
import sqlite3
from datetime import datetime

class AnalyzedTrackData(GeneralDriver):

    def __init__(self, logger: CustomLogger, db_path: str):
        GeneralDriver.__init__(self, logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        self.logger.print("Executando create table")

        # Criando a consulta SQL com as novas colunas
        query = f'''
        CREATE TABLE IF NOT EXISTS perm_data (
            motorist_id INTEGER NOT NULL,  -- Chave estrangeira referenciando motoristas
            truck_id INTEGER NOT NULL,     -- Chave estrangeira referenciando trucks
            data TEXT NOT NULL,
            dia_da_semana TEXT NOT NULL,
            inicio_jornada TEXT,
            in_refeicao TEXT,
            fim_refeicao TEXT,
            fim_jornada TEXT,
            observacao TEXT,
            tempo_refeicao TEXT,
            intersticio TEXT,
            tempo_intervalo TEXT,
            tempo_carga_descarga TEXT,
            jornada_total TEXT,
            tempo_direcao TEXT,
            direcao_sem_pausa TEXT,
            in_descanso_1 TEXT,
            fim_descanso_1 TEXT,
            in_descanso_2 TEXT,
            fim_descanso_2 TEXT,
            in_descanso_3 TEXT,
            fim_descanso_3 TEXT,
            in_descanso_4 TEXT,
            fim_descanso_4 TEXT,
            in_descanso_5 TEXT,
            fim_descanso_5 TEXT,
            in_descanso_6 TEXT,
            fim_descanso_6 TEXT,
            in_descanso_7 TEXT,
            fim_descanso_7 TEXT,
            in_descanso_8 TEXT,
            fim_descanso_8 TEXT,
            in_car_desc_1 TEXT,
            fim_car_desc_1 TEXT,
            in_car_desc_2 TEXT,
            fim_car_desc_2 TEXT,
            in_car_desc_3 TEXT,
            fim_car_desc_3 TEXT,
            in_car_desc_4 TEXT,
            fim_car_desc_4 TEXT,
            in_car_desc_5 TEXT,
            fim_car_desc_5 TEXT,
            in_car_desc_6 TEXT,
            fim_car_desc_6 TEXT,
            in_car_desc_7 TEXT,
            fim_car_desc_7 TEXT,
            PRIMARY KEY (data, truck_id),
            FOREIGN KEY (motorist_id) REFERENCES motorists(id),
            FOREIGN KEY (truck_id) REFERENCES trucks(id)
        );
        '''
        self.exec_query(query, log_success=False)

        self.logger.print("Create table executado com sucesso.")


    def get_last_update_date_for_motorist(self, motorist_id: int) -> Optional[Tuple]:
        """
        Retorna a data do registro mais recente para um dado motorista na tabela perm_data.
        A data é retornada no formato DD-MM-YYYY como está armazenada no banco.
        """
        query = """
            SELECT data FROM perm_data
            WHERE motorist_id = ?
            ORDER BY substr(data, 7, 4) DESC, substr(data, 4, 2) DESC, substr(data, 1, 2) DESC
            LIMIT 1
        """
        # Ordena pelo ano, depois mês, depois dia para garantir a data mais recente
        return self.exec_query(query, params=(motorist_id,), fetchone=True)

    def get_first_record_date_for_motorist(self, motorist_id: int) -> Optional[Tuple]:
        """
        Retorna a data do registro mais antigo para um dado motorista na tabela perm_data.
        A data é retornada no formato DD-MM-YYYY como está armazenada no banco.
        """
        query = """
            SELECT data FROM perm_data
            WHERE motorist_id = ?
            ORDER BY substr(data, 7, 4), substr(data, 4, 2), substr(data, 1, 2)
            LIMIT 1
        """
        # Ordena pelo ano, depois mês, depois dia para garantir a data mais antiga
        return self.exec_query(query, params=(motorist_id,), fetchone=True)

    def check_record_exists_for_date(self, motorist_id: int, date_ddmmyyyy: str) -> bool:
        """
        Verifica se existe um registro para um dado motorista em uma data específica (DD-MM-YYYY)
        na tabela perm_data OU na tabela dayoff.
        """
        # Verifica na tabela perm_data
        query_perm_data = """
            SELECT COUNT(*) FROM perm_data
            WHERE motorist_id = ? AND data = ?
        """
        result_perm_data = self.exec_query(query_perm_data, params=(motorist_id, date_ddmmyyyy), fetchone=True)
        if result_perm_data is not None and result_perm_data[0] > 0:
            return True # Encontrado em perm_data

        # Se não encontrado em perm_data, verifica na tabela dayoff
        # Precisamos de uma instância do TrackDayOffDriver para isso
        # Assumindo que você tem acesso ao logger e db_path aqui, ou pode passar
        # eles para o construtor da AnalyzedTrackData se for mais apropriado.
        # Por simplicidade, vou criar uma instância temporária aqui.
        # Se você já tem uma instância de TrackDayOffDriver disponível em outro lugar
        # e puder passá-la para AnalyzedTrackData durante a inicialização, seria melhor.
        # Por enquanto, vamos fazer assim:
        # Crie o logger e db_path apropriados se não estiverem acessíveis diretamente
        # Ex: dayoff_logger = CustomLogger(source="DAYOFF_CHECK", debug=DEBUG)
        # Ex: dayoff_driver_instance = TrackDayOffDriver(logger=dayoff_logger, db_path=DB_PATH)
        # Mas para este exemplo, vou simular a query diretamente se não tiver TrackDayOffDriver instance

        # Alternativa 1: Se você tiver acesso a self.dayoff_driver (menos acoplado)
        # if hasattr(self, 'dayoff_driver') and self.dayoff_driver:
        #     return self.dayoff_driver.check_dayoff_exists_for_date(motorist_id, date_ddmmyyyy)
        # else:
        #     # Alternativa 2: Executa a query diretamente na tabela dayoff (mais acoplado)
        query_dayoff = """
            SELECT COUNT(*) FROM dayoff
            WHERE motorist_id = ? AND data = ?
        """
        result_dayoff = self.exec_query(query_dayoff, params=(motorist_id, date_ddmmyyyy), fetchone=True)
        if result_dayoff is not None and result_dayoff[0] > 0:
             return True # Encontrado em dayoff


        return False # Não encontrado em nenhuma das tabelas

        # Nota: Você precisará garantir que o TrackDayOffDriver está importado neste arquivo
        # e que a AnalyzedTrackData tem acesso a ele ou que você está usando a Alternativa 2.
        # A Alternativa 1 (passar a instância de TrackDayOffDriver para AnalyzedTrackData) é
        # geralmente uma prática melhor para gerenciamento de dependências.
        # Se optar pela Alternativa 2, a importação 'from model.drivers.dayoff_driver import TrackDayOffDriver'
        # deve estar no topo do arquivo data_driver.py.    

    def check_record_exists_for_truck_date(self, truck_id: int, date_ddmmyyyy: str) -> bool:
        """
        Verifica se existe um registro para uma dada placa em uma data específica (DD-MM-YYYY)
        na tabela perm_data.
        
        Parâmetros:
            truck_id (int): ID do caminhão/placa
            date_ddmmyyyy (str): Data no formato DD-MM-YYYY
            
        Retorno:
            bool: True se existe registro, False caso contrário
        """
        query = """
            SELECT COUNT(*) FROM perm_data
            WHERE truck_id = ? AND data = ?
        """
        result = self.exec_query(query, params=(truck_id, date_ddmmyyyy), fetchone=True)
        return result is not None and result[0] > 0

    def get_motorist_name(self, motorist_id):
        """
        Busca o nome do motorista pelo ID.
        
        :param motorist_id: ID do motorista
        :return: Nome do motorista ou string de erro
        """
        try:
            query = "SELECT nome FROM motorists WHERE id = ?"
            result = self.exec_query(query=query, params=(motorist_id,), fetchone=True)
            if result and len(result) > 0:
                return result[0]
            else:
                return f"ID {motorist_id} (não encontrado)"
        except Exception as e:
            self.logger.register_log(f"Erro ao buscar nome do motorista {motorist_id}: {e}")
            return f"ID {motorist_id} (erro)"

    def get_existing_motorist_info(self, truck_id, data):
        """
        Busca informações do motorista que já tem registro para uma data/placa específica.
        
        :param truck_id: ID do caminhão
        :param data: Data no formato DD-MM-YYYY
        :return: Dicionário com informações do motorista existente
        """
        try:
            query = """
                SELECT p.motorist_id, m.nome 
                FROM perm_data p 
                JOIN motorists m ON p.motorist_id = m.id 
                WHERE p.truck_id = ? AND p.data = ?
            """
            result = self.exec_query(query=query, params=(truck_id, data), fetchone=True)
            if result and len(result) >= 2:
                return {
                    'motorist_id': result[0],
                    'motorist_name': result[1]
                }
            else:
                return {
                    'motorist_id': None,
                    'motorist_name': 'Motorista desconhecido'
                }
        except Exception as e:
            self.logger.register_log(f"Erro ao buscar motorista existente para truck_id={truck_id}, data={data}: {e}")
            return {
                'motorist_id': None,
                'motorist_name': 'Erro ao buscar motorista'
            }

    def insert_data_from_json(self, data_json, motorist_id, truck_id, replace: bool=False):
        """Insere lista de linhas do frontend. Se replace=False não sobrescreve datas existentes e retorna conflitos; se True sobrescreve."""
        conflitos, ins, ign, sub = [], 0, 0, 0
        motorist_name = self.get_motorist_name(motorist_id)

        for linha in data_json:
            date_key = linha.get('Data')
            
            # Verifica TODOS os conflitos antes de decidir o que fazer
            conflicts_found = []
            
            # Verifica se o caminhão já tem jornada de outro motorista nesta data
            truck_conflict = self.exec_query(
                "SELECT motorist_id FROM perm_data WHERE data=? AND truck_id=? AND motorist_id!=?",
                params=(date_key, truck_id, motorist_id), fetchone=True
            )
            if truck_conflict:
                other_motorist_name = self.get_motorist_name(truck_conflict[0])
                conflicts_found.append({
                    'type': 'truck_conflict',
                    'data': truck_conflict,
                    'conflict_obj': {
                        'data': date_key,
                        'tipo': 'Caminhão ocupado',
                        'descricao': f"Caminhão já possui jornada registrada para o motorista {other_motorist_name} na data {date_key}"
                    }
                })
            
            # Verifica se o motorista já tem qualquer registro (jornada) nesta data
            motorist_journey_conflict = self.exec_query(
                "SELECT truck_id FROM perm_data WHERE data=? AND motorist_id=?",
                params=(date_key, motorist_id), fetchone=True
            )
            if motorist_journey_conflict:
                conflicts_found.append({
                    'type': 'motorist_journey_conflict',
                    'data': motorist_journey_conflict,
                    'conflict_obj': {
                        'data': date_key,
                        'tipo': 'Motorista já possui jornada',
                        'descricao': f"Motorista {motorist_name} já possui jornada registrada na data {date_key}"
                    }
                })
                
            # Verifica se o motorista já tem dayoff registrado nesta data
            motorist_dayoff_conflict = self.exec_query(
                "SELECT motivo FROM dayoff WHERE data=? AND motorist_id=?",
                params=(date_key, motorist_id), fetchone=True
            )
            if motorist_dayoff_conflict:
                motivo = motorist_dayoff_conflict[0]
                conflicts_found.append({
                    'type': 'motorist_dayoff_conflict',
                    'data': motorist_dayoff_conflict,
                    'conflict_obj': {
                        'data': date_key,
                        'tipo': 'Motorista já possui folga',
                        'descricao': f"Motorista {motorist_name} já possui folga ({motivo}) registrada na data {date_key}"
                    }
                })
            
            # Se há conflitos e não é para substituir, adiciona todos os conflitos e pula
            if conflicts_found and not replace:
                for conflict in conflicts_found:
                    conflitos.append(conflict['conflict_obj'])
                ign += 1
                continue
                
            # Se chegou até aqui e replace=True, remove TODOS os conflitos encontrados
            if replace and conflicts_found:
                for conflict in conflicts_found:
                    if conflict['type'] == 'truck_conflict':
                        # Remove jornada de outro motorista no mesmo caminhão e data
                        other_motorist_id = conflict['data'][0]
                        self.exec_query("DELETE FROM infractions WHERE motorist_id=? AND data=?",
                                      params=(other_motorist_id, date_key))
                        self.exec_query("DELETE FROM perm_data WHERE data=? AND truck_id=? AND motorist_id=?",
                                      params=(date_key, truck_id, other_motorist_id))
                        sub += 1
                    
                    elif conflict['type'] == 'motorist_journey_conflict':
                        # Remove jornada existente do mesmo motorista (qualquer caminhão)
                        self.exec_query("DELETE FROM infractions WHERE motorist_id=? AND data=?",
                                      params=(motorist_id, date_key))
                        self.exec_query("DELETE FROM perm_data WHERE data=? AND motorist_id=?",
                                      params=(date_key, motorist_id))
                        sub += 1
                    
                    elif conflict['type'] == 'motorist_dayoff_conflict':
                        # Remove dayoff existente do mesmo motorista
                        self.exec_query("DELETE FROM dayoff WHERE data=? AND motorist_id=?",
                                      params=(date_key, motorist_id))
                        sub += 1
            
            # build row
            desc = []
            for i in range(1, 9):
                desc.append(linha.get(f'Início Descanso {i}', '') or linha.get(f'In. Descanso {i}', ''))
                desc.append(linha.get(f'Fim Descanso {i}', ''))
            row = {
                'motorist_id': motorist_id,
                'truck_id': truck_id,
                'data': date_key,
                'dia_da_semana': linha.get('Dia') or linha.get('Dia da Semana'),
                'inicio_jornada': linha.get('Início Jornada'),
                'in_refeicao': linha.get('Início Refeição') or linha.get('In. Refeição'),
                'fim_refeicao': linha.get('Fim Refeição'),
                'fim_jornada': linha.get('Fim de Jornada'),
                'observacao': linha.get('Observação'),
                'tempo_refeicao': linha.get('Tempo Refeição'),
                'intersticio': linha.get('Interstício'),
                'tempo_intervalo': linha.get('Tempo Intervalo'),
                'tempo_carga_descarga': linha.get('Tempo Carga/Descarga'),
                'jornada_total': linha.get('Jornada Total'),
                'tempo_direcao': linha.get('Tempo Direção'),
                'direcao_sem_pausa': linha.get('Direção Sem Pausa'),
                'in_descanso_1': desc[0],'fim_descanso_1':desc[1],'in_descanso_2':desc[2],'fim_descanso_2':desc[3],
                'in_descanso_3': desc[4],'fim_descanso_3':desc[5],'in_descanso_4':desc[6],'fim_descanso_4':desc[7],
                'in_descanso_5': desc[8],'fim_descanso_5':desc[9],'in_descanso_6':desc[10],'fim_descanso_6':desc[11],
                'in_descanso_7': desc[12],'fim_descanso_7':desc[13],'in_descanso_8':desc[14],'fim_descanso_8':desc[15]
            }
            
            self.upsert_from_dict(row)
            ins += 1
        return {'tem_conflitos': bool(conflitos), 'conflitos': conflitos,
                'registros_inseridos': ins, 'registros_ignorados': ign,
                'registros_substituidos': sub}

    def replace_data_from_json(self, data_json, motorist_id, truck_id):
        """Sobrescreve registros existentes chamando insert_data_from_json com replace=True."""
        return self.insert_data_from_json(data_json, motorist_id, truck_id, replace=True)

    def check_conflicts_only(self, data_json, motorist_id, truck_id):
        """
        Verifica apenas conflitos sem inserir dados.
        Retorna o mesmo formato que insert_data_from_json mas sem inserir nada.
        """
        conflitos, ins, ign, sub = [], 0, 0, 0
        motorist_name = self.get_motorist_name(motorist_id)

        for linha in data_json:
            date_key = linha.get('Data')
            
            # Verifica TODOS os conflitos
            conflicts_found = []
            
            # Verifica se o caminhão já tem jornada de outro motorista nesta data
            truck_conflict = self.exec_query(
                "SELECT motorist_id FROM perm_data WHERE data=? AND truck_id=? AND motorist_id!=?",
                params=(date_key, truck_id, motorist_id), fetchone=True
            )
            if truck_conflict:
                other_motorist_name = self.get_motorist_name(truck_conflict[0])
                conflicts_found.append({
                    'type': 'truck_conflict',
                    'data': truck_conflict,
                    'conflict_obj': {
                        'data': date_key,
                        'tipo': 'Caminhão ocupado',
                        'descricao': f"Caminhão já possui jornada registrada para o motorista {other_motorist_name} na data {date_key}"
                    }
                })
            
            # Verifica se o motorista já tem qualquer registro (jornada) nesta data
            motorist_journey_conflict = self.exec_query(
                "SELECT truck_id FROM perm_data WHERE data=? AND motorist_id=?",
                params=(date_key, motorist_id), fetchone=True
            )
            if motorist_journey_conflict:
                conflicts_found.append({
                    'type': 'motorist_journey_conflict',
                    'data': motorist_journey_conflict,
                    'conflict_obj': {
                        'data': date_key,
                        'tipo': 'Motorista já possui jornada',
                        'descricao': f"Motorista {motorist_name} já possui jornada registrada na data {date_key}"
                    }
                })
                
            # Verifica se o motorista já tem dayoff registrado nesta data
            motorist_dayoff_conflict = self.exec_query(
                "SELECT motivo FROM dayoff WHERE data=? AND motorist_id=?",
                params=(date_key, motorist_id), fetchone=True
            )
            if motorist_dayoff_conflict:
                motivo = motorist_dayoff_conflict[0]
                conflicts_found.append({
                    'type': 'motorist_dayoff_conflict',
                    'data': motorist_dayoff_conflict,
                    'conflict_obj': {
                        'data': date_key,
                        'tipo': 'Motorista já possui folga',
                        'descricao': f"Motorista {motorist_name} já possui folga ({motivo}) registrada na data {date_key}"
                    }
                })
            
            # Se há conflitos, adiciona todos os conflitos
            if conflicts_found:
                for conflict in conflicts_found:
                    conflitos.append(conflict['conflict_obj'])
                ign += 1
            else:
                ins += 1
                
        return {'tem_conflitos': bool(conflitos), 'conflitos': conflitos,
                'registros_inseridos': ins, 'registros_ignorados': ign,
                'registros_substituidos': sub}

    def delete_perm_data(self, where_columns: list, where_values: tuple) -> int:
        """
        Deleta um registro na tabela perm_data com base nos parâmetros fornecidos.

        :param where_columns: Lista de colunas usadas para filtrar a exclusão.
        :type where_columns: list
        :param where_values: Valores correspondentes às colunas de filtro.
        :type where_values: tuple
        :return: Número de linhas afetadas.
        :rtype: int
        """
        self.logger.register_log(f"Deletando perm_data com dado(s) '{where_values}' na(s) coluna(s) '{where_columns}'.")

        where_clause = " AND ".join([f"{col}=?" for col in where_columns])

        query = f"DELETE FROM perm_data WHERE {where_clause}"

        delete_data = ", ".join([f"{where_columns[i]}: {where_values[i]}" for i in range(len(where_values))])

        row_count = self.exec_query(query=query, params=where_values)

        self.logger.print(f"{row_count} linhas afetadas ao excluir o perm_data com os dados {delete_data}.")

        return row_count

    def update_perm_data(self, set_columns: list, set_values: tuple, where_columns: list, where_values: tuple) -> int:
        """
        Atualiza informações de perm_data no banco de dados.
        Se a atualização for bem-sucedida, a operação será confirmada.

        :param set_columns: Lista de colunas a serem atualizadas.
        :type set_columns: list
        :param set_values: Valores correspondentes às colunas a serem atualizadas.
        :type set_values: tuple
        :param where_columns: Lista de colunas usadas para encontrar o perm_data.
        :type where_columns: list
        :param where_values: Valores correspondentes às colunas de busca.
        :type where_values: tuple
        :return: Número de linhas afetadas.
        :rtype: int
        """
        if not set_columns or not set_values or len(set_columns) != len(set_values):
            raise ValueError(
                "Os parâmetros 'set_columns' e 'set_values' devem ter o mesmo tamanho e não podem ser vazios.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        # Construção dinâmica das cláusulas SET e WHERE
        set_clause = ", ".join([f"{col}=?" for col in set_columns])
        where_clause = " AND ".join([f"{col}=?" for col in where_columns])

        query = f"UPDATE perm_data SET {set_clause} WHERE {where_clause}"

        row_count = self.exec_query(query=query, params=set_values + where_values, fetchone=False, log_success=True)

        return row_count

    def retrieve_perm_data(self, where_columns, where_values) -> Optional[tuple]:
        """
        Consulta um perm_data no banco de dados. Se existir, retorna os dados completos.
        Se não existir, retorna None.

        :param where_columns: Lista de colunas para filtrar a busca.
        :type where_columns: list
        :param where_values: Valores correspondentes às colunas em 'where_columns'.
        :type where_values: tuple
        :return: Dados encontrados ou None caso não exista.
        :rtype: tuple or None
        """
        self.logger.print(f"Consultando no BD por perm_data com dado(s) {where_values} na(s) coluna(s) {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        conditions = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"SELECT * FROM perm_data WHERE {conditions}"

        perm_data = self.exec_query(query=query, params=where_values, fetchone=True, log_success=False)

        return perm_data

    def retrieve_by_datetime_range(
            self,
            start_datetime: str = None,
            end_datetime: str = None,
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
            f"Consultando registros com condições: "
            f"start_datetime={start_datetime}, end_datetime={end_datetime}, "
            f"where_columns={where_columns}, where_values={where_values}."
        )

        # Validação: Ou start/end datetime ou where_columns/where_values devem ser fornecidos
        if not (start_datetime and end_datetime) and not (where_columns and where_values):
            raise ValueError("É necessário fornecer start_datetime e end_datetime ou where_columns e where_values.")

        conditions = []
        params = []

        # Se start_datetime e end_datetime forem fornecidos, pesquisar por data
        if start_datetime and end_datetime:
            conditions.append(
                "strftime('%Y-%m-%d', substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2)) BETWEEN ? AND ?")
            params.extend([start_datetime, end_datetime])

        # Se where_columns e where_values forem fornecidos, pesquisar pelas colunas
        if where_columns and where_values:
            if len(where_columns) != len(where_values):
                raise ValueError("where_columns e where_values devem ter o mesmo tamanho.")
            conditions.extend([f"{col}=?" for col in where_columns])
            params.extend(where_values)

        # Construir a string das condições
        condition_str = " AND ".join(conditions)

        query = (
            f"SELECT motorist_id, truck_id, data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, "
            f"observacao, tempo_refeicao, intersticio, tempo_intervalo, tempo_carga_descarga, jornada_total, "
            f"tempo_direcao, direcao_sem_pausa, in_descanso_1, fim_descanso_1, in_descanso_2, fim_descanso_2, "
            f"in_descanso_3, fim_descanso_3, in_descanso_4, fim_descanso_4, in_descanso_5, fim_descanso_5, "
            f"in_descanso_6, fim_descanso_6, in_descanso_7, fim_descanso_7, in_descanso_8, fim_descanso_8, "
            f"in_car_desc_1, fim_car_desc_1, in_car_desc_2, fim_car_desc_2, in_car_desc_3, fim_car_desc_3, "
            f"in_car_desc_4, fim_car_desc_4, in_car_desc_5, fim_car_desc_5, in_car_desc_6, fim_car_desc_6, "
            f"in_car_desc_7, fim_car_desc_7 "
            f"FROM perm_data WHERE {condition_str}"
        )

        # DEBUG: Query executada

        # Conectando ao banco de dados e executando a consulta
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))

        # Recuperando todos os resultados
        rows = cursor.fetchall()
        conn.close()

        return rows

    def retrieve_df_by_datetime_range(
            self,
            start_datetime: str = None,
            end_datetime: str = None,
            where_columns: list = None,
            where_values: tuple = ()
    ) -> pd.DataFrame:
        """
        Consulta registros na tabela com base em um intervalo de data e hora,
        e outras condições opcionais.

        :param start_datetime: Data e hora inicial no formato 'YYYY-MM-DD HH:MM:SS'.
        :param end_datetime: Data e hora final no formato 'YYYY-MM-DD HH:MM:SS'.
        :param where_columns: Lista opcional de colunas para filtragem adicional.
        :param where_values: Valores correspondentes às colunas adicionais.
        :return: DataFrame com os registros encontrados ou DataFrame vazio.
        """
        self.logger.print(
            f"Consultando registros com condições: "
            f"start_datetime={start_datetime}, end_datetime={end_datetime}, "
            f"where_columns={where_columns}, where_values={where_values}."
        )

        # Validação: Ou start/end datetime ou where_columns/where_values devem ser fornecidos
        if not (start_datetime and end_datetime) and not (where_columns and where_values):
            raise ValueError("É necessário fornecer start_datetime e end_datetime ou where_columns e where_values.")

        conditions = []
        params = []

        # Se start_datetime e end_datetime forem fornecidos, pesquisar por data
        if start_datetime and end_datetime:
            conditions.append(
                "strftime('%Y-%m-%d', substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2)) BETWEEN ? AND ?")
            params.extend([start_datetime, end_datetime])

        # Se where_columns e where_values forem fornecidos, pesquisar pelas colunas
        if where_columns and where_values:
            if len(where_columns) != len(where_values):
                raise ValueError("where_columns e where_values devem ter o mesmo tamanho.")
            conditions.extend([f"{col}=?" for col in where_columns])
            params.extend(where_values)

        # Construir a string das condições
        condition_str = " AND ".join(conditions)

        query = (
            f"SELECT motorist_id, truck_id, data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, "
            f"observacao, tempo_refeicao, intersticio, tempo_intervalo, tempo_carga_descarga, jornada_total, "
            f"tempo_direcao, direcao_sem_pausa, in_descanso_1, fim_descanso_1, in_descanso_2, fim_descanso_2, "
            f"in_descanso_3, fim_descanso_3, in_descanso_4, fim_descanso_4, in_descanso_5, fim_descanso_5, "
            f"in_descanso_6, fim_descanso_6, in_descanso_7, fim_descanso_7, in_descanso_8, fim_descanso_8, "
            f"in_car_desc_1, fim_car_desc_1, in_car_desc_2, fim_car_desc_2, in_car_desc_3, fim_car_desc_3, "
            f"in_car_desc_4, fim_car_desc_4, in_car_desc_5, fim_car_desc_5, in_car_desc_6, fim_car_desc_6, "
            f"in_car_desc_7, fim_car_desc_7 "
            f"FROM perm_data WHERE {condition_str}"
        )

        # DEBUG: Query executada

        # Conectando ao banco de dados e usando pandas para retornar o DataFrame
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=tuple(params))
        conn.close()

        time_columns = [
            'inicio_jornada', 'in_refeicao', 'fim_refeicao', 'fim_jornada',
            'in_descanso_1', 'fim_descanso_1', 'in_descanso_2', 'fim_descanso_2',
            'in_descanso_3', 'fim_descanso_3', 'in_descanso_4', 'fim_descanso_4',
            'in_descanso_5', 'fim_descanso_5', 'in_descanso_6', 'fim_descanso_6',
            'in_descanso_7', 'fim_descanso_7', 'in_descanso_8', 'fim_descanso_8',
            'in_car_desc_1', 'fim_car_desc_1', 'in_car_desc_2', 'fim_car_desc_2',
            'in_car_desc_3', 'fim_car_desc_3', 'in_car_desc_4', 'fim_car_desc_4',
            'in_car_desc_5', 'fim_car_desc_5', 'in_car_desc_6', 'fim_car_desc_6',
            'in_car_desc_7', 'fim_car_desc_7'
        ]

        # Convertendo todas as colunas de data/hora para datetime, caso exista.
        for col in time_columns:
            if col in df.columns:
                # Combinando as colunas 'data' e 'col' diretamente e convertendo para datetime
                df[col] = pd.to_datetime(df['data'].astype(str) + ' ' + df[col].astype(str), format='%d-%m-%Y %H:%M',
                                         errors='coerce')

        # Agora converte a coluna 'data' para datetime no formato correto
        df['data'] = pd.to_datetime(df['data'], format='%d-%m-%Y')

        return df

    def retrieve_last_n_records(
            self,
            n: int = 10,  # N é o número de registros que você quer retornar
            where_columns: list = None,
            where_values: tuple = ()
    ) -> pd.DataFrame:
        """
        Consulta os N últimos registros na tabela com base nas condições fornecidas,
        ordenados pela data no formato 'YYYY-MM-DD'.

        :param n: Número de registros a retornar.
        :param where_columns: Lista opcional de colunas para filtragem adicional.
        :param where_values: Valores correspondentes às colunas adicionais.
        :return: DataFrame com os registros encontrados ou DataFrame vazio.
        """
        self.logger.print(
            f"Consultando os {n} últimos registros com as condições: "
            f"where_columns={where_columns}, where_values={where_values}."
        )

        conditions = []
        params = []

        # Se where_columns e where_values forem fornecidos, pesquisar pelas colunas
        if where_columns and where_values:
            if len(where_columns) != len(where_values):
                raise ValueError("where_columns e where_values devem ter o mesmo tamanho.")
            conditions.extend([f"{col}=?" for col in where_columns])
            params.extend(where_values)

        # Construir a string das condições
        condition_str = " AND ".join(conditions)

        # Seleciona os registros com base nas condições fornecidas e limita a quantidade com ORDER BY
        query = (
            f"SELECT motorist_id, truck_id, data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, "
            f"observacao, tempo_refeicao, intersticio, tempo_intervalo, tempo_carga_descarga, jornada_total, "
            f"tempo_direcao, direcao_sem_pausa, in_descanso_1, fim_descanso_1, in_descanso_2, fim_descanso_2, "
            f"in_descanso_3, fim_descanso_3, in_descanso_4, fim_descanso_4, in_descanso_5, fim_descanso_5, "
            f"in_descanso_6, fim_descanso_6, in_descanso_7, fim_descanso_7, in_descanso_8, fim_descanso_8, "
            f"in_car_desc_1, fim_car_desc_1, in_car_desc_2, fim_car_desc_2, in_car_desc_3, fim_car_desc_3, "
            f"in_car_desc_4, fim_car_desc_4, in_car_desc_5, fim_car_desc_5, in_car_desc_6, fim_car_desc_6, "
            f"in_car_desc_7, fim_car_desc_7 "
            f"FROM perm_data WHERE {condition_str} "
            f"ORDER BY strftime('%Y-%m-%d', substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2)) DESC "
            f"LIMIT ?"
        )

        # Adicionando N ao parâmetro params para LIMIT
        params.append(n)

        self.logger.print(f"Executando query no perm_data: {query}")
        self.logger.print(f"Params: {params}")

        # Conectando ao banco de dados e usando pandas para retornar o DataFrame
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=tuple(params))
        conn.close()

        time_columns = [
            'inicio_jornada', 'in_refeicao', 'fim_refeicao', 'fim_jornada',
            'in_descanso_1', 'fim_descanso_1', 'in_descanso_2', 'fim_descanso_2',
            'in_descanso_3', 'fim_descanso_3', 'in_descanso_4', 'fim_descanso_4',
            'in_descanso_5', 'fim_descanso_5', 'in_descanso_6', 'fim_descanso_6',
            'in_descanso_7', 'fim_descanso_7', 'in_descanso_8', 'fim_descanso_8',
            'in_car_desc_1', 'fim_car_desc_1', 'in_car_desc_2', 'fim_car_desc_2',
            'in_car_desc_3', 'fim_car_desc_3', 'in_car_desc_4', 'fim_car_desc_4',
            'in_car_desc_5', 'fim_car_desc_5', 'in_car_desc_6', 'fim_car_desc_6',
            'in_car_desc_7', 'fim_car_desc_7'
        ]

        # Convertendo todas as colunas de data/hora para datetime, caso exista.
        for col in time_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df['data'].astype(str) + ' ' + df[col].astype(str), format='%d-%m-%Y %H:%M',
                                         errors='coerce')

        # Agora converte a coluna 'data' para datetime no formato correto
        df['data'] = pd.to_datetime(df['data'], format='%d-%m-%Y')

        return df

    def retrieve_n_records_before_date(
            self,
            n: int = 10,  # N é o número de registros que você quer retornar
            target_date: str = None,  # Data específica no formato 'DD-MM-YYYY'
            where_columns: list = None,
            where_values: tuple = (),
            output_format = 'df'
    ) -> pd.DataFrame | list | None:
        """
        Consulta os N registros mais antigos antes de uma data específica, ordenados pela data no formato 'YYYY-MM-DD'.

        :param n: Número de registros a retornar.
        :param target_date: Data até onde os registros devem ser retornados.
        :param where_columns: Lista opcional de colunas para filtragem adicional.
        :param where_values: Valores correspondentes às colunas adicionais.
        :return: DataFrame com os registros encontrados ou DataFrame vazio.
        """
        self.logger.print(
            f"Consultando os {n} registros antes da data {target_date} com as condições: "
            f"where_columns={where_columns}, where_values={where_values}."
        )

        conditions = []
        params = []

        # Se where_columns e where_values forem fornecidos, pesquisar pelas colunas
        if where_columns and where_values:
            if len(where_columns) != len(where_values):
                raise ValueError("where_columns e where_values devem ter o mesmo tamanho.")
            conditions.extend([f"{col}=?" for col in where_columns])
            params.extend(where_values)

        # Adicionar condição para pegar registros antes da data fornecida
        if target_date:
            target_date = datetime.strptime(target_date, '%d-%m-%Y').strftime('%Y-%m-%d')
            conditions.append(
                "strftime('%Y-%m-%d', substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2)) < ?")
            params.append(target_date)

        # Construir a string das condições
        condition_str = " AND ".join(conditions) if conditions else ""

        # Seleciona os registros com base nas condições fornecidas e limita a quantidade com ORDER BY
        query = (
            f"SELECT motorist_id, truck_id, data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada, "
            f"observacao, tempo_refeicao, intersticio, tempo_intervalo, tempo_carga_descarga, jornada_total, "
            f"tempo_direcao, direcao_sem_pausa, in_descanso_1, fim_descanso_1, in_descanso_2, fim_descanso_2, "
            f"in_descanso_3, fim_descanso_3, in_descanso_4, fim_descanso_4, in_descanso_5, fim_descanso_5, "
            f"in_descanso_6, fim_descanso_6, in_descanso_7, fim_descanso_7, in_descanso_8, fim_descanso_8, "
            f"in_car_desc_1, fim_car_desc_1, in_car_desc_2, fim_car_desc_2, in_car_desc_3, fim_car_desc_3, "
            f"in_car_desc_4, fim_car_desc_4, in_car_desc_5, fim_car_desc_5, in_car_desc_6, fim_car_desc_6, "
            f"in_car_desc_7, fim_car_desc_7 "
            f"FROM perm_data WHERE {condition_str} "
            f"ORDER BY strftime('%Y-%m-%d', substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2)) DESC "
            f"LIMIT ?"
        )

        # Adicionando N ao parâmetro params para LIMIT
        params.append(n)

        self.logger.print(f"Executando query no perm_data: {query}")
        self.logger.print(f"Params: {params}")

        # Conectando ao banco de dados e usando pandas para retornar o DataFrame
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=tuple(params))
        conn.close()

        if output_format == 'df':

            time_columns = [
                'inicio_jornada', 'in_refeicao', 'fim_refeicao', 'fim_jornada',
                'in_descanso_1', 'fim_descanso_1', 'in_descanso_2', 'fim_descanso_2',
                'in_descanso_3', 'fim_descanso_3', 'in_descanso_4', 'fim_descanso_4',
                'in_descanso_5', 'fim_descanso_5', 'in_descanso_6', 'fim_descanso_6',
                'in_descanso_7', 'fim_descanso_7', 'in_descanso_8', 'fim_descanso_8',
                'in_car_desc_1', 'fim_car_desc_1', 'in_car_desc_2', 'fim_car_desc_2',
                'in_car_desc_3', 'fim_car_desc_3', 'in_car_desc_4', 'fim_car_desc_4',
                'in_car_desc_5', 'fim_car_desc_5', 'in_car_desc_6', 'fim_car_desc_6',
                'in_car_desc_7', 'fim_car_desc_7'
            ]

            # Convertendo todas as colunas de data/hora para datetime, caso exista.
            for col in time_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df['data'].astype(str) + ' ' + df[col].astype(str), format='%d-%m-%Y %H:%M',
                                             errors='coerce')

            # Agora converte a coluna 'data' para datetime no formato correto
            df['data'] = pd.to_datetime(df['data'], format='%d-%m-%Y')

            return df

        elif output_format == 'dict':
            # Convertendo todas as colunas datetime para string ou None se forem NaT
            for col in df.select_dtypes(include=['datetime64']).columns:
                df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)

            return df.to_dict(orient='records')

        else:
            return None

    def retrieve_all_perm_data(self) -> list:
        """
        Retorna uma lista contendo todos os dados de todos os perm_data.

        :return: Uma lista contendo todos os dados de perm_data.
        :rtype: list(tuple)
        """
        self.logger.print("Consultando todos os perm_data da tabela.")

        query = "SELECT * FROM perm_data"

        perm_data = self.exec_query(query=query, fetchone=False, log_success=False)

        return perm_data

    def upsert_from_dict(self, row: Dict[str, any]):
        """Insere ou atualiza um dia de jornada usando ON CONFLICT"""
        cols   = ','.join(row.keys())
        placeholders = ','.join(['?'] * len(row))
        update_cols = [c for c in row.keys() if c not in ('data', 'truck_id')]
        update_stmt = ','.join([f"{c}=excluded.{c}" for c in update_cols])

        sql = f"""INSERT INTO perm_data ({cols}) VALUES ({placeholders})
                 ON CONFLICT(data,truck_id) DO UPDATE SET {update_stmt};"""
        self.exec_query(sql, params=tuple(row.values()))