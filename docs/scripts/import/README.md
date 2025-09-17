# 📥 Scripts de Importação

Esta pasta contém scripts relacionados à importação de dados no sistema RPZ.

## 📋 **Scripts Disponíveis:**

### `import_motorists_excel.py`
- **Função:** Importa dados de motoristas de arquivos Excel
- **Uso:** Importação principal de dados de motoristas
- **Execução:** `python scripts/import/import_motorists_excel.py`

### `import_correct_ids.py`
- **Função:** Corrige IDs de motoristas no sistema
- **Uso:** Correção de identificadores únicos
- **Execução:** `python scripts/import/import_correct_ids.py`

### `force_clean_import.py`
- **Função:** Importação forçada com limpeza de dados
- **Uso:** Importação quando há dados conflitantes
- **Execução:** `python scripts/import/force_clean_import.py`

### `clean_and_import.py`
- **Função:** Limpeza e importação de dados
- **Uso:** Processo completo de limpeza + importação
- **Execução:** `python scripts/import/clean_and_import.py`

## ⚠️ **Observações:**
- Execute os scripts com cuidado, especialmente os de importação forçada
- Sempre faça backup antes de executar scripts de importação
- Verifique os logs após a execução 