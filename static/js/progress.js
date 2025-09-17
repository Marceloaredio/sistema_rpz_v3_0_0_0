/**
 * Utilitário para gerenciar a barra de progresso global
 */
class ProgressManager {
    constructor() {
        // Garante que só existe uma instância
        if (ProgressManager.instance) {
            return ProgressManager.instance;
        }
        ProgressManager.instance = this;
        
        // Usa o progressManager global em vez do progressBar
        this.progressManager = window.progressManager;
        this.activeRequests = 0;
    }

    /**
     * Inicia uma operação com barra de progresso
     * @param {string} title - Título da operação
     * @param {string} message - Mensagem inicial
     */
    startOperation(title = 'Processando, aguarde...', message = 'Carregando...') {
        this.activeRequests++;
        if (this.activeRequests === 1) {
            this.progressManager.startOperation(title, message);
        }
    }

    /**
     * Atualiza o progresso de uma operação
     * @param {number} percent - Porcentagem de progresso (0-100)
     * @param {string} message - Mensagem de status opcional
     */
    updateProgress(percent, message = '') {
        if (this.activeRequests > 0) {
            this.progressManager.updateProgress(percent, message);
        }
    }

    /**
     * Finaliza uma operação
     * @param {Function} callback - Função opcional a ser executada após esconder a barra
     */
    finishOperation(callback = null) {
        this.activeRequests = Math.max(0, this.activeRequests - 1);
        if (this.activeRequests === 0) {
            this.progressManager.finishOperation(callback);
        }
    }

    /**
     * Configura interceptadores para requisições AJAX do jQuery
     */
    setupAjaxInterceptors() {
        if (!window.jQuery) return;
        
        const self = this;
        
        // Intercepta início da requisição
        $(document).ajaxStart(function() {
            self.startOperation();
        });

        // Intercepta envio da requisição
        $(document).ajaxSend(function(event, jqXHR, settings) {
            self.progressManager.setMessage(`Processando informações...`);

            // Configura o XHR para monitorar o progresso do upload
            if (settings.xhr && settings.data instanceof FormData) {
                const oldXhr = settings.xhr;
                settings.xhr = function() {
                    const xhr = oldXhr();
                    xhr.upload.addEventListener('progress', function(e) {
                        if (e.lengthComputable) {
                            const percentComplete = (e.loaded / e.total) * 100;
                            self.updateProgress(percentComplete, 'Enviando dados...');
                        }
                    });
                    return xhr;
                };
            }
        });

        // Intercepta sucesso da requisição
        $(document).ajaxSuccess(function(event, jqXHR, settings) {
            self.updateProgress(100, 'Concluído com sucesso!');
        });

        // Intercepta conclusão da requisição (sucesso ou erro)
        $(document).ajaxComplete(function() {
            self.finishOperation();
        });

        // Intercepta erros
        $(document).ajaxError(function(event, jqXHR, settings, error) {
            self.progressManager.setMessage(`Erro: ${error}`);
            setTimeout(() => self.finishOperation(), 2000);
        });
    }

    /**
     * Configura interceptadores para Fetch API
     */
    setupFetchInterceptors() {
        const originalFetch = window.fetch;
        const self = this;

        window.fetch = function(...args) {
            self.startOperation();
            
            return originalFetch.apply(this, args)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    self.updateProgress(100, 'Concluído com sucesso!');
                    self.finishOperation();
                    return response;
                })
                .catch(error => {
                    self.progressManager.setMessage(`Erro: ${error.message}`);
                    setTimeout(() => self.finishOperation(), 2000);
                    throw error;
                });
        };
    }
}

// Inicializa o gerenciador de progresso quando o documento estiver pronto
$(document).ready(function() {
    const progress = new ProgressManager();
    progress.setupAjaxInterceptors();
    progress.setupFetchInterceptors();
    
    // Expõe o gerenciador globalmente para uso em outros scripts
    window.progressManager = progress;
});

// Exemplo de uso manual:
/*
// Iniciar uma operação
progressManager.startOperation('Enviando arquivo', 'Preparando envio...');

// Atualizar progresso
progressManager.updateProgress(30, 'Processando dados...');

// Finalizar operação
progressManager.finishOperation(() => {
    alert('Operação concluída com sucesso!');
});
*/ 