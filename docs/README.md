# 🚀 Sistema RPZ v3.0.0.0

Sistema de gerenciamento de motoristas com integração Google Sheets e Google Forms.

> **✨ Versão Otimizada:** Esta versão passou por um processo completo de limpeza e otimização, resultando em melhor performance e código mais limpo.

## 📋 Características

- ✅ **Gestão de Motoristas:** Cadastro, edição, visualização e exclusão
- ✅ **Integração Google:** Sincronização automática com Google Sheets e Forms
- ✅ **Interface Moderna:** Design responsivo e intuitivo
- ✅ **Validações:** CPF, CNH, datas e campos obrigatórios
- ✅ **Logs Detalhados:** Rastreamento completo de todas as operações
- ✅ **Backup Automático:** Sistema de backup do banco de dados
- ✅ **Multi-usuário:** Sistema de login e controle de acesso

## 🧹 Otimizações Realizadas (v3.0.0.0)

### **Limpeza de Código:**
- ✅ Removidos arquivos duplicados e desnecessários
- ✅ Consolidadas funções wrapper redundantes
- ✅ Eliminados imports duplicados
- ✅ Removida tabela vazia do banco de dados

### **Otimização de Arquivos:**
- ✅ Consolidados arquivos CSS redundantes
- ✅ Removidos arquivos de documentação obsoletos
- ✅ Eliminadas pastas `__pycache__` (394 removidas)
- ✅ Otimizado banco de dados (redução de ~3.35MB)

### **Melhorias de Performance:**
- ✅ Código mais limpo e organizado
- ✅ Menor uso de espaço em disco
- ✅ Carregamento mais rápido
- ✅ Manutenibilidade melhorada

## 🚀 Instalação Rápida

### **Windows:**
```bash
# Executar o instalador automático
install.bat

# Ou instalação manual:
pip install -r requirements.txt
python app.py
```

### **Linux/Mac:**
```bash
# Executar o instalador automático
chmod +x install.sh
./install.sh

# Ou instalação manual:
pip3 install -r requirements.txt
python3 app.py
```

## 🔧 Configuração

### **1. Acesso ao Sistema**
- **URL:** http://localhost:5000
- **Login:** admin@admin.com
- **Senha:** root12345

### **2. Integração Google (Opcional)**

#### **Instalar Dependências Google:**
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

#### **Configurar Credenciais:**
1. Crie projeto no [Google Cloud Console](https://console.cloud.google.com/)
2. Ative as APIs: **Google Sheets API** e **Google Forms API**
3. Crie uma **Service Account**
4. Baixe o arquivo JSON de credenciais
5. Renomeie para `credentials.json`
6. Coloque na pasta `credentials/`

#### **Compartilhar Recursos:**
- **Planilha Google Sheets:** Compartilhe com o email da Service Account
- **Google Forms:** Compartilhe cada formulário com o email da Service Account

#### **Testar Configuração:**
```bash
python test_google_integration.py
```

## 📁 Estrutura do Projeto

```
sistema_rpz_v3_0_0_0/
├── app.py                          # Aplicação principal
├── requirements.txt                 # Dependências Python
├── install.bat                     # Instalador Windows
├── install.sh                      # Instalador Linux/Mac
├── INSTALACAO.md                  # Guia detalhado de instalação
├── GOOGLE_SETUP.md                # Configuração Google
├── credentials/
│   └── credentials.json            # Credenciais Google (opcional)
├── dbs/
│   └── db_app.db                  # Banco de dados SQLite
├── logs/
│   ├── ROUTES_error.log           # Logs de erro
│   └── verif_forms_google.txt     # Logs da integração Google
├── static/                        # Arquivos estáticos
│   ├── css/                       # Estilos CSS
│   └── js/                        # JavaScript
├── templates/                     # Templates HTML
├── controller/                    # Lógica de controle
├── model/                         # Modelos de dados
└── view/                          # Rotas e views
```

## 🔗 Funcionalidades

### **Gestão de Motoristas**
- ✅ Cadastro completo com validações
- ✅ Edição inline nos detalhes
- ✅ Visualização em cards responsivos
- ✅ Exclusão lógica (status "Desligado")
- ✅ Filtros e busca
- ✅ Status automático baseado em vencimentos

### **Integração Google**
- ✅ Inserção automática no Google Sheets
- ✅ Ordenação alfabética da planilha
- ✅ Atualização de 9 Google Forms
- ✅ Logs detalhados de todas as operações
- ✅ Timeout para evitar travamentos

### **Interface**
- ✅ Design moderno e responsivo
- ✅ Modais para cadastro e edição
- ✅ Indicadores visuais de status
- ✅ Validação em tempo real
- ✅ Máscaras de entrada (CPF, CNH, etc.)

## ⚙️ Configurações Avançadas

### **Porta Personalizada**
```python
# Editar app.py linha final:
app.run(host='0.0.0.0', port=8080, debug=False)
```

### **Servidor de Produção**
```bash
# Usar waitress (recomendado):
waitress-serve --host=0.0.0.0 --port=8080 app:app

# Ou usar gunicorn (Linux):
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### **Docker (Opcional)**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:app"]
```

## 🔍 Troubleshooting

### **Erro: "ModuleNotFoundError"**
```bash
# Verificar dependências:
pip list | grep -E "(Flask|pandas|gspread)"
```

### **Erro: "Port already in use"**
```bash
# Windows:
netstat -ano | findstr :5000
taskkill /PID [PID] /F

# Linux/Mac:
lsof -i :5000
kill -9 [PID]
```

### **Integração Google não funciona**
1. Verificar se `credentials.json` existe
2. Verificar se APIs estão ativadas no Google Cloud
3. Verificar se recursos estão compartilhados
4. Verificar logs em `logs/verif_forms_google.txt`

### **Banco de dados corrompido**
```bash
# Fazer backup:
cp dbs/db_app.db dbs/db_app_backup.db
# Restaurar de backup se necessário
```

## 📊 Logs e Monitoramento

### **Arquivos de Log**
- `logs/ROUTES_error.log` - Erros gerais do sistema
- `logs/verif_forms_google.txt` - Logs da integração Google

### **Monitoramento**
- Status dos motoristas atualizado automaticamente
- Logs de todas as operações de CRUD
- Rastreamento de erros com códigos únicos

## 🔒 Segurança

- ✅ Validação de entrada em todos os campos
- ✅ Sanitização de dados
- ✅ Controle de acesso por usuário
- ✅ Logs de auditoria
- ✅ Backup automático do banco

## 📞 Suporte

### **Documentação**
- `INSTALACAO.md` - Guia completo de instalação
- `GOOGLE_SETUP.md` - Configuração da integração Google
- `README.md` - Este arquivo

### **Testes**
```bash
# Testar integração Google:
python test_google_integration.py

# Verificar logs:
tail -f logs/verif_forms_google.txt
```

### **Contato**
- Verificar logs em `logs/`
- Executar testes de integração
- Consultar documentação específica

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

---

**Versão:** 2.0.0.2  
**Última atualização:** Agosto 2025  
**Desenvolvido para:** Sistema RPZ 