# 📋 Manual do Usuário: Carga Horária em Critérios Especiais

## 🎯 **Visão Geral**

Este manual descreve como utilizar a nova funcionalidade de **"Carga Horária Especial"** no módulo de Fechamento de Ponto do Sistema RPZ. Esta funcionalidade permite configurar valores específicos de carga horária para diferentes motivos de ausência, além do comportamento padrão baseado em dias da semana e feriados.

---

## ✨ **Funcionalidades Principais**

### **1. Configuração de Carga Horária Especial**
- **Dropdown de seleção** com opções de 00:00 a 12:00 horas
- **Valor "Padrão"** para manter comportamento existente
- **Integração automática** com cálculos de hora extra 50%

### **2. Critérios Especiais Suportados**
- **GARAGEM**: Configuração específica para motoristas na garagem
- **CARGA/DESCARGA**: Configuração para operações de carga/descarga
- **Critérios personalizados**: Qualquer motivo pode ter carga horária especial

### **3. Cálculos Automáticos**
- **Hora Extra 50%**: Calculada automaticamente baseada na carga horária especial
- **Integração com relatórios**: Valores aparecem nas exportações PDF e Excel
- **Compatibilidade total**: Funciona com sistema existente

---

## 🚀 **Como Usar**

### **Passo 1: Acessar Configurações**
1. Navegue para **"Parâmetros"** → **"Fechamento de Ponto"**
2. Localize a seção **"Critérios Especiais"**
3. Clique em **"Adicionar Novo Critério"** ou edite um existente

### **Passo 2: Configurar Carga Horária**
1. **Preencha os campos básicos**:
   - **Motivo/Placa**: Nome do critério (ex: GARAGEM, FOLGA, etc.)
   - **Valor da Diária**: Valor em reais para o critério
   - **Ajuda Alimentação**: Valor da ajuda alimentação

2. **Configure a Carga Horária**:
   - **Dropdown "Carga Horária"**: Selecione o valor desejado
   - **Opções disponíveis**:
     - **"Padrão"**: Usa regras existentes (dias úteis, sábados, domingos, feriados)
     - **"00:00"** a **"12:00"**: Horas específicas (apenas horas inteiras)

### **Passo 3: Salvar e Aplicar**
1. Clique em **"Adicionar Critério"** ou **"Salvar"**
2. O sistema aplica automaticamente a nova configuração
3. Os cálculos são atualizados em tempo real

---

## 📊 **Exemplos de Configuração**

### **Exemplo 1: GARAGEM com 6 horas**
```
Motivo/Placa: GARAGEM
Valor da Diária: R$ 0,00
Ajuda Alimentação: R$ 25,00
Carga Horária: 06:00
```
**Resultado**: Motoristas na garagem terão carga horária de 6 horas, independente do dia da semana.

### **Exemplo 2: FOLGA com regras padrão**
```
Motivo/Placa: FOLGA
Valor da Diária: R$ 0,00
Ajuda Alimentação: R$ 0,00
Carga Horária: Padrão
```
**Resultado**: Usa regras existentes (0h domingos/feriados, 4h sábados, 8h dias úteis).

### **Exemplo 3: CARGA/DESCARGA com 4 horas**
```
Motivo/Placa: CARGA/DESCARGA
Valor da Diária: R$ 50,00
Ajuda Alimentação: R$ 20,00
Carga Horária: 04:00
```
**Resultado**: Operações de carga/descarga terão carga horária de 4 horas.

---

## 🧮 **Como os Cálculos Funcionam**

### **Carga Horária Especial Ativa**
- **Quando configurado**: Usa o valor específico (ex: 06:00 = 360 minutos)
- **Hora Extra 50%**: Calculada como `Jornada Total - Carga Horária Especial`
- **Exemplo**: Jornada de 8h com carga horária de 6h = 2h de hora extra

### **Carga Horária Padrão**
- **Quando "Padrão"**: Usa regras existentes do sistema
- **Dias úteis**: 8 horas (480 minutos)
- **Sábados**: 4 horas (240 minutos)
- **Domingos/Feriados**: 0 horas

### **Critérios com Jornada**
- **GARAGEM e CARGA/DESCARGA**: Podem ter jornada informada pelo usuário
- **H. Trabalhadas**: Usa valor informado para cálculos de hora extra
- **Outros critérios**: H. Trabalhadas = 0 por padrão

---

## 📋 **Regras e Limitações**

### **Valores Permitidos**
- **Formato**: Apenas horas inteiras (HH:00)
- **Range**: 00:00 a 12:00
- **Padrão**: Valor "Padrão" para comportamento existente

### **Critérios Fixos**
- **GARAGEM**: Não pode ser excluído (critério fixo)
- **CARGA/DESCARGA**: Não pode ser excluído (critério fixo)
- **Outros critérios**: Podem ser editados e excluídos normalmente

### **Validações**
- **Frontend**: Dropdown controla valores válidos
- **Backend**: Validação antes de salvar no banco
- **Formato**: Aceita apenas "Padrão" ou "HH:00"

---

## 🔍 **Verificando Configurações**

### **Lista de Critérios**
1. Na seção **"Critérios Especiais"**
2. Visualize todos os critérios configurados
3. **Carga Horária** aparece na lista para cada critério
4. Clique no ícone de **editar** para modificar

### **Edição de Critérios**
1. Clique no ícone **✏️ (editar)** do critério
2. Modifique o campo **"Carga Horária"**
3. Clique em **✓ (salvar)** para aplicar mudanças
4. Clique em **✗ (cancelar)** para descartar

---

## 📊 **Relatórios e Exportações**

### **Tabelas HTML**
- **Coluna "Carga Horária"**: Mostra valor especial se configurado
- **Coluna "H.E. 50%"**: Calculada automaticamente baseada na carga horária
- **Valores especiais**: Aparecem destacados quando aplicável

### **Exportação Excel**
- **Mesmas colunas**: Carga Horária e H.E. 50%
- **Valores especiais**: Populam as colunas existentes
- **Formato**: Mantém formatação e estilos existentes

### **Exportação PDF**
- **Layout consistente**: Mesma estrutura das tabelas HTML
- **Valores especiais**: Aparecem normalmente nas colunas correspondentes

---

## ⚠️ **Troubleshooting**

### **Problema: Dropdown não aparece**
**Solução**: Verifique se está na tela correta (Parâmetros → Fechamento de Ponto)

### **Problema: Valor não é salvo**
**Solução**: 
1. Verifique se todos os campos obrigatórios estão preenchidos
2. Certifique-se de clicar em "Salvar"
3. Recarregue a página se necessário

### **Problema: Cálculos não atualizam**
**Solução**:
1. Verifique se o critério foi salvo corretamente
2. Confirme se a carga horária não está como "Padrão"
3. Teste com um critério diferente

### **Problema: Erro ao editar critério**
**Solução**:
1. Verifique se o critério não é GARAGEM ou CARGA/DESCARGA
2. Tente recarregar a página
3. Verifique permissões de usuário

---

## 🔧 **Configurações Técnicas**

### **Feature Flag**
- **Controle**: Funcionalidade pode ser ativada/desativada
- **Configuração**: Arquivo `config/config.ini`
- **Seção**: `[FECHAMENTO]`
- **Chave**: `CARGA_HORARIA_ESPECIAL_ENABLED`

### **Banco de Dados**
- **Tabela**: `criterios_diaria`
- **Coluna**: `carga_horaria_especial`
- **Valor padrão**: "Padrão"
- **Tipo**: TEXT

### **Compatibilidade**
- **Sistema existente**: Totalmente compatível
- **Dados históricos**: Preservados
- **Funcionalidades**: Todas mantidas

---

## 📞 **Suporte**

### **Em caso de dúvidas**
1. **Verifique este manual** primeiro
2. **Teste com dados simples** para isolar o problema
3. **Contate o suporte técnico** com detalhes do problema

### **Informações para suporte**
- **Versão do sistema**: RPZ v3.0.0.0
- **Módulo**: Fechamento de Ponto
- **Funcionalidade**: Carga Horária Especial
- **Data de implementação**: Agosto/2025

---

## 📝 **Changelog**

### **Versão 1.0 (Agosto/2025)**
- ✅ Implementação inicial da funcionalidade
- ✅ Interface de configuração completa
- ✅ Cálculos automáticos integrados
- ✅ Exportações PDF/Excel funcionais
- ✅ Testes de integração e performance
- ✅ Documentação completa

---

*Manual criado em 01/08/2025 - Versão 1.0*  
*Sistema RPZ v3.0.0.0 - Módulo Fechamento de Ponto*
