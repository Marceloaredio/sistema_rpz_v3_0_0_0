/**
 * Funcionalidades de edição inline dos motoristas
 * Inclui máscaras, validações e comportamentos específicos para edição
 */

// ===== MÁSCARAS E VALIDAÇÕES PARA EDIÇÃO INLINE =====

function initializeEditMasks() {
    // Máscara para datas (dd/mm/aaaa) - Todos os campos de data
    const dateInputs = document.querySelectorAll('.info-input[placeholder*="dd/mm/aaaa"], .info-input[name*="vencimento"], .info-input[name*="data_"], .info-input[name="primeira_cnh"], .info-input[name="data_expedicao"], .info-input[name="data_admissao"], .info-input[name="data_nascimento"], .info-input[name="done_toxicologico_clt"], .info-input[name="done_toxicologico_cnh"], .info-input[name="done_aso_semestral"], .info-input[name="done_aso_periodico"], .info-input[name="done_mopp"], .info-input[name="done_buonny"]');
    dateInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 8) value = value.substring(0, 8);
            
            if (value.length >= 4) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4) + '/' + value.substring(4);
            } else if (value.length >= 2) {
                value = value.substring(0, 2) + '/' + value.substring(2);
            }
            
            e.target.value = value;
        });
        
        // Validação de data
        input.addEventListener('blur', function() {
            const value = this.value;
            if (value.length > 0 && !isValidDate(value)) {
                showEditFieldError(this, 'Data inválida');
            } else {
                clearEditFieldError(this);
            }
        });
    });

    // Máscara para CPF (000.000.000-00)
    const cpfInputs = document.querySelectorAll('.info-input[name="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.substring(0, 11);
            
            if (value.length >= 10) {
                value = value.substring(0, 3) + '.' + value.substring(3, 6) + '.' + value.substring(6, 9) + '-' + value.substring(9);
            } else if (value.length >= 7) {
                value = value.substring(0, 3) + '.' + value.substring(3, 6) + '.' + value.substring(6);
            } else if (value.length >= 4) {
                value = value.substring(0, 3) + '.' + value.substring(3);
            }
            
            e.target.value = value;
        });
        
        // Validação de CPF
        input.addEventListener('blur', function() {
            const value = this.value.replace(/\D/g, '');
            if (value.length > 0 && value.length !== 11) {
                showEditFieldError(this, 'CPF inválido');
            } else {
                clearEditFieldError(this);
            }
        });
    });

    // Máscara para CNH (apenas números)
    const cnhInputs = document.querySelectorAll('.info-input[name="cnh"]');
    cnhInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
        
        // Validação de CNH
        input.addEventListener('blur', function() {
            const value = this.value.replace(/\D/g, '');
            if (value.length > 0 && value.length !== 11) {
                showEditFieldError(this, 'Número de CNH inválido');
            } else {
                clearEditFieldError(this);
            }
        });
    });

    // Máscara para RG (números e letras)
    const rgInputs = document.querySelectorAll('.info-input[name="rg"]');
    rgInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Permitir números e letras, remover apenas caracteres especiais
            e.target.value = e.target.value.replace(/[^a-zA-Z0-9]/g, '');
        });
    });

    // Máscara para Código SAP (apenas números, máximo 9 dígitos)
    const sapInputs = document.querySelectorAll('.info-input[name="codigo_sap"]');
    sapInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 9);
        });
    });

    // Máscara para CTPS (apenas números, máximo 10 dígitos)
    const ctpsInputs = document.querySelectorAll('.info-input[name="ctps"]');
    ctpsInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 10);
        });
    });

    // Máscara para telefone ((00) 00000-0000)
    const telefoneInputs = document.querySelectorAll('.info-input[name="telefone"]');
    telefoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.substring(0, 11);
            
            if (value.length >= 7) {
                value = '(' + value.substring(0, 2) + ') ' + value.substring(2, 7) + '-' + value.substring(7);
            } else if (value.length >= 3) {
                value = '(' + value.substring(0, 2) + ') ' + value.substring(2);
            } else if (value.length >= 1) {
                value = '(' + value.substring(0);
            }
            
            e.target.value = value;
        });
    });

    // Converter nome para maiúsculas
    const nomeInputs = document.querySelectorAll('.info-input[name="nome"]');
    nomeInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.toUpperCase();
        });
    });

    // Validação de email
    const emailInputs = document.querySelectorAll('.info-input[name="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = this.value;
            if (value.length > 0 && !isValidEmail(value)) {
                showEditFieldError(this, 'Email inválido');
            } else {
                clearEditFieldError(this);
            }
        });
    });
}

// ===== FUNÇÕES AUXILIARES =====

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidDate(dateStr) {
    if (!dateStr || dateStr.length !== 10) return false;
    
    const parts = dateStr.split('/');
    if (parts.length !== 3) return false;
    
    const day = parseInt(parts[0]);
    const month = parseInt(parts[1]);
    const year = parseInt(parts[2]);
    
    if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
    
    if (day < 1 || day > 31) return false;
    if (month < 1 || month > 12) return false;
    if (year < 1900 || year > 2100) return false;
    
    return true;
}

function showEditFieldError(field, message) {
    // Remove erro anterior
    clearEditFieldError(field);
    
    // Adiciona classe de erro
    field.classList.add('error');
    
    // Cria mensagem de erro
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #dc3545;
        font-size: 12px;
        margin-top: 2px;
        font-style: italic;
    `;
    
    // Insere após o campo
    field.parentNode.appendChild(errorDiv);
}

function clearEditFieldError(field) {
    field.classList.remove('error');
    const errorDiv = field.parentNode.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function clearAllEditErrors() {
    document.querySelectorAll('.info-input.error').forEach(field => {
        clearEditFieldError(field);
    });
}

// ===== INICIALIZAÇÃO =====

// Inicializar máscaras quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    initializeEditMasks();
});

// Função para reinicializar máscaras quando um card entra em modo de edição
function reinitializeEditMasks() {
    // Pequeno delay para garantir que os inputs foram criados
    setTimeout(() => {
        initializeEditMasks();
    }, 100);
} 