import configparser
import os
from datetime import timedelta
from flask import Flask, render_template
import secrets
from waitress import serve

from view.config_routes import config_bp
from view.track_routes import track_bp
from view.closure_routes import closure_bp
from view.common_routes import common_bp
from view.public_routes import public_bp
from view.parameters_route import params_bp
from view.ssma_routes import ssma_bp

# Pega as configurações do arquivo .ini
config = configparser.ConfigParser()
config.read('config/config.ini')

# Lê configurações com prioridade para variáveis de ambiente
host = os.getenv('HOST', config.get('GENERAL', 'HOST', fallback='127.0.0.1'))
port = int(os.getenv('PORT', config.get('GENERAL', 'PORT', fallback=5000)))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true' or config.getboolean('GENERAL', 'DEBUG', fallback=True)

app = Flask(__name__)
# Usa variável de ambiente para chave secreta em produção
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.permanent_session_lifetime = timedelta(hours=2)
app.config['DEBUG'] = DEBUG  # Define também no Flask

# Filtro para formatar datas nas templates Jinja2
from datetime import datetime
import json

def datetimeformat(value, format='%d/%m/%Y'):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except Exception:
            return value
    return value.strftime(format)

def from_json(value):
    """Converte uma string JSON em lista Python"""
    try:
        return json.loads(value) if value else []
    except (json.JSONDecodeError, TypeError):
        return []

app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['from_json'] = from_json

# Handler personalizado para erro 403
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error_403.html'), 403

app.register_blueprint(config_bp)
app.register_blueprint(track_bp)
app.register_blueprint(closure_bp)
app.register_blueprint(common_bp)
app.register_blueprint(public_bp)
app.register_blueprint(params_bp)
app.register_blueprint(ssma_bp)

# Roda o servidor com o host e porta do arquivo .ini
if __name__ == '__main__':
    if DEBUG:
        app.run(host=host, port=port, debug=True)
    else:
        serve(app, host=host, port=port)
