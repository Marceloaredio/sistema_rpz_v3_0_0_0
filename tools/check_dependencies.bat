@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    VERIFICADOR DE DEPENDENCIAS
echo    Sistema RPZ v2.0.0.2
echo ========================================
echo.

:: Verificar se ambiente virtual está ativo
if not defined VIRTUAL_ENV (
    echo [AVISO] Ambiente virtual nao ativo
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [ERRO] Falha ao ativar ambiente virtual
        pause
        exit /b 1
    )
)

echo [OK] Ambiente virtual ativo

echo.
echo ========================================
echo    VERIFICANDO DEPENDENCIAS
echo ========================================
echo.

:: Verificar dependências instaladas vs requirements.txt
echo Verificando dependencias de producao...
pip check
if errorlevel 1 (
    echo [AVISO] Problemas encontrados nas dependencias
) else (
    echo [OK] Dependencias de producao OK
)

echo.
echo Verificando dependencias faltantes...
pip install -r requirements.txt --dry-run
if errorlevel 1 (
    echo [AVISO] Algumas dependencias podem estar faltando
) else (
    echo [OK] Todas as dependencias de producao instaladas
)

echo.
echo ========================================
echo    VERIFICANDO VULNERABILIDADES
echo ========================================
echo.

:: Verificar se safety está instalado
python -c "import safety" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Safety nao instalado. Instalando...
    pip install safety
)

:: Verificar vulnerabilidades
echo Verificando vulnerabilidades conhecidas...
safety check
if errorlevel 1 (
    echo [AVISO] Vulnerabilidades encontradas!
    echo Execute: pip install --upgrade [pacote]
) else (
    echo [OK] Nenhuma vulnerabilidade conhecida encontrada
)

echo.
echo ========================================
echo    VERIFICANDO VERSOES
echo ========================================
echo.

echo Versoes das dependencias principais:
python -c "
import sys
packages = ['flask', 'pandas', 'openpyxl', 'reportlab', 'waitress']
for pkg in packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', 'N/A')
        print(f'{pkg:12} {version}')
    except ImportError:
        print(f'{pkg:12} NAO INSTALADO')
"

echo.
echo ========================================
echo    OPCOES DE MANUTENCAO
echo ========================================
echo.
echo 1. Atualizar todas as dependencias
echo 2. Verificar dependencias obsoletas
echo 3. Limpar cache do pip
echo 4. Sair
echo.
set /p choice="Digite sua escolha (1-4): "

if "%choice%"=="1" goto update_all
if "%choice%"=="2" goto check_outdated
if "%choice%"=="3" goto clean_cache
if "%choice%"=="4" goto exit
goto exit

:update_all
echo.
echo Atualizando todas as dependencias...
pip install --upgrade -r requirements.txt
echo [OK] Atualizacao concluida
pause
goto exit

:check_outdated
echo.
echo Verificando dependencias obsoletas...
pip list --outdated
echo.
echo Para atualizar uma dependencia especifica:
echo pip install --upgrade [nome_do_pacote]
pause
goto exit

:clean_cache
echo.
echo Limpando cache do pip...
pip cache purge
echo [OK] Cache limpo
pause
goto exit

:exit
echo.
echo Verificacao concluida!
echo.
pause 