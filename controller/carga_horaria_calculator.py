#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Carga Horária Especial - Sistema RPZ v3.0.0.0

Este módulo implementa a lógica de cálculo para carga horária especial
nos critérios especiais do módulo Fechamento de Ponto.

Autor: Sistema RPZ
Data: 01/08/2025
Versão: 1.0
"""

from typing import Optional, Tuple
from config.feature_flags import is_carga_horaria_especial_enabled, get_carga_horaria_max_horas
import re

class CargaHorariaCalculator:
    """
    Classe para cálculos de carga horária especial.
    """
    
    @staticmethod
    def converter_tempo_para_minutos(tempo_str: str) -> int:
        """
        Converte tempo no formato "HH:00" para minutos.
        
        :param tempo_str: Tempo no formato "HH:00" ou "Padrão"
        :return: Tempo em minutos
        """
        if not tempo_str or tempo_str == 'Padrão':
            return 0
        
        # Validar formato
        if not CargaHorariaCalculator.validar_formato_tempo(tempo_str):
            raise ValueError(f'Formato de tempo inválido: {tempo_str}. Use formato "HH:00"')
        
        # Extrair horas
        horas = int(tempo_str.split(':')[0])
        return horas * 60
    
    @staticmethod
    def converter_minutos_para_tempo(minutos: int) -> str:
        """
        Converte minutos para formato "HH:00".
        
        :param minutos: Tempo em minutos
        :return: Tempo no formato "HH:00"
        """
        if minutos == 0:
            return "00:00"
        
        horas = minutos // 60
        return f"{horas:02d}:00"
    
    @staticmethod
    def validar_formato_tempo(tempo_str: str) -> bool:
        """
        Valida se o formato de tempo está correto.
        
        :param tempo_str: Tempo a ser validado
        :return: True se válido, False caso contrário
        """
        if not tempo_str:
            return False
        
        if tempo_str == 'Padrão':
            return True
        
        # Validar formato HH:00 (apenas horas inteiras)
        pattern = r'^(0[0-9]|1[0-2]):00$'
        return bool(re.match(pattern, tempo_str))
    
    @staticmethod
    def calcular_carga_horaria_especial(
        criterio_especial: str,
        dia_semana: str,
        data: str,
        feriados: list,
        carga_horaria_configurada: str = 'Padrão'
    ) -> int:
        """
        Calcula a carga horária para critérios especiais.
        
        :param criterio_especial: Critério especial (ex: "GARAGEM", "FÉRIAS")
        :param dia_semana: Dia da semana
        :param data: Data no formato DD-MM-YYYY
        :param feriados: Lista de feriados
        :param carga_horaria_configurada: Carga horária configurada no critério
        :return: Carga horária em minutos
        """
        # Verificar se a funcionalidade está habilitada
        if not is_carga_horaria_especial_enabled():
            # Usar lógica padrão se funcionalidade desabilitada
            return CargaHorariaCalculator._calcular_carga_horaria_padrao(
                criterio_especial, dia_semana, data, feriados
            )
        
        # 🆕 ORDEM DE PRIORIDADE CORRETA:
        # 1º Prioridade: Configurações especiais do critério (se houver)
        if carga_horaria_configurada and carga_horaria_configurada != 'Padrão':
            return CargaHorariaCalculator.converter_tempo_para_minutos(carga_horaria_configurada)
        
        # 2º Prioridade: Feriados → "00:00"
        if data in feriados:
            return 0
        
        # 3º Prioridade: Dias da Semana → Segunda a Sexta: "08:00", Sábado: "04:00", Domingo: "00:00"
        return CargaHorariaCalculator._calcular_carga_horaria_padrao(
            criterio_especial, dia_semana, data, feriados
        )
    
    @staticmethod
    def _calcular_carga_horaria_padrao(
        criterio_especial: str,
        dia_semana: str,
        data: str,
        feriados: list
    ) -> int:
        """
        Calcula carga horária usando lógica padrão existente.
        
        :param criterio_especial: Critério especial
        :param dia_semana: Dia da semana
        :param data: Data
        :param feriados: Lista de feriados
        :return: Carga horária em minutos
        """
        # Critérios que sempre têm carga horária 0
        criterios_zero = ["FÉRIAS", "ATESTADO", "AFASTAMENTO", "LIC. ÓBITO", "LIC. PATERNIDADE", "LIC. MATERNIDADE"]
        if criterio_especial.upper() in criterios_zero:
            return 0
        
        # 🆕 NOTA: Feriados já foram verificados na função principal
        # Esta função agora só trata dias da semana
        
        # Domingo sempre 0
        if dia_semana.upper() == "DOMINGO":
            return 0
        
        # Sábado: 4 horas (240 minutos)
        if dia_semana.upper() == "SÁBADO":
            return 240
        
        # Dias úteis: 8 horas (480 minutos)
        return 480
    
    @staticmethod
    def calcular_hora_extra_50_especial(
        jornada_total: int,
        carga_horaria: str,
        criterio_especial: str
    ) -> int:
        """
        Calcula hora extra 50% para critérios especiais.
        
        :param jornada_total: Jornada total em minutos
        :param carga_horaria: Carga horária configurada
        :param criterio_especial: Critério especial
        :return: Hora extra 50% em minutos
        """
        # Verificar se a funcionalidade está habilitada
        if not is_carga_horaria_especial_enabled():
            # Usar lógica padrão se funcionalidade desabilitada
            return CargaHorariaCalculator._calcular_hora_extra_50_padrao(
                jornada_total, criterio_especial
            )
        
        # Se critério especial tem valor específico, usar ele
        if carga_horaria and carga_horaria != 'Padrão':
            carga_horaria_minutos = CargaHorariaCalculator.converter_tempo_para_minutos(carga_horaria)
            return max(-1440, jornada_total - carga_horaria_minutos)  # Limite de -24h
        
        # Caso contrário, usar lógica padrão
        return CargaHorariaCalculator._calcular_hora_extra_50_padrao(
            jornada_total, criterio_especial
        )
    
    @staticmethod
    def _calcular_hora_extra_50_padrao(jornada_total: int, criterio_especial: str) -> int:
        """
        Calcula hora extra 50% usando lógica padrão.
        
        :param jornada_total: Jornada total em minutos
        :param criterio_especial: Critério especial
        :return: Hora extra 50% em minutos
        """
        # Critérios especiais que têm jornada
        criterios_com_jornada = ["GARAGEM", "CARGA/DESCARGA"]
        
        if criterio_especial.upper() in criterios_com_jornada:
            # Usar jornada total informada pelo usuário
            return max(0, jornada_total - 480)  # 8h padrão
        else:
            # Outros critérios não têm jornada
            return 0
    
    @staticmethod
    def calcular_horas_trabalhadas_especial(
        jornada_total: int,
        criterio_especial: str
    ) -> int:
        """
        Calcula horas trabalhadas para critérios especiais.
        
        :param jornada_total: Jornada total em minutos
        :param criterio_especial: Critério especial
        :return: Horas trabalhadas em minutos
        """
        # Verificar se a funcionalidade está habilitada
        if not is_carga_horaria_especial_enabled():
            # Usar lógica padrão se funcionalidade desabilitada
            return CargaHorariaCalculator._calcular_horas_trabalhadas_padrao(criterio_especial)
        
        # Critérios especiais que têm jornada
        criterios_com_jornada = ["GARAGEM", "CARGA/DESCARGA"]
        
        if criterio_especial.upper() in criterios_com_jornada:
            return jornada_total  # Usar valor informado pelo usuário
        else:
            return 0  # Padrão para outros critérios
    
    @staticmethod
    def _calcular_horas_trabalhadas_padrao(criterio_especial: str) -> int:
        """
        Calcula horas trabalhadas usando lógica padrão.
        
        :param criterio_especial: Critério especial
        :return: Horas trabalhadas em minutos
        """
        # Critérios especiais que têm jornada
        criterios_com_jornada = ["GARAGEM", "CARGA/DESCARGA"]
        
        if criterio_especial.upper() in criterios_com_jornada:
            return 480  # 8h padrão
        else:
            return 0
    
    @staticmethod
    def validar_carga_horaria_configurada(carga_horaria: str) -> Tuple[bool, str]:
        """
        Valida carga horária configurada.
        
        :param carga_horaria: Carga horária a ser validada
        :return: Tupla (é_válida, mensagem_erro)
        """
        if not carga_horaria:
            return False, "Carga horária não pode ser vazia"
        
        if carga_horaria == 'Padrão':
            return True, ""
        
        if not CargaHorariaCalculator.validar_formato_tempo(carga_horaria):
            return False, f'Formato inválido: {carga_horaria}. Use "Padrão" ou "HH:00" (ex: "08:00")'
        
        # Verificar limite máximo
        try:
            horas = int(carga_horaria.split(':')[0])
            max_horas = get_carga_horaria_max_horas()
            if horas > max_horas:
                return False, f'Horas excedem o limite máximo de {max_horas}:00'
        except ValueError:
            return False, f'Valor de horas inválido: {carga_horaria}'
        
        return True, ""

# Funções de conveniência para uso direto
def calcular_carga_horaria_especial(
    criterio_especial: str,
    dia_semana: str,
    data: str,
    feriados: list,
    carga_horaria_configurada: str = 'Padrão'
) -> int:
    """Função de conveniência para cálculo de carga horária especial."""
    return CargaHorariaCalculator.calcular_carga_horaria_especial(
        criterio_especial, dia_semana, data, feriados, carga_horaria_configurada
    )

def calcular_hora_extra_50_especial(
    jornada_total: int,
    carga_horaria: str,
    criterio_especial: str
) -> int:
    """Função de conveniência para cálculo de hora extra 50% especial."""
    return CargaHorariaCalculator.calcular_hora_extra_50_especial(
        jornada_total, carga_horaria, criterio_especial
    )

def calcular_horas_trabalhadas_especial(
    jornada_total: int,
    criterio_especial: str
) -> int:
    """Função de conveniência para cálculo de horas trabalhadas especiais."""
    return CargaHorariaCalculator.calcular_horas_trabalhadas_especial(
        jornada_total, criterio_especial
    )

# Exemplo de uso:
if __name__ == "__main__":
    print("🧮 Calculadora de Carga Horária Especial")
    print("=" * 50)
    
    # Testes básicos
    print(f"Converter '08:00' para minutos: {CargaHorariaCalculator.converter_tempo_para_minutos('08:00')}")
    print(f"Converter 480 minutos para tempo: {CargaHorariaCalculator.converter_minutos_para_tempo(480)}")
    
    # Testes de validação
    print(f"Validar '08:00': {CargaHorariaCalculator.validar_formato_tempo('08:00')}")
    print(f"Validar '08:30': {CargaHorariaCalculator.validar_formato_tempo('08:30')}")
    print(f"Validar 'Padrão': {CargaHorariaCalculator.validar_formato_tempo('Padrão')}")
    
    # Testes de cálculo
    feriados_teste = ['25-12-2025']
    carga_horaria = calcular_carga_horaria_especial('GARAGEM', 'Segunda-feira', '25-12-2025', feriados_teste, '06:00')
    print(f"Carga horária para GARAGEM em 25/12/2025 com 06:00: {carga_horaria} minutos")
    
    he_50 = calcular_hora_extra_50_especial(600, '06:00', 'GARAGEM')
    print(f"Hora extra 50% para jornada de 10h com carga de 6h: {he_50} minutos")
