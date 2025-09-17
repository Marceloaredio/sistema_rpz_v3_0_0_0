import os
import os.path

# Modo debug - liga logs detalhados (prioridade para variável de ambiente)
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

# Caminho do banco de dados SQLite
DB_PATH = os.path.join('dbs', 'db_app.db')

# Extensões de arquivo que o sistema aceita
ALLOWED_EXTENSIONS = ['csv', 'xls', 'xlsx']

# Dicionário com os tipos de infração e suas descrições
INFRACTION_DICT = {
    2: "Tempo insuficiente de Refeição.",
    3: "Jornada diária total maior que o permitido (Limite Máximo de Horas: 13 Hrs)",
    4: "Tempo de interstício insuficiente (Mínimo de Horas de Interstício: 11 Hrs)",
    5: "Tempo insuficiente de descanso a cada 5:30 hrs de Direção (Obrigatório 30 minutos de intervalo, podendo ser fracionado)",
    6: "Máximo de dias consecutivos trabalhados ultrapassado (Máximo de 6 dias consecutivos)",
    7: "Máximo de horas semanais trabalhadas ultrapassada (Máximo de 72 Horas semanais)",
    8: "Descanso semanal não Realizado (Mínimo de 35 hrs ininterruptas para descanso semanal."
}

# Tempos mínimos e máximos em segundos (baseado na legislação)

# Tempo mínimo de refeição (1 hora)
TEMPO_ALMOCO = 3600

# Tempo máximo de trabalho diário (13 horas)
TEMPO_TRABALHO_DIARIO = 46800

# Tempo mínimo de interstício entre jornadas (11 horas)
TEMPO_INTERSTICIO = 28800

# Tempo máximo de direção sem pausa (5 horas e 30 minutos)
TEMPO_MAX_DIRECAO = 19800

# Tempo mínimo de descanso a cada período de direção (30 minutos)
TEMPO_MIN_DESCANSO = 1800

# Máximo de dias consecutivos trabalhados (6 dias)
MAX_DIAS_CONSECUTIVOS_TRABALHADOS = 6

# Máximo de horas semanais trabalhadas (72 horas)
MAX_HORAS_SEMANAIS = 259200

# Tempo mínimo de descanso semanal (35 horas)
MIN_DESCANSO_SEMANAL = 126000
