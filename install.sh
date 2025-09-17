#!/bin/bash

echo "========================================"
echo "   INSTALADOR SISTEMA RPZ v2.0.0.2"
echo "========================================"
echo

echo "[1/5] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não encontrado!"
    echo "Por favor, instale Python 3.8+ primeiro."
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi
echo "✅ Python encontrado"

echo
echo "[2/5] Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    echo "ERRO: pip3 não encontrado!"
    echo "Por favor, instale pip3 primeiro."
    exit 1
fi
echo "✅ pip encontrado"

echo
echo "[3/5] Instalando dependências..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependências!"
    echo "Verifique se tem conexão com internet."
    exit 1
fi
echo "✅ Dependências instaladas"

echo
echo "[4/5] Criando pastas necessárias..."
mkdir -p logs
mkdir -p dbs
mkdir -p credentials
mkdir -p backups
echo "✅ Pastas criadas"

echo
echo "[5/5] Testando instalação..."
python3 -c "import flask; print('✅ Flask OK')" 2>/dev/null
python3 -c "import pandas; print('✅ Pandas OK')" 2>/dev/null
python3 -c "import gspread; print('✅ Google Sheets OK')" 2>/dev/null
echo "✅ Instalação concluída!"

echo
echo "========================================"
echo "    INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "========================================"
echo
echo "Para executar o sistema:"
echo "  python3 app.py"
echo
echo "Para acessar:"
echo "  http://localhost:5000"
echo
echo "Login padrão:"
echo "  Email: admin@admin.com"
echo "  Senha: root12345"
echo
echo "Para configurar integração Google:"
echo "  1. Coloque credentials.json na pasta credentials/"
echo "  2. Execute: python3 test_google_integration.py"
echo
echo "Para executar em produção:"
echo "  waitress-serve --host=0.0.0.0 --port=8080 app:app"
echo 