# Rotas disponíveis para todos os usuários, não precisam de autenticação.

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from model.drivers.user_driver import UserDriver
from model.db_model import User

from controller.utils import CustomLogger

from global_vars import DB_PATH, DEBUG


public_bp = Blueprint('public', __name__)

routes_logger = CustomLogger(source="ROUTES", debug=DEBUG)
user_driver = UserDriver(logger=routes_logger, db_path=DB_PATH)

@public_bp.route('/')
def main_page():
    if 'user' not in session:
        return redirect(url_for('public.login'))

    user_location = request.args.get("location")

    username = session['user']['name']

    if not user_location:
        user_location = session['user'].get('location', 'Home')

    return render_template('main.html', username=username, location=user_location)

@public_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_email = request.form.get('email').lower().strip()
        input_password = request.form.get('senha').strip()

        found_user = user_driver.retrieve_user(where_columns=['email', 'password'],
                                               where_values=(input_email, input_password))
        found_user_obj = User(found_user)

        if not found_user:
            flash("Usuário não encontrado ou senha incorreta")
            return redirect(url_for('public.login'))

        else:
            session.permanent = True
            session['user'] = {
                "name": found_user_obj.name,
                "email": found_user_obj.email,
                "is_admin": found_user_obj.is_admin
            }
            return redirect(url_for('public.main_page', location="Início"))

    return render_template('login.html')