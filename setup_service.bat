@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    CONFIGURADOR DE SERVICO - NSSM
echo ========================================
echo.

:: Verificar se está rodando como administrador
net session >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Execute este script como Administrador!
    echo Clique com botao direito e selecione "Executar como administrador"
    pause
    exit /b 1
)

echo [OK] Executando como administrador

:: Verificar se NSSM está disponível
if not exist "nssm.exe" (
    echo [ERRO] NSSM nao encontrado!
    echo.
    echo Para baixar o NSSM:
    echo 1. Acesse: https://nssm.cc/download
    echo 2. Baixe a versao Windows 64-bit
    echo 3. Extraia nssm.exe para esta pasta
    echo 4. Execute este script novamente
    pause
    exit /b 1
)

echo [OK] NSSM encontrado

:: Obter caminho atual
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

echo Diretorio atual: %CURRENT_DIR%

:: Verificar se o ambiente virtual existe
if not exist "%CURRENT_DIR%\venv" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat primeiro
    pause
    exit /b 1
)

:: Verificar se app.py existe
if not exist "%CURRENT_DIR%\app.py" (
    echo [ERRO] app.py nao encontrado!
    pause
    exit /b 1
)

echo.
echo Configurando servico "SistemaRPZ"...

:: Remover serviço se já existir
echo Verificando se o servico ja existe...
nssm.exe remove "SistemaRPZ" confirm >nul 2>&1

:: Instalar o serviço
echo Instalando servico...
nssm.exe install "SistemaRPZ" "%CURRENT_DIR%\venv\Scripts\python.exe" "%CURRENT_DIR%\app.py"

:: Configurar diretório de trabalho
echo Configurando diretorio de trabalho...
nssm.exe set "SistemaRPZ" AppDirectory "%CURRENT_DIR%"

:: Configurar descrição
echo Configurando descricao...
nssm.exe set "SistemaRPZ" Description "Sistema de Gestao de Jornada de Motoristas RPZ v2.0.0.2"

:: Configurar tipo de inicialização (Automático)
echo Configurando inicializacao automatica...
nssm.exe set "SistemaRPZ" Start SERVICE_AUTO_START

:: Configurar dependências (se necessário)
echo Configurando dependencias...
nssm.exe set "SistemaRPZ" DependOnService Tcpip

:: Configurar usuário (opcional - comentado para usar Local System)
:: nssm.exe set "SistemaRPZ" ObjectName ".\usuario" "senha"

echo.
echo ========================================
echo    SERVICO CONFIGURADO COM SUCESSO!
echo ========================================
echo.
echo Nome do servico: SistemaRPZ
echo.
echo Comandos utéis:
echo - Iniciar: net start SistemaRPZ
echo - Parar: net stop SistemaRPZ
echo - Status: sc query SistemaRPZ
echo - Remover: nssm.exe remove SistemaRPZ confirm
echo.
echo Para iniciar o servico agora, digite: net start SistemaRPZ
echo.
pause 