/**
 * Funcionalidades do formulário de cadastro de motoristas
 * Inclui máscaras, validações e submissão do formulário
 */

// ===== FUNCIONALIDADES DO MODAL =====

// Abrir modal
function openMotoristModal() {
    document.getElementById('modal-novo-motorista').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

// Fechar modal
function closeModal() {
    document.getElementById('modal-novo-motorista').style.display = 'none';
    document.body.style.overflow = 'auto';
    // Limpar formulário
    document.getElementById('form-novo-motorista').reset();
    clearValidationErrors();
}

// Fechar modal ao clicar fora
function setupModalEvents() {
    const modal = document.getElementById('modal-novo-motorista');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
    }
}

// ===== MÁSCARAS DE ENTRADA =====

function initializeFormMasks() {
    // Máscara para datas (dd/mm/aaaa)
    const dateInputs = document.querySelectorAll('input[placeholder*="dd/mm/aaaa"]');
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
        
        // Adicionar funcionalidade de calendário com duplo clique
        input.addEventListener('dblclick', function(e) {
            e.preventDefault();
            openCalendar(this);
        });
        
        // Adicionar cursor pointer para indicar que é clicável
        input.style.cursor = 'pointer';
    });

    // Máscara para CPF (000.000.000-00)
    const cpfInput = document.getElementById('cpf');
    if (cpfInput) {
        cpfInput.addEventListener('input', function(e) {
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
    }

    // Máscara para CNH (apenas números)
    const cnhInput = document.getElementById('cnh');
    if (cnhInput) {
        cnhInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }

    // Máscara para RG (números e letras)
    const rgInput = document.getElementById('rg');
    if (rgInput) {
        rgInput.addEventListener('input', function(e) {
            // Permitir números e letras, remover apenas caracteres especiais
            e.target.value = e.target.value.replace(/[^a-zA-Z0-9]/g, '');
        });
    }

    // Máscara para Código SAP (apenas números, máximo 9 dígitos)
    const sapInput = document.getElementById('codigo_sap');
    if (sapInput) {
        sapInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 9);
        });
    }

    // Máscara para CTPS (apenas números, máximo 10 dígitos)
    const ctpsInput = document.getElementById('ctps');
    if (ctpsInput) {
        ctpsInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 10);
        });
    }

    // Máscara para telefone ((00) 00000-0000)
    const telefoneInput = document.getElementById('telefone');
    if (telefoneInput) {
        telefoneInput.addEventListener('input', function(e) {
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
    }

    // Converter nome para maiúsculas
    const nomeInput = document.getElementById('nome');
    if (nomeInput) {
        nomeInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.toUpperCase();
        });
    }
}

// ===== VALIDAÇÕES =====

function initializeFormValidations() {
    // Validação de CPF
    const cpfInput = document.getElementById('cpf');
    if (cpfInput) {
        cpfInput.addEventListener('blur', function() {
            const value = this.value.replace(/\D/g, '');
            if (value.length > 0 && value.length !== 11) {
                showFieldError(this, 'CPF inválido');
            } else {
                clearFieldError(this);
            }
        });
    }

    // Validação de CNH
    const cnhInput = document.getElementById('cnh');
    if (cnhInput) {
        cnhInput.addEventListener('blur', function() {
            const value = this.value.replace(/\D/g, '');
            if (value.length > 0 && value.length !== 11) {
                showFieldError(this, 'Número de CNH inválido');
            } else {
                clearFieldError(this);
            }
        });
    }

    // Validação de email
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const value = this.value;
            if (value.length > 0 && !isValidEmail(value)) {
                showFieldError(this, 'Email inválido');
            } else {
                clearFieldError(this);
            }
        });
    }

    // Validação de datas
    const dateInputs = document.querySelectorAll('input[placeholder*="dd/mm/aaaa"]');
    dateInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = this.value;
            if (value.length > 0 && !isValidDate(value)) {
                showFieldError(this, 'Data inválida');
            } else {
                clearFieldError(this);
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
    if (!/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) return false;
    
    const parts = dateStr.split('/');
    const day = parseInt(parts[0]);
    const month = parseInt(parts[1]);
    const year = parseInt(parts[2]);
    
    if (year < 1900 || year > 2100) return false;
    if (month < 1 || month > 12) return false;
    
    const date = new Date(year, month - 1, day);
    return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
}

function showFieldError(field, message) {
    clearFieldError(field);
    field.style.borderColor = '#e74c3c';
    field.style.boxShadow = '0 0 0 3px rgba(231, 76, 60, 0.1)';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.color = '#e74c3c';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '4px';
    errorDiv.style.fontWeight = '500';
    
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.style.borderColor = '#e2e8f0';
    field.style.boxShadow = '';
    
    const errorDiv = field.parentNode.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function clearValidationErrors() {
    const errorDivs = document.querySelectorAll('.field-error');
    errorDivs.forEach(div => div.remove());
    
    const inputs = document.querySelectorAll('.form-group input, .form-group select');
    inputs.forEach(input => {
        input.style.borderColor = '#e2e8f0';
        input.style.boxShadow = '';
    });
}

// ===== SUBMISSÃO DO FORMULÁRIO =====

function setupFormSubmission() {
    const form = document.getElementById('form-novo-motorista');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validar campos obrigatórios
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    showFieldError(field, 'Campo obrigatório');
                    isValid = false;
                } else {
                    clearFieldError(field);
                }
            });

            // Validar checkboxes de verificação
            const confJornada = document.querySelector('input[name="conf_jornada"]');
            const confFecham = document.querySelector('input[name="conf_fecham"]');
            
            if (!confJornada.checked && !confFecham.checked) {
                showFieldError(confJornada.parentNode.parentNode, 'Selecione pelo menos uma opção de verificação');
                isValid = false;
            }

            if (isValid) {
                submitMotoristForm(this);
            }
        });
    }
}

function submitMotoristForm(form) {
    // Preparar dados do formulário
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Manter datas no formato dd/mm/aaaa
    const dateFields = [
        'data_admissao', 'data_nascimento', 'primeira_cnh', 'data_expedicao', 
        'vencimento_cnh', 'done_mopp', 'vencimento_mopp', 'done_toxicologico_clt',
        'vencimento_toxicologico_clt', 'done_toxicologico_cnh', 'vencimento_toxicologico_cnh',
        'done_aso_periodico', 'vencimento_aso_periodico', 'done_aso_semestral',
        'vencimento_aso_semestral', 'done_buonny', 'vencimento_buonny'
    ];
    
    // Não converter datas - manter formato dd/mm/aaaa
    dateFields.forEach(field => {
        if (data[field]) {
            // Manter o formato original dd/mm/aaaa
            // data[field] permanece inalterado
        }
    });
    
    // Converter checkboxes para valores booleanos
    data.conf_jornada = data.conf_jornada === '1' ? '1' : '0';
    data.conf_fecham = data.conf_fecham === '1' ? '1' : '0';
    
    // Mostrar indicador de progresso
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton ? submitButton.innerHTML : 'Salvando...';
    if (submitButton) {
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        submitButton.disabled = true;
    }
    
    // Enviar dados para o backend com timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 segundos de timeout
    
    fetch('/api/motorists', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        return response.json();
    })
    .then(result => {
        // Restaurar botão
        if (submitButton) {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
        
        if (result.success) {
            alert('Motorista cadastrado com sucesso!');
            closeModal();
            // Recarregar a página para mostrar o novo motorista
            window.location.reload();
        } else {
            alert('Erro ao cadastrar motorista: ' + (result.message || 'Erro desconhecido'));
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        
        // Restaurar botão
        if (submitButton) {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
        
        console.error('Erro:', error);
        if (error.name === 'AbortError') {
            alert('Tempo limite excedido. O motorista pode ter sido salvo, mas a integração com Google pode ter falhado. Verifique os logs.');
        } else {
            alert('Erro ao cadastrar motorista. Tente novamente.');
        }
    });
}

// ===== FUNCIONALIDADE DE CALENDÁRIO =====

let currentCalendarField = null;

function openCalendar(inputField) {
    currentCalendarField = inputField;
    
    // Remover calendário existente se houver
    const existingCalendar = document.getElementById('date-calendar');
    if (existingCalendar) {
        existingCalendar.remove();
    }
    
    // Criar calendário
    const calendar = document.createElement('div');
    calendar.id = 'date-calendar';
    calendar.style.cssText = `
        position: absolute;
        background: white;
        border: 1px solid #ccc;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 16px;
        z-index: 10000;
        font-family: Arial, sans-serif;
        font-size: 14px;
        min-width: 280px;
    `;
    
    // Posicionar calendário
    const rect = inputField.getBoundingClientRect();
    calendar.style.left = rect.left + 'px';
    calendar.style.top = (rect.bottom + 5) + 'px';
    
    // Obter data atual ou data do campo
    let currentDate = new Date();
    if (inputField.value) {
        const parts = inputField.value.split('/');
        if (parts.length === 3) {
            currentDate = new Date(parts[2], parts[1] - 1, parts[0]);
        }
    }
    
    // Criar cabeçalho do calendário
    const header = document.createElement('div');
    header.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #eee;
    `;
    
    const monthYear = document.createElement('div');
    monthYear.style.cssText = `
        font-weight: bold;
        font-size: 16px;
        color: #333;
    `;
    
    const months = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    
    function updateCalendar() {
        monthYear.textContent = `${months[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
        
        // Limpar corpo do calendário
        const body = calendar.querySelector('.calendar-body');
        if (body) body.remove();
        
        const calendarBody = document.createElement('div');
        calendarBody.className = 'calendar-body';
        calendarBody.style.cssText = `
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
        `;
        
        // Cabeçalho dos dias da semana
        const daysOfWeek = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
        daysOfWeek.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.textContent = day;
            dayHeader.style.cssText = `
                text-align: center;
                font-weight: bold;
                color: #666;
                padding: 8px 4px;
                font-size: 12px;
            `;
            calendarBody.appendChild(dayHeader);
        });
        
        // Obter primeiro dia do mês e número de dias
        const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());
        
        // Criar células do calendário
        for (let i = 0; i < 42; i++) {
            const cell = document.createElement('div');
            const currentCellDate = new Date(startDate);
            currentCellDate.setDate(startDate.getDate() + i);
            
            cell.textContent = currentCellDate.getDate();
            cell.style.cssText = `
                text-align: center;
                padding: 8px 4px;
                cursor: pointer;
                border-radius: 4px;
                font-size: 14px;
                transition: background-color 0.2s;
            `;
            
            // Estilizar células
            if (currentCellDate.getMonth() !== currentDate.getMonth()) {
                cell.style.color = '#ccc';
            } else {
                cell.style.color = '#333';
            }
            
            // Destacar data atual
            const today = new Date();
            if (currentCellDate.toDateString() === today.toDateString()) {
                cell.style.backgroundColor = '#e3f2fd';
                cell.style.fontWeight = 'bold';
            }
            
            // Evento de clique para selecionar data
            cell.addEventListener('click', function() {
                const day = currentCellDate.getDate().toString().padStart(2, '0');
                const month = (currentCellDate.getMonth() + 1).toString().padStart(2, '0');
                const year = currentCellDate.getFullYear();
                
                currentCalendarField.value = `${day}/${month}/${year}`;
                calendar.remove();
                currentCalendarField = null;
            });
            
            // Hover effect
            cell.addEventListener('mouseenter', function() {
                if (currentCellDate.getMonth() === currentDate.getMonth()) {
                    this.style.backgroundColor = '#f0f0f0';
                }
            });
            
            cell.addEventListener('mouseleave', function() {
                if (currentCellDate.getMonth() === currentDate.getMonth()) {
                    this.style.backgroundColor = '';
                }
            });
            
            calendarBody.appendChild(cell);
        }
        
        calendar.appendChild(calendarBody);
    }
    
    // Botões de navegação
    const prevBtn = document.createElement('button');
    prevBtn.innerHTML = '&lt;';
    prevBtn.style.cssText = `
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        color: #666;
        padding: 4px 8px;
        border-radius: 4px;
        transition: background-color 0.2s;
    `;
    prevBtn.addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() - 1);
        updateCalendar();
    });
    prevBtn.addEventListener('mouseenter', function() {
        this.style.backgroundColor = '#f0f0f0';
    });
    prevBtn.addEventListener('mouseleave', function() {
        this.style.backgroundColor = '';
    });
    
    const nextBtn = document.createElement('button');
    nextBtn.innerHTML = '&gt;';
    nextBtn.style.cssText = prevBtn.style.cssText;
    nextBtn.addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() + 1);
        updateCalendar();
    });
    nextBtn.addEventListener('mouseenter', function() {
        this.style.backgroundColor = '#f0f0f0';
    });
    nextBtn.addEventListener('mouseleave', function() {
        this.style.backgroundColor = '';
    });
    
    header.appendChild(prevBtn);
    header.appendChild(monthYear);
    header.appendChild(nextBtn);
    calendar.appendChild(header);
    
    // Inicializar calendário
    updateCalendar();
    
    // Adicionar ao documento
    document.body.appendChild(calendar);
    
    // Fechar calendário ao clicar fora
    document.addEventListener('click', function closeCalendar(e) {
        if (!calendar.contains(e.target) && e.target !== inputField) {
            calendar.remove();
            currentCalendarField = null;
            document.removeEventListener('click', closeCalendar);
        }
    });
}

// ===== INICIALIZAÇÃO =====

document.addEventListener('DOMContentLoaded', function() {
    // Configurar eventos do modal
    setupModalEvents();
    
    // Configurar máscaras e validações
    initializeFormMasks();
    initializeFormValidations();
    
    // Configurar submissão do formulário
    setupFormSubmission();
    
    // Configurar botão "Novo Motorista"
    const btnNovoMotorista = document.querySelector('.btn-novo-motorista');
    if (btnNovoMotorista) {
        btnNovoMotorista.addEventListener('click', function(e) {
            e.preventDefault();
            openMotoristModal();
        });
    }
});

// Exportar funções para uso global
window.openMotoristModal = openMotoristModal;
window.closeModal = closeModal; 