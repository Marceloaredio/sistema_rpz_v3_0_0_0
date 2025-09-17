# 📋 Critérios e Valores - Módulo Fechamento de Ponto

## 📊 Visão Geral

Este documento descreve todos os critérios e valores configurados no sistema de fechamento de ponto, incluindo parâmetros padrão e critérios especiais para diferentes motivos de ausência.

---

## 🎯 Parâmetros Padrão do Sistema

### **Valores Base Configurados**

| Parâmetro | Valor Atual | Descrição |
|-----------|-------------|-----------|
| **Diária Padrão** | R$ 100,00 | Valor padrão da diária para todos os motoristas |
| **Ajuda Alimentação** | R$ 50,00 | Valor padrão da ajuda de alimentação |

---

## 📋 Critérios Especiais por Motivo

### **Critérios Cadastrados no Sistema**

| ID | Motivo | Diária | Alimentação | Descrição |
|----|--------|--------|-------------|-----------|
| 11 | **GARAGEM** | R$ 0,00 | R$ 30,00 | teste |
| 12 | **FOLGA** | R$ 0,00 | R$ 0,00 | - |
| 16 | **TESTE26** | R$ 0,00 | R$ 0,00 | - |
| 17 | **FÉRIAS** | R$ 0,00 | R$ 0,00 | Férias - sem diária e sem alimentação |
| 18 | **AFASTAMENTO** | R$ 0,00 | R$ 0,00 | Afastamento - sem diária e sem alimentação |
| 19 | **ATESTADO** | R$ 0,00 | R$ 0,00 | Atestado médico - sem diária e sem alimentação |
| 20 | **LIC. ÓBITO** | R$ 0,00 | R$ 0,00 | Licença por óbito - sem diária e sem alimentação |
| 21 | **LIC. PATERNIDADE** | R$ 0,00 | R$ 0,00 | Licença paternidade - sem diária e sem alimentação |
| 22 | **LIC. MATERNIDADE** | R$ 0,00 | R$ 0,00 | Licença maternidade - sem diária e sem alimentação |
| 23 | **CARGA/DESCARGA** | R$ 90,00 | R$ 0,00 | - |

---

## 🔄 Comportamento dos Critérios

### **Critérios com Comportamento Especial**

#### **1. GARAGEM e CARGA/DESCARGA**
- **Tipo**: Motivos especiais que requerem dados de jornada
- **Campos Obrigatórios**:
  - Veículo (placa)
  - Início de jornada
  - Fim de jornada
  - Início de refeição
  - Fim de refeição
- **Tabela de Salvamento**: `perm_data_fecham`
- **Cálculo de Carga Horária**:
  - Domingo → 00:00
  - Sábado → 04:00
  - Segunda a sexta → 08:00
  - Feriado → 00:00

#### **2. Outros Motivos (FOLGA, FÉRIAS, etc.)**
- **Tipo**: Motivos simples sem dados de jornada
- **Campos**: Apenas motorista, período e motivo
- **Tabela de Salvamento**: `dayoff_fecham`
- **Cálculo**: Sem carga horária (apenas diária e alimentação)

---

## ⚡ Cálculos Condicionais e Valores Especiais

### **📊 Valores Condicionados aos Critérios**

O sistema aplica valores diferentes baseados no critério selecionado:

#### **Critérios Especiais (GARAGEM, CARGA/DESCARGA)**
- **Diária**: Valor específico do critério (ex: GARAGEM = R$ 0,00, CARGA/DESCARGA = R$ 90,00)
- **Alimentação**: Valor específico do critério (ex: GARAGEM = R$ 30,00, CARGA/DESCARGA = R$ 0,00)
- **Carga Horária**: Calculada baseada no dia da semana
- **Horas Extras**: Calculadas automaticamente
- **Adicional Noturno**: Aplicado quando necessário

#### **Critérios Simples (FOLGA, FÉRIAS, etc.)**
- **Diária**: Valor específico do critério
- **Alimentação**: Valor específico do critério
- **Carga Horária**: 00:00 (sem cálculo)
- **Horas Extras**: 00:00 (sem cálculo)
- **Adicional Noturno**: 00:00 (sem cálculo)

### **🕐 Cálculos de Carga Horária**

#### **Regras de Cálculo por Dia da Semana**
| Dia | Carga Horária | Observação |
|-----|---------------|------------|
| **Domingo** | 00:00 | Sem trabalho |
| **Segunda a Sexta** | 08:00 | Dias úteis |
| **Sábado** | 04:00 | Meio período |
| **Feriado** | 00:00 | Sem trabalho |

#### **Aplicação nos Critérios Especiais**
- **GARAGEM**: Segue as regras padrão de carga horária
- **CARGA/DESCARGA**: Segue as regras padrão de carga horária
- **Outros motivos**: Não aplicam carga horária

### **💰 Cálculos de Horas Extras e Adicionais**

#### **Hora Extra 50%**
- **Quando**: Jornada total > Carga horária
- **Cálculo**: `Hora Extra 50% = Jornada Total - Carga Horária - Hora Extra Noturna`
- **Aplicação**: Apenas para critérios especiais (GARAGEM, CARGA/DESCARGA)

#### **Hora Extra 100%**
- **Quando**: Jornada em domingos/feriados ou após limite
- **Cálculo**: Baseado em regras específicas da empresa
- **Aplicação**: Apenas para critérios especiais

#### **Hora Extra Noturna**
- **Quando**: Trabalho entre 22:00 e 05:00
- **Cálculo**: `Hora Extra Noturna = Tempo noturno - Carga horária noturna`
- **Adicional**: 20% sobre o valor da hora extra noturna
- **Aplicação**: Apenas para critérios especiais

#### **Adicional Noturno**
- **Quando**: Trabalho entre 22:00 e 05:00
- **Cálculo**: 20% sobre o valor da hora normal
- **Aplicação**: Apenas para critérios especiais

### **📋 Exemplo Prático de Cálculos**

#### **Cenário: GARAGEM em Segunda-feira**
- **Jornada**: 06:00 às 18:00 (12 horas)
- **Refeição**: 12:00 às 13:00 (1 hora)
- **Carga Horária**: 08:00 (segunda-feira)
- **Cálculos**:
  - **Tempo Efetivo**: 12:00 - 1:00 = 11:00
  - **Hora Extra 50%**: 11:00 - 8:00 = 3:00
  - **Hora Extra Noturna**: 0:00 (não há trabalho noturno)
  - **Adicional Noturno**: 0:00

#### **Cenário: CARGA/DESCARGA em Sábado**
- **Jornada**: 08:00 às 16:00 (8 horas)
- **Refeição**: 12:00 às 13:00 (1 hora)
- **Carga Horária**: 04:00 (sábado)
- **Cálculos**:
  - **Tempo Efetivo**: 8:00 - 1:00 = 7:00
  - **Hora Extra 50%**: 7:00 - 4:00 = 3:00
  - **Hora Extra Noturna**: 0:00
  - **Adicional Noturno**: 0:00

### **🎯 Valores Específicos por Critério**

#### **GARAGEM**
- **Diária**: R$ 0,00
- **Alimentação**: R$ 30,00
- **Carga Horária**: Calculada por dia da semana
- **Horas Extras**: Calculadas automaticamente

#### **CARGA/DESCARGA**
- **Diária**: R$ 90,00
- **Alimentação**: R$ 0,00
- **Carga Horária**: Calculada por dia da semana
- **Horas Extras**: Calculadas automaticamente

#### **FOLGA, FÉRIAS, AFASTAMENTO, etc.**
- **Diária**: R$ 0,00
- **Alimentação**: R$ 0,00
- **Carga Horária**: 00:00 (sem cálculo)
- **Horas Extras**: 00:00 (sem cálculo)

---

## 📊 Estatísticas dos Critérios

### **Distribuição por Valor de Diária**
- **R$ 0,00**: 8 critérios (80%) - Motivos simples sem trabalho
- **R$ 90,00**: 1 critério (10%) - CARGA/DESCARGA
- **R$ 100,00**: 1 critério (padrão) - Valor base do sistema

### **Distribuição por Valor de Alimentação**
- **R$ 0,00**: 9 critérios (90%) - Sem ajuda de alimentação
- **R$ 30,00**: 1 critério (10%) - GARAGEM
- **R$ 50,00**: 1 critério (padrão) - Valor base do sistema

### **Distribuição por Tipo de Cálculo**
- **Critérios Especiais**: 2 (20%) - GARAGEM, CARGA/DESCARGA
  - Calculam carga horária
  - Calculam horas extras
  - Aplicam adicional noturno
- **Critérios Simples**: 8 (80%) - FOLGA, FÉRIAS, etc.
  - Sem carga horária
  - Sem horas extras
  - Sem adicional noturno

---

## ⚙️ Configuração e Manutenção

### **Como Adicionar Novos Critérios**
1. Acesse o módulo de **Parâmetros de Fechamento**
2. Clique em **"Adicionar Critério"**
3. Preencha:
   - **Motivo**: Nome do critério
   - **Diária**: Valor da diária
   - **Alimentação**: Valor da ajuda de alimentação
   - **Descrição**: Descrição opcional

### **Como Editar Critérios Existentes**
1. Localize o critério na lista
2. Clique no ícone de **editar** (lápis)
3. Modifique os valores desejados
4. Clique em **salvar** (✓)

### **Como Excluir Critérios**
1. Localize o critério na lista
2. Clique no ícone de **excluir** (lixeira)
3. Confirme a exclusão

---

## 🔍 Detalhes Técnicos

### **Estrutura da Tabela `criterios_diaria`**
```sql
CREATE TABLE criterios_diaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_filtro TEXT NOT NULL,
    valor_filtro TEXT NOT NULL,
    valor_diaria REAL NOT NULL,
    valor_ajuda_alimentacao REAL NOT NULL,
    descricao TEXT,
    data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### **Estrutura da Tabela `parametros_fechamento`**
```sql
CREATE TABLE parametros_fechamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_parametro TEXT NOT NULL UNIQUE,
    valor TEXT NOT NULL,
    descricao TEXT,
    ativo INTEGER DEFAULT 1,
    data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
)
```

---

## 📝 Notas Importantes

### **Valores Padrão**
- Quando um critério não é encontrado, o sistema usa os valores padrão:
  - **Diária**: R$ 100,00
  - **Alimentação**: R$ 50,00

### **Normalização de Valores**
- Todos os valores de filtro são normalizados (maiúsculas, sem acentos)
- Evita duplicidade de critérios similares

### **Compatibilidade**
- O sistema é compatível com motivos antigos e novos
- Critérios podem ser editados sem afetar dados históricos

### **Aplicação dos Valores no Sistema**

#### **Fluxo de Cálculo**
1. **Seleção do Critério**: Sistema identifica o tipo de critério
2. **Aplicação de Valores**: 
   - Critérios especiais → Valores específicos + cálculos de jornada
   - Critérios simples → Apenas valores específicos
3. **Cálculos Automáticos**:
   - Carga horária baseada no dia da semana
   - Horas extras quando jornada > carga horária
   - Adicional noturno para trabalho entre 22:00-05:00

#### **Tabelas de Salvamento**
- **Critérios Especiais**: `perm_data_fecham` (com dados de jornada)
- **Critérios Simples**: `dayoff_fecham` (apenas dados básicos)

#### **Valores Condicionais**
- **Diária**: Valor específico do critério ou padrão (R$ 100,00)
- **Alimentação**: Valor específico do critério ou padrão (R$ 50,00)
- **Carga Horária**: Calculada apenas para critérios especiais
- **Horas Extras**: Calculadas apenas para critérios especiais

---

## 🚀 Última Atualização

**Data**: 01/08/2025  
**Versão**: 3.0.0.0  
**Status**: Ativo e Funcionando

---

*Documento gerado automaticamente pelo sistema de fechamento de ponto.* 