# Rotas disponíveis para todos os usuários autenticados que possuem acesso ao módulo SSMA.

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from controller.decorators import route_access_required
from controller.utils import CustomLogger
from global_vars import DEBUG, DB_PATH

ssma_bp = Blueprint('ssma', __name__)

ssma_logger = CustomLogger(source="SSMA", debug=DEBUG)

@ssma_bp.route('/checklist_control')
@route_access_required
def checklist_control():
    """
    Página de controle de check lists do módulo SSMA.
    Requer autorização específica para o setor SSMA.
    """
    try:
        # Página temporária - módulo SSMA em desenvolvimento
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SSMA - Controle de Check Lists</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }
                .content { padding: 20px; background: #f8f9fa; border-radius: 8px; margin-top: 20px; }
                .status { background: #e74c3c; color: white; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 SSMA - Controle de Check Lists</h1>
                    <p>Módulo de Segurança, Saúde e Meio Ambiente</p>
                </div>
                <div class="content">
                    <div class="status">
                        <h3>🚧 Em Desenvolvimento</h3>
                        <p>O módulo SSMA está sendo implementado. Esta página será substituída pela interface completa de controle de check lists.</p>
                    </div>
                    <h3>✅ Funcionalidades Planejadas:</h3>
                    <ul>
                        <li>Cadastro de check lists</li>
                        <li>Controle de frequência</li>
                        <li>Relatórios de conformidade</li>
                        <li>Gestão de não conformidades</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        ssma_logger.register_log(f"Erro ao acessar controle de check lists: {e}")
        return f"Erro ao carregar página: {str(e)}", 500

# Aqui você pode adicionar mais rotas do módulo SSMA conforme necessário
# Por exemplo:
# - /ssma/checklist/create
# - /ssma/checklist/edit/<id>
# - /ssma/checklist/delete/<id>
# - /ssma/reports
# etc. 