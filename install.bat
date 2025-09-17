@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    INSTALADOR SISTEMA RPZ v2.0.0.2
echo ========================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.8+ primeiro
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version

echo.
echo Criando ambiente virtual...
python -m venv venv
if errorlevel 1 (
    echo [ERRO] Falha ao criar ambiente virtual
    pause
    exit /b 1
)

echo [OK] Ambiente virtual criado

echo.
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERRO] Falha ao ativar ambiente virtual
    pause
    exit /b 1
)

echo [OK] Ambiente virtual ativado

echo.
echo Escolha o tipo de instalacao:
echo 1. Producao (apenas dependencias necessarias)
echo 2. Desenvolvimento (inclui ferramentas de dev)
echo.
set /p install_type="Digite sua escolha (1 ou 2): "

if "%install_type%"=="2" (
    echo.
    echo Instalando dependencias de desenvolvimento...
    pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [AVISO] Falha com requirements-dev.txt, tentando versao minimalista...
        pip install -r requirements-minimal.txt
        if errorlevel 1 (
            echo [ERRO] Falha ao instalar dependencias de desenvolvimento
            pause
            exit /b 1
        )
        echo [OK] Dependencias de desenvolvimento instaladas (versao minimalista)
    ) else (
        echo [OK] Dependencias de desenvolvimento instaladas
    )
) else (
    echo.
    echo Instalando dependencias de producao...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [AVISO] Falha com requirements.txt, tentando versao minimalista...
        pip install -r requirements-minimal.txt
        if errorlevel 1 (
            echo [ERRO] Falha ao instalar dependencias
            pause
            exit /b 1
        )
        echo [OK] Dependencias instaladas (versao minimalista)
    ) else (
        echo [OK] Dependencias instaladas
    )
)

echo.
echo Criando pastas necessarias...
if not exist "logs" mkdir logs
if not exist "dbs" mkdir dbs

echo [OK] Pastas criadas

echo.
echo ========================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Para executar o sistema:
echo 1. Execute: start.bat
echo 2. Acesse: http://localhost:5000
echo 3. Login: admin@admin.com / Rpz#2025@@
echo.
echo Para configurar como servico, consulte o README.md
echo.
if "%install_type%"=="2" (
    echo Ferramentas de desenvolvimento instaladas:
    echo - pytest: para testes
    echo - black: formatador de codigo
    echo - flake8: linter de codigo
    echo - mypy: verificacao de tipos
    echo.
)
pause 