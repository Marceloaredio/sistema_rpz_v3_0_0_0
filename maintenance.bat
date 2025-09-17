@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    MANUTENCAO SISTEMA RPZ v2.0.0.2
echo ========================================
echo.

:: Menu de opções
:menu
echo Escolha uma opcao:
echo.
echo 1. Verificar status do sistema
echo 2. Limpar logs antigos
echo 3. Otimizar banco de dados
echo 4. Verificar integridade
echo 5. Backup manual
echo 6. Restaurar backup
echo 7. Reinstalar dependencias
echo 8. Sair
echo.
set /p choice="Digite sua escolha (1-8): "

if "%choice%"=="1" goto status
if "%choice%"=="2" goto clean_logs
if "%choice%"=="3" goto optimize_db
if "%choice%"=="4" goto check_integrity
if "%choice%"=="5" goto manual_backup
if "%choice%"=="6" goto restore_backup
if "%choice%"=="7" goto reinstall_deps
if "%choice%"=="8" goto exit
goto menu

:status
echo.
echo ========================================
echo    VERIFICANDO STATUS DO SISTEMA
echo ========================================
echo.

:: Verificar se o serviço está rodando
echo [1/5] Verificando servico...
sc query "SistemaRPZ" | find "RUNNING" >nul
if not errorlevel 1 (
    echo [OK] Servico SistemaRPZ esta rodando
) else (
    echo [AVISO] Servico SistemaRPZ nao esta rodando
)

:: Verificar se o banco existe
echo [2/5] Verificando banco de dados...
if exist "dbs\db_app.db" (
    echo [OK] Banco de dados encontrado
    for %%A in ("dbs\db_app.db") do echo     Tamanho: %%~zA bytes
) else (
    echo [ERRO] Banco de dados nao encontrado
)

:: Verificar ambiente virtual
echo [3/5] Verificando ambiente virtual...
if exist "venv" (
    echo [OK] Ambiente virtual encontrado
) else (
    echo [ERRO] Ambiente virtual nao encontrado
)

:: Verificar dependências
echo [4/5] Verificando dependencias...
python -c "import flask" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Dependencias instaladas
) else (
    echo [ERRO] Dependencias nao encontradas
)

:: Verificar portas
echo [5/5] Verificando porta 5000...
netstat -ano | findstr :5000 >nul
if not errorlevel 1 (
    echo [AVISO] Porta 5000 esta em uso
) else (
    echo [OK] Porta 5000 livre
)

echo.
pause
goto menu

:clean_logs
echo.
echo ========================================
echo    LIMPANDO LOGS ANTIGOS
echo ========================================
echo.

:: Verificar se logs existem
if not exist "logs" (
    echo [AVISO] Pasta de logs nao encontrada
    pause
    goto menu
)

:: Contar arquivos antes
for /f %%i in ('dir /b logs\*.log 2^>nul ^| find /c /v ""') do set count_before=%%i
echo Logs encontrados: %count_before%

:: Remover logs com mais de 30 dias
echo Removendo logs com mais de 30 dias...
forfiles /p "logs" /s /m *.log /d -30 /c "cmd /c del @path" 2>nul

:: Contar arquivos depois
for /f %%i in ('dir /b logs\*.log 2^>nul ^| find /c /v ""') do set count_after=%%i
echo Logs restantes: %count_after%

echo [OK] Limpeza concluida
pause
goto menu

:optimize_db
echo.
echo ========================================
echo    OTIMIZANDO BANCO DE DADOS
echo ========================================
echo.

:: Verificar se o banco existe
if not exist "dbs\db_app.db" (
    echo [ERRO] Banco de dados nao encontrado
    pause
    goto menu
)

:: Parar o serviço
echo Parando servico...
net stop "SistemaRPZ" >nul 2>&1

:: Fazer backup antes
echo Fazendo backup antes da otimizacao...
call backup.bat >nul 2>&1

:: Otimizar banco (usando Python)
echo Otimizando banco de dados...
python -c "
import sqlite3
import os
conn = sqlite3.connect('dbs/db_app.db')
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.close()
print('Otimizacao concluida')
"

:: Reiniciar o serviço
echo Reiniciando servico...
net start "SistemaRPZ" >nul 2>&1

echo [OK] Otimizacao concluida
pause
goto menu

:check_integrity
echo.
echo ========================================
echo    VERIFICANDO INTEGRIDADE
echo ========================================
echo.

:: Verificar se o banco existe
if not exist "dbs\db_app.db" (
    echo [ERRO] Banco de dados nao encontrado
    pause
    goto menu
)

:: Verificar integridade do banco
echo Verificando integridade do banco...
python -c "
import sqlite3
conn = sqlite3.connect('dbs/db_app.db')
cursor = conn.execute('PRAGMA integrity_check')
result = cursor.fetchone()
if result[0] == 'ok':
    print('[OK] Banco de dados integro')
else:
    print('[ERRO] Problemas encontrados:', result[0])
conn.close()
"

:: Verificar tabelas
echo Verificando tabelas...
python -c "
import sqlite3
conn = sqlite3.connect('dbs/db_app.db')
cursor = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
tables = cursor.fetchall()
print('Tabelas encontradas:', len(tables))
for table in tables:
    print('  -', table[0])
conn.close()
"

pause
goto menu

:manual_backup
echo.
echo ========================================
echo    BACKUP MANUAL
echo ========================================
echo.

call backup.bat
goto menu

:restore_backup
echo.
echo ========================================
echo    RESTAURAR BACKUP
echo ========================================
echo.

:: Verificar se existem backups
if not exist "backups" (
    echo [ERRO] Pasta de backups nao encontrada
    pause
    goto menu
)

:: Listar backups disponíveis
echo Backups disponiveis:
dir /b backups\*.db 2>nul
if errorlevel 1 (
    echo [ERRO] Nenhum backup encontrado
    pause
    goto menu
)

echo.
set /p backup_file="Digite o nome do arquivo de backup (ex: db_app_2024-01-01_10-30-00.db): "

if not exist "backups\%backup_file%" (
    echo [ERRO] Arquivo nao encontrado
    pause
    goto menu
)

echo.
echo [ATENCAO] Isso vai substituir o banco atual!
set /p confirm="Tem certeza? (s/N): "
if /i not "%confirm%"=="s" goto menu

:: Parar o serviço
echo Parando servico...
net stop "SistemaRPZ" >nul 2>&1

:: Fazer backup do banco atual
echo Fazendo backup do banco atual...
copy "dbs\db_app.db" "dbs\db_app_backup_antes_restore.db" >nul 2>&1

:: Restaurar backup
echo Restaurando backup...
copy "backups\%backup_file%" "dbs\db_app.db"

:: Reiniciar o serviço
echo Reiniciando servico...
net start "SistemaRPZ" >nul 2>&1

echo [OK] Backup restaurado com sucesso
pause
goto menu

:reinstall_deps
echo.
echo ========================================
echo    REINSTALANDO DEPENDENCIAS
echo ========================================
echo.

:: Verificar se ambiente virtual existe
if not exist "venv" (
    echo [ERRO] Ambiente virtual nao encontrado
    echo Execute install.bat primeiro
    pause
    goto menu
)

:: Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

:: Reinstalar dependências
echo Reinstalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

echo [OK] Dependencias reinstaladas
pause
goto menu

:exit
echo.
echo Obrigado por usar o Sistema RPZ!
echo.
exit /b 0 