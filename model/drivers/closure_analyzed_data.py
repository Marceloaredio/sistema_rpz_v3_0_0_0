from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class AnalyzedClosureData(GeneralDriver):
    def __init__(self, logger: CustomLogger, db_path: str):
        """
        Inicializa a classe AnalyzedClosureData.

        :param logger: Instância de um logger customizado para registrar logs.
        :param db_path: Caminho para o banco de dados.
        """
        super().__init__(logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        """
        Cria as tabelas de fechamento com as novas colunas daily_value e food_value.
        """
        self.logger.print("Criando tabelas de fechamento com valores de diária e alimentação.")

        # Tabela perm_data_fecham
        query_perm_data = '''
        CREATE TABLE IF NOT EXISTS perm_data_fecham (
            motorist_id INTEGER NOT NULL,
            truck_id    INTEGER,
            data        TEXT    NOT NULL,
            dia_da_semana TEXT  NOT NULL,

            -- Horários principais
            inicio_jornada   TEXT,
            in_refeicao      TEXT,
            fim_refeicao     TEXT,
            fim_jornada      TEXT,
            observacao       TEXT,

            -- Tempos consolidados
            tempo_refeicao   TEXT,
            intersticio      TEXT,
            tempo_intervalo  TEXT,
            tempo_carga_descarga TEXT,
            jornada_total    TEXT,
            tempo_direcao    TEXT,
            direcao_sem_pausa TEXT,
            carga_horaria    TEXT,
            hextra_50        TEXT,
            hextra_100       TEXT,
            he_noturno       TEXT,

            -- Descansos (até 8)
            in_desc_1  TEXT, fim_desc_1  TEXT,
            in_desc_2  TEXT, fim_desc_2  TEXT,
            in_desc_3  TEXT, fim_desc_3  TEXT,
            in_desc_4  TEXT, fim_desc_4  TEXT,
            in_desc_5  TEXT, fim_desc_5  TEXT,
            in_desc_6  TEXT, fim_desc_6  TEXT,
            in_desc_7  TEXT, fim_desc_7  TEXT,
            in_desc_8  TEXT, fim_desc_8  TEXT,

            -- Carga/Descarga (até 7)
            in_car_desc_1 TEXT, fim_car_desc_1 TEXT,
            in_car_desc_2 TEXT, fim_car_desc_2 TEXT,
            in_car_desc_3 TEXT, fim_car_desc_3 TEXT,
            in_car_desc_4 TEXT, fim_car_desc_4 TEXT,
            in_car_desc_5 TEXT, fim_car_desc_5 TEXT,
            in_car_desc_6 TEXT, fim_car_desc_6 TEXT,
            in_car_desc_7 TEXT, fim_car_desc_7 TEXT,

            -- Valores financeiros
            daily_value REAL DEFAULT 90.00,
            food_value  REAL DEFAULT 0.00,

            PRIMARY KEY (motorist_id, data),
            FOREIGN KEY (motorist_id) REFERENCES motorists(id),
            FOREIGN KEY (truck_id)   REFERENCES trucks(id)
        )'''
        self.exec_query(query_perm_data, log_success=False)
        self.logger.print("Tabelas de fechamento criadas com sucesso.")

    def add_perm_data_fecham(self, motorist_id: int, truck_id: int, data: str, dia_da_semana: str,
                             inicio_jornada: str, in_refeicao: str, fim_refeicao: str, fim_jornada: str,
                             observacao: str, tempo_refeicao: str, intersticio: str, tempo_intervalo: str,
                             tempo_carga_descarga: str, jornada_total: str, tempo_direcao: str,
                             direcao_sem_pausa: str, descanso_1: tuple, descanso_2: tuple, descanso_3: tuple,
                             descanso_4: tuple, descanso_5: tuple, descanso_6: tuple, descanso_7: tuple,
                             descanso_8: tuple, car_desc_1: tuple, car_desc_2: tuple, car_desc_3: tuple,
                             car_desc_4: tuple, car_desc_5: tuple, car_desc_6: tuple, car_desc_7: tuple,
                             daily_value: float = None, food_value: float = None) -> int:
        """
        Adiciona um registro de perm_data com valores de diária e alimentação.

        :param motorist_id: ID do motorista
        :param truck_id: ID do caminhão
        :param data: Data no formato DD-MM-YYYY
        :param dia_da_semana: Dia da semana
        :param inicio_jornada: Horário de início da jornada
        :param in_refeicao: Horário de início da refeição
        :param fim_refeicao: Horário de fim da refeição
        :param fim_jornada: Horário de fim da jornada
        :param observacao: Observações
        :param tempo_refeicao: Tempo de refeição
        :param intersticio: Interstício
        :param tempo_intervalo: Tempo de intervalo
        :param tempo_carga_descarga: Tempo de carga/descarga
        :param jornada_total: Jornada total
        :param tempo_direcao: Tempo de direção
        :param direcao_sem_pausa: Direção sem pausa
        :param descanso_1 a descanso_8: Períodos de descanso
        :param car_desc_1 a car_desc_7: Períodos de carga/descarga
        :param daily_value: Valor da diária (opcional)
        :param food_value: Valor da ajuda alimentação (opcional)
        :return: Número de linhas afetadas
        """
        self.logger.print(f"Adicionando perm_data: motorista {motorist_id}, caminhão {truck_id}, data {data}")

        # Se não foram fornecidos valores, usar os padrões
        if daily_value is None:
            daily_value = 90.00
        if food_value is None:
            food_value = 0.00

        query = '''
        INSERT OR REPLACE INTO perm_data_fecham (
            motorist_id, truck_id, data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada,
            observacao, tempo_refeicao, intersticio, tempo_intervalo, tempo_carga_descarga, jornada_total,
            tempo_direcao, direcao_sem_pausa, in_desc_1, fim_desc_1, in_desc_2, fim_desc_2,
            in_desc_3, fim_desc_3, in_desc_4, fim_desc_4, in_desc_5, fim_desc_5,
            in_desc_6, fim_desc_6, in_desc_7, fim_desc_7, in_desc_8, fim_desc_8,
            in_car_desc_1, fim_car_desc_1, in_car_desc_2, fim_car_desc_2, in_car_desc_3, fim_car_desc_3,
            in_car_desc_4, fim_car_desc_4, in_car_desc_5, fim_car_desc_5, in_car_desc_6, fim_car_desc_6,
            in_car_desc_7, fim_car_desc_7, daily_value, food_value
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        params = (
            motorist_id, truck_id, data, dia_da_semana, inicio_jornada, in_refeicao, fim_refeicao, fim_jornada,
            observacao, tempo_refeicao, intersticio, tempo_intervalo, tempo_carga_descarga, jornada_total,
            tempo_direcao, direcao_sem_pausa, *descanso_1, *descanso_2, *descanso_3, *descanso_4, *descanso_5,
            *descanso_6, *descanso_7, *descanso_8, *car_desc_1, *car_desc_2, *car_desc_3, *car_desc_4,
            *car_desc_5, *car_desc_6, *car_desc_7, daily_value, food_value
        )

        result = self.exec_query(query, params=params)
        return result if result is not None else 0

    def get_perm_data_fecham_by_motorist(self, motorist_id: int, start_date: str = None, end_date: str = None) -> List[Tuple]:
        """
        Busca registros de perm_data_fecham por motorista e período opcional.

        :param motorist_id: ID do motorista
        :param start_date: Data inicial (opcional)
        :param end_date: Data final (opcional)
        :return: Lista de registros
        """
        if start_date and end_date:
            query = '''
            SELECT * FROM perm_data_fecham 
            WHERE motorist_id = ? AND data BETWEEN ? AND ?
            ORDER BY data
            '''
            result = self.exec_query(query, params=(motorist_id, start_date, end_date), fetchone=False)
        else:
            query = '''
            SELECT * FROM perm_data_fecham 
            WHERE motorist_id = ?
            ORDER BY data
            '''
            result = self.exec_query(query, params=(motorist_id,), fetchone=False)

        return result if result else [] 

    def upsert_from_dict(self, row: Dict[str, any]):
        """Insere ou atualiza um dia de fechamento usando ON CONFLICT"""
        cols   = ','.join(row.keys())
        placeholders = ','.join(['?'] * len(row))
        update_cols = [c for c in row.keys() if c not in ('motorist_id', 'data')]
        update_stmt = ','.join([f"{c}=excluded.{c}" for c in update_cols])

        # CORREÇÃO: Incluir truck_id na chave de conflito para permitir atualização
        sql = f"""INSERT INTO perm_data_fecham ({cols}) VALUES ({placeholders})
                 ON CONFLICT(motorist_id,data) DO UPDATE SET {update_stmt};"""
        
        self.logger.print(f"🔍 DEBUG - upsert_from_dict:")
        self.logger.print(f"   motorist_id: {row.get('motorist_id')}")
        self.logger.print(f"   truck_id: {row.get('truck_id')}")
        self.logger.print(f"   data: {row.get('data')}")
        self.logger.print(f"   SQL: {sql}")
        
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

    def insert_data_from_json(self, tabela: List[Dict], motorist_id: int, truck_id: int, replace: bool=False):
        """Insere lista de linhas do frontend. Se replace=False não sobrescreve datas existentes e retorna conflitos; se True sobrescreve."""
        conflitos, ins, ign, sub = [], 0, 0, 0
        motorist_name = self.get_motorist_name(motorist_id)

        self.logger.print(f"💾 insert_data_from_json - Iniciando inserção:")
        self.logger.print(f"   motorist_id: {motorist_id}")
        self.logger.print(f"   truck_id: {truck_id}")
        self.logger.print(f"   replace: {replace} (tipo: {type(replace)})")
        self.logger.print(f"   replace == True: {replace == True}")
        self.logger.print(f"   replace is True: {replace is True}")
        self.logger.print(f"   len(tabela): {len(tabela)}")

        # NOVA LÓGICA: Se não é para substituir, verificar TODOS os conflitos primeiro
        if not replace:
            self.logger.print(f"🔍 Modo NÃO substituir - Verificando conflitos primeiro")
            # Verificar todos os conflitos antes de inserir qualquer coisa
            for linha in tabela:
                date_key = linha.get('Data')
                
                # Verifica TODOS os conflitos
                conflicts_found = []
                
                # Verifica se o caminhão já tem jornada de outro motorista nesta data (se truck_id fornecido)
                if truck_id:
                    truck_conflict = self.exec_query(
                        "SELECT motorist_id FROM perm_data_fecham WHERE data=? AND truck_id=? AND motorist_id!=?",
                        params=(date_key, truck_id, motorist_id), fetchone=True
                    )
                    if truck_conflict:
                        try:
                            other_motorist_name = self.get_motorist_name(truck_conflict[0])
                        except:
                            other_motorist_name = f"ID {truck_conflict[0]}"
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
                    "SELECT truck_id FROM perm_data_fecham WHERE data=? AND motorist_id=?",
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
                    "SELECT motivo FROM dayoff_fecham WHERE data=? AND motorist_id=?",
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
            
            # Se há conflitos, retornar sem inserir nada
            if conflitos:
                self.logger.print(f"🚫 Conflitos encontrados em modo NÃO substituir - retornando sem inserir")
                return {'tem_conflitos': True, 'conflitos': conflitos,
                        'registros_inseridos': 0, 'registros_ignorados': ign,
                        'registros_substituidos': 0}

        # Se chegou até aqui, inserir todos os registros (replace=True ou não há conflitos)
        if replace:
            self.logger.print(f"💾 Modo SUBSTITUIR - Inserindo com substituição")
        else:
            self.logger.print(f"💾 Modo NORMAL - Inserindo sem conflitos")
            
        for linha in tabela:
            date_key = linha.get('Data')
            
            # Se replace=True, verificar e remover conflitos antes de inserir
            if replace:
                self.logger.print(f"🔍 Verificando conflitos para substituição na data: {date_key}")
                conflicts_found = []
                
                # Verifica se o caminhão já tem jornada de outro motorista nesta data (se truck_id fornecido)
                if truck_id:
                    truck_conflict = self.exec_query(
                        "SELECT motorist_id FROM perm_data_fecham WHERE data=? AND truck_id=? AND motorist_id!=?",
                        params=(date_key, truck_id, motorist_id), fetchone=True
                    )
                    if truck_conflict:
                        conflicts_found.append({
                            'type': 'truck_conflict',
                            'data': truck_conflict
                        })
                        self.logger.print(f"🚫 Conflito de caminhão encontrado para substituição: {date_key}")
                
                # Verifica se o motorista já tem qualquer registro (jornada) nesta data
                motorist_journey_conflict = self.exec_query(
                    "SELECT truck_id FROM perm_data_fecham WHERE data=? AND motorist_id=?",
                    params=(date_key, motorist_id), fetchone=True
                )
                if motorist_journey_conflict:
                    conflicts_found.append({
                        'type': 'motorist_journey_conflict',
                        'data': motorist_journey_conflict
                    })
                    self.logger.print(f"🚫 Conflito de jornada do motorista encontrado para substituição: {date_key}")
                    
                # Verifica se o motorista já tem dayoff registrado nesta data
                motorist_dayoff_conflict = self.exec_query(
                    "SELECT motivo FROM dayoff_fecham WHERE data=? AND motorist_id=?",
                    params=(date_key, motorist_id), fetchone=True
                )
                if motorist_dayoff_conflict:
                    conflicts_found.append({
                        'type': 'motorist_dayoff_conflict',
                        'data': motorist_dayoff_conflict
                    })
                    self.logger.print(f"🚫 Conflito de dayoff do motorista encontrado para substituição: {date_key}")
                
            # Se chegou até aqui e replace=True, remove TODOS os conflitos encontrados
            if replace and conflicts_found:
                self.logger.print(f"🗑️ Removendo {len(conflicts_found)} conflitos para substituição na data: {date_key}")
                for conflict in conflicts_found:
                    if conflict['type'] == 'truck_conflict':
                        # Remove jornada de outro motorista no mesmo caminhão e data
                        other_motorist_id = conflict['data'][0]
                        self.exec_query("DELETE FROM perm_data_fecham WHERE data=? AND truck_id=? AND motorist_id=?",
                                      params=(date_key, truck_id, other_motorist_id))
                        sub += 1
                        self.logger.print(f"🗑️ Removido conflito de caminhão: motorista {other_motorist_id}")
                    
                    elif conflict['type'] == 'motorist_journey_conflict':
                        # Remove jornada existente do mesmo motorista (qualquer caminhão)
                        self.exec_query("DELETE FROM perm_data_fecham WHERE data=? AND motorist_id=?",
                                      params=(date_key, motorist_id))
                        sub += 1
                        self.logger.print(f"🗑️ Removido conflito de jornada do motorista")
                    
                    elif conflict['type'] == 'motorist_dayoff_conflict':
                        # Remove dayoff existente do mesmo motorista
                        self.exec_query("DELETE FROM dayoff_fecham WHERE data=? AND motorist_id=?",
                                      params=(date_key, motorist_id))
                        sub += 1
                        self.logger.print(f"🗑️ Removido conflito de dayoff do motorista")
            # build row
            desc = []
            for i in range(1, 9):
                desc.append(linha.get(f'Início Descanso {i}', '') or linha.get(f'In. Descanso {i}', ''))
                desc.append(linha.get(f'Fim Descanso {i}', ''))
            # 🆕 CORREÇÃO: Converter placa para ID do truck se necessário
            truck_id_final = linha.get('truck_id') or truck_id
            
            # Se truck_id_final é uma string (placa), converter para ID
            if isinstance(truck_id_final, str) and truck_id_final.strip():
                try:
                    from model.drivers.truck_driver import TruckDriver
                    truck_driver = TruckDriver(logger=self.logger, db_path=self.db_path)
                    placa_original = truck_id_final  # Guardar a placa original
                    truck_info = truck_driver.retrieve_truck(['placa'], [placa_original])
                    if truck_info:
                        truck_id_final = truck_info[0]  # Primeiro campo é o ID
                        self.logger.print(f"🔄 Convertido placa '{placa_original}' para truck_id: {truck_id_final}")
                    else:
                        self.logger.print(f"⚠️ Placa '{placa_original}' não encontrada, usando truck_id=None")
                        truck_id_final = None
                except Exception as e:
                    self.logger.print(f"❌ Erro ao converter placa '{truck_id_final}' para ID: {e}")
                    truck_id_final = None
            
            row = {
                'motorist_id': motorist_id,
                'truck_id': truck_id_final,  # 🆕 CORREÇÃO: Usar truck_id convertido
                'data': date_key,
                'dia_da_semana': linha.get('Dia') or linha.get('Dia da Semana'),
                'inicio_jornada': linha.get('Início Jornada'),
                'in_refeicao': linha.get('Início Refeição') or linha.get('In. Refeição'),
                'fim_refeicao': linha.get('Fim Refeição'),
                'fim_jornada': linha.get('Fim de Jornada'),
                'observacao': linha.get('Observação'),
                'tempo_refeicao': linha.get('Tempo Refeição'),
                'tempo_intervalo': linha.get('Tempo Intervalo'),
                'jornada_total': linha.get('H. Trabalhadas') or linha.get('Jornada Total'),
                'carga_horaria': linha.get('Carga Horária'),
                'hextra_50': linha.get('H.extra 50%'),
                'hextra_100': linha.get('H.extra 100%'),
                'he_noturno': linha.get('H.E. Not'),
                'daily_value': float(str(linha.get('Diária', linha.get('daily_value', '0'))).replace('R$','').replace(',','.')),
                'food_value': float(str(linha.get('Ajuda Alimentação', linha.get('food_value', '0'))).replace('R$','').replace(',','.')),
                'in_desc_1': desc[0],'fim_desc_1':desc[1],'in_desc_2':desc[2],'fim_desc_2':desc[3],
                'in_desc_3': desc[4],'fim_desc_3':desc[5],'in_desc_4':desc[6],'fim_desc_4':desc[7],
                'in_desc_5': desc[8],'fim_desc_5':desc[9],'in_desc_6':desc[10],'fim_desc_6':desc[11],
                'in_desc_7': desc[12],'fim_desc_7':desc[13],'in_desc_8':desc[14],'fim_desc_8':desc[15]
            }
            
            # 🆕 DEBUG: Log detalhado antes de salvar
            self.logger.print(f"🔍 DEBUG - Dados para salvar na data {date_key}:")
            self.logger.print(f"   motorist_id: {row['motorist_id']} (tipo: {type(row['motorist_id']).__name__})")
            self.logger.print(f"   truck_id: {row['truck_id']} (tipo: {type(row['truck_id']).__name__})")
            self.logger.print(f"   data: {row['data']} (tipo: {type(row['data']).__name__})")
            self.logger.print(f"   observacao: {row['observacao']}")
            self.logger.print(f"   daily_value: {row['daily_value']} (tipo: {type(row['daily_value']).__name__})")
            self.logger.print(f"   food_value: {row['food_value']} (tipo: {type(row['food_value']).__name__})")
            self.logger.print(f"   Chaves disponíveis na linha: {list(linha.keys())}")
            self.logger.print(f"   Valor 'Diária' na linha: {linha.get('Diária', 'NÃO ENCONTRADO')}")
            self.logger.print(f"   Valor 'Ajuda Alimentação' na linha: {linha.get('Ajuda Alimentação', 'NÃO ENCONTRADO')}")
            
            self.upsert_from_dict(row)
            ins += 1
            self.logger.print(f"✅ Inserido/atualizado registro para data: {date_key}")
            
        self.logger.print(f"💾 insert_data_from_json - Resultado final:")
        self.logger.print(f"   conflitos: {len(conflitos)}")
        self.logger.print(f"   ins: {ins}")
        self.logger.print(f"   ign: {ign}")
        self.logger.print(f"   sub: {sub}")
        self.logger.print(f"   tem_conflitos: {bool(conflitos)}")
            
        return {'tem_conflitos': bool(conflitos), 'conflitos': conflitos,
                'registros_inseridos': ins, 'registros_ignorados': ign,
                'registros_substituidos': sub}

    def check_conflicts_only(self, data_json, motorist_id, truck_id):
        """
        Verifica apenas conflitos sem inserir dados.
        Retorna o mesmo formato que insert_data_from_json mas sem inserir nada.
        """
        conflitos, ins, ign, sub = [], 0, 0, 0
        try:
            motorist_name = self.get_motorist_name(motorist_id)
        except:
            motorist_name = f"ID {motorist_id}"

        self.logger.print(f"🔍 check_conflicts_only - Iniciando verificação:")
        self.logger.print(f"   motorist_id: {motorist_id}")
        self.logger.print(f"   truck_id: {truck_id}")
        self.logger.print(f"   len(data_json): {len(data_json)}")

        for linha in data_json:
            date_key = linha.get('Data')
            self.logger.print(f"🔍 Verificando data: {date_key}")
            
            # Verifica TODOS os conflitos
            conflicts_found = []
            
            # Verifica se o caminhão já tem jornada de outro motorista nesta data (se truck_id fornecido)
            if truck_id:
                truck_conflict = self.exec_query(
                    "SELECT motorist_id FROM perm_data_fecham WHERE data=? AND truck_id=? AND motorist_id!=?",
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
                    self.logger.print(f"🚫 Conflito de caminhão encontrado: {date_key}")
            
            # Verifica se o motorista já tem qualquer registro (jornada) nesta data
            motorist_journey_conflict = self.exec_query(
                "SELECT truck_id FROM perm_data_fecham WHERE data=? AND motorist_id=?",
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
                self.logger.print(f"🚫 Conflito de jornada do motorista encontrado: {date_key}")
                
            # Verifica se o motorista já tem dayoff registrado nesta data
            motorist_dayoff_conflict = self.exec_query(
                "SELECT motivo FROM dayoff_fecham WHERE data=? AND motorist_id=?",
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
                self.logger.print(f"🚫 Conflito de dayoff do motorista encontrado: {date_key}")
            
            # Se há conflitos, adiciona todos os conflitos
            if conflicts_found:
                for conflict in conflicts_found:
                    conflitos.append(conflict['conflict_obj'])
                ign += 1
                self.logger.print(f"🚫 Data {date_key} tem {len(conflicts_found)} conflitos - IGNORADA")
            else:
                ins += 1
                self.logger.print(f"✅ Data {date_key} sem conflitos - OK para inserção")
                
        self.logger.print(f"🔍 check_conflicts_only - Resultado final:")
        self.logger.print(f"   conflitos: {len(conflitos)}")
        self.logger.print(f"   ins: {ins}")
        self.logger.print(f"   ign: {ign}")
        self.logger.print(f"   tem_conflitos: {bool(conflitos)}")
                
        return {'tem_conflitos': bool(conflitos), 'conflitos': conflitos,
                'registros_inseridos': ins, 'registros_ignorados': ign,
                'registros_substituidos': sub}

    def replace_data_from_json(self, tabela: List[Dict], motorist_id: int, truck_id: int):
        """Sobrescreve registros existentes chamando insert_data_from_json com replace=True."""
        return self.insert_data_from_json(tabela, motorist_id, truck_id, replace=True) 

    def get_last_update_date_for_motorist(self, motorist_id: int) -> Optional[Tuple]:
        """
        Retorna a data do registro mais recente para um dado motorista na tabela perm_data_fecham.
        A data é retornada no formato DD-MM-YYYY como está armazenada no banco.
        """
        query = """
            SELECT data FROM perm_data_fecham
            WHERE motorist_id = ?
            ORDER BY substr(data, 7, 4) DESC, substr(data, 4, 2) DESC, substr(data, 1, 2) DESC
            LIMIT 1
        """
        # Ordena pelo ano, depois mês, depois dia para garantir a data mais recente
        return self.exec_query(query, params=(motorist_id,), fetchone=True)

    def delete_perm_data(self, where_columns: list, where_values: tuple) -> int:
        """
        Exclui registros da tabela perm_data_fecham baseado nas condições fornecidas.
        
        :param where_columns: Lista de colunas para a cláusula WHERE
        :param where_values: Tupla com os valores correspondentes
        :return: Número de linhas afetadas
        """
        where_clause = ' AND '.join([f"{col}=?" for col in where_columns])
        query = f"DELETE FROM perm_data_fecham WHERE {where_clause}"
        return self.exec_query(query, params=where_values) 