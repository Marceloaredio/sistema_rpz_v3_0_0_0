@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    VERIFICADOR DE ARQUIVOS
echo    Sistema RPZ v2.0.0.2
echo ========================================
echo.

echo Verificando arquivos essenciais...
echo.

:: Lista de arquivos essenciais
set "files_ok=0"
set "files_missing=0"

:: Verificar arquivos principais
if exist "app.py" (
    echo [OK] app.py
    set /a files_ok+=1
) else (
    echo [ERRO] app.py - NAO ENCONTRADO
    set /a files_missing+=1
)

if exist "requirements.txt" (
    echo [OK] requirements.txt
    set /a files_ok+=1
) else (
    echo [ERRO] requirements.txt - NAO ENCONTRADO
    set /a files_missing+=1
)

if exist "config.ini" (
    echo [OK] config.ini
    set /a files_ok+=1
) else (
    echo [ERRO] config.ini - NAO ENCONTRADO
    set /a files_missing+=1
)

if exist "global_vars.py" (
    echo [OK] global_vars.py
    set /a files_ok+=1
) else (
    echo [ERRO] global_vars.py - NAO ENCONTRADO
    set /a files_missing+=1
)

echo.
echo Verificando pastas essenciais...
echo.

:: Verificar pastas principais
if exist "controller" (
    echo [OK] pasta controller/
    set /a files_ok+=1
) else (
    echo [ERRO] pasta controller/ - NAO ENCONTRADA
    set /a files_missing+=1
)

if exist "model" (
    echo [OK] pasta model/
    set /a files_ok+=1
) else (
    echo [ERRO] pasta model/ - NAO ENCONTRADA
    set /a files_missing+=1
)

if exist "view" (
    echo [OK] pasta view/
    set /a files_ok+=1
) else (
    echo [ERRO] pasta view/ - NAO ENCONTRADA
    set /a files_missing+=1
)

if exist "templates" (
    echo [OK] pasta templates/
    set /a files_ok+=1
) else (
    echo [ERRO] pasta templates/ - NAO ENCONTRADA
    set /a files_missing+=1
)

if exist "static" (
    echo [OK] pasta static/
    set /a files_ok+=1
) else (
    echo [ERRO] pasta static/ - NAO ENCONTRADA
    set /a files_missing+=1
)

echo.
echo Verificando arquivos de desenvolvimento...
echo.

:: Verificar arquivos de desenvolvimento (opcionais)
if exist "requirements-dev.txt" (
    echo [OK] requirements-dev.txt
    set /a files_ok+=1
) else (
    echo [AVISO] requirements-dev.txt - NAO ENCONTRADO (opcional)
)

if exist "pyproject.toml" (
    echo [OK] pyproject.toml
    set /a files_ok+=1
) else (
    echo [AVISO] pyproject.toml - NAO ENCONTRADO (opcional)
)

if exist "README.md" (
    echo [OK] README.md
    set /a files_ok+=1
) else (
    echo [AVISO] README.md - NAO ENCONTRADO (opcional)
)

if exist "DEVELOPER.md" (
    echo [OK] DEVELOPER.md
    set /a files_ok+=1
) else (
    echo [AVISO] DEVELOPER.md - NAO ENCONTRADO (opcional)
)

echo.
echo ========================================
echo    RESUMO DA VERIFICACAO
echo ========================================
echo.
echo Arquivos/pastas encontrados: %files_ok%
echo Arquivos/pastas faltando: %files_missing%
echo.

if %files_missing% gtr 0 (
    echo [ATENCAO] Alguns arquivos essenciais estao faltando!
    echo.
    echo Possiveis causas:
    echo 1. Script executado de diretorio incorreto
    echo 2. Arquivos corrompidos ou deletados
    echo 3. Download incompleto do projeto
    echo.
    echo Diretorio atual: %CD%
    echo.
    echo Solucoes:
    echo 1. Execute este script da pasta raiz do projeto
    echo 2. Refaça o download do projeto
    echo 3. Restaure de um backup
) else (
    echo [OK] Todos os arquivos essenciais encontrados!
    echo.
    echo O sistema parece estar completo e pronto para uso.
)

echo.
echo ========================================
echo    VERIFICACAO CONCLUIDA
echo ========================================
echo.
pause 