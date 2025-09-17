from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import Optional, Tuple
import sqlite3

class TrackDayOffDriver(GeneralDriver):
    """
    Classe para gerenciamento da tabela dayoff, que armazena os dias de folga (férias) de motoristas.

    Parâmetros:
    - logger (CustomLogger): instância de logger personalizada.
    - db_path (str): caminho para o banco de dados SQLite.

    Tabela associada:
    - dayoff(id, motorist_id, data, motivo)
    """

    def __init__(self, logger: CustomLogger, db_path: str):
        super().__init__(logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        self.logger.print("Executando create table para dayoff")
        query = '''
        CREATE TABLE IF NOT EXISTS dayoff (
            motorist_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            motivo TEXT NOT NULL,
            PRIMARY KEY (motorist_id, data, motivo),
            FOREIGN KEY (motorist_id) REFERENCES motorists(id) ON DELETE CASCADE
        );
        '''
        try:
            self.exec_query(query, log_success=True)
            self.logger.print("Tabela dayoff criada com sucesso.")
        except Exception as e:
            self.logger.print(f"[ERRO] Falha ao criar tabela dayoff: {e}")

    def get_last_dayoff_date_for_motorist(self, motorist_id: int) -> Optional[Tuple]:
        """
        Retorna a data do registro de folga mais recente para um dado motorista na tabela dayoff.
        A data é retornada no formato DD-MM-YYYY como está armazenada no banco.
        """
        query = """
            SELECT data FROM dayoff
            WHERE motorist_id = ?
            ORDER BY substr(data, 7, 4) DESC, substr(data, 4, 2) DESC, substr(data, 1, 2) DESC
            LIMIT 1
        """
        # Ordena pelo ano, depois mês, depois dia para garantir a data mais recente
        return self.exec_query(query, params=(motorist_id,), fetchone=True)

    def get_first_dayoff_date_for_motorist(self, motorist_id: int) -> Optional[Tuple]:
        """
        Retorna a data do registro de folga mais antigo para um dado motorista na tabela dayoff.
        A data é retornada no formato DD-MM-YYYY como está armazenada no banco.
        """
        query = """
            SELECT data FROM dayoff
            WHERE motorist_id = ?
            ORDER BY substr(data, 7, 4), substr(data, 4, 2), substr(data, 1, 2)
            LIMIT 1
        """
        # Ordena pelo ano, depois mês, depois dia para garantir a data mais antiga
        return self.exec_query(query, params=(motorist_id,), fetchone=True)

    def create_dayoff(self, motorist_id: int, data: str, motivo: Optional[str] = None) -> bool:
        """
        Registra um dia de folga para um motorista no formato DD-MM-YYYY.

        :param motorist_id: ID do motorista.
        :param data: Data no formato DD-MM-YYYY.
        :param motivo: Motivo da folga (opcional).
        :return: True se inserido, False se ignorado ou erro.
        """
        self.logger.print(f"[INFO] Registrando folga: motorista_id={motorist_id}, data={data}, motivo={motivo}")

        query = '''
            INSERT OR IGNORE INTO dayoff (motorist_id, data, motivo)
            VALUES (?, ?, ?)
        '''

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, (motorist_id, data, motivo))
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                self.logger.print(f"[AVISO] Registro já existente (ignorado): {motorist_id} - {data}")
            else:
                self.logger.print(f"[SUCESSO] Registro salvo: {motorist_id} - {data}")

            return affected > 0

        except Exception as e:
            self.logger.print(f"[ERRO] Erro ao salvar folga: {e}")
            return False

    def replace_dayoff(self, motorist_id: int, data: str, motivo: Optional[str] = None) -> bool:
        """
        Substitui um dia de folga para um motorista no formato DD-MM-YYYY.
        Remove registros existentes e insere o novo.

        :param motorist_id: ID do motorista.
        :param data: Data no formato DD-MM-YYYY.
        :param motivo: Motivo da folga (opcional).
        :return: True se substituído com sucesso, False se erro.
        """
        self.logger.print(f"[DEBUG] replace_dayoff: Iniciando - motorist_id={motorist_id}, data={data}, motivo={motivo}")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remove registros existentes para esta data e motorista
            self.logger.print(f"[DEBUG] replace_dayoff: Removendo registros existentes")
            cursor.execute("DELETE FROM dayoff WHERE motorist_id = ? AND data = ?", (motorist_id, data))
            deleted_rows = cursor.rowcount
            self.logger.print(f"[DEBUG] replace_dayoff: Registros removidos = {deleted_rows}")
            
            # Insere o novo registro
            self.logger.print(f"[DEBUG] replace_dayoff: Inserindo novo registro")
            cursor.execute("INSERT INTO dayoff (motorist_id, data, motivo) VALUES (?, ?, ?)", 
                         (motorist_id, data, motivo))
            inserted_rows = cursor.rowcount
            self.logger.print(f"[DEBUG] replace_dayoff: Registros inseridos = {inserted_rows}")
            
            conn.commit()
            conn.close()

            self.logger.print(f"[DEBUG] replace_dayoff: Operação concluída com sucesso")
            return True

        except Exception as e:
            self.logger.print(f"[DEBUG] replace_dayoff: Erro = {e}")
            return False

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

    def insert_data_from_json(self, data_json, motorist_id, replace: bool=False):
        """
        Insere registros de folga no banco de dados a partir de um JSON contendo dados de jornada.
        Se replace=False não sobrescreve datas existentes e retorna conflitos; se True sobrescreve.

        :param data_json: Lista de dicionários com os dados de jornada
        :param motorist_id: ID do motorista
        :param replace: Se True, substitui registros existentes; se False, retorna conflitos
        :return: dict com informações sobre a inserção, incluindo conflitos encontrados
        """
        self.logger.print(f"[DEBUG] insert_data_from_json: Iniciando com motorist_id={motorist_id}, replace={replace}")
        self.logger.print(f"[DEBUG] insert_data_from_json: data_json={data_json}")
        
        motivos_especiais = [
            'FOLGA','FÉRIAS','AFASTAMENTO','ATESTADO','AT. MÉDICO','FALTA',
            'LIC. ÓBITO','LIC. PATERNIDADE','LIC. MATERNIDADE','GARAGEM',
            'CARGA/DESCARGA','MANUTENÇÃO','folga','manutenção'
        ]
        conflitos, ins, ign, sub = [], 0, 0, 0
        motorist_name = self.get_motorist_name(motorist_id)

        for record in data_json:
            try:
                data = record.get("Data")
                if not data:
                    self.logger.print(f"[DEBUG] insert_data_from_json: Data não encontrada no registro {record}")
                    continue

                observacao = record.get("Observação", "").strip().upper()
                self.logger.print(f"[DEBUG] insert_data_from_json: Processando data={data}, observacao={observacao}")
                
                if observacao in motivos_especiais:
                    self.logger.print(f"[DEBUG] insert_data_from_json: Observação '{observacao}' é motivo especial")
                    # Verifica TODOS os conflitos antes de decidir o que fazer
                    conflicts_found = []
                    
                    # Verifica se o motorista já tem folga registrada nesta data
                    dayoff_conflict = self.exec_query("SELECT motivo FROM dayoff WHERE motorist_id=? AND data=?",
                                                     params=(motorist_id, data), fetchone=True)
                    
                    if dayoff_conflict:
                        motivo_existente = dayoff_conflict[0]
                        self.logger.print(f"[DEBUG] insert_data_from_json: Conflito de folga encontrado - motivo_existente={motivo_existente}")
                        conflicts_found.append({
                            'type': 'dayoff_conflict',
                            'data': dayoff_conflict,
                            'conflict_obj': {
                                'data': data,
                                'tipo': 'Motorista já possui folga',
                                'descricao': f"Motorista {motorist_name} já possui folga ({motivo_existente}) registrada na data {data}"
                            }
                        })
                    
                    # Verifica se o motorista já tem jornada registrada nesta data
                    journey_conflict = self.exec_query("SELECT truck_id FROM perm_data WHERE motorist_id=? AND data=?",
                                                      params=(motorist_id, data), fetchone=True)
                    
                    if journey_conflict:
                        self.logger.print(f"[DEBUG] insert_data_from_json: Conflito de jornada encontrado - truck_id={journey_conflict[0]}")
                        conflicts_found.append({
                            'type': 'journey_conflict',
                            'data': journey_conflict,
                            'conflict_obj': {
                                'data': data,
                                'tipo': 'Motorista já possui jornada',
                                'descricao': f"Motorista {motorist_name} já possui jornada registrada na data {data}"
                            }
                        })
                    
                    # Se há conflitos e não é para substituir, adiciona todos os conflitos e pula
                    if conflicts_found and not replace:
                        self.logger.print(f"[DEBUG] insert_data_from_json: Conflitos encontrados e replace=False, ignorando registro")
                        for conflict in conflicts_found:
                            conflitos.append(conflict['conflict_obj'])
                        ign += 1
                        continue
                    
                    # Se chegou até aqui e replace=True, remove TODOS os conflitos encontrados
                    if replace and conflicts_found:
                        self.logger.print(f"[DEBUG] insert_data_from_json: Replace=True, removendo conflitos")
                        for conflict in conflicts_found:
                            if conflict['type'] == 'journey_conflict':
                                # Remove jornada existente do mesmo motorista
                                self.exec_query("DELETE FROM infractions WHERE motorist_id=? AND data=?",
                                                params=(motorist_id, data))
                                self.exec_query("DELETE FROM perm_data WHERE motorist_id=? AND data=?",
                                              params=(motorist_id, data))
                                sub += 1
                            elif conflict['type'] == 'dayoff_conflict':
                                # O replace_dayoff já cuida de remover dayoff existente
                                sub += 1

                    # Inserir ou substituir o registro
                    self.logger.print(f"[DEBUG] insert_data_from_json: Chamando replace_dayoff para data={data}, motivo={observacao}")
                    success = self.replace_dayoff(motorist_id=motorist_id, data=data, motivo=observacao)
                    if success:
                        ins += 1
                        self.logger.print(f"[DEBUG] insert_data_from_json: Registro inserido com sucesso")
                    else:
                        self.logger.print(f"[DEBUG] insert_data_from_json: Erro ao inserir registro")
                else:
                    self.logger.print(f"[DEBUG] insert_data_from_json: Observação '{observacao}' não é motivo especial, ignorando")

            except Exception as e:
                self.logger.print(f"[DEBUG] insert_data_from_json: Erro no registro {record}: {e}")

        result = {
            'tem_conflitos': bool(conflitos),
            'conflitos': conflitos,
            'registros_inseridos': ins,
            'registros_ignorados': ign,
            'registros_substituidos': sub
        }
        
        self.logger.print(f"[DEBUG] insert_data_from_json: Resultado final = {result}")
        return result

    def replace_data_from_json(self, data_json, motorist_id):
        """Sobrescreve registros existentes chamando insert_data_from_json com replace=True."""
        return self.insert_data_from_json(data_json, motorist_id, replace=True)

    def check_conflicts_only(self, data_json, motorist_id):
        """
        Verifica apenas conflitos sem inserir dados.
        Retorna o mesmo formato que insert_data_from_json mas sem inserir nada.
        """

        conflitos, ins, ign, sub = [], 0, 0, 0
        motorist_name = self.get_motorist_name(motorist_id)

        for record in data_json:
            try:
                data = record.get("Data")
                if not data:
                    continue

                observacao = record.get("Observação", "").strip().upper()
                if observacao:
                    # Verifica TODOS os conflitos
                    conflicts_found = []
                    
                    # Verifica se o motorista já tem folga registrada nesta data
                    dayoff_conflict = self.exec_query("SELECT motivo FROM dayoff WHERE motorist_id=? AND data=?",
                                                     params=(motorist_id, data), fetchone=True)
                    
                    if dayoff_conflict:
                        motivo_existente = dayoff_conflict[0]
                        conflicts_found.append({
                            'type': 'dayoff_conflict',
                            'data': dayoff_conflict,
                            'conflict_obj': {
                                'data': data,
                                'tipo': 'Motorista já possui folga',
                                'descricao': f"Motorista {motorist_name} já possui folga ({motivo_existente}) registrada na data {data}"
                            }
                        })
                    
                    # Verifica se o motorista já tem jornada registrada nesta data
                    journey_conflict = self.exec_query("SELECT truck_id FROM perm_data WHERE motorist_id=? AND data=?",
                                                      params=(motorist_id, data), fetchone=True)
                    
                    if journey_conflict:
                        conflicts_found.append({
                            'type': 'journey_conflict',
                            'data': journey_conflict,
                            'conflict_obj': {
                                'data': data,
                                'tipo': 'Motorista já possui jornada',
                                'descricao': f"Motorista {motorist_name} já possui jornada registrada na data {data}"
                            }
                        })
                    
                    # Se há conflitos, adiciona todos os conflitos
                    if conflicts_found:
                        for conflict in conflicts_found:
                            conflitos.append(conflict['conflict_obj'])
                        ign += 1
                    else:
                        ins += 1

            except Exception as e:
                print(f"Erro no registro {record}: {e}")

        return {
            'tem_conflitos': bool(conflitos),
            'conflitos': conflitos,
            'registros_inseridos': ins,
            'registros_ignorados': ign,
            'registros_substituidos': sub
        }

    def retrieve_dayoffs_by_motorist(self, motorist_id: int):
        """
        Retorna todos os dias de folga registrados para um motorista específico.

        Parâmetros:
        - motorist_id (int): ID do motorista.

        Retorno:
        - Lista de dicionários com os dias de folga.
        """
        self.logger.print(f"Consultando folgas do motorista_id={motorist_id}")
        query = '''
            SELECT id, motorist_id, data, motivo
            FROM dayoff
            WHERE motorist_id = ?
            ORDER BY substr(data, 7, 4) DESC, substr(data, 4, 2) DESC, substr(data, 1, 2) DESC
        '''
        return self.exec_query(query=query, params=(motorist_id,), fetchone=False)

    def delete_dayoff(self, dayoff_id: int):
        """
        Remove um registro de folga pelo ID.

        Parâmetros:
        - dayoff_id (int): ID do registro.

        Retorno:
        - Resultado da execução da query.
        """
        self.logger.print(f"Removendo folga com id={dayoff_id}")
        query = 'DELETE FROM dayoff WHERE id = ?'
        return self.exec_query(query=query, params=(dayoff_id,))

    def update_dayoff(self, dayoff_id: int, data: Optional[str], motivo: Optional[str]):
        """
        Atualiza os dados de um registro de folga.

        Parâmetros:
        - dayoff_id (int): ID da folga.
        - data (str): Nova data da folga.
        - motivo (str): Novo motivo.

        Retorno:
        - Resultado da execução da query.
        """
        self.logger.print(f"Atualizando folga id={dayoff_id}")
        columns = []
        params = []

        if data:
            columns.append("data = ?")
            params.append(data)
        if motivo is not None:
            columns.append("motivo = ?")
            params.append(motivo)

        if not columns:
            self.logger.print("Nenhum campo para atualizar.")
            return 0

        query = f"UPDATE dayoff SET {', '.join(columns)} WHERE id = ?"
        params.append(dayoff_id)
        return self.exec_query(query=query, params=tuple(params))

    

    def retrieve_all_dayoffs(self):
        """
        Retorna todos os registros da tabela dayoff.

        Retorno:
        - Lista de tuplas no formato (motorist_id, data, motivo)
        """
        self.logger.print("Recuperando todos os registros da tabela dayoff")
        query = '''
            SELECT motorist_id, data, motivo
            FROM dayoff
            ORDER BY substr(data, 7, 4) DESC, substr(data, 4, 2) DESC, substr(data, 1, 2) DESC
        '''
        return self.exec_query(query=query, fetchone=False)



