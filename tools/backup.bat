@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    BACKUP SISTEMA RPZ v2.0.0.2
echo ========================================
echo.

:: Verificar se está rodando como administrador (opcional)
net session >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Execute como administrador para melhor compatibilidade
)

:: Criar pasta de backup se não existir
if not exist "backups" mkdir backups

:: Obter data e hora atual
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "datestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

echo Data/Hora: %datestamp%

:: Verificar se o banco existe
if not exist "dbs\db_app.db" (
    echo [ERRO] Banco de dados nao encontrado!
    echo Verifique se o sistema foi executado pelo menos uma vez
    pause
    exit /b 1
)

:: Parar o serviço se estiver rodando (opcional)
echo Verificando se o servico esta rodando...
sc query "SistemaRPZ" | find "RUNNING" >nul
if not errorlevel 1 (
    echo Parando servico para backup...
    net stop "SistemaRPZ"
    timeout /t 3 /nobreak >nul
)

:: Fazer backup do banco
echo Fazendo backup do banco de dados...
copy "dbs\db_app.db" "backups\db_app_%datestamp%.db"

if errorlevel 1 (
    echo [ERRO] Falha ao fazer backup!
    pause
    exit /b 1
)

echo [OK] Backup criado: backups\db_app_%datestamp%.db

:: Fazer backup dos logs (opcional)
if exist "logs" (
    echo Fazendo backup dos logs...
    xcopy "logs" "backups\logs_%datestamp%\" /E /I /Y >nul
    echo [OK] Logs copiados: backups\logs_%datestamp%\
)

:: Reiniciar o serviço se estava rodando
sc query "SistemaRPZ" | find "STOPPED" >nul
if not errorlevel 1 (
    echo Reiniciando servico...
    net start "SistemaRPZ"
)

:: Limpar backups antigos (manter apenas os últimos 7 dias)
echo Limpando backups antigos...
forfiles /p "backups" /s /m *.db /d -7 /c "cmd /c del @path" 2>nul
forfiles /p "backups" /s /m logs_* /d -7 /c "cmd /c rmdir /s /q @path" 2>nul

echo.
echo ========================================
echo    BACKUP CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Arquivos criados:
echo - backups\db_app_%datestamp%.db
if exist "logs" echo - backups\logs_%datestamp%\
echo.
echo Para restaurar um backup:
echo 1. Pare o servico: net stop SistemaRPZ
echo 2. Copie o arquivo .db para dbs\db_app.db
echo 3. Inicie o servico: net start SistemaRPZ
echo.
pause 