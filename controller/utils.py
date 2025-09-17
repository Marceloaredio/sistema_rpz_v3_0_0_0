import logging
import os
import random
import string
from datetime import datetime, timedelta


def generate_code():
    """
    Gera código aleatório de 10 digitos para rastreamento de logs.

    Esta função gera um código aleatório com 10 caracteres, utilizando letras (maiúsculas e minúsculas)
    e números. Esse código pode ser usado para rastrear ou identificar logs de forma única.

    :return: Código aleatório de 10 caracteres.
    :rtype: str
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


class CustomLogger:
    def __init__(self, source, debug=False):
        """
        Cria e configura um logger com arquivos de log separados para informações gerais e erros.

        O logger criado possui:
        - Um handler para registrar mensagens de nível INFO apenas em 'logs/{source}_info.log'.
        - Um handler para registrar mensagens de nível ERROR apenas em 'logs/{source}_error.log'.
        - Um handler opcional para exibir mensagens de nível DEBUG no terminal.
        - Remove e fecha os handlers existentes antes de adicionar novos.

        :param source: Nome base dos arquivos de log.
        :type source: str
        :param debug: Define se os logs de nível DEBUG devem ser exibidos no terminal.
        :type debug: bool
        :return: Um objeto logger configurado.
        :rtype: logging.Logger
        """
        self.logger = logging.getLogger(source)
        self.debug = debug

        # Remove handlers antigos e fecha eles direito
        while self.logger.hasHandlers():
            handler = self.logger.handlers[0]
            handler.close()
            self.logger.removeHandler(handler)

        self.logger.setLevel(logging.DEBUG)

        # Cria a pasta 'logs' se não existir
        os.makedirs("logs", exist_ok=True)

        # Função auxiliar para criar handlers
        def create_handler(filename, level):
            handler = logging.FileHandler(filename, mode="a")
            handler.setLevel(level)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            return handler

        # Cria handlers separados pra info e erro
        info_handler = create_handler(f"logs/{source}_info.log", logging.INFO)
        error_handler = create_handler(f"logs/{source}_error.log", logging.ERROR)

        # Mostra erros no console também
        error_console_handler = logging.StreamHandler()
        error_console_handler.setLevel(logging.ERROR)
        error_console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(error_console_handler)

        # Filtro pra garantir que só INFO vai pro handler de INFO
        class InfoFilter(logging.Filter):
            def filter(self, record):
                return logging.INFO <= record.levelno < logging.ERROR  # Só INFO e WARNING

        info_handler.addFilter(InfoFilter())  # Aplica o filtro no handler de INFO

        # Adiciona os handlers no logger
        self.logger.addHandler(info_handler)
        self.logger.addHandler(error_handler)

        # Se debug estiver ligado, mostra DEBUG no terminal
        if debug:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)  # Mostra DEBUG no terminal
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(console_handler)

    def register_log(self, info_msg: str, error_msg: str = None):
        """
        Registra uma mensagem de log com nível INFO e, se fornecido, uma mensagem de erro com nível ERROR.

        Se uma mensagem de erro for fornecida, um código de erro será gerado e incluído na mensagem de informação.
        A mensagem de erro será registrada no log de erros, juntamente com o código gerado.

        :param info_msg: A mensagem de log a ser registrada com nível INFO.
        :type info_msg: str
        :param error_msg: A mensagem de erro a ser registrada com nível ERROR (opcional).
        :type error_msg: str, opcional
        :return: None
        :rtype: None
        """
        if error_msg:
            error_code = generate_code()
            info_msg = "[ERRO] " + info_msg + f" Busque a causa do erro pelo código {error_code} no log de erros."
            self.logger.error(f"Código de erro: {error_code} - {error_msg}")

        # Não registra logs de consulta SELECT
        if 'SELECT' not in info_msg:
            self.logger.info(info_msg)

    def print(self, debug_msg):
        """
        Registra uma mensagem de log com nível DEBUG no console se o modo de debug estiver ativado.

        :param debug_msg: A mensagem de log a ser registrada com nível DEBUG.
        :type debug_msg: any
        :return: None
        :rtype: None
        """
        if self.debug:
            self.logger.debug(debug_msg)


def seconds_to_str_HM(segundos: float) -> str:
    """
    Converte um valor de tempo em segundos para o formato 'HH:MM'.

    Parâmetros:
    -----------
    segundos : float
        O valor do tempo em segundos que será convertido.

    Retorna:
    --------
    str
        A string formatada no formato 'HH:MM'.
    """
    # Garante que a entrada seja um valor numérico válido
    if segundos is None or segundos < 0:
        return "00:00"  # Retorna "00:00" caso o valor seja inválido

    total_minutos = int(segundos // 60)  # Calcula minutos totais
    horas = total_minutos // 60  # Calcula as horas
    minutos = total_minutos % 60  # Calcula os minutos restantes

    # Garante que o formato seja sempre 'HH:MM', com duas casas decimais para os minutos
    return f"{horas:02d}:{minutos:02d}"


def convert_date_format(date_string: str, input_format: str = '%Y-%m-%d', output_format: str = '%d-%m-%Y') -> str:
    """
    Converte uma string de data de um formato para outro.

    Parâmetros:
        date_string (str): A data como string no formato de entrada.
        input_format (str): O formato da data de entrada. O padrão é '%Y-%m-%d'.
        output_format (str): O formato desejado de saída. O padrão é '%d-%m-%Y'.

    Retorna:
        str: A data convertida para o formato de saída.
    """
    # Converte a string para um objeto datetime com base no formato de entrada
    date_object = datetime.strptime(date_string, input_format)

    # Retorna a data no formato desejado
    return date_object.strftime(output_format)


def generate_date_range(start_date, end_date):
    datas = []
    current_date = start_date
    while current_date <= end_date:
        datas.append(current_date.strftime('%d-%m-%Y'))
        current_date += timedelta(days=1)
    return datas
