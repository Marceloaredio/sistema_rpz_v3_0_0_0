@echo off
:: Navegar para o diretório onde está o script
cd /d "%~dp0"

echo ========================================
echo    CORRIGIR PROBLEMAS DE CODIFICACAO
echo    Sistema RPZ v2.0.0.2
echo ========================================
echo.

echo Este script vai corrigir problemas de codificacao nos arquivos.
echo.

:: Verificar se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

echo [OK] Python encontrado

echo.
echo ========================================
echo    CORRIGINDO ARQUIVOS
echo ========================================
echo.

:: Corrigir requirements.txt
echo Corrigindo requirements.txt...
python -c "
import os
import sys

def fix_file_encoding(filename):
    try:
        # Tentar ler com UTF-8
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remover caracteres especiais e emojis
        import re
        # Remover emojis e caracteres especiais
        content = re.sub(r'[^\x00-\x7F]+', '', content)
        # Substituir acentos por versões sem acento
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n',
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C', 'Ñ': 'N'
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Salvar com encoding UTF-8
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'[OK] {filename} corrigido')
        return True
    except Exception as e:
        print(f'[ERRO] Falha ao corrigir {filename}: {e}')
        return False

# Corrigir arquivos
files_to_fix = ['requirements.txt', 'requirements-dev.txt']
for file in files_to_fix:
    if os.path.exists(file):
        fix_file_encoding(file)
    else:
        print(f'[AVISO] {file} nao encontrado')
"

echo.
echo ========================================
echo    VERIFICANDO CORRECAO
echo ========================================
echo.

:: Testar se o requirements.txt agora funciona
echo Testando instalacao de dependencias...
python -c "
import sys
try:
    import pip
    print('[OK] pip disponivel')
    
    # Tentar ler requirements.txt
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        print('[OK] requirements.txt pode ser lido')
        
    # Verificar se tem caracteres especiais
    import re
    special_chars = re.findall(r'[^\x00-\x7F]', content)
    if special_chars:
        print(f'[AVISO] Ainda tem {len(special_chars)} caracteres especiais')
    else:
        print('[OK] Nenhum caractere especial encontrado')
        
except Exception as e:
    print(f'[ERRO] Problema persistente: {e}')
"

echo.
echo ========================================
echo    OPCOES ADICIONAIS
echo ========================================
echo.
echo Se ainda houver problemas, voce pode:
echo 1. Usar requirements-minimal.txt (sem comentarios)
echo 2. Instalar dependencias manualmente
echo 3. Verificar a codificacao do sistema
echo.

set /p choice="Deseja testar a instalacao agora? (s/N): "
if /i "%choice%"=="s" (
    echo.
    echo Testando instalacao...
    pip install -r requirements.txt --dry-run
    if errorlevel 1 (
        echo [AVISO] Ainda ha problemas. Use requirements-minimal.txt
    ) else (
        echo [OK] Instalacao funcionando corretamente!
    )
)

echo.
echo ========================================
echo    CORRECAO CONCLUIDA
echo ========================================
echo.
pause 