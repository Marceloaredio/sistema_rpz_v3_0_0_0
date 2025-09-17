from typing import List, Optional, Tuple


def safe_get(data, index, default=None):
    try:
        return data[index] if index < len(data) else default
    except Exception:
        return default


class User:
    def __init__(self, info: Optional[List]):
        if info is not None and len(info) >= 4:
            self.name = info[0]
            self.email = info[1]
            self.password = info[2]
            self.is_admin = bool(info[3])
            self.authorized_routes = info[4] if len(info) > 4 else '[]'
        else:
            self.name = None
            self.email = None
            self.password = None
            self.is_admin = False
            self.authorized_routes = '[]'


class Truck:
    def __init__(self, info: List[Optional[str]]):
        if info is not None and len(info) == 15:
            self.id = safe_get(info, 0)
            self.placa = safe_get(info, 1)
            self.identificacao = safe_get(info, 2)
            self.ano = safe_get(info, 3)
            self.modelo = safe_get(info, 4)
            self.vencimento_aet_dnit = safe_get(info, 5)
            self.vencimento_aet_mg = safe_get(info, 6)
            self.vencimento_aet_sp = safe_get(info, 7)
            self.vencimento_aet_go = safe_get(info, 8)
            self.vencimento_civ_cipp = safe_get(info, 9)
            self.vencimento_cronotografo = safe_get(info, 10)
            self.exercicio_crlv = safe_get(info, 11)
            self.peso_tara = safe_get(info, 12)
            self.link_documentacao = safe_get(info, 13)
            self.status = safe_get(info, 14)
        else:
            self.id = None
            self.placa = None
            self.identificacao = None
            self.ano = None
            self.modelo = None
            self.vencimento_aet_dnit = None
            self.vencimento_aet_mg = None
            self.vencimento_aet_sp = None
            self.vencimento_aet_go = None
            self.vencimento_civ_cipp = None
            self.vencimento_cronotografo = None
            self.exercicio_crlv = None
            self.peso_tara = None
            self.link_documentacao = None
            self.status = None


class Motorist:
    def __init__(self, info: List[Optional[str]]):
        if info is not None and len(info) == 37:
            self.id = safe_get(info, 0)
            self.nome = safe_get(info, 1)
            self.data_admissao = safe_get(info, 2)
            self.cpf = safe_get(info, 3)
            self.cnh = safe_get(info, 4)
            self.rg = safe_get(info, 5)
            self.codigo_sap = safe_get(info, 6)
            self.operacao = safe_get(info, 7)
            self.ctps = safe_get(info, 8)
            self.serie = safe_get(info, 9)
            self.data_nascimento = safe_get(info, 10)
            self.primeira_cnh = safe_get(info, 11)
            self.data_expedicao = safe_get(info, 12)
            self.vencimento_cnh = safe_get(info, 13)
            self.done_mopp = safe_get(info, 14)
            self.vencimento_mopp = safe_get(info, 15)
            self.done_toxicologico_clt = safe_get(info, 16)
            self.vencimento_toxicologico_clt = safe_get(info, 17)
            self.done_aso_semestral = safe_get(info, 18)
            self.vencimento_aso_semestral = safe_get(info, 19)
            self.done_aso_periodico = safe_get(info, 20)
            self.vencimento_aso_periodico = safe_get(info, 21)
            self.done_buonny = safe_get(info, 22)
            self.vencimento_buonny = safe_get(info, 23)
            self.telefone = safe_get(info, 24)
            self.endereco = safe_get(info, 25)
            self.filiacao = safe_get(info, 26)
            self.estado_civil = safe_get(info, 27)
            self.filhos = safe_get(info, 28)
            self.cargo = safe_get(info, 29)
            self.empresa = safe_get(info, 30)
            self.status = safe_get(info, 31)
            self.conf_jornada = safe_get(info, 32)
            self.conf_fecham = safe_get(info, 33)
            self.done_toxicologico_cnh = safe_get(info, 34)
            self.vencimento_toxicologico_cnh = safe_get(info, 35)
            self.email = safe_get(info, 36)
        else:
            self.id = None
            self.nome = None
            self.data_admissao = None
            self.cpf = None
            self.cnh = None
            self.rg = None
            self.codigo_sap = None
            self.operacao = None
            self.ctps = None
            self.serie = None
            self.data_nascimento = None
            self.primeira_cnh = None
            self.data_expedicao = None
            self.vencimento_cnh = None
            self.done_mopp = None
            self.vencimento_mopp = None
            self.done_toxicologico_clt = None
            self.vencimento_toxicologico_clt = None
            self.done_aso_semestral = None
            self.vencimento_aso_semestral = None
            self.done_aso_periodico = None
            self.vencimento_aso_periodico = None
            self.done_buonny = None
            self.vencimento_buonny = None
            self.telefone = None
            self.endereco = None
            self.filiacao = None
            self.estado_civil = None
            self.filhos = None
            self.cargo = None
            self.empresa = None
            self.status = None
            self.conf_jornada = None
            self.conf_fecham = None
            self.done_toxicologico_cnh = None
            self.vencimento_toxicologico_cnh = None
            self.email = None


class TrackData:
    def __init__(self, info: List[Optional[str]]):
        if info is not None and len(info) >= 9:
            self.placa = safe_get(info, 0)
            self.data_iso = safe_get(info, 1)
            self.vel = float(info[2]) if info[2] is not None else None
            self.latitude = float(info[3]) if info[3] is not None else None
            self.longitude = float(info[4]) if info[4] is not None else None
            self.uf = safe_get(info, 5)
            self.cidade = safe_get(info, 6)
            self.rua = safe_get(info, 7)
            self.ignicao = info[8] if info[8] in ['Ligada', 'Desligada'] else None
        else:
            self.placa = None
            self.data_iso = None
            self.vel = None
            self.latitude = None
            self.longitude = None
            self.uf = None
            self.cidade = None
            self.rua = None
            self.ignicao = None



class Event:
    def __init__(self, start: str, end: str):
        self.start = start
        self.end = end

    def __repr__(self):
        return f"Event(start={self.start}, end={self.end})"


class PermData:
    def __init__(self, data: tuple):
        """
        Inicializa a classe com uma tupla contendo os dados da tabela perm_data.

        :param data: Tupla contendo os dados retornados da tabela perm_data.
        :type data: tuple
        """
        # Atributos simples com base nos índices da tupla
        self.motorista = data[0]  # Índice 0: motorista
        self.placa = data[1]  # Índice 1: placa
        self.data = data[2]  # Índice 2: data
        self.dia_da_semana = data[3]  # Índice 3: dia_da_semana
        self.observacao = data[8]  # Índice 8: observacao
        self.tempo_refeicao = data[9]  # Índice 9: tempo_refeicao
        self.intersticio = data[10]  # Índice 10: intersticio
        self.tempo_intervalo = data[11]  # Índice 11: tempo_intervalo
        self.tempo_carga_descarga = data[12]  # Índice 12: tempo_carga_descarga
        self.jornada_total = data[13]  # Índice 13: jornada_total
        self.tempo_direcao = data[14]  # Índice 14: tempo_direcao
        self.direcao_sem_pausa = data[15]  # Índice 15: direcao_sem_pausa

        self.jornada = self._parse_event(data, prefix="inicio_jornada", suffix="fim_jornada")

        # Refeição (um único evento)
        self.refeicao = self._parse_event(data, prefix="in_refeicao", suffix="fim_refeicao")

        # Descansos (lista de eventos)
        self.descansos = self._parse_events(data, prefix="in_descanso", suffix="fim_descanso")

        # Carga/Descarga (lista de eventos)
        self.cargas_descargas = self._parse_events(data, prefix="in_car_desc", suffix="fim_car_desc")

    def _parse_event(self, data: tuple, prefix: str, suffix: str) -> Optional[Event]:
        """
        Parse um evento único de refeição a partir dos dados.

        :param data: Tupla com os dados.
        :param prefix: Prefixo da chave (in_refeicao).
        :param suffix: Sufixo da chave (fim_refeicao).
        :return: Objeto Event ou None se não houver dados.
        """
        start_index = self._get_event_index(prefix)
        end_index = self._get_event_index(suffix)

        start_value = data[start_index] if start_index is not None else None
        end_value = data[end_index] if end_index is not None else None
        if start_value or end_value:  # Se qualquer valor for preenchido, criamos o evento
            return Event(start=start_value, end=end_value)
        return None

    def _parse_events(self, data: tuple, prefix: str, suffix: str) -> List[Event]:
        """
        Parse eventos de descanso ou carga/descarga a partir dos dados.

        :param data: Tupla com os dados.
        :param prefix: Prefixo da chave (in_descanso ou in_car_desc).
        :param suffix: Sufixo da chave (fim_descanso ou fim_car_desc).
        :return: Lista de objetos Event.
        """
        events = []
        for i in range(1, 9):  # Temos 8 eventos possíveis (in_descanso_1, fim_descanso_1, etc.)
            start_index = self._get_event_index(f"{prefix}_{i}")
            end_index = self._get_event_index(f"{suffix}_{i}")
            start_value = data[start_index] if start_index is not None else None
            end_value = data[end_index] if end_index is not None else None
            if start_value or end_value:  # Se qualquer valor for preenchido, criamos o evento
                events.append(Event(start=start_value, end=end_value))
        return events

    def _get_event_index(self, event_name: str) -> Optional[int]:
        """
        Obtém o índice da tupla correspondente ao nome do evento.

        :param event_name: Nome do evento (ex: 'inicio_jornada', 'fim_jornada', etc.)
        :return: Índice do evento ou None se não encontrado.
        """
        event_indices = {
            'inicio_jornada': 4, 'fim_jornada': 7,
            'in_refeicao': 5, 'fim_refeicao': 6,
            'in_descanso_1': 16, 'fim_descanso_1': 17,
            'in_descanso_2': 18, 'fim_descanso_2': 19,
            'in_descanso_3': 20, 'fim_descanso_3': 21,
            'in_descanso_4': 22, 'fim_descanso_4': 23,
            'in_descanso_5': 24, 'fim_descanso_5': 25,
            'in_descanso_6': 26, 'fim_descanso_6': 27,
            'in_descanso_7': 28, 'fim_descanso_7': 29,
            'in_descanso_8': 30, 'fim_descanso_8': 31,
            'in_car_desc_1': 32, 'fim_car_desc_1': 33,
            'in_car_desc_2': 34, 'fim_car_desc_2': 35,
            'in_car_desc_3': 36, 'fim_car_desc_3': 37,
            'in_car_desc_4': 38, 'fim_car_desc_4': 39,
            'in_car_desc_5': 40, 'fim_car_desc_5': 41,
            'in_car_desc_6': 42, 'fim_car_desc_6': 43,
            'in_car_desc_7': 44, 'fim_car_desc_7': 45
        }

        return event_indices.get(event_name)

    def __repr__(self):
        return (f"PermData(motorista={self.motorista}, placa={self.placa}, data={self.data}, "
                f"dia_da_semana={self.dia_da_semana}, inicio_jornada={self.jornada.start}, "
                f"in_refeicao={self.refeicao.start if self.refeicao else None}, "
                f"fim_refeicao={self.refeicao.end if self.refeicao else None}, "
                f"fim_jornada={self.jornada.end if self.jornada else None}, "
                f"observacao={self.observacao}, tempo_refeicao={self.tempo_refeicao}, "
                f"intersticio={self.intersticio}, tempo_intervalo={self.tempo_intervalo}, "
                f"tempo_carga_descarga={self.tempo_carga_descarga}, jornada_total={self.jornada_total}, "
                f"tempo_direcao={self.tempo_direcao}, direcao_sem_pausa={self.direcao_sem_pausa}, "
                f"refeicao={self.refeicao}, descansos={self.descansos}, cargas_descargas={self.cargas_descargas})")


class Company:
    def __init__(self, info: List[Optional[str]]):
        if info is not None and len(info) >= 3:
            self.id = safe_get(info, 0)
            self.enterprise = safe_get(info, 1)
            self.cnpj = safe_get(info, 2)
        else:
            self.id = None
            self.enterprise = None
            self.cnpj = None

    



