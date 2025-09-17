from datetime import timedelta
try:
    import pandas as pd
except ImportError:
    print("AVISO: pandas não disponível, usando stub")
    import pandas_stub as pd
from typing import List, Iterable


def sum_work_and_non_work(events: Iterable) -> tuple:
    """
    Soma a duração total dos eventos de trabalho e não-trabalho.

    Esta função percorre uma lista de eventos, onde cada evento é uma tupla contendo:
    - Tipo de evento ('trabalho' ou outro tipo, como 'descanso', 'refeição', etc.)
    - Hora de início do evento.
    - Hora de término do evento.
    - Duração do evento (objeto timedelta).

    A função acumula a duração dos eventos de trabalho e não-trabalho separadamente e retorna
    essas somas como tuplas de objetos `timedelta`.

    Parâmetros:
    -----------
    events : Iterable
        Um iterável de eventos, onde cada evento é uma tupla com os seguintes valores:
        - event_type (str): O tipo de evento ('trabalho', 'descanso', etc.).
        - start_time (datetime): Hora de início do evento.
        - end_time (datetime): Hora de término do evento.
        - duration (timedelta): A duração do evento.

    Retorna:
    --------
    tuple
        Uma tupla com duas durações:
        - A primeira é a soma do tempo de trabalho (timedelta).
        - A segunda é a soma do tempo de não-trabalho (timedelta).
    """

    # Inicializa as durações acumuladas para trabalho e não-trabalho
    work_total = timedelta()  # Duração total de trabalho
    non_work_total = timedelta()  # Duração total de não-trabalho

    # Itera sobre os eventos fornecidos para acumular as durações
    for event in events:
        event_type, start_time, end_time, duration = event

        # Verifica se o tipo de evento é 'trabalho'
        if event_type == 'trabalho':
            work_total += duration  # Soma a duração do trabalho
        else:
            non_work_total += duration  # Soma a duração dos eventos não-trabalho

    # Retorna as durações totais como uma tupla
    return work_total, non_work_total


def split_work_into_chunks(sorted_events_with_work: List, max_work_duration_seconds=19800) -> List:
    """
    Divide os eventos de trabalho em segmentos com duração máxima definida por max_work_duration_seconds.
    Se o tempo de trabalho exceder o limite, divide o trabalho em vários segmentos.
    Os eventos intermediários (descanso, refeição, etc.) são adicionados corretamente entre os segmentos de trabalho.

    :param sorted_events_with_work: Lista de eventos ordenados com tipo, início, fim e duração.
    :param max_work_duration_seconds: Duração máxima de trabalho em segundos (ex: 5 horas e 30 minutos seria 19800 segundos).
    :return: Lista de segmentos de trabalho divididos, onde cada segmento contém eventos agrupados com duração inferior ou igual a max_work_duration_seconds.
    """

    all_segments = []  # Lista para armazenar os segmentos de trabalho
    current_work_duration = 0  # Duração total de trabalho acumulada (em segundos)
    current_group = []  # Grupo de eventos (trabalho + outros eventos)

    for event in sorted_events_with_work:
        event_type, start_time, end_time, duration = event  # Desempacota o evento

        # Verifica se o evento é de tipo 'trabalho'
        if event_type == 'trabalho':
            work_duration = duration.total_seconds()  # Duração do evento de trabalho

            # Caso a soma do tempo de trabalho ultrapasse o limite
            if current_work_duration + work_duration > max_work_duration_seconds:
                exceeding_time = (current_work_duration + work_duration) - max_work_duration_seconds

                # Divide o trabalho atual para ajustar à duração máxima permitida
                current_end_time = end_time - timedelta(seconds=exceeding_time)
                current_duration = current_end_time - start_time

                # Adiciona o trabalho até o limite de 5:30
                current_group.append(('trabalho', start_time, current_end_time, current_duration))

                # Adiciona o grupo atual com o primeiro segmento de trabalho
                all_segments.append(current_group)

                # Inicia um novo grupo para o restante do trabalho
                current_group = []
                new_start_time = current_end_time
                new_end_time = new_start_time + timedelta(seconds=exceeding_time)

                # Adiciona o restante do trabalho ao novo grupo
                current_group.append(('trabalho', new_start_time, new_end_time, timedelta(seconds=exceeding_time)))
                current_work_duration = exceeding_time  # Atualiza a duração de trabalho acumulada

            else:
                # Se o trabalho não exceder o limite, apenas adiciona ao grupo
                current_group.append(event)
                current_work_duration += work_duration  # Soma o tempo de trabalho acumulado

        else:
            # Se o evento não for do tipo 'trabalho', adiciona-o diretamente ao grupo atual
            current_group.append(event)

    # Adiciona o último grupo de eventos restantes
    all_segments.append(current_group)

    return all_segments


def split_time_delta(timedelta_value):
    """
    Divide o timedelta, pd.Timestamp ou pd.Timedelta em horas e minutos, retornando os valores como números.

    Esta função verifica o tipo de entrada, podendo ser:
    - pd.Timestamp: A data será convertida para horas e minutos a partir da "epoch" (1970-01-01).
    - pd.Timedelta: O tempo será convertido diretamente para horas e minutos.
    - datetime.timedelta: O tempo será convertido para horas e minutos diretamente.

    Parâmetros:
    -----------
    timedelta_value : pd.Timestamp | pd.Timedelta | timedelta
        O valor de tempo a ser dividido.

    Retorna:
    --------
    list
        Lista contendo dois valores inteiros: o número de horas e minutos.
    """

    # Verificar o tipo do valor fornecido e processá-lo de acordo
    if isinstance(timedelta_value, pd.Timestamp):
        # Para pd.Timestamp, calcula as horas e minutos desde a "epoch" (1970-01-01)
        return [int(timedelta_value.hour), int(timedelta_value.minute)]

    elif isinstance(timedelta_value, pd.Timedelta):
        # Para pd.Timedelta, converte para segundos e calcula as horas e minutos
        total_seconds = timedelta_value.total_seconds()

    elif isinstance(timedelta_value, timedelta):
        # Para datetime.timedelta, também converte diretamente para segundos
        total_seconds = timedelta_value.total_seconds()

    else:
        # Se o tipo não for válido, levanta um erro
        raise ValueError("O valor fornecido não é do tipo pd.Timedelta nem pd.Timestamp nem datetime.timedelta")

    # Calcular as horas e minutos a partir do total de segundos
    hours = total_seconds // 3600  # Número de horas
    minutes = (total_seconds % 3600) // 60  # Número de minutos restantes

    return [int(hours), int(minutes)]  # Retorna uma lista com horas e minutos


def get_sorted_events_with_work_periods(row):
    """
    Calcula os períodos de trabalho e outros eventos (refeição, descanso, carga/descarga)
    de um motorista, e retorna esses eventos ordenados por horário, incluindo as durações.

    Parâmetros:
    -----------
    row : pd.Series
        Linha de dados com informações sobre a jornada de trabalho, incluindo horários de
        início e fim dos eventos de refeição, descanso, carga/descarga e jornada.

    Retorna:
    --------
    list : Lista de tuplas
        Cada tupla contém o tipo do evento ('trabalho', 'refeicao', 'descanso', 'carga_descarga'),
        o horário de início, o horário de fim e a duração do evento como pd.Timedelta.
    """
    events = []  # Lista de eventos com tipo e horários de início e fim

    # Adicionar os eventos de refeição (se existirem)
    if pd.notna(row['in_refeicao']) and pd.notna(row['fim_refeicao']):
        events.append(('refeicao', row['in_refeicao'], row['fim_refeicao']))

    # Adicionar os eventos de descanso (até 8 eventos de descanso)
    for i in range(1, 9):
        in_descanso = row.get(f'in_descanso_{i}')
        fim_descanso = row.get(f'fim_descanso_{i}')
        if pd.notna(in_descanso) and pd.notna(fim_descanso):
            events.append(('descanso', in_descanso, fim_descanso))

    # Adicionar os eventos de carga/descarga (até 7 eventos de carga/descarga)
    for i in range(1, 8):
        in_car_desc = row.get(f'in_car_desc_{i}')
        fim_car_desc = row.get(f'fim_car_desc_{i}')
        if pd.notna(in_car_desc) and pd.notna(fim_car_desc):
            events.append(('carga_descarga', in_car_desc, fim_car_desc))

    # Ordenar os eventos por horário de início (ascendente)
    events_sorted = sorted(events, key=lambda x: x[1])

    # Lista para armazenar os períodos de trabalho e outros eventos
    all_events = []

    # Inicializar o tempo de trabalho antes do primeiro evento
    prev_end = row['inicio_jornada']

    # Iterar sobre os eventos ordenados para calcular os períodos de trabalho
    for event in events_sorted:
        event_start = event[1]
        event_end = event[2]

        # Se houver um intervalo entre o fim do último evento e o início do atual,
        # esse intervalo é um período de trabalho
        if event_start > prev_end:
            work_duration = event_start - prev_end
            all_events.append(('trabalho', prev_end, event_start, work_duration))

        # Adicionar o evento atual
        event_duration = event_end - event_start
        all_events.append((event[0], event_start, event_end, event_duration))

        prev_end = event_end

    # Adicionar o período de trabalho final (se houver)
    if prev_end < row['fim_jornada']:
        work_duration = row['fim_jornada'] - prev_end
        all_events.append(('trabalho', prev_end, row['fim_jornada'], work_duration))

    return all_events
