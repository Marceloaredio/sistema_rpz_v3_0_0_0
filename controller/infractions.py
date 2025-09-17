try:
    import pandas as pd
except ImportError:
    print("AVISO: pandas não disponível, usando stub")
    import pandas_stub as pd
from datetime import timedelta

from controller.infractions_data import sum_work_and_non_work, split_work_into_chunks, split_time_delta
from controller.utils import CustomLogger
from global_vars import *

logger = CustomLogger("INFRACTIONS", debug=DEBUG)


def get_snack_infraction(row):
    """
    Verifica se houve infração relacionada ao tempo de refeição.
    - Se o tempo de refeição for inferior ao tempo mínimo exigido, marca outra infração.

    Parâmetros:
    -----------
    row : pd.Series
        Linha do dataframe que contém os dados de refeição (colunas 'in_refeicao' e 'fim_refeicao').

    Retorna:
    --------
    dict : dicionário com a infração, a data da infração, o horário de início e a duração da refeição.
    """
    return_dict = {'infraction_type': None,
                   'date': row['data'].date().strftime('%d-%m-%Y'),
                   'time': None,
                   'duration': None}

    # Só verifica se tem horário de início e fim da refeição
    if (not pd.isna(row.get('in_refeicao')) and not pd.isna(row.get('fim_refeicao')) and 
        row.get('in_refeicao') and row.get('fim_refeicao')):

        # Calcula quanto tempo durou a refeição
        snack_time_delta = row['fim_refeicao'] - row['in_refeicao']
        snack_hours, snack_minutes = split_time_delta(snack_time_delta)

        # Pega o horário que começou a refeição
        snack_start_hours, snack_start_minutes = split_time_delta(row['in_refeicao'])

        # Se o tempo de refeição foi menor que o mínimo, marca infração
        if snack_time_delta.total_seconds() < TEMPO_ALMOCO:
            return_dict['infraction_type'] = 2  # Infração 2: Tempo de refeição abaixo do mínimo exigido
            return_dict['time'] = f"{snack_start_hours:02}:{snack_start_minutes:02}"
            return_dict['duration'] = f"{snack_hours:02}:{snack_minutes:02}"

        return return_dict


def get_daily_worktime_infraction(row):
    """
    Verifica se a jornada de trabalho diária ultrapassou o limite de tempo permitido.

    Parâmetros:
    -----------
    row : pd.Series
        Linha do DataFrame que contém as informações da jornada de trabalho (colunas 'inicio_jornada' e 'fim_jornada').

    Retorna:
    --------
    dict : Dicionário com a infração, o horário de término da jornada e a duração da jornada.
    """
    return_dict = {'infraction_type': None,
                   'date': None,
                   'time': None,
                   'duration': None}

    # Calcula quanto tempo durou a jornada toda
    daily_worked_time_delta = row['fim_jornada'] - row['inicio_jornada']

    # Se a jornada passou do limite diário, marca infração
    if daily_worked_time_delta.total_seconds() > TEMPO_TRABALHO_DIARIO:
        # Converte a duração da jornada para horas e minutos
        daily_worked_time_hours, daily_worked_time_minutes = split_time_delta(daily_worked_time_delta)

        # Pega o horário que terminou a jornada
        track_end_hour, track_end_minute = split_time_delta(row['fim_jornada'])

        # Marca a infração
        return_dict['infraction_type'] = 3
        return_dict['time'] = f"{track_end_hour:02}:{track_end_minute:02}"
        return_dict['duration'] = f"{daily_worked_time_hours:02}:{daily_worked_time_minutes:02}"
        return_dict['date'] = row['data'].date().strftime('%d-%m-%Y')

    return return_dict


def get_interstice_infraction(row):
    """
    Verifica se a diferença de tempo entre duas jornadas (interstício) é inferior ao mínimo permitido.

    Parâmetros:
    -----------
    row : pd.Series
        Linha do DataFrame com informações da jornada de trabalho atual.
    prev_row : pd.Series, opcional
        Linha do DataFrame com informações da jornada de trabalho anterior.

    Retorna:
    --------
    dict : Dicionário com a infração, o horário do início da jornada e a duração do interstício.
    """
    return_dict = {'infraction_type': None,
                   'date': None,
                   'time': None,
                   'duration': None}

    interstice = row['intersticio']
    
    # Verificar se o interstício é válido
    if pd.isna(interstice) or not interstice or interstice == '':
        return return_dict
    
    try:
        hours, minutes = map(int, interstice.split(":"))
    except (ValueError, AttributeError):
        # Se não conseguir converter, retorna sem infração
        return return_dict

    interstice_delta = timedelta(hours=hours, minutes=minutes)

    # Se não tem interstício, não tem o que verificar
    if interstice_delta.total_seconds() == 0:
        return return_dict

    # Pega o horário que começou a jornada atual
    track_start_hour, track_start_minute = split_time_delta(row['inicio_jornada'])

    # Se o intervalo entre jornadas foi menor que o mínimo, marca infração
    if interstice_delta.total_seconds() < TEMPO_INTERSTICIO:
        return_dict['infraction_type'] = 4
        return_dict['time'] = f'{track_start_hour:02}:{track_start_minute:02}'
        return_dict['duration'] = f'{hours:02}:{minutes:02}'
        return_dict['date'] = row['data'].date().strftime('%d-%m-%Y')

    return return_dict


def get_rest_between_work_infractions(row: pd.Series) -> list:
    """
    Verifica infrações relacionadas ao descanso entre períodos de direção.
    
    A função acumula o tempo de direção e soma os descansos intermediários.
    Quando o tempo acumulado de direção atinge o máximo permitido (mesmo que seja
    no meio de um período), verifica se o descanso acumulado é suficiente.
    Um período de direção pode ser dividido em dois se necessário.

    Parâmetros:
    -----------
    row : pd.Series
        Linha do DataFrame que contém os eventos ordenados (sorted_events).

    Retorna:
    --------
    list : Lista de infrações encontradas.
    """
    infractions_list = []
    events = row.get('sorted_events', [])
    
    # Debug: Log dos eventos
    logger.print(f"DEBUG: Data {row['data'].date().strftime('%d-%m-%Y')} - Eventos: {events}")
    
    if not events:
        logger.print(f"DEBUG: Nenhum evento encontrado para a data {row['data'].date().strftime('%d-%m-%Y')}")
        return infractions_list

    accumulated_work = timedelta()
    accumulated_rest = timedelta()
    current_work_start = None
    remaining_work = None

    for event in events:
        event_type, start_time, end_time, duration = event
        
        # Debug: Log de cada evento
        logger.print(f"DEBUG: Processando evento - Tipo: {event_type}, Início: {start_time}, Fim: {end_time}, Duração: {duration}")

        if event_type == 'trabalho':
            if remaining_work:
                # Continua o trabalho anterior que foi dividido + novo evento de trabalho
                remaining_time = remaining_work
                work_time_left = remaining_work + duration
                remaining_work = None
                logger.print(f"DEBUG: Continuando trabalho anterior + novo evento - Duração total: {work_time_left} (restante: {remaining_time} + atual: {duration})")
            else:
                # Novo período de trabalho
                current_work_start = start_time
                work_time_left = duration

            while work_time_left.total_seconds() > 0:
                # Calcula quanto tempo falta para atingir o máximo permitido
                time_until_max = timedelta(seconds=TEMPO_MAX_DIRECAO) - accumulated_work
                
                # Debug: Log dos cálculos
                logger.print(f"DEBUG: Trabalho acumulado: {accumulated_work}, Tempo até máximo: {time_until_max}, Trabalho restante: {work_time_left}")

                if work_time_left <= time_until_max:
                    # Se o tempo restante não ultrapassa o limite, adiciona todo
                    accumulated_work += work_time_left
                    work_time_left = timedelta()
                    logger.print(f"DEBUG: Adicionando todo o trabalho restante. Novo acumulado: {accumulated_work}")
                else:
                    # Se ultrapassa, divide o período
                    accumulated_work += time_until_max # Adiciona o tempo até o máximo permitido (5:30)
                    work_time_left -= time_until_max # Subtrai o tempo até o máximo permitido do tempo restante
                    
                    # Debug: Log da divisão
                    logger.print(f"DEBUG: Dividindo período. Atingiu 5:30, Restante: {work_time_left}")

                    # Verifica se houve infração (descanso insuficiente)
                    logger.print(f"DEBUG: Verificando infração - Descanso acumulado: {accumulated_rest} ({accumulated_rest.total_seconds()}s), Mínimo: {TEMPO_MIN_DESCANSO}s")
                    
                    if accumulated_rest.total_seconds() < TEMPO_MIN_DESCANSO:
                        hours, minutes = split_time_delta(accumulated_rest)
                        infraction_time = (current_work_start + time_until_max).strftime('%H:%M') if isinstance(current_work_start, pd.Timestamp) else str(current_work_start)
                        
                        infraction = {
                            'infraction_type': 5,
                            'date': row['data'].date().strftime('%d-%m-%Y'),
                            'time': infraction_time,
                            'duration': f'{hours:02}:{minutes:02}'
                        }
                        
                        infractions_list.append(infraction)
                        logger.print(f"DEBUG: INFRAÇÃO DETECTADA: {infraction}")

                    # SEMPRE zera contadores após verificação e continua com tempo restante
                    accumulated_work = timedelta()
                    accumulated_rest = timedelta()
                    current_work_start = start_time + time_until_max if isinstance(start_time, pd.Timestamp) else None
                    logger.print(f"DEBUG: Zerando contadores. Continuando com trabalho restante: {work_time_left}")
                    
                    # Continue no loop para processar o tempo restante (pode gerar outra infração)

        else:  # Eventos de descanso
            if accumulated_work.total_seconds() > 0:
                # Só acumula descanso se houver trabalho anterior
                accumulated_rest += duration
                logger.print(f"DEBUG: Acumulando descanso após trabalho. Novo descanso acumulado: {accumulated_rest}")
            else:
                # Se não houver trabalho acumulado, este descanso inicia um novo período
                accumulated_rest = duration
                logger.print(f"DEBUG: Iniciando novo período com descanso: {accumulated_rest}")

    # Verifica uma última vez ao final da jornada
    logger.print(f"DEBUG: Verificação final - Trabalho acumulado: {accumulated_work} ({accumulated_work.total_seconds()}s), Descanso acumulado: {accumulated_rest} ({accumulated_rest.total_seconds()}s)")
    
    if accumulated_work.total_seconds() >= TEMPO_MAX_DIRECAO and accumulated_rest.total_seconds() < TEMPO_MIN_DESCANSO:
        hours, minutes = split_time_delta(accumulated_rest)
        last_time = events[-1][2].strftime('%H:%M') if isinstance(events[-1][2], pd.Timestamp) else events[-1][2]
        
        infraction = {
            'infraction_type': 5,
            'date': row['data'].date().strftime('%d-%m-%Y'),
            'time': last_time,
            'duration': f'{hours:02}:{minutes:02}'
        }
        
        infractions_list.append(infraction)
        logger.print(f"DEBUG: INFRAÇÃO FINAL DETECTADA: {infraction}")

    logger.print(f"DEBUG: Total de infrações encontradas: {len(infractions_list)}")
    return infractions_list


def convert_json_to_df(table_records, motorist_id, truck_id):
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
    df = None

    for record in table_records:

        # Extração dos campos do JSON
        data = record["Data"]
        dia_da_semana = record["Dia da Semana"]
        inicio_jornada = record["Início Jornada"]
        in_refeicao = record["In. Refeição"]
        fim_refeicao = record["Fim Refeição"]
        fim_jornada = record["Fim de Jornada"]
        observacao = record["Observação"]

        if observacao or not inicio_jornada:
            continue

        tempo_refeicao = record["Tempo Refeição"]
        intersticio = record["Interstício"]
        tempo_intervalo = record["Tempo Intervalo"]
        tempo_carga_descarga = record["Tempo Carga/Descarga"]
        jornada_total = record["Jornada Total"]
        tempo_direcao = record["Tempo Direção"]
        direcao_sem_pausa = record["Direção sem Pausa"]

        # Descanso
        descanso_1 = (record["In. Descanso 1"], record["Fim Descanso 1"])
        descanso_2 = (record["In. Descanso 2"], record["Fim Descanso 2"])
        descanso_3 = (record["In. Descanso 3"], record["Fim Descanso 3"])
        descanso_4 = (record["In. Descanso 4"], record["Fim Descanso 4"])
        descanso_5 = (record["In. Descanso 5"], record["Fim Descanso 5"])
        descanso_6 = (record["In. Descanso 6"], record["Fim Descanso 6"])
        descanso_7 = (record["In. Descanso 7"], record["Fim Descanso 7"])
        descanso_8 = (record["In. Descanso 8"], record["Fim Descanso 8"])

        # Carga/Descarga
        car_desc_1 = (record["In. Car/Desc 1"], record["Fim Car/Desc 1"])
        car_desc_2 = (record["In. Car/Desc 2"], record["Fim Car/Desc 2"])
        car_desc_3 = (record["In. Car/Desc 3"], record["Fim Car/Desc 3"])
        car_desc_4 = (record["In. Car/Desc 4"], record["Fim Car/Desc 4"])
        car_desc_5 = (record["In. Car/Desc 5"], record["Fim Car/Desc 5"])
        car_desc_6 = (record["In. Car/Desc 6"], record["Fim Car/Desc 6"])
        car_desc_7 = (record["In. Car/Desc 7"], record["Fim Car/Desc 7"])

        data_dict = {
            'motorist_id': motorist_id,
            'truck_id': truck_id,
            'data': data,
            'dia_da_semana': dia_da_semana,
            'inicio_jornada': inicio_jornada,
            'in_refeicao': in_refeicao,
            'fim_refeicao': fim_refeicao,
            'fim_jornada': fim_jornada,
            'observacao': observacao,
            'tempo_refeicao': tempo_refeicao,
            'intersticio': intersticio,
            'tempo_intervalo': tempo_intervalo,
            'tempo_carga_descarga': tempo_carga_descarga,
            'jornada_total': jornada_total,
            'tempo_direcao': tempo_direcao,
            'direcao_sem_pausa': direcao_sem_pausa,
            'in_descanso_1': descanso_1[0], 'fim_descanso_1': descanso_1[1],
            'in_descanso_2': descanso_2[0], 'fim_descanso_2': descanso_2[1],
            'in_descanso_3': descanso_3[0], 'fim_descanso_3': descanso_3[1],
            'in_descanso_4': descanso_4[0], 'fim_descanso_4': descanso_4[1],
            'in_descanso_5': descanso_5[0], 'fim_descanso_5': descanso_5[1],
            'in_descanso_6': descanso_6[0], 'fim_descanso_6': descanso_6[1],
            'in_descanso_7': descanso_7[0], 'fim_descanso_7': descanso_7[1],
            'in_descanso_8': descanso_8[0], 'fim_descanso_8': descanso_8[1],
            'in_car_desc_1': car_desc_1[0], 'fim_car_desc_1': car_desc_1[1],
            'in_car_desc_2': car_desc_2[0], 'fim_car_desc_2': car_desc_2[1],
            'in_car_desc_3': car_desc_3[0], 'fim_car_desc_3': car_desc_3[1],
            'in_car_desc_4': car_desc_4[0], 'fim_car_desc_4': car_desc_4[1],
            'in_car_desc_5': car_desc_5[0], 'fim_car_desc_5': car_desc_5[1],
            'in_car_desc_6': car_desc_6[0], 'fim_car_desc_6': car_desc_6[1],
            'in_car_desc_7': car_desc_7[0], 'fim_car_desc_7': car_desc_7[1]
        }
        new_row_df = pd.DataFrame([data_dict])

        for col in time_columns:
            if col in new_row_df.columns:
                # Combinando as colunas 'data' e 'col' diretamente e convertendo para datetime
                new_row_df[col] = pd.to_datetime(new_row_df['data'].astype(str) + ' ' + new_row_df[col].astype(str),
                                                 format='%d-%m-%Y %H:%M',
                                                 errors='coerce')
        new_row_df['data'] = pd.to_datetime(new_row_df['data'], format='%d-%m-%Y')

        if new_row_df.empty:
            continue

        if df is None:
            df = new_row_df
        else:
            df = pd.concat([df, new_row_df], ignore_index=True)

    if df is not None and not df.empty:
        df = df.drop_duplicates(subset=['data'])
    return df


def compute_infractions(df):
    """
    Computa todas as infrações com base nos dados fornecidos no DataFrame.

    Verifica e registra infrações de acordo com as condições fornecidas para:
    - Tempo de trabalho diário
    - Tempo de descanso entre os trabalhos
    - Tempo de interstício
    - Descanso semanal e dias consecutivos trabalhados

    Tipos de infração:
    ------------------
    2. **Tempo insuficiente de refeição**: Se o tempo da refeição for inferior ao mínimo exigido.
    3. **Trabalho diário total maior que o permitido**: Caso o tempo de trabalho diário exceda o limite máximo de horas
    trabalhadas (incluindo descanso e refeições).
    4. **Tempo de interstício insuficiente**: Se o tempo de descanso entre jornadas de trabalho (interstício) for
    inferior ao mínimo exigido.
    5. **Sem descanso o suficiente a cada X tempo de direção**: Caso o motorista não tenha descanso suficiente após um
    tempo de direção, sendo o descanso podendo ser fragmentado.
    6. **Máximo de dias consecutivos trabalhados ultrapassado**: Caso o motorista ultrapasse o limite de dias
    consecutivos trabalhados.
    7. **Máximo de horas semanais trabalhadas ultrapassada**: Caso o motorista ultrapasse o limite de horas semanais
    trabalhadas.
    8. **Mínimo de descanso semanal não atingido**: Caso o motorista não tenha o mínimo de descanso semanal necessário .

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados dos motoristas com as colunas:
        - 'fim_jornada'
        - 'inicio_jornada'
        - 'in_refeicao'
        - 'fim_refeicao'
        - 'data', entre outros.

    Retorna:
    --------
    infractions : list
        Lista de dicionários contendo informações sobre as infrações encontradas.
    """
    infractions = []
    dias_consecutivos_trabalhados = 0
    horas_trabalhadas_semanais_delta = timedelta(days=0)

    for i in range(df.shape[0]):
        row = df.iloc[i, :]
        print(row)
        horas_trabalhadas_delta = row['fim_jornada'] - row['inicio_jornada']

        # Quebra os tempos de início e fim em horas e minutos
        track_end_hours, track_end_minutes = split_time_delta(row['fim_jornada'])
        track_start_hours, track_start_minutes = split_time_delta(row['inicio_jornada'])

        # Verifica infrações de refeição, trabalho e descanso
        snack_infraction = get_snack_infraction(row)
        infractions.append(snack_infraction)

        daily_worktime_infraction = get_daily_worktime_infraction(row)
        infractions.append(daily_worktime_infraction)

        rest_between_work_infractions = get_rest_between_work_infractions(row)
        infractions.extend(rest_between_work_infractions)

        if i > 0:
            prev_row = df.iloc[i - 1]

            interstice_infraction = get_interstice_infraction(row)
            infractions.append(interstice_infraction)

            interstice = row['intersticio']

            hours, minutes = map(int, interstice.split(":"))

            interstice_delta = timedelta(hours=hours, minutes=minutes)

            # Verificar se a data anterior está ausente ou se o intervalo entre os dias é superior a 1
            # if interstice_delta.total_seconds() > 24 * 60 * 60
            # Trocar o if abaixo pelo comentário acima, se quiser fazer a verificação pelo interstício.
            if pd.isna(prev_row['data']) or (row['data'] - prev_row['data']).days > 1:
                dias_consecutivos_trabalhados = 1  # Reinicia a contagem dos dias consecutivos trabalhados
                horas_trabalhadas_semanais_delta = horas_trabalhadas_delta  # Reinicia a contagem das horas semanais
                horas_descanso_semanal_delta = interstice_delta  # Descanso semanal baseado no interstício

                weekly_rest_hours, weekly_rest_minutes = split_time_delta(horas_descanso_semanal_delta)

                # Se o descanso semanal for inferior ao mínimo, registra uma infração
                if horas_descanso_semanal_delta.total_seconds() < MIN_DESCANSO_SEMANAL:
                    infractions.append({
                        'infraction_type': 8,
                        'date': row['data'].date().strftime('%d-%m-%Y'),
                        'time': f"{track_start_hours:02}:{track_start_minutes:02}",
                        'duration': f"{weekly_rest_hours:02}:{weekly_rest_minutes:02}"
                    })

            else:
                # Se ainda estiver dentro dos dias consecutivos trabalhados, aumenta o contador
                dias_consecutivos_trabalhados += 1

                # Se o limite de dias consecutivos for excedido, registra uma infração
                if dias_consecutivos_trabalhados > MAX_DIAS_CONSECUTIVOS_TRABALHADOS:
                    infractions.append({
                        'infraction_type': 6,
                        'date': row['data'].date().strftime('%d-%m-%Y'),
                        'time': f"{track_end_hours:02}:{track_end_minutes:02}",
                        'duration': dias_consecutivos_trabalhados
                    })

                # Atualiza as horas trabalhadas durante a semana
                horas_trabalhadas_semanais_delta += horas_trabalhadas_delta

                # Verifica se as horas semanais ultrapassaram o limite
                if horas_trabalhadas_semanais_delta.total_seconds() > MAX_HORAS_SEMANAIS:
                    weekly_worked_hours, weekly_worked_minutes = split_time_delta(horas_trabalhadas_semanais_delta)
                    infractions.append({
                        'infraction_type': 7,
                        'date': row['data'].date().strftime('%d-%m-%Y'),
                        'time': f"{track_end_hours:02}:{track_end_minutes:02}",
                        'duration': f"{weekly_worked_hours:02}:{weekly_worked_minutes:02}"
                    })

    # Remove infrações nulas e infrações sem tipo definido
    infractions = [infraction for infraction in infractions if infraction and infraction.get('infraction_type') is not None]

    # Adicionando descrição
    for infraction in infractions:
        infraction_type = infraction.get('infraction_type')
        infraction['infraction_desc'] = INFRACTION_DICT.get(infraction_type)

    return infractions



