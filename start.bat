@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    INICIANDO SISTEMA RPZ v2.0.0.2
echo ========================================
echo.

:: Verificar se o ambiente virtual existe
if not exist "venv" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat primeiro
    pause
    exit /b 1
)

:: Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

:: Verificar se as dependências estão instaladas
echo Verificando dependencias...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Dependencias nao encontradas!
    echo Execute install.bat primeiro
    pause
    exit /b 1
)

echo [OK] Dependencias encontradas

:: Verificar se as pastas necessárias existem
if not exist "logs" mkdir logs
if not exist "dbs" mkdir dbs

echo.
echo Iniciando o sistema...
echo Acesse: http://localhost:5000
echo Para parar: Ctrl+C
echo.

:: Executar o sistema
python app.py

pause
