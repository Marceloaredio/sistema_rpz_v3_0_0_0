from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
from typing import List, Tuple, Dict

class ClosureDayOffDriver(GeneralDriver):
    def __init__(self, logger: CustomLogger, db_path: str):
        super().__init__(logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        """
        Cria as tabelas de fechamento com as novas colunas daily_value e food_value.
        """
        self.logger.print("Criando tabelas de Dayoff para fechamento.")

        # Tabela dayoff_fecham
        query_dayoff = '''
        CREATE TABLE IF NOT EXISTS dayoff_fecham (
            motorist_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            motivo TEXT NOT NULL,
            daily_value REAL DEFAULT 90.00,
            food_value  REAL DEFAULT 0.00,
            PRIMARY KEY (motorist_id, data, motivo),
            FOREIGN KEY (motorist_id) REFERENCES motorists(id) ON DELETE CASCADE
        )
        '''
        self.exec_query(query_dayoff, log_success=False)

        self.logger.print("Tabelas de Dayoff para fechamento criadas com sucesso.")

    def insert_dayoff(self, motorist_id: int, data: str, motivo: str, daily_value: float = None, food_value: float = None) -> int:
        """
        Adiciona um registro de dayoff com valores de diária e alimentação.

        :param motorist_id: ID do motorista
        :param data: Data no formato DD-MM-YYYY
        :param motivo: Motivo do dayoff
        :param daily_value: Valor da diária (opcional)
        :param food_value: Valor da ajuda alimentação (opcional)
        :return: Número de linhas afetadas
        """
        self.logger.print(f"Adicionando dayoff: motorista {motorist_id}, data {data}, motivo {motivo}")

        # Se não foram fornecidos valores, usar os padrões
        if daily_value is None:
            daily_value = 90.00
        if food_value is None:
            food_value = 0.00

        query = '''
        INSERT OR REPLACE INTO dayoff_fecham (motorist_id, data, motivo, daily_value, food_value)
        VALUES (?, ?, ?, ?, ?)
        '''
        
        result = self.exec_query(query, params=(motorist_id, data, motivo, daily_value, food_value))
        return result if result is not None else 0
    

    def get_dayoff_fecham_by_motorist(self, motorist_id: int, start_date: str = None, end_date: str = None) -> List[Tuple]:
        """
        Busca registros de dayoff_fecham por motorista e período opcional.

        :param motorist_id: ID do motorista
        :param start_date: Data inicial (opcional)
        :param end_date: Data final (opcional)
        :return: Lista de registros
        """
        if start_date and end_date:
            query = '''
            SELECT * FROM dayoff_fecham 
            WHERE motorist_id = ? AND data BETWEEN ? AND ?
            ORDER BY data
            '''
            result = self.exec_query(query, params=(motorist_id, start_date, end_date), fetchone=False)
        else:
            query = '''
            SELECT * FROM dayoff_fecham 
            WHERE motorist_id = ?
            ORDER BY data
            '''
            result = self.exec_query(query, params=(motorist_id,), fetchone=False)

        return result if result else []

    def upsert_from_dict(self, row: dict):
        """Insere ou atualiza registro de folga (dayoff_fecham)."""
        # Garantir que todos os campos obrigatórios estejam presentes
        if 'daily_value' not in row:
            row['daily_value'] = 90.00
        if 'food_value' not in row:
            row['food_value'] = 0.00
        if 'carga_horaria_esp' not in row:
            row['carga_horaria_esp'] = ''
        if 'hextra_50_esp' not in row:
            row['hextra_50_esp'] = ''

        # DEBUG: Log dos campos que serão inseridos
        self.logger.print(f"🔍 DEBUG - upsert_from_dict: campos a serem inseridos: {list(row.keys())}")
        self.logger.print(f"🔍 DEBUG - upsert_from_dict: valores: {list(row.values())}")

        cols = ','.join(row.keys())
        ph   = ','.join(['?'] * len(row))
        upd  = ','.join([f"{c}=excluded.{c}" for c in row.keys() if c not in ('motorist_id','data','motivo')])
        sql  = f"""INSERT INTO dayoff_fecham ({cols}) VALUES ({ph})
                 ON CONFLICT(motorist_id,data,motivo) DO UPDATE SET {upd};"""
        
        # DEBUG: Log da query SQL
        self.logger.print(f"🔍 DEBUG - upsert_from_dict: SQL: {sql}")
        
        self.exec_query(sql, params=tuple(row.values()))

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

    def insert_data_from_json(self, dados_folga: List[Dict], replace: bool=False):
        """Insere dados de folga. Se replace=False não sobrescreve datas existentes e retorna conflitos; se True sobrescreve."""
        conflitos, ins, ign, sub = [], 0, 0, 0
        
        for dados in dados_folga:
            try:
                # Debug: verificar se motorist_id está presente
                if 'motorist_id' not in dados:
                    self.logger.register_log(f"ERRO: motorist_id não encontrado no dicionário dados. Chaves: {list(dados.keys())}")
                    continue
                    
                motorist_id = dados['motorist_id']
                data = dados['data']
                motivo = dados['motivo']
                daily_value = dados.get('daily_value', 90.00)
                food_value = dados.get('food_value', 0.00)
                
                motorist_name = self.get_motorist_name(motorist_id)
                
                # VERIFICAR SE OS CÁLCULOS ESPECIAIS JÁ FORAM ENVIADOS PELO FRONTEND
                carga_horaria_esp = dados.get('carga_horaria_esp', '')
                hextra_50_esp = dados.get('hextra_50_esp', '')
                
                # DEBUG: Log dos dados recebidos
                self.logger.print(f"🔍 DEBUG - Dados recebidos para {motivo}:")
                self.logger.print(f"   - carga_horaria_esp: '{carga_horaria_esp}'")
                self.logger.print(f"   - hextra_50_esp: '{hextra_50_esp}'")
                self.logger.print(f"   - Todos os campos: {list(dados.keys())}")
                
                # DEBUG EXTENSO para valores negativos no driver
                self.logger.print(f"🔍 DEBUG - Verificação de valores negativos no driver:")
                self.logger.print(f"   - hextra_50_esp original: '{hextra_50_esp}'")
                self.logger.print(f"   - hextra_50_esp type: {type(hextra_50_esp)}")
                self.logger.print(f"   - hextra_50_esp length: {len(hextra_50_esp) if hextra_50_esp else 0}")
                if hextra_50_esp:
                    self.logger.print(f"   - hextra_50_esp.find('-'): {hextra_50_esp.find('-')}")
                    self.logger.print(f"   - hextra_50_esp.startswith('-'): {hextra_50_esp.startswith('-')}")
                    self.logger.print(f"   - hextra_50_esp[0]: '{hextra_50_esp[0]}'")
                    self.logger.print(f"   - hextra_50_esp == '-04:00': {hextra_50_esp == '-04:00'}")
                    self.logger.print(f"   - hextra_50_esp == '-04:00': {hextra_50_esp == '-04:00'}")
                    self.logger.print(f"   - hextra_50_esp in dados: {hextra_50_esp in dados.values()}")
                else:
                    self.logger.print(f"   - hextra_50_esp está vazio ou None")
                
                # Se não foram enviados pelo frontend, calcular automaticamente
                if not carga_horaria_esp and not hextra_50_esp:
                    try:
                        from controller.carga_horaria_calculator import CargaHorariaCalculator
                        from config.feature_flags import is_carga_horaria_especial_enabled
                        
                        # Só calcular se a funcionalidade estiver habilitada
                        if is_carga_horaria_especial_enabled():
                            calc = CargaHorariaCalculator()
                            
                            # Buscar critério especial configurado
                            criterio_query = "SELECT carga_horaria_especial FROM criterios_diaria WHERE valor_filtro = ?"
                            criterio_result = self.exec_query(criterio_query, params=(motivo,), fetchone=True)
                            
                            if criterio_result and criterio_result[0] and criterio_result[0] != 'Padrão':
                                carga_horaria_especial = criterio_result[0]
                                carga_horaria_esp = carga_horaria_especial
                                
                                # Calcular hora extra 50% especial
                                # Para critérios especiais, assumir jornada de 8h (480 min) como padrão
                                jornada_total = 480  # 8 horas em minutos
                                carga_horaria_minutos = calc.converter_tempo_para_minutos(carga_horaria_especial)
                                he_50_minutos = max(0, jornada_total - carga_horaria_minutos)
                                hextra_50_esp = calc.converter_minutos_para_tempo(he_50_minutos)
                                
                                self.logger.print(f"🔧 Carga Horária Especial calculada automaticamente: {motivo} -> {carga_horaria_esp} -> HE 50%: {hextra_50_esp}")
                            else:
                                self.logger.print(f"ℹ️ Critério {motivo} usa carga horária padrão")
                                
                    except Exception as e:
                        self.logger.print(f"⚠️ Erro ao calcular carga horária especial para {motivo}: {e}")
                        # Continuar com valores vazios em caso de erro
                else:
                    self.logger.print(f"🔧 Usando cálculos especiais do frontend para {motivo}: carga={carga_horaria_esp}, he50={hextra_50_esp}")
                
            except Exception as e:
                self.logger.register_log(f"Erro ao processar dados: {e}. Dados: {dados}")
                continue
            
            # Verifica TODOS os conflitos antes de decidir o que fazer
            conflicts_found = []
            
            # Verificar se já existe registro para esta data e motorista (dayoff)
            dayoff_conflict = self.exec_query(
                "SELECT motivo FROM dayoff_fecham WHERE motorist_id=? AND data=?",
                params=(motorist_id, data),
                fetchone=True
            )
            
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
            journey_conflict = self.exec_query(
                "SELECT truck_id FROM perm_data_fecham WHERE motorist_id=? AND data=?",
                params=(motorist_id, data),
                fetchone=True
            )
            
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
            
            # Se há conflitos e não é para substituir, adiciona todos os conflitos e pula
            if conflicts_found and not replace:
                for conflict in conflicts_found:
                    conflitos.append(conflict['conflict_obj'])
                ign += 1
                continue
            
            # Se chegou até aqui e replace=True, remove TODOS os conflitos encontrados
            if replace and conflicts_found:
                for conflict in conflicts_found:
                    if conflict['type'] == 'journey_conflict':
                        # Remove jornada existente do mesmo motorista
                        self.exec_query("DELETE FROM perm_data_fecham WHERE motorist_id=? AND data=?",
                                      params=(motorist_id, data))
                        sub += 1
                    elif conflict['type'] == 'dayoff_conflict':
                        # Remove folga existente do mesmo motorista na mesma data
                        self.exec_query("DELETE FROM dayoff_fecham WHERE motorist_id=? AND data=?",
                                      params=(motorist_id, data))
                        sub += 1
                
            # Preparar dados para inserção (INCLUINDO CAMPOS ESPECIAIS)
            row = {
                'motorist_id': motorist_id,
                'data': data,
                'motivo': motivo,
                'daily_value': daily_value,
                'food_value': food_value,
                'carga_horaria_esp': carga_horaria_esp,
                'hextra_50_esp': hextra_50_esp
            }
            
            # DEBUG EXTENSO antes da inserção
            self.logger.print(f"🔍 DEBUG - Dados finais antes da inserção:")
            self.logger.print(f"   - row: {row}")
            self.logger.print(f"   - carga_horaria_esp: '{row['carga_horaria_esp']}'")
            self.logger.print(f"   - hextra_50_esp: '{row['hextra_50_esp']}'")
            self.logger.print(f"   - hextra_50_esp type: {type(row['hextra_50_esp'])}")
            self.logger.print(f"   - hextra_50_esp == '-04:00': {row['hextra_50_esp'] == '-04:00'}")
            
            # Se replace=True, usar INSERT simples (já deletamos os conflitos)
            if replace:
                query = '''
                INSERT INTO dayoff_fecham (motorist_id, data, motivo, daily_value, food_value, carga_horaria_esp, hextra_50_esp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
                self.logger.print(f"🔍 DEBUG - Query INSERT: {query}")
                self.logger.print(f"🔍 DEBUG - Parâmetros: ({motorist_id}, {data}, {motivo}, {daily_value}, {food_value}, '{carga_horaria_esp}', '{hextra_50_esp}')")
                self.exec_query(query, params=(motorist_id, data, motivo, daily_value, food_value, carga_horaria_esp, hextra_50_esp))
            else:
                # Se não é replace, usar upsert (que só substitui se for mesmo motivo)
                self.logger.print(f"🔍 DEBUG - Usando upsert_from_dict")
                self.upsert_from_dict(row)
            
            ins += 1
            
        return {
            'tem_conflitos': bool(conflitos),
            'conflitos': conflitos,
            'registros_inseridos': ins,
            'registros_ignorados': ign,
            'registros_substituidos': sub
        }

    def replace_data_from_json(self, tabela: List[dict], motorist_id: int):
        """Sobrescreve registros existentes chamando insert_data_from_json com replace=True."""
        return self.insert_data_from_json(tabela, replace=True)

    def check_conflicts_only(self, data_json, motorist_id):
        """
        Verifica apenas conflitos sem inserir dados.
        Retorna o mesmo formato que insert_data_from_json mas sem inserir nada.
        """

        conflitos, ins, ign, sub = [], 0, 0, 0
        motorist_name = self.get_motorist_name(motorist_id)

        for record in data_json:
            try:
                data = record.get("data")
                if not data:
                    continue

                motivo = record.get("motivo", "").strip().upper()
                if motivo:
                    # Verifica TODOS os conflitos
                    conflicts_found = []
                    
                    # Verifica se o motorista já tem folga registrada nesta data (dayoff_fecham)
                    dayoff_conflict = self.exec_query("SELECT motivo FROM dayoff_fecham WHERE motorist_id=? AND data=?",
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
                    
                    # Verifica se o motorista já tem jornada registrada nesta data (perm_data_fecham)
                    journey_conflict = self.exec_query("SELECT truck_id FROM perm_data_fecham WHERE motorist_id=? AND data=?",
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
                self.logger.register_log(f"Erro no registro {record}: {e}")

        return {
            'tem_conflitos': bool(conflitos),
            'conflitos': conflitos,
            'registros_inseridos': ins,
            'registros_ignorados': ign,
            'registros_substituidos': sub
        }