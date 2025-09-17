# Rotas disponíveis para todos os usuários autenticados.

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from controller.decorators import route_access_required

common_bp = Blueprint('common', __name__)

@common_bp.route("/logout")
@route_access_required
def logout():
    del session['user']
    return redirect(url_for('public.login'))

@common_bp.route('/home', methods=['GET'])
@route_access_required 
def home():
    return render_template('home.html')