# 📁 Scripts do Sistema RPZ

Esta pasta contém todos os scripts organizados por categoria para facilitar o uso e manutenção.

## 📂 **Estrutura de Pastas:**

### 📥 **`import/`** - Scripts de Importação
- Scripts para importar dados de motoristas
- Correção de IDs e limpeza de dados
- **4 scripts disponíveis**

### 🔍 **`check/`** - Scripts de Verificação
- Scripts de diagnóstico e validação
- Verificação de estrutura de dados
- **3 scripts disponíveis**

### ⚙️ **`admin/`** - Scripts Administrativos
- Operações críticas do sistema
- Desativação e exclusão de dados
- **2 scripts disponíveis**

### 🧪 **`test/`** - Scripts de Teste
- Validação de integrações
- Testes de conectividade
- **1 script disponível**

## 🚀 **Como Usar:**

### **Execução de Scripts:**
```bash
# Scripts de importação
python scripts/import/import_motorists_excel.py

# Scripts de verificação
python scripts/check/check_email.py

# Scripts administrativos
python scripts/admin/deactivate_motorist.py

# Scripts de teste
python scripts/test/test_google_integration.py
```

### **Ordem Recomendada:**
1. **Verificação:** Execute scripts de `check/` primeiro
2. **Teste:** Valide com scripts de `test/`
3. **Importação:** Use scripts de `import/` conforme necessário
4. **Administração:** Use scripts de `admin/` com cuidado

## ⚠️ **Avisos Importantes:**
- **Backup:** Sempre faça backup antes de executar scripts
- **Logs:** Monitore logs durante execução
- **Teste:** Teste em ambiente de desenvolvimento primeiro
- **Permissões:** Verifique permissões antes de executar

## 📋 **Documentação:**
- Cada pasta tem seu próprio README.md
- Consulte a documentação específica antes de usar
- Verifique logs após execução 