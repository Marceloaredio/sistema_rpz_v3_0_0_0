# 🧹 Scripts de Limpeza do Sistema RPZ

## 📋 **Visão Geral**

Este diretório contém todos os scripts necessários para executar o plano de limpeza do Sistema RPZ de forma segura e controlada.

## 🚀 **Scripts Principais**

### **1. cleanup_orchestrator.py** - Orquestrador Principal
**Função:** Executa todo o processo de limpeza de forma controlada

```bash
# Executar limpeza completa
python scripts/cleanup_orchestrator.py all

# Executar fase específica
python scripts/cleanup_orchestrator.py phase 2

# Retomar limpeza interrompida
python scripts/cleanup_orchestrator.py resume 3

# Verificar status atual
python scripts/cleanup_orchestrator.py status
```

### **2. cleanup_helper.py** - Helper de Limpeza
**Função:** Executa tarefas específicas de limpeza e análise

```bash
# Análise completa
python scripts/cleanup_helper.py full

# Comandos específicos
python scripts/cleanup_helper.py backup      # Criar backup
python scripts/cleanup_helper.py deps        # Verificar dependências
python scripts/cleanup_helper.py imports     # Verificar imports
python scripts/cleanup_helper.py duplicates  # Procurar duplicatas
python scripts/cleanup_helper.py pycache     # Remover __pycache__
python scripts/cleanup_helper.py gitignore   # Atualizar .gitignore
python scripts/cleanup_helper.py report      # Gerar relatório
```

### **3. validation_helper.py** - Helper de Validação
**Função:** Valida se as funcionalidades estão funcionando após cada fase

```bash
# Validação completa
python scripts/validation_helper.py full

# Validação por fase
python scripts/validation_helper.py phase 2

# Validações específicas
python scripts/validation_helper.py critical  # Arquivos críticos
python scripts/validation_helper.py database  # Banco de dados
python scripts/validation_helper.py web       # Aplicação web
```

### **4. rollback_helper.py** - Helper de Rollback
**Função:** Permite reverter mudanças em caso de problemas

```bash
# Listar backups disponíveis
python scripts/rollback_helper.py list

# Restauração interativa
python scripts/rollback_helper.py interactive

# Restaurar fase específica
python scripts/rollback_helper.py phase 2

# Restauração de emergência
python scripts/rollback_helper.py emergency

# Criar ponto de restauração
python scripts/rollback_helper.py point
```

## 📊 **Fluxo de Execução Recomendado**

### **1. Preparação Inicial**
```bash
# 1. Verificar se estamos no diretório correto
pwd  # Deve estar em sistema_rpz_v3_0_0_0

# 2. Executar análise completa
python scripts/cleanup_helper.py full

# 3. Verificar se tudo está funcionando
python scripts/validation_helper.py critical
```

### **2. Execução da Limpeza**
```bash
# Opção 1: Execução automática completa
python scripts/cleanup_orchestrator.py all

# Opção 2: Execução fase por fase (recomendado)
python scripts/cleanup_orchestrator.py phase 1
python scripts/validation_helper.py phase 1
python scripts/cleanup_orchestrator.py phase 2
python scripts/validation_helper.py phase 2
# ... e assim por diante
```

### **3. Em Caso de Problemas**
```bash
# 1. Parar imediatamente
# Ctrl+C ou fechar terminal

# 2. Verificar status
python scripts/cleanup_orchestrator.py status

# 3. Executar rollback se necessário
python scripts/rollback_helper.py emergency

# 4. Verificar se sistema voltou ao normal
python scripts/validation_helper.py critical
```

## ⚠️ **Precauções Importantes**

### **Antes de Executar:**
- [ ] **Backup completo** do sistema
- [ ] **Verificar espaço em disco** (pelo menos 2GB livres)
- [ ] **Fechar aplicação** se estiver rodando
- [ ] **Verificar permissões** de escrita
- [ ] **Ler documentação** completa

### **Durante a Execução:**
- [ ] **Não interromper** o processo
- [ ] **Monitorar logs** regularmente
- [ ] **Verificar validações** após cada fase
- [ ] **Manter backups** atualizados

### **Após a Execução:**
- [ ] **Testar funcionalidades** críticas
- [ ] **Verificar performance** do sistema
- [ ] **Atualizar documentação** se necessário
- [ ] **Manter logs** para referência futura

## 📁 **Estrutura de Logs**

```
logs/
├── cleanup.log              # Logs do processo de limpeza
├── validation.log           # Logs de validação
├── rollback.log            # Logs de rollback
├── orchestrator.log        # Logs do orquestrador
└── current_phase.txt       # Fase atual (para retomada)
```

## 🔧 **Configurações**

### **Arquivos de Configuração:**
- `docs/PLANO_LIMPEZA_SISTEMA.md` - Plano detalhado
- `docs/CONFIG_LIMPEZA.md` - Configurações específicas
- `docs/RELATORIO_LIMPEZA.md` - Relatório gerado

### **Variáveis de Ambiente:**
```bash
# Opcional: Definir timeout para comandos
export CLEANUP_TIMEOUT=300

# Opcional: Definir nível de log
export LOG_LEVEL=INFO
```

## 🚨 **Solução de Problemas**

### **Problema: Script não executa**
```bash
# Verificar permissões
chmod +x scripts/*.py

# Verificar Python
python --version

# Verificar dependências
pip install -r requirements.txt
```

### **Problema: Backup falha**
```bash
# Verificar espaço em disco
df -h

# Verificar permissões
ls -la backups/

# Criar diretório manualmente
mkdir -p backups
```

### **Problema: Validação falha**
```bash
# Verificar logs
tail -f logs/validation.log

# Executar validação específica
python scripts/validation_helper.py critical

# Verificar banco de dados
python scripts/validation_helper.py database
```

### **Problema: Rollback falha**
```bash
# Listar backups disponíveis
python scripts/rollback_helper.py list

# Verificar integridade do backup
ls -la backups/

# Executar rollback manual
python scripts/rollback_helper.py restore <backup_name>
```

## 📞 **Suporte**

### **Em caso de problemas:**
1. **Verificar logs** em `logs/`
2. **Consultar documentação** em `docs/`
3. **Executar validações** específicas
4. **Usar rollback** se necessário

### **Comandos de diagnóstico:**
```bash
# Status geral
python scripts/cleanup_orchestrator.py status

# Validação completa
python scripts/validation_helper.py full

# Listar backups
python scripts/rollback_helper.py list

# Verificar logs
tail -f logs/orchestrator.log
```

## 📈 **Métricas de Sucesso**

### **Antes da Limpeza:**
- Arquivos: ~200
- Tamanho: ~50MB
- Linhas de código: ~15.000

### **Após a Limpeza:**
- Arquivos: ~150 (-25%)
- Tamanho: ~35MB (-30%)
- Linhas de código: ~12.000 (-20%)

## 🎯 **Próximos Passos**

Após a limpeza bem-sucedida:

1. **Testar funcionalidades** críticas
2. **Otimizar performance** se necessário
3. **Atualizar documentação** do sistema
4. **Configurar CI/CD** para evitar regressões
5. **Implementar monitoramento** contínuo

---

**Última atualização:** $(date)  
**Versão:** 1.0  
**Status:** Pronto para uso

