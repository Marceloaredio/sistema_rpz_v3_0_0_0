# 🚀 Guia de Instalação - Sistema RPZ v2.0.0.2

## 📋 Pré-requisitos

- **Python 3.8+** instalado
- **pip** (gerenciador de pacotes Python)
- **Git** (opcional, para clonar o repositório)

## 🔧 Instalação Rápida

### 1. **Baixar/Clonar o Projeto**
```bash
# Se usando Git:
git clone [URL_DO_REPOSITORIO]
cd sistema_rpz_v3_0_0_0

# Ou baixar e extrair o arquivo ZIP
```

### 2. **Instalar Dependências**
```bash
# Instalar todas as dependências (incluindo Google):
pip install -r requirements.txt

# OU instalar apenas dependências essenciais (sem Google):
pip install Flask==2.3.3 Werkzeug==2.3.7 Jinja2==3.1.2 waitress==2.1.2 pandas==2.0.3 openpyxl==3.1.2 xlrd==2.0.1
```

### 3. **Executar o Sistema**
```bash
python app.py
```

### 4. **Acessar o Sistema**
- Abra o navegador
- Acesse: `http://localhost:5000`
- Login padrão: `admin@admin.com` / `root12345`

## 🔗 Integração com Google (Opcional)

### **Para ativar a integração com Google Sheets e Forms:**

#### 1. **Instalar Dependências Google**
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

#### 2. **Configurar Credenciais**
- Crie um projeto no Google Cloud Console
- Ative as APIs: Google Sheets API e Google Forms API
- Crie uma Service Account
- Baixe o arquivo JSON de credenciais
- Renomeie para `credentials.json`
- Coloque na pasta `credentials/`

#### 3. **Compartilhar Recursos**
- **Planilha Google Sheets:** Compartilhe com o email da Service Account
- **Google Forms:** Compartilhe cada formulário com o email da Service Account

#### 4. **Verificar Configuração**
```bash
python test_google_integration.py
```

## 📁 Estrutura de Arquivos Importantes

```
sistema_rpz_v3_0_0_0/
├── app.py                          # Arquivo principal
├── requirements.txt                 # Dependências
├── credentials/
│   └── credentials.json            # Credenciais Google (opcional)
├── dbs/
│   └── db_app.db                  # Banco de dados SQLite
├── logs/
│   ├── ROUTES_error.log           # Logs de erro
│   └── verif_forms_google.txt     # Logs da integração Google
└── static/                        # Arquivos estáticos (CSS, JS)
```

## ⚙️ Configurações Avançadas

### **Porta Personalizada**
```bash
# Editar app.py linha final:
app.run(host='0.0.0.0', port=8080, debug=False)
```

### **Servidor de Produção**
```bash
# Usar waitress (já incluído):
waitress-serve --host=0.0.0.0 --port=8080 app:app
```

### **Variáveis de Ambiente**
```bash
# Criar arquivo .env (opcional):
FLASK_ENV=production
FLASK_DEBUG=False
```

## 🔍 Troubleshooting

### **Erro: "ModuleNotFoundError"**
```bash
# Verificar se todas as dependências estão instaladas:
pip list | grep -E "(Flask|pandas|gspread)"
```

### **Erro: "Port already in use"**
```bash
# Mudar porta no app.py ou matar processo:
netstat -ano | findstr :5000
taskkill /PID [PID] /F
```

### **Integração Google não funciona**
1. Verificar se `credentials.json` existe
2. Verificar se APIs estão ativadas no Google Cloud
3. Verificar se recursos estão compartilhados
4. Verificar logs em `logs/verif_forms_google.txt`

### **Banco de dados corrompido**
```bash
# Fazer backup e restaurar:
cp dbs/db_app.db dbs/db_app_backup.db
# Restaurar de backup se necessário
```

## 📞 Suporte

- **Logs:** Verificar arquivos em `logs/`
- **Testes:** Executar `python test_google_integration.py`
- **Documentação:** Verificar `GOOGLE_SETUP.md` para configuração Google

## 🚀 Deploy em Produção

### **Usando Waitress (Recomendado)**
```bash
waitress-serve --host=0.0.0.0 --port=8080 --call app:app
```

### **Usando Gunicorn (Linux)**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### **Usando Docker (Opcional)**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:app"]
```

---

## ✅ Checklist de Instalação

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Sistema executando (`python app.py`)
- [ ] Acesso via navegador (`http://localhost:5000`)
- [ ] Login funcionando
- [ ] Integração Google configurada (opcional)
- [ ] Logs funcionando
- [ ] Backup do banco de dados

**🎉 Sistema instalado com sucesso!** 