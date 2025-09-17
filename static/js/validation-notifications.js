/**
 * Sistema de Notificações de Validação de Cálculos
 * Exibe mensagens de validação para o usuário
 */

class ValidationNotifications {
    constructor() {
        this.notificationContainer = null;
        this.init();
    }
    
    init() {
        // Criar container para notificações
        this.createNotificationContainer();
        
        // Interceptar respostas AJAX para verificar validação
        this.interceptAjaxResponses();
    }
    
    createNotificationContainer() {
        // Remover container existente se houver
        const existingContainer = document.getElementById('validation-notifications');
        if (existingContainer) {
            existingContainer.remove();
        }
        
        // Criar novo container
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = 'validation-notifications';
        this.notificationContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 99999;
            max-width: 400px;
            font-family: Arial, sans-serif;
        `;
        
        document.body.appendChild(this.notificationContainer);
    }
    
    interceptAjaxResponses() {
        // Interceptar respostas de salvar dados
        const originalAjax = window.jQuery ? window.jQuery.ajax : null;
        
        if (originalAjax) {
            window.jQuery.ajax = function(settings) {
                const originalSuccess = settings.success;
                const validator = this;
                
                settings.success = function(response, textStatus, xhr) {
                    // Verificar se há dados de validação na resposta
                    if (response && response.validation) {
                        validator.showValidationMessage(response.validation);
                    }
                    
                    // Chamar callback original
                    if (originalSuccess) {
                        originalSuccess.call(this, response, textStatus, xhr);
                    }
                };
                
                return originalAjax.call(this, settings);
            }.bind(this);
        }
        
        // Também interceptar $.post e $.get
        if (window.jQuery) {
            const originalPost = window.jQuery.post;
            const originalGet = window.jQuery.get;
            const validator = this;
            
            window.jQuery.post = function(url, data, callback, type) {
                const originalCallback = callback;
                
                callback = function(response, textStatus, xhr) {
                    if (response && response.validation) {
                        validator.showValidationMessage(response.validation);
                    }
                    
                    if (originalCallback) {
                        originalCallback.call(this, response, textStatus, xhr);
                    }
                };
                
                return originalPost.call(this, url, data, callback, type);
            };
            
            window.jQuery.get = function(url, data, callback, type) {
                const originalCallback = callback;
                
                callback = function(response, textStatus, xhr) {
                    if (response && response.validation) {
                        validator.showValidationMessage(response.validation);
                    }
                    
                    if (originalCallback) {
                        originalCallback.call(this, response, textStatus, xhr);
                    }
                };
                
                return originalGet.call(this, url, data, callback, type);
            };
        }
    }
    
    showValidationMessage(validationData) {
        const status = validationData.status;
        const message = validationData.message;
        
        let notificationType = 'info';
        let icon = 'ℹ️';
        let backgroundColor = '#e3f2fd';
        let borderColor = '#2196f3';
        
        if (status === 'valid') {
            notificationType = 'success';
            icon = '✅';
            backgroundColor = '#e8f5e8';
            borderColor = '#4caf50';
        } else if (status === 'divergent') {
            notificationType = 'warning';
            icon = '⚠️';
            backgroundColor = '#fff3e0';
            borderColor = '#ff9800';
        } else if (status === 'error') {
            notificationType = 'error';
            icon = '❌';
            backgroundColor = '#ffebee';
            borderColor = '#f44336';
        }
        
        this.createNotification(icon, message, notificationType, backgroundColor, borderColor);
        
        // Se há divergência, mostrar detalhes adicionais
        if (status === 'divergent' && validationData.reprocess_result) {
            this.showReprocessDetails(validationData.reprocess_result);
        }
    }
    
    createNotification(icon, message, type, bgColor, borderColor) {
        const notification = document.createElement('div');
        notification.className = `validation-notification ${type}`;
        notification.style.cssText = `
            background-color: ${bgColor};
            border: 2px solid ${borderColor};
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
            animation: slideInRight 0.3s ease-out;
            position: relative;
            overflow: hidden;
            z-index: 99999;
            font-weight: 500;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: flex-start;">
                <div style="font-size: 24px; margin-right: 12px; flex-shrink: 0;">${icon}</div>
                <div style="flex: 1;">
                    <div style="font-weight: bold; margin-bottom: 5px; color: #333;">
                        Validação de Cálculos
                    </div>
                    <div style="color: #666; line-height: 1.4;">
                        ${message}
                    </div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; font-size: 18px; cursor: pointer; color: #999; margin-left: 10px;">
                    ×
                </button>
            </div>
        `;
        
        this.notificationContainer.appendChild(notification);
        
        // Auto-remover após 10 segundos (exceto para divergências)
        if (type !== 'warning') {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                        }
                    }, 300);
                }
            }, 10000); // Aumentado para 10 segundos para dar tempo de ver
        }
    }
    
    showReprocessDetails(reprocessResult) {
        const totalCorrected = reprocessResult.total_corrected || 0;
        const period = reprocessResult.period || 'período recente';
        
        const message = `
            <strong>Reprocessamento Automático:</strong><br>
            • ${totalCorrected} registros foram reprocessados<br>
            • Período: ${period}<br>
            • Todos os cálculos foram corrigidos automaticamente
        `;
        
        this.createNotification(
            '🔄',
            message,
            'info',
            '#e8f5e8',
            '#4caf50'
        );
    }
    
    // Método para mostrar notificação manual
    showManualNotification(type, message) {
        let icon = 'ℹ️';
        let bgColor = '#e3f2fd';
        let borderColor = '#2196f3';
        
        switch (type) {
            case 'success':
                icon = '✅';
                bgColor = '#e8f5e8';
                borderColor = '#4caf50';
                break;
            case 'warning':
                icon = '⚠️';
                bgColor = '#fff3e0';
                borderColor = '#ff9800';
                break;
            case 'error':
                icon = '❌';
                bgColor = '#ffebee';
                borderColor = '#f44336';
                break;
        }
        
        this.createNotification(icon, message, type, bgColor, borderColor);
    }
    
    // Método para limpar todas as notificações
    clearAll() {
        if (this.notificationContainer) {
            this.notificationContainer.innerHTML = '';
        }
    }
}

// Adicionar estilos CSS para animações
const validationStyles = document.createElement('style');
validationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .validation-notification {
        transition: all 0.3s ease;
    }
    
    .validation-notification:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
`;

document.head.appendChild(validationStyles);

// Inicializar sistema de notificações quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    window.validationNotifications = new ValidationNotifications();
});

// Função global para mostrar notificações manualmente
function showValidationNotification(type, message) {
    if (window.validationNotifications) {
        window.validationNotifications.showManualNotification(type, message);
    }
} 