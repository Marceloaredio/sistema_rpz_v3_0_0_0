from controller.utils import CustomLogger
from model.drivers.general_driver import GeneralDriver
import sqlite3
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
import unicodedata


class ParametersDriver(GeneralDriver):
    def __init__(self, logger: CustomLogger, db_path: str):
        """
        Inicializa a classe ParametersDriver.

        :param logger: Instância de um logger customizado para registrar logs.
        :param db_path: Caminho para o banco de dados.
        """
        super().__init__(logger=logger, db_path=db_path)
        self.create_tables()

    def create_tables(self):
        """
        Cria as tabelas necessárias para os parâmetros de fechamento.
        """
        self.logger.print("Criando tabelas de parâmetros de fechamento.")

        # Tabela principal de parâmetros
        query_main = '''
        CREATE TABLE IF NOT EXISTS parametros_fechamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_parametro TEXT NOT NULL UNIQUE,
            valor TEXT NOT NULL,
            descricao TEXT,
            ativo INTEGER DEFAULT 1,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.exec_query(query_main, log_success=False)

        # Tabela para critérios especiais de diária
        query_criterios = '''
        CREATE TABLE IF NOT EXISTS criterios_diaria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_filtro TEXT NOT NULL,
            valor_filtro TEXT NOT NULL,
            valor_diaria REAL NOT NULL,
            valor_ajuda_alimentacao REAL NOT NULL,
            descricao TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.exec_query(query_criterios, log_success=False)

        # Tabela para feriados regionais
        query_feriados = '''
        CREATE TABLE IF NOT EXISTS feriados_regionais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT DEFAULT 'regional',
            ano INTEGER NOT NULL DEFAULT 0,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.exec_query(query_feriados, log_success=False)

        # Verificar se já existem parâmetros antes de inserir valores padrão
        self._insert_default_values_if_needed()

        self.logger.print("Tabelas de parâmetros criadas com sucesso.")

    def _insert_default_values_if_needed(self):
        """
        Insere valores padrão nas tabelas apenas se não existirem.
        """
        # Verificar se já existem parâmetros
        query_check = "SELECT COUNT(*) FROM parametros_fechamento"
        result = self.exec_query(query_check, fetchone=True)
        
        if result and isinstance(result, (list, tuple)) and result[0] > 0:
            self.logger.print("Parâmetros já existem, pulando inserção de valores padrão.")
            return
        
        # Inserir valores padrão apenas se não existirem
        self.logger.print("Inserindo valores padrão...")
        default_params = [
            ('diaria_padrao', '90.00', 'Valor padrão da diária'),
            ('ajuda_alimentacao', '0.00', 'Valor da ajuda de alimentação')
        ]
        
        for param in default_params:
            query = '''
            INSERT OR IGNORE INTO parametros_fechamento (tipo_parametro, valor, descricao)
            VALUES (?, ?, ?)
            '''
            self.exec_query(query, params=param)

        # Inserir feriados nacionais padrão apenas se não existirem
        self._insert_national_holidays_if_needed()

    def _insert_national_holidays_if_needed(self):
        """
        Insere feriados nacionais padrão apenas se não existirem.
        """
        # Verificar se já existem feriados
        query_check = "SELECT COUNT(*) FROM feriados_regionais"
        result = self.exec_query(query_check, fetchone=True)
        
        if result and isinstance(result, (list, tuple)) and result[0] > 0:
            self.logger.print("Feriados já existem, pulando inserção de feriados padrão.")
            return
        
        # Feriados nacionais padrão (ano atual)
        current_year = datetime.now().year
        national_holidays = [
            (f'01-01-{current_year}', 'Confraternização Universal', current_year),
            (f'21-04-{current_year}', 'Tiradentes', current_year),
            (f'01-05-{current_year}', 'Dia do Trabalho', current_year),
            (f'07-09-{current_year}', 'Independência do Brasil', current_year),
            (f'12-10-{current_year}', 'Nossa Senhora Aparecida', current_year),
            (f'02-11-{current_year}', 'Finados', current_year),
            (f'15-11-{current_year}', 'Proclamação da República', current_year),
            (f'25-12-{current_year}', 'Natal', current_year)
        ]
        
        for holiday in national_holidays:
            query = '''
            INSERT INTO feriados_regionais (data, descricao, tipo, ano)
            VALUES (?, ?, 'nacional', ?)
            '''
            self.exec_query(query, params=holiday)

    def get_all_parameters(self, ano_busca: Optional[int] = None) -> Dict:
        """
        Retorna todos os parâmetros de fechamento.

        :param ano_busca: Ano para buscar feriados (opcional)
        :return: Dicionário com todos os parâmetros
        """
        self.logger.print("Buscando todos os parâmetros de fechamento.")

        # Buscar parâmetros principais
        query_params = "SELECT tipo_parametro, valor, descricao FROM parametros_fechamento"
        params_result = self.exec_query(query_params, fetchone=False)
        if params_result is not None and isinstance(params_result, int):
            params_result = []

        # Buscar critérios especiais
        query_criterios = "SELECT id, tipo_filtro, valor_filtro, valor_diaria, valor_ajuda_alimentacao, descricao, carga_horaria_especial FROM criterios_diaria"
        criterios_result = self.exec_query(query_criterios, fetchone=False)
        if criterios_result is not None and isinstance(criterios_result, int):
            criterios_result = []

        # Buscar feriados
        if ano_busca is None:
            ano_busca = datetime.now().year
        query_feriados = "SELECT id, data, descricao, tipo, ano FROM feriados_regionais WHERE ano = ? ORDER BY data"
        feriados_result = self.exec_query(query_feriados, params=(ano_busca,), fetchone=False)
        if feriados_result is not None and isinstance(feriados_result, int):
            feriados_result = []

        # Organizar dados
        parameters = {}
        if params_result:
            for param in params_result:
                if isinstance(param, (list, tuple)):
                    parameters[param[0]] = {
                        'valor': param[1],
                        'descricao': param[2]
                    }

        criterios = []
        if criterios_result:
            for criterio in criterios_result:
                if isinstance(criterio, (list, tuple)):
                    criterios.append({
                        'id': criterio[0],
                        'tipo_filtro': criterio[1],
                        'valor_filtro': criterio[2],
                        'valor_diaria': criterio[3],
                        'valor_ajuda_alimentacao': criterio[4],
                        'descricao': criterio[5],
                        'carga_horaria_especial': criterio[6] if len(criterio) > 6 else 'Padrão'
                    })

        feriados = []
        if feriados_result:
            for feriado in feriados_result:
                if isinstance(feriado, (list, tuple)):
                    feriados.append({
                        'id': feriado[0],
                        'data': feriado[1],
                        'descricao': feriado[2],
                        'tipo': feriado[3],
                        'ano': feriado[4]
                    })

        return {
            'parametros': parameters,
            'criterios': criterios,
            'feriados': feriados
        }

    def update_parameter(self, tipo_parametro: str, valor: str, descricao: Optional[str] = None) -> int:
        """
        Atualiza um parâmetro específico.

        :param tipo_parametro: Tipo do parâmetro
        :param valor: Novo valor
        :param descricao: Descrição opcional
        :return: Número de linhas afetadas
        """
        self.logger.print(f"Atualizando parâmetro {tipo_parametro} para {valor}")

        query = '''
        UPDATE parametros_fechamento 
        SET valor = ?, data_atualizacao = CURRENT_TIMESTAMP
        WHERE tipo_parametro = ?
        '''
        
        result = self.exec_query(query, params=(valor, tipo_parametro))
        return result if isinstance(result, int) else 0

    def _normalize(self, s: str) -> str:
        """
        Normaliza uma string removendo acentos e convertendo para maiúsculas.
        """
        if not s:
            return ''
        # Remove acentos e converte para maiúsculas
        s = unicodedata.normalize('NFKD', s)
        s = ''.join([c for c in s if not unicodedata.combining(c)])
        return s.upper().strip()
    
    def _validar_carga_horaria_especial(self, carga_horaria: str) -> bool:
        """
        Valida se a carga horária especial está no formato correto.
        
        :param carga_horaria: Carga horária a ser validada
        :return: True se válida, False caso contrário
        """
        if not carga_horaria:
            return False
        
        if carga_horaria == 'Padrão':
            return True
        
        # Validar formato HH:00 (apenas horas inteiras)
        import re
        pattern = r'^(0[0-9]|1[0-2]):00$'
        return bool(re.match(pattern, carga_horaria))
    
    def _validar_criterio_especial(self, valor_filtro: str) -> bool:
        """
        Verifica se um critério é especial e não pode ser excluído.
        
        :param valor_filtro: Valor do filtro a ser verificado
        :return: True se é critério especial, False caso contrário
        """
        criterios_especiais = ['GARAGEM', 'CARGA/DESCARGA']
        return valor_filtro.upper() in criterios_especiais

    def add_criterio_diaria(self, valor_filtro: str, valor_diaria: float, valor_ajuda_alimentacao: float, descricao: Optional[str] = None, carga_horaria_especial: str = 'Padrão') -> int:
        """
        Adiciona um novo critério especial para diária, sem duplicidade e normalizando o valor do filtro.
        Se já existir um critério com o mesmo filtro, retorna erro.
        """
        self.logger.print(f"[DEBUG] add_criterio_diaria chamado com: valor_filtro={valor_filtro}, valor_diaria={valor_diaria}, valor_ajuda_alimentacao={valor_ajuda_alimentacao}, descricao={descricao}, carga_horaria_especial={carga_horaria_especial}")
        
        # Validar carga horária especial
        if not self._validar_carga_horaria_especial(carga_horaria_especial):
            raise ValueError(f'Carga horária especial inválida: {carga_horaria_especial}. Use "Padrão" ou formato "HH:00" (ex: "08:00")')
        
        valor_filtro_norm = self._normalize(valor_filtro)
        self.logger.print(f"[DEBUG] valor_filtro normalizado: {valor_filtro_norm}")

        # Verificar se a tabela existe
        check_table_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='criterios_diaria'"
        table_exists = self.exec_query(check_table_query, fetchone=True)
        self.logger.print(f"[DEBUG] Tabela criterios_diaria existe: {table_exists}")

        # Verificar se já existe critério usando a função de normalização
        query_check = '''
        SELECT id, valor_filtro FROM criterios_diaria WHERE valor_filtro = ?
        '''
        result = self.exec_query(query_check, params=(valor_filtro_norm,), fetchone=True)
        self.logger.print(f"[DEBUG] Resultado da busca por duplicidade: {result}")
        if result and isinstance(result, (list, tuple)) and len(result) > 0:
            self.logger.print(f"[ERROR] Já existe um critério cadastrado com este valor de filtro! valor_filtro_norm={valor_filtro_norm}")
            raise Exception('Já existe um critério cadastrado com este valor de filtro!')

        # Se não existe, inserir novo
        query = '''
        INSERT INTO criterios_diaria (tipo_filtro, valor_filtro, valor_diaria, valor_ajuda_alimentacao, descricao, carga_horaria_especial)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        self.logger.print(f"[DEBUG] Executando query de inserção: {query}")
        descricao_safe = descricao if descricao else ''
        carga_horaria_safe = carga_horaria_especial if carga_horaria_especial else 'Padrão'
        self.logger.print(f"[DEBUG] Parâmetros de inserção: ('motivo', '{valor_filtro_norm}', {valor_diaria}, {valor_ajuda_alimentacao}, '{descricao_safe}', '{carga_horaria_safe}')")
        
        result = self.exec_query(query, params=('motivo', valor_filtro_norm, valor_diaria, valor_ajuda_alimentacao, descricao_safe, carga_horaria_safe))
        self.logger.print(f"[DEBUG] Resultado da inserção: {result} (tipo: {type(result)})")
        
        # Buscar o ID do critério recém-inserido
        search_query = "SELECT id FROM criterios_diaria WHERE valor_filtro = ? ORDER BY id DESC LIMIT 1"
        search_result = self.exec_query(search_query, params=(valor_filtro_norm,), fetchone=True)
        self.logger.print(f"[DEBUG] Busca por valor_filtro após inserção: {search_result}")
        if search_result and isinstance(search_result, (list, tuple)) and len(search_result) > 0:
            return search_result[0]
        self.logger.print(f"[ERROR] Retornando 0 - não conseguiu inserir ou buscar o ID")
        return 0

    def update_criterio_diaria(self, criterio_id: int, valor_filtro: str, valor_diaria: float, valor_ajuda_alimentacao: float, descricao: Optional[str] = None, carga_horaria_especial: str = 'Padrão') -> int:
        """
        Atualiza um critério existente.

        :param criterio_id: ID do critério
        :param valor_filtro: Valor do filtro
        :param valor_diaria: Valor da diária
        :param valor_ajuda_alimentacao: Valor da ajuda alimentação
        :param descricao: Descrição opcional
        :param carga_horaria_especial: Carga horária especial (padrão: 'Padrão')
        :return: Número de linhas afetadas
        """
        self.logger.print(f"Atualizando critério {criterio_id}")
        
        # Validar carga horária especial
        if not self._validar_carga_horaria_especial(carga_horaria_especial):
            raise ValueError(f'Carga horária especial inválida: {carga_horaria_especial}. Use "Padrão" ou formato "HH:00" (ex: "08:00")')

        query = '''
        UPDATE criterios_diaria 
        SET valor_filtro = ?, valor_diaria = ?, valor_ajuda_alimentacao = ?, descricao = ?, carga_horaria_especial = ?, data_atualizacao = CURRENT_TIMESTAMP
        WHERE id = ?
        '''
        
        result = self.exec_query(query, params=(valor_filtro, valor_diaria, valor_ajuda_alimentacao, descricao, carga_horaria_especial, criterio_id))
        return result if isinstance(result, int) else 0

    def delete_criterio_diaria(self, criterio_id: int) -> int:
        """
        Remove um critério de diária (exclusão real).
        Critérios especiais (GARAGEM, CARGA/DESCARGA) não podem ser excluídos.

        :param criterio_id: ID do critério
        :return: Número de linhas afetadas
        """
        self.logger.print(f"Removendo critério {criterio_id}")
        
        # Verificar se é um critério especial
        query_check = "SELECT valor_filtro FROM criterios_diaria WHERE id = ?"
        result_check = self.exec_query(query_check, params=(criterio_id,), fetchone=True)
        
        if result_check and isinstance(result_check, (list, tuple)) and len(result_check) > 0:
            valor_filtro = result_check[0]
            if self._validar_criterio_especial(valor_filtro):
                raise ValueError(f'Não é possível excluir o critério especial "{valor_filtro}". Este critério é fixo e não pode ser removido.')
        
        query = "DELETE FROM criterios_diaria WHERE id = ?"
        result = self.exec_query(query, params=(criterio_id,))
        return result if isinstance(result, int) else 0

    def add_feriado(self, data: str, descricao: str, tipo: str = 'regional', ano: Optional[int] = None) -> int:
        """
        Adiciona um novo feriado.

        :param data: Data no formato DD-MM-YYYY
        :param descricao: Descrição do feriado
        :param tipo: Tipo do feriado (regional ou nacional)
        :param ano: Ano do feriado
        :return: ID do feriado criado
        """
        if not ano:  # pega None, string vazia ou 0
            try:
                ano = int(data.split('-')[2])
            except:
                from datetime import datetime
                ano = datetime.now().year
        self.logger.print(f"Adicionando feriado: {data} - {descricao} - Ano: {ano}")
        query = '''
        INSERT INTO feriados_regionais (data, descricao, tipo, ano)
        VALUES (?, ?, ?, ?)
        '''
        result = self.exec_query(query, params=(data, descricao, tipo, ano))
        return result if isinstance(result, int) else 0

    def delete_feriado(self, feriado_id: int) -> int:
        """
        Remove um feriado (exclusão real).

        :param feriado_id: ID do feriado
        :return: Número de linhas afetadas
        """
        self.logger.print(f"Removendo feriado {feriado_id}")

        query = "DELETE FROM feriados_regionais WHERE id = ?"
        result = self.exec_query(query, params=(feriado_id,))
        return result if isinstance(result, int) else 0

    def is_holiday(self, data: str) -> bool:
        """
        Verifica se uma data é feriado.

        :param data: Data no formato DD-MM-YYYY
        :return: True se for feriado, False caso contrário
        """
        query = "SELECT COUNT(*) FROM feriados_regionais WHERE data = ?"
        result = self.exec_query(query, params=(data,), fetchone=True)
        
        return result is not None and isinstance(result, (list, tuple)) and len(result) > 0 and result[0] > 0

    def get_diaria_value(self, placa: Optional[str] = None) -> float:
        """
        Retorna o valor da diária baseado nos critérios especiais.

        :param placa: Placa do veículo (opcional)
        :return: Valor da diária
        """
        # Primeiro, buscar o valor padrão
        query_padrao = "SELECT valor FROM parametros_fechamento WHERE tipo_parametro = 'diaria_padrao'"
        result = self.exec_query(query_padrao, fetchone=True)
        
        if not result or not isinstance(result, (list, tuple)) or len(result) == 0:
            return 90.00  # Valor padrão se não encontrar
        
        valor_padrao = float(result[0])

        # Se não tiver placa, retorna o valor padrão
        if placa is None:
            return valor_padrao

        # Verificar se há critérios especiais para esta placa
        query_criterio = '''
        SELECT valor_diaria FROM criterios_diaria 
        WHERE valor_filtro = ?
        '''
        result = self.exec_query(query_criterio, params=(placa,), fetchone=True)
        
        if result is not None and isinstance(result, (list, tuple)) and len(result) > 0:
            return float(result[0])
        
        return valor_padrao

    def get_ajuda_alimentacao(self) -> float:
        """
        Retorna o valor da ajuda de alimentação.

        :return: Valor da ajuda de alimentação
        """
        query = "SELECT valor FROM parametros_fechamento WHERE tipo_parametro = 'ajuda_alimentacao'"
        result = self.exec_query(query, fetchone=True)
        
        if result is not None and isinstance(result, (list, tuple)) and len(result) > 0:
            return float(result[0])
        
        return 0.00  # Valor padrão

    def get_diaria_value_by_motivo(self, motivo: Optional[str] = None) -> float:
        """
        Retorna o valor da diária baseado no motivo (para tabela dayoff_fecham).

        :param motivo: Motivo do dayoff
        :return: Valor da diária
        """
        # Primeiro, buscar o valor padrão
        query_padrao = "SELECT valor FROM parametros_fechamento WHERE tipo_parametro = 'diaria_padrao'"
        result = self.exec_query(query_padrao, fetchone=True)
        
        if not result or not isinstance(result, (list, tuple)) or len(result) == 0:
            return 90.00  # Valor padrão se não encontrar
        
        valor_padrao = float(result[0])

        # Se não tiver motivo, retorna o valor padrão
        if motivo is None:
            return valor_padrao

        # Verificar se há critérios especiais para este motivo
        query_criterio = '''
        SELECT valor_diaria FROM criterios_diaria 
        WHERE valor_filtro = ?
        '''
        result = self.exec_query(query_criterio, params=(motivo,), fetchone=True)
        
        if result is not None and isinstance(result, (list, tuple)) and len(result) > 0:
            return float(result[0])
        
        return valor_padrao

    def get_ajuda_alimentacao_by_motivo(self, motivo: Optional[str] = None) -> float:
        """
        Retorna o valor da ajuda alimentação baseado no motivo (para tabela dayoff_fecham).

        :param motivo: Motivo do dayoff
        :return: Valor da ajuda alimentação
        """
        # Primeiro, buscar o valor padrão
        query_padrao = "SELECT valor FROM parametros_fechamento WHERE tipo_parametro = 'ajuda_alimentacao'"
        result = self.exec_query(query_padrao, fetchone=True)
        
        if not result or not isinstance(result, (list, tuple)) or len(result) == 0:
            return 0.00  # Valor padrão se não encontrar
        
        valor_padrao = float(result[0])

        # Se não tiver motivo, retorna o valor padrão
        if motivo is None:
            return valor_padrao

        # Verificar se há critérios especiais para este motivo
        query_criterio = '''
        SELECT valor_ajuda_alimentacao FROM criterios_diaria 
        WHERE valor_filtro = ?
        '''
        result = self.exec_query(query_criterio, params=(motivo,), fetchone=True)
        
        if result is not None and isinstance(result, (list, tuple)) and len(result) > 0:
            return float(result[0])
        
        return valor_padrao 