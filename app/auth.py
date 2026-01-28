# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Administrador
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import exists
from datetime import datetime, timezone
from .security import rate_limit
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, template_folder="templates")

@auth_bp.route("/register", methods=["GET"])
def register_form():
    return render_template("register.html")


@auth_bp.route("/register", methods=["POST"])
@rate_limit(max_requests=5, window=3600)  # 5 tentativas por hora
def register():
    try:
        data = request.form if request.form else request.json or {}
        user_name = data.get("user_name")
        password = data.get("user_password")
        name_user = data.get("name_user")
        email = data.get("email")

        # Validação de entrada
        from .security import validate_input, validate_password_strength
        valid, error_msg = validate_input(
            data,
            required_fields=["user_name", "user_password", "name_user"],
            max_lengths={"user_name": 50, "name_user": 100, "email": 100}
        )
        if not valid:
            flash(error_msg, "danger")
            return redirect(url_for("auth.register_form"))

        # Validação de força da senha
        valid_pwd, pwd_error = validate_password_strength(password)
        if not valid_pwd:
            flash(pwd_error, "danger")
            return redirect(url_for("auth.register_form"))

        if db.session.query(Administrador.id).filter_by(user_name=user_name).scalar():
            flash("Usuário já existe", "warning")
            return redirect(url_for("auth.register_form"))

        try:
            hashed = generate_password_hash(password)
        except Exception as e:
            logger.error(f"Erro ao gerar hash da senha: {str(e)}", exc_info=True)
            flash("Erro ao processar senha", "danger")
            return redirect(url_for("auth.register_form"))
        
        admin = Administrador(user_name=user_name, user_password=hashed, name_user=name_user, email=email)
        db.session.add(admin)
        db.session.commit()

        flash("Administrador criado com sucesso. Faça login.", "success")
        return redirect(url_for("auth.login_form"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário: {str(e)}", exc_info=True)
        flash("Erro ao criar usuário", "danger")
        return redirect(url_for("auth.register_form"))


@auth_bp.route("/login", methods=["GET"])
def login_form():
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
@rate_limit(max_requests=10, window=3600)  # 10 tentativas por hora
def login():
    try:
        user_name = request.form.get("user_name")
        password = request.form.get("user_password")
        
        # Validação de entrada
        from .security import validate_input
        data = {"user_name": user_name, "user_password": password}
        valid, error_msg = validate_input(
            data,
            required_fields=["user_name", "user_password"],
            max_lengths={"user_name": 50}
        )
        if not valid:
            flash(error_msg, "danger")
            return redirect(url_for("auth.login_form"))

        admin = Administrador.query.filter_by(user_name=user_name).first()
        if not admin:
            logger.warning(f"Tentativa de login falhada: usuário '{user_name}' não encontrado")
            flash("Usuário ou senha inválidos", "danger")
            return redirect(url_for("auth.login_form"))
        
        try:
            password_valid = check_password_hash(admin.user_password, password)
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {str(e)}", exc_info=True)
            flash("Erro ao processar autenticação", "danger")
            return redirect(url_for("auth.login_form"))
        
        if not password_valid:
            logger.warning(f"Tentativa de login falhada: senha inválida para usuário '{user_name}'")
            flash("Usuário ou senha inválidos", "danger")
            return redirect(url_for("auth.login_form"))

        # Verificar se usuário está ativo
        if hasattr(admin, 'status'):
            if admin.status == 'INATIVO':
                flash("Usuário inativo. Contate o administrador.", "danger")
                return redirect(url_for("auth.login_form"))

        # Registrar último acesso
        if hasattr(admin, 'last_login'):
            try:
                admin.last_login = datetime.now(timezone.utc)
                db.session.commit()
            except SQLAlchemyError as e:
                logger.error(f"Erro ao atualizar último acesso: {str(e)}", exc_info=True)
                db.session.rollback()

        try:
            login_user(admin)
            logger.info(f"Login bem-sucedido: usuário '{user_name}' (ID: {admin.id})")
        except Exception as e:
            logger.error(f"Erro ao fazer login do usuário: {str(e)}", exc_info=True)
            flash("Erro ao iniciar sessão", "danger")
            return redirect(url_for("auth.login_form"))
        
        return redirect(url_for("dashboard.index"))
    except SQLAlchemyError as e:
        logger.error(f"Erro ao fazer login: {str(e)}", exc_info=True)
        flash("Erro ao fazer login", "danger")
        return redirect(url_for("auth.login_form"))


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("Sessão finalizada com sucesso.", "info") 
    return redirect(url_for("auth.login_form"))