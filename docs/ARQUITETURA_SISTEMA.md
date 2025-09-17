# 🏗️ Arquitetura do Sistema RPZ v3.0.0.0

**Versão:** 3.0.0.0  
**Última Atualização:** 15 de Setembro de 2025  
**Status:** ✅ Otimizado e Funcional

---

## 📋 **VISÃO GERAL**

O Sistema RPZ é uma aplicação web Flask para gerenciamento de motoristas com integração Google Sheets e Google Forms. A arquitetura segue o padrão MVC (Model-View-Controller) com separação clara de responsabilidades.

---

## 🏛️ **ARQUITETURA GERAL**

```
sistema_rpz_v3_0_0_0/
├── 📁 app.py                 # Aplicação principal Flask
├── 📁 global_vars.py         # Variáveis globais e constantes
├── 📁 config/                # Configurações do sistema
├── 📁 controller/            # Lógica de negócio (MVC Controller)
├── 📁 model/                 # Modelos de dados (MVC Model)
├── 📁 view/                  # Rotas e templates (MVC View)
├── 📁 static/                # Arquivos estáticos (CSS, JS, imagens)
├── 📁 templates/             # Templates HTML
├── 📁 dbs/                   # Banco de dados SQLite
├── 📁 scripts/               # Scripts utilitários
└── 📁 docs/                  # Documentação
```

---

## 🔧 **COMPONENTES PRINCIPAIS**

### **1. Aplicação Principal (`app.py`)**
- **Função:** Ponto de entrada da aplicação Flask
- **Responsabilidades:**
  - Configuração da aplicação
  - Registro de blueprints
  - Configuração de sessões
  - Tratamento de erros
  - Inicialização do servidor

### **2. Configuração Global (`global_vars.py`)**
- **Função:** Central de constantes e configurações
- **Conteúdo:**
  - Configurações de debug
  - Caminhos de arquivos
  - Constantes de tempo (legislação trabalhista)
  - Dicionário de infrações
  - Extensões de arquivo permitidas

### **3. Controladores (`controller/`)**
- **Função:** Lógica de negócio e processamento de dados
- **Arquivos principais:**
  - `utils.py` - Utilitários gerais e logging
  - `data.py` - Processamento de dados de rastreamento
  - `infractions.py` - Cálculo de infrações trabalhistas
  - `infractions_data.py` - Funções auxiliares para infrações
  - `google_integration.py` - Integração com Google Sheets/Forms
  - `google_sheets.py` - Gerenciamento de planilhas Google

### **4. Modelos (`model/`)**
- **Função:** Representação dos dados e acesso ao banco
- **Estrutura:**
  - `db_model.py` - Classes de entidades (User, Truck, Motorist, etc.)
  - `drivers/` - Drivers de acesso ao banco de dados
    - `general_driver.py` - Driver base
    - `motorist_driver.py` - Operações com motoristas
    - `truck_driver.py` - Operações com veículos
    - `user_driver.py` - Operações com usuários

### **5. Visualizações (`view/`)**
- **Função:** Rotas HTTP e renderização de templates
- **Arquivos principais:**
  - `public_routes.py` - Rotas públicas (login)
  - `common_routes.py` - Rotas comuns (logout, home)
  - `track_routes.py` - Rotas de rastreamento
  - `closure_routes.py` - Rotas de fechamento
  - `config_routes.py` - Rotas de configuração
  - `parameters_route.py` - Rotas de parâmetros

---

## 🗄️ **BANCO DE DADOS**

### **Tecnologia:** SQLite 3
### **Localização:** `dbs/db_app.db`
### **Tabelas Principais:**

#### **Entidades Core:**
- `motorists` - Dados dos motoristas
- `trucks` - Dados dos veículos
- `users` - Usuários do sistema
- `companies` - Empresas

#### **Dados de Rastreamento:**
- `vehicle_data` - Dados brutos de rastreamento
- `perm_data` - Dados de permissões
- `dayoff` - Dados de folgas

#### **Dados de Fechamento:**
- `vehicle_data_fecham` - Dados de fechamento
- `perm_data_fecham` - Permissões de fechamento
- `dayoff_fecham` - Folgas de fechamento

#### **Infrações e Análises:**
- `infractions` - Infrações trabalhistas
- `infractions_old` - Infrações antigas
- `removed_infractions` - Infrações removidas

#### **Configurações:**
- `criterios_diaria` - Critérios diários
- `parametros_fechamento` - Parâmetros de fechamento
- `feriados_regionais` - Feriados regionais

#### **Auditoria:**
- `closure_block_classifications` - Classificações de blocos
- `closure_block_classifications_audit` - Auditoria de classificações

---

## 🎨 **INTERFACE DO USUÁRIO**

### **Tecnologias Frontend:**
- **HTML5** - Estrutura das páginas
- **CSS3** - Estilização (11 arquivos otimizados)
- **JavaScript** - Interatividade (7 arquivos)
- **Bootstrap** - Framework CSS
- **Font Awesome** - Ícones
- **DataTables** - Tabelas interativas

### **Templates Principais:**
- `login.html` - Página de login
- `home.html` - Página inicial
- `main.html` - Layout principal
- `motorist_config.html` - Configuração de motoristas
- `track.html` - Rastreamento
- `closure.html` - Fechamento

---

## 🔌 **INTEGRAÇÕES EXTERNAS**

### **Google Sheets:**
- **Função:** Sincronização de dados de motoristas
- **Implementação:** `controller/google_integration.py`
- **Autenticação:** Service Account JSON

### **Google Forms:**
- **Função:** Atualização automática de formulários
- **Implementação:** `controller/google_integration.py`
- **Método:** Google Forms API

---

## 📊 **FLUXO DE DADOS**

### **1. Entrada de Dados:**
```
Arquivo Excel/CSV → data.py → processamento → banco de dados
```

### **2. Cálculo de Infrações:**
```
Dados de rastreamento → infractions.py → análise → registro de infrações
```

### **3. Integração Google:**
```
Banco de dados → google_integration.py → Google Sheets/Forms
```

### **4. Geração de Relatórios:**
```
Dados processados → templates → HTML/PDF → usuário
```

---

## 🛡️ **SEGURANÇA**

### **Autenticação:**
- Sistema de login com sessões
- Controle de acesso por rotas
- Decorator `@route_access_required`

### **Validação de Dados:**
- Validação de CPF/CNH
- Sanitização de entradas
- Verificação de tipos de arquivo

### **Logs e Auditoria:**
- Logs detalhados de operações
- Rastreamento de mudanças
- Sistema de backup automático

---

## ⚡ **PERFORMANCE**

### **Otimizações Implementadas:**
- **Banco de dados:** VACUUM e ANALYZE executados
- **Arquivos estáticos:** CSS consolidado
- **Código:** Funções wrapper removidas
- **Cache:** Pastas __pycache__ eliminadas

### **Métricas de Performance:**
- **Tamanho reduzido:** ~6.5MB
- **Arquivos otimizados:** 12 removidos
- **Banco otimizado:** 1 tabela vazia removida
- **Cache limpo:** 394 pastas removidas

---

## 🔧 **MANUTENÇÃO**

### **Scripts de Apoio:**
- `scripts/cleanup_helper.py` - Limpeza do sistema
- `scripts/validation_helper.py` - Validação de integridade
- `scripts/rollback_helper.py` - Rollback de mudanças

### **Logs do Sistema:**
- `logs/` - Diretório de logs
- Categorização por módulo
- Rotação automática

### **Backup:**
- Backup automático do banco
- Versionamento de configurações
- Scripts de restauração

---

## 📈 **MÉTRICAS DO SISTEMA**

### **Estatísticas Atuais:**
- **Total de arquivos:** ~6.330
- **Tamanho do projeto:** ~58.5MB
- **Linhas de código:** ~12.000
- **Tabelas de banco:** 21
- **Templates HTML:** 41
- **Arquivos CSS:** 11
- **Arquivos JS:** 7

### **Dependências Python:**
- **Flask** - Framework web
- **Pandas** - Processamento de dados
- **SQLite3** - Banco de dados
- **Gspread** - Google Sheets API
- **ReportLab** - Geração de PDF
- **OpenPyXL** - Manipulação de Excel

---

## 🚀 **DEPLOY E CONFIGURAÇÃO**

### **Requisitos do Sistema:**
- Python 3.8+
- SQLite 3
- Navegador web moderno
- Acesso à internet (para integração Google)

### **Configuração:**
1. Instalar dependências: `pip install -r requirements.txt`
2. Configurar `config/config.ini`
3. Executar: `python app.py`
4. Acessar: `http://localhost:5000`

### **Variáveis de Ambiente:**
- `DEBUG` - Modo de debug
- `HOST` - Host do servidor
- `PORT` - Porta do servidor
- `SECRET_KEY` - Chave secreta da sessão

---

## 📚 **DOCUMENTAÇÃO ADICIONAL**

- `docs/README.md` - Guia principal
- `docs/INSTALACAO.md` - Instruções de instalação
- `docs/GOOGLE_SETUP.md` - Configuração Google
- `docs/RELATORIO_FINAL_LIMPEZA.md` - Relatório de otimização

---

**Documentação gerada automaticamente pelo Sistema RPZ v3.0.0.0**  
**Data:** 15 de Setembro de 2025  
**Status:** ✅ ATUALIZADO E OTIMIZADO




