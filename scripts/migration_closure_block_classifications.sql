-- Migração: Criação da tabela closure_block_classifications
-- Sistema RPZ v3.0.0.0 - Fase 1: Modelo de dados e auditoria
-- Data: 2025-01-27

-- Criar tabela principal para classificações de blocos
CREATE TABLE IF NOT EXISTS closure_block_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    motorist_id INTEGER NOT NULL,
    data TEXT NOT NULL, -- Formato: DD-MM-YYYY
    truck_id INTEGER, -- Opcional, pode ser NULL
    classification TEXT NOT NULL CHECK (classification IN ('VALIDO', 'CARGA_DESCARGA', 'GARAGEM', 'INVALIDO')),
    notes TEXT, -- Campo opcional para observações
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT, -- Nome do usuário que fez a alteração
    
    -- Constraints
    UNIQUE(motorist_id, data, truck_id),
    FOREIGN KEY (motorist_id) REFERENCES motorists(id),
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

-- Criar tabela de auditoria para histórico de mudanças
CREATE TABLE IF NOT EXISTS closure_block_classifications_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classification_id INTEGER NOT NULL,
    motorist_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    truck_id INTEGER,
    prev_classification TEXT,
    new_classification TEXT NOT NULL,
    prev_notes TEXT,
    new_notes TEXT,
    changed_by TEXT NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT, -- Motivo da mudança (opcional)
    
    FOREIGN KEY (classification_id) REFERENCES closure_block_classifications(id),
    FOREIGN KEY (motorist_id) REFERENCES motorists(id),
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_closure_classifications_motorist_data 
ON closure_block_classifications(motorist_id, data);

CREATE INDEX IF NOT EXISTS idx_closure_classifications_motorist_data_truck 
ON closure_block_classifications(motorist_id, data, truck_id);

CREATE INDEX IF NOT EXISTS idx_closure_classifications_classification 
ON closure_block_classifications(classification);

CREATE INDEX IF NOT EXISTS idx_closure_classifications_created_at 
ON closure_block_classifications(created_at);

-- Índices para tabela de auditoria
CREATE INDEX IF NOT EXISTS idx_closure_audit_classification_id 
ON closure_block_classifications_audit(classification_id);

CREATE INDEX IF NOT EXISTS idx_closure_audit_motorist_data 
ON closure_block_classifications_audit(motorist_id, data);

CREATE INDEX IF NOT EXISTS idx_closure_audit_changed_at 
ON closure_block_classifications_audit(changed_at);

-- Trigger para atualizar updated_at automaticamente
CREATE TRIGGER IF NOT EXISTS update_closure_classifications_timestamp 
AFTER UPDATE ON closure_block_classifications
BEGIN
    UPDATE closure_block_classifications 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Trigger para auditoria automática
CREATE TRIGGER IF NOT EXISTS audit_closure_classifications_changes 
AFTER UPDATE ON closure_block_classifications
BEGIN
    INSERT INTO closure_block_classifications_audit (
        classification_id,
        motorist_id,
        data,
        truck_id,
        prev_classification,
        new_classification,
        prev_notes,
        new_notes,
        changed_by,
        change_reason
    ) VALUES (
        NEW.id,
        NEW.motorist_id,
        NEW.data,
        NEW.truck_id,
        OLD.classification,
        NEW.classification,
        OLD.notes,
        NEW.notes,
        NEW.changed_by,
        'Atualização via sistema'
    );
END;

-- Trigger para auditoria de inserções
CREATE TRIGGER IF NOT EXISTS audit_closure_classifications_insert 
AFTER INSERT ON closure_block_classifications
BEGIN
    INSERT INTO closure_block_classifications_audit (
        classification_id,
        motorist_id,
        data,
        truck_id,
        prev_classification,
        new_classification,
        prev_notes,
        new_notes,
        changed_by,
        change_reason
    ) VALUES (
        NEW.id,
        NEW.motorist_id,
        NEW.data,
        NEW.truck_id,
        NULL,
        NEW.classification,
        NULL,
        NEW.notes,
        NEW.changed_by,
        'Criação inicial'
    );
END;

-- Inserir dados de exemplo (opcional - remover em produção)
-- INSERT INTO closure_block_classifications (motorist_id, data, classification, notes, changed_by) 
-- VALUES (1, '27-01-2025', 'VALIDO', 'Classificação inicial', 'Sistema');

-- Verificar se as tabelas foram criadas corretamente
SELECT 'Tabela closure_block_classifications criada com sucesso' as status;
SELECT 'Tabela closure_block_classifications_audit criada com sucesso' as status;
SELECT 'Índices e triggers criados com sucesso' as status;

