/**
 * Utilitários para formatação de modais de conflitos
 */

/**
 * Formatar conflitos para exibição em modal SweetAlert2
 * @param {Array} conflitos - Array de objetos de conflito ou strings
 * @returns {string} HTML formatado para o modal
 */
function formatConflictsForModal(conflitos) {
    if (!conflitos || conflitos.length === 0) {
        return '<div class="conflict-item"><div class="conflict-description">Nenhum conflito específico informado.</div></div>';
    }

    let html = '<div class="conflicts-container">';
    
    conflitos.forEach(function(conflito) {
        if (typeof conflito === 'string') {
            // Formato antigo - apenas texto
            html += '<div class="conflict-item">';
            html += '<div class="conflict-description">' + conflito + '</div>';
            html += '</div>';
        } else if (typeof conflito === 'object' && conflito !== null) {
            // Formato novo - objeto estruturado
            const tipo = conflito.tipo || 'Registro';
            const descricao = conflito.descricao || 'Conflito detectado';
            const data = conflito.data || '';
            
            // Determinar classe CSS baseada no tipo
            let cssClass = 'conflict-item';
            if (tipo === 'Caminhão ocupado') {
                cssClass += ' truck-occupied';
            } else if (tipo === 'Motorista já possui jornada') {
                cssClass += ' motorist-journey';
            } else if (tipo === 'Motorista já possui folga') {
                cssClass += ' motorist-dayoff';
            } else if (tipo === 'Jornada') {
                cssClass += ' journey-conflict';
            } else if (tipo === 'Dayoff') {
                cssClass += ' dayoff-conflict';
            }
            
            html += '<div class="' + cssClass + '">';
            if (data) {
                html += '<div class="conflict-date">' + data + '</div>';
            }
            html += '<div class="conflict-type">' + tipo + '</div>';
            html += '<div class="conflict-description">' + descricao + '</div>';
            html += '</div>';
        }
    });
    
    html += '</div>';
    return html;
}

/**
 * Exibir modal de conflitos com formatação padronizada
 * @param {Array} conflitos - Array de conflitos
 * @param {Function} onConfirm - Callback para quando usuário confirma substituição
 * @param {Function} onCancel - Callback para quando usuário cancela (opcional)
 */
function showConflictModal(conflitos, onConfirm, onCancel) {
    const formattedHTML = formatConflictsForModal(conflitos);
    
    Swal.fire({
        title: 'Conflitos encontrados',
        html: 'Já existem registros para:<br><br>' + formattedHTML + '<br>Substituir?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Substituir',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        reverseButtons: true,
        customClass: {
            popup: 'conflict-modal-popup',
            title: 'conflict-modal-title',
            htmlContainer: 'conflict-modal-content',
            confirmButton: 'conflict-modal-confirm',
            cancelButton: 'conflict-modal-cancel'
        }
    }).then((result) => {
        if (result.isConfirmed && typeof onConfirm === 'function') {
            onConfirm();
        } else if (result.isDismissed && typeof onCancel === 'function') {
            onCancel();
        }
    });
}

/**
 * Processar resposta de conflito da API e exibir modal
 * @param {Object} response - Resposta da API contendo conflitos
 * @param {Function} onConfirm - Callback para quando usuário confirma substituição
 * @param {Function} onCancel - Callback para quando usuário cancela (opcional)
 */
function handleConflictResponse(response, onConfirm, onCancel) {
    // Tenta usar o formato novo primeiro, depois fallback para formato antigo
    const conflitos = response.conflitos_detalhados || response.conflitos || [];
    showConflictModal(conflitos, onConfirm, onCancel);
}

/**
 * Converter lista simples de conflitos em formato detalhado
 * @param {Array} conflictsArray - Array de strings de conflito
 * @returns {Array} Array de objetos de conflito formatados
 */
function convertSimpleConflictsToDetailed(conflictsArray) {
    if (!Array.isArray(conflictsArray)) {
        return [];
    }
    
    return conflictsArray.map(function(conflict) {
        if (typeof conflict === 'string') {
            // Tentar extrair data do início da string
            const dataParts = conflict.match(/^(\d{2}-\d{2}-\d{4})/);
            const data = dataParts ? dataParts[1] : '';
            
            return {
                data: data,
                tipo: 'Conflito',
                descricao: conflict
            };
        }
        return conflict;
    });
} 