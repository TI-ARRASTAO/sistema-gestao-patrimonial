from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Redireciona para o dashboard se logado, senão para login"""
    if current_user.is_authenticated:
        restricted_roles = ['USUARIO', 'VISUALIZADOR', 'GERENTE']
        if current_user.role in restricted_roles:
            return redirect(url_for("relatorios.index"))
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login_form"))

@main_bp.route("/test-animations")
@login_required
def test_animations():
    """Página de teste das animações avançadas"""
    return render_template("test_animations.html")