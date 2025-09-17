# 📋 Implementação de Critérios Especiais - Módulo Jornada

## 🎯 Objetivo

Implementar um sistema de critérios especiais personalizados no módulo jornada, permitindo que o usuário cadastre critérios customizados que serão utilizados tanto na geração de blocos de análise quanto na inserção de dados de folgas.

## 🔍 Análise da Situação Atual

### **Problemas Identificados:**
1. **Inconsistência**: `track_analysis.html` usa critérios hardcoded, enquanto `closure_analysis.html` usa dinâmicos
2. **Falta de Flexibilidade**: Usuário não pode criar critérios personalizados
3. **Duplicação**: Critérios fixos em `track_insert_data_page.html` não são reutilizáveis

### **Estrutura Atual:**
- **Módulo Fechamento**: Já possui sistema de critérios dinâmicos via `ParametersDriver`
- **Módulo Jornada**: Usa critérios hardcoded em templates
- **Banco de Dados**: Tabela `criterios_diaria` já existe no módulo fechamento

## 🏗️ Arquitetura da Solução

### **1. Nova Tabela no Módulo Jornada**
```sql
CREATE TABLE IF NOT EXISTS criterios_jornada (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_criterio TEXT NOT NULL UNIQUE,
    abreviacao TEXT NOT NULL UNIQUE, -- 3 letras para identificação rápida
    descricao TEXT,
    requer_horarios INTEGER DEFAULT 0, -- 0=Não, 1=Sim
    tipo_horarios INTEGER DEFAULT 0, -- 0=Campos abertos, 1=Horários pré-definidos
    inicio_jornada TEXT, -- HH:MM (apenas se tipo_horarios=1)
    fim_jornada TEXT,    -- HH:MM (apenas se tipo_horarios=1)
    inicio_refeicao TEXT, -- HH:MM (apenas se tipo_horarios=1)
    fim_refeicao TEXT,   -- HH:MM (apenas se tipo_horarios=1)
    criterio_fixo INTEGER DEFAULT 0, -- 0=Editável, 1=Fixo (não pode editar/excluir)
    ativo INTEGER DEFAULT 1,
    data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### **2. Novo Driver para Critérios de Jornada**
```python
# model/drivers/jornada_criterios_driver.py
class JornadaCriteriosDriver(GeneralDriver):
    def create_tables(self)
    def create_criterio(self, nome, abreviacao, descricao, requer_horarios, tipo_horarios, horarios)
    def get_all_criterios(self)
    def get_criterios_editaveis(self)  # Exclui critérios fixos
    def update_criterio(self, id, dados)  # Valida se não é fixo
    def delete_criterio(self, id)  # Valida se não é fixo
    def create_criterios_fixos(self)  # Cria critérios padrão
    def generate_abreviacao_sugestao(self, nome)  # Gera sugestão de 3 letras
    def validate_abreviacao(self, abreviacao, exclude_id=None)  # Valida unicidade
```

### **3. Critérios Fixos Padrão**
Os seguintes critérios serão criados automaticamente e **não poderão ser editados ou excluídos**:
- **Folga** (FOL) - Sem necessidade de horários
- **Férias** (FÉR) - Sem necessidade de horários  
- **Afastamento** (AFS) - Sem necessidade de horários
- **AT. Médico** (ATM) - Sem necessidade de horários

### **4. Sistema de Abreviações**
- **Campo obrigatório** de 3 letras para identificação rápida
- **Sugestão automática**: Primeiras 3 letras do nome do critério
- **Editável**: Usuário pode modificar a sugestão
- **Validação**: Deve ser único no sistema
- **Critérios fixos**: Abreviações pré-definidas e não editáveis

## 📋 Fases de Implementação

### **FASE 1: Estrutura Base (Semana 1)**

#### **1.1 Criação do Driver**
- [ ] Criar `model/drivers/jornada_criterios_driver.py`
- [ ] Implementar métodos CRUD básicos
- [ ] Implementar validação de critérios fixos
- [ ] Método para criar critérios fixos padrão
- [ ] Testes unitários do driver

#### **1.2 Nova Tabela**
- [ ] Adicionar criação da tabela `criterios_jornada`
- [ ] Criar critérios fixos padrão automaticamente
- [ ] Validação da estrutura
- [ ] Testes de integridade dos critérios fixos

#### **1.3 Rota de Parâmetros**
- [ ] Criar `view/jornada_parameters_routes.py`
- [ ] Rota `GET /jornada/parameters` para listar critérios
- [ ] Rota `POST /jornada/parameters` para criar critério
- [ ] Rota `PUT /jornada/parameters/<id>` para editar critério
- [ ] Rota `DELETE /jornada/parameters/<id>` para excluir critério

### **FASE 2: Interface de Gerenciamento (Semana 2)**

#### **2.1 Template de Parâmetros**
- [ ] Criar `templates/jornada_parameters.html`
- [ ] Formulário para cadastro de critérios
- [ ] Tabela para listagem e edição
- [ ] Modal para confirmação de exclusão
- [ ] Diferenciação visual entre critérios fixos e editáveis

#### **2.2 Funcionalidades da Interface**
- [ ] Validação de campos obrigatórios
- [ ] Campo de abreviação com sugestão automática
- [ ] Validação de unicidade da abreviação
- [ ] Toggle para "Requer definição de horários"
- [ ] Toggle para "Tipo de horários" (Campos abertos vs Pré-definidos)
- [ ] Campos condicionais de horários pré-definidos
- [ ] Validação de formato de horário (HH:MM)
- [ ] Bloqueio de edição/exclusão para critérios fixos
- [ ] Feedback visual de sucesso/erro

#### **2.3 JavaScript de Apoio**
- [ ] `static/js/jornada_parameters.js`
- [ ] Funções para toggle de campos condicionais
- [ ] Geração automática de sugestão de abreviação
- [ ] Validação de formulário em tempo real
- [ ] Validação de unicidade da abreviação via AJAX
- [ ] Confirmação de exclusão (apenas para critérios editáveis)
- [ ] Bloqueio de ações para critérios fixos

### **FASE 3: Integração com Templates Existentes (Semana 3)**

#### **3.1 Atualização do track_analysis.html**
- [ ] Substituir critérios hardcoded por dinâmicos
- [ ] Carregar critérios via `{{ criterias }}`
- [ ] Implementar lógica condicional para campos de horários
- [ ] Aplicar horários pré-definidos quando critério selecionado
- [ ] Manter funcionalidade `toggleCamposHorarios()` para critérios com campos abertos

#### **3.2 Atualização do track_insert_data_page.html**
- [ ] Substituir select hardcoded por dinâmico
- [ ] Carregar critérios via `{{ criterias }}`
- [ ] Manter validação existente
- [ ] Preservar funcionalidade de autocomplete

#### **3.3 Atualização das Rotas de Análise**
- [ ] Modificar `view/track_routes.py`
- [ ] Adicionar carregamento de critérios em `track_analysis()`
- [ ] Adicionar carregamento de critérios em `insert_data()`
- [ ] Manter compatibilidade com código existente

### **FASE 4: Funcionalidades Avançadas (Semana 4)**

#### **4.1 Campos de Horários Dinâmicos**
- [ ] Implementar lógica para critérios que abrem campos
- [ ] Validação de horários predefinidos
- [ ] Aplicação automática de horários nos templates
- [ ] Feedback visual para critérios especiais

#### **4.2 Validações e Melhorias**
- [ ] Validação de horários (início < fim)
- [ ] Prevenção de duplicação de nomes
- [ ] Logs de auditoria para alterações
- [ ] Backup automático de critérios

#### **4.3 Testes e Documentação**
- [ ] Testes de integração
- [ ] Documentação da API
- [ ] Guia do usuário
- [ ] Testes de performance

## 🔧 Detalhamento Técnico

### **Estrutura de Dados do Critério**
```json
{
    "id": 1,
    "nome_criterio": "Manutenção Preventiva",
    "abreviacao": "MAN",
    "descricao": "Veículo em manutenção preventiva",
    "requer_horarios": 1,
    "tipo_horarios": 1,
    "inicio_jornada": "08:00",
    "fim_jornada": "17:00",
    "inicio_refeicao": "12:00",
    "fim_refeicao": "13:00",
    "criterio_fixo": 0,
    "ativo": 1
}
```

### **Tipos de Configuração de Horários**

#### **1. Sem Horários (requer_horarios = 0)**
- Critérios como "Folga", "Férias", "Afastamento", "AT. Médico"
- Não abrem campos de horários
- Aplicação direta sem configurações adicionais

#### **2. Campos Abertos (requer_horarios = 1, tipo_horarios = 0)**
- Usuário preenche horários na hora da análise/inserção
- Campos aparecem dinamicamente quando critério é selecionado
- Flexibilidade total para o usuário

#### **3. Horários Pré-definidos (requer_horarios = 1, tipo_horarios = 1)**
- Horários são definidos no cadastro do critério
- Aplicados automaticamente quando critério é selecionado
- Padronização e agilidade na operação

### **Fluxo de Uso**
1. **Usuário acessa** `/jornada/parameters`
2. **Cadastra critério** com configurações desejadas:
   - Nome e descrição
   - Abreviação (sugestão automática das 3 primeiras letras)
   - Se requer horários (Sim/Não)
   - Se sim: Tipo de horários (Campos abertos/Pré-definidos)
   - Se pré-definidos: Define horários específicos
3. **Sistema valida** unicidade da abreviação
4. **Critério fica disponível** em `track_analysis.html` e `track_insert_data_page.html`
5. **Sistema aplica** configuração conforme critério:
   - **Sem horários**: Aplicação direta
   - **Campos abertos**: Mostra campos para preenchimento
   - **Pré-definidos**: Aplica horários automaticamente

### **Compatibilidade**
- ✅ **Não altera** módulos existentes (fechamento, configurações)
- ✅ **Mantém** funcionalidade atual dos templates
- ✅ **Preserva** validações e lógica existente
- ✅ **Adiciona** funcionalidade sem quebrar código atual

## 📊 Cronograma de Implementação

| Fase | Duração | Entregáveis | Dependências |
|------|---------|-------------|--------------|
| Fase 1 | 1 semana | Driver + Tabela + Rotas | Nenhuma |
| Fase 2 | 1 semana | Interface de Gerenciamento | Fase 1 |
| Fase 3 | 1 semana | Integração com Templates | Fase 1 + 2 |
| Fase 4 | 1 semana | Funcionalidades Avançadas | Fase 3 |

## 🎯 Benefícios Esperados

### **Para o Usuário:**
- ✅ **Flexibilidade**: Criar critérios personalizados
- ✅ **Produtividade**: Horários predefinidos ou campos abertos conforme necessidade
- ✅ **Consistência**: Mesmos critérios em todas as telas
- ✅ **Facilidade**: Interface intuitiva de gerenciamento
- ✅ **Padronização**: Critérios fixos para situações comuns
- ✅ **Controle**: Escolha entre flexibilidade e padronização
- ✅ **Identificação Rápida**: Abreviações de 3 letras para referência rápida
- ✅ **Sugestão Inteligente**: Geração automática de abreviações

### **Para o Sistema:**
- ✅ **Manutenibilidade**: Código organizado e modular
- ✅ **Escalabilidade**: Fácil adição de novos critérios
- ✅ **Consistência**: Padrão único de critérios
- ✅ **Performance**: Carregamento otimizado

## ⚠️ Considerações Importantes

### **Limitações:**
- Critérios são específicos do módulo jornada
- Não interfere com critérios do módulo fechamento
- Migração de dados existentes pode ser necessária

### **Riscos:**
- **Baixo**: Alterações são isoladas no módulo jornada
- **Mitigação**: Testes extensivos em ambiente de desenvolvimento
- **Rollback**: Possível reverter para critérios hardcoded se necessário

## 🚀 Próximos Passos

1. **Aprovação** do plano de implementação
2. **Setup** do ambiente de desenvolvimento
3. **Início** da Fase 1 - Estrutura Base
4. **Revisão** semanal do progresso
5. **Testes** contínuos durante desenvolvimento

---

**Documento criado em:** {{ data_atual }}  
**Versão:** 1.0  
**Autor:** Sistema RPZ v3.0.0.0
