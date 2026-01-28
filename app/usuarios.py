# -*- coding: utf-8 -*-
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import secrets
import string
import logging
import os
import re

from . import db
from .models import Administrador
from .constants import (MSG_DADOS_INVALIDOS, MSG_EMAIL_INVALIDO, MSG_EMAIL_DUPLICADO, 
                        MSG_SUCESSO_CRIAR, MSG_ERRO_GENERICO, DEFAULT_PASSWORD_LENGTH)
from .validators import validate_email, validate_required_fields, sanitize_string

logger = logging.getLogger(__name__)

usuarios_bp = Blueprint("usuarios", __name__, template_folder="templates")

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@usuarios_bp.route("/", methods=["GET"])
@login_required
def index():
    """Lista todos os usuários - rota principal"""
    # Verificar se é admin
    if not current_user.is_authenticated or current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar usuários.", "error")
        return redirect(url_for("dashboard.index"))
    return list_usuarios()

@usuarios_bp.route("/list", methods=["GET"])
@login_required
@require_permission('manage_users')
def list_usuarios():
    try:
        usuarios = Administrador.query.all()
        total_usuarios = len(usuarios)
        ativos = len([u for u in usuarios if u.status == 'ATIVO'])
        inativos = total_usuarios - ativos
        
        kpis = {
            "total": total_usuarios,
            "ativos": ativos,
            "inativos": inativos,
            "admins": len([u for u in usuarios if getattr(u, 'role', 'USUARIO') == 'ADMIN'])
        }
        
        return render_template("dashboard/usuarios.html", usuarios=usuarios, kpis=kpis)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao listar usuários: {str(e)}", exc_info=True)
        flash("Erro ao carregar usuários", "error")
        return render_template("dashboard/usuarios.html", usuarios=[], kpis={"total": 0, "ativos": 0, "inativos": 0, "admins": 0})

@usuarios_bp.route("/create", methods=["POST"])
@login_required
@require_permission('manage_users')
def create_usuario():
    data = request.form if request.form else request.get_json()
    if not data:
        return jsonify({"error": MSG_DADOS_INVALIDOS}), 400
    
    is_valid, missing_field = validate_required_fields(data, ['email', 'nome', 'perfil'])
    if not is_valid:
        return jsonify({"error": f"{missing_field} é obrigatório"}), 400
    
    email = sanitize_string(data.get("email"))
    nome = sanitize_string(data.get("nome"))
    perfil = sanitize_string(data.get("perfil"))
    setor = sanitize_string(data.get("setor"))
    
    # Validar setor obrigatório para GERENTE e VISUALIZADOR
    if perfil in ['GERENTE', 'VISUALIZADOR'] and not setor:
        return jsonify({"error": "Setor é obrigatório para Gerente e Visualizador"}), 400
    
    if not validate_email(email):
        return jsonify({"error": MSG_EMAIL_INVALIDO}), 400
    
    try:
        if Administrador.query.filter_by(email=email).first():
            return jsonify({"error": MSG_EMAIL_DUPLICADO}), 400
        
        username = email.split("@")[0]
        counter = 1
        original_username = username
        while Administrador.query.filter_by(user_name=username).first():
            username = f"{original_username}{counter}"
            counter += 1
        
        senha = sanitize_string(data.get("senha"))
        if not senha:
            senha = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(DEFAULT_PASSWORD_LENGTH))
        
        usuario = Administrador(
            user_name=username,
            user_password=generate_password_hash(senha),
            name_user=nome,
            email=email,
            role=perfil,
            setor=setor if setor else None,
            status='ATIVO' if data.get('ativo') else 'INATIVO'
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        return jsonify({"success": MSG_SUCESSO_CRIAR, "senha": senha}), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário: {str(e)}", exc_info=True)
        return jsonify({"error": MSG_ERRO_GENERICO}), 500

@usuarios_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_usuario(id):
    usuario = Administrador.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        return jsonify({"error": "Não é possível excluir seu próprio usuário"}), 400
    
    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"success": "Usuário removido com sucesso"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao remover usuário {id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500

@usuarios_bp.route("/<int:id>/activate", methods=["POST"])
@login_required
def activate_usuario(id):
    usuario = Administrador.query.get_or_404(id)
    
    try:
        usuario.status = 'ATIVO'
        db.session.commit()
        return jsonify({"success": "Usuário ativado com sucesso"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao ativar usuário {id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500

@usuarios_bp.route("/<int:id>/deactivate", methods=["POST"])
@login_required
def deactivate_usuario(id):
    usuario = Administrador.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        return jsonify({"error": "Não é possível desativar seu próprio usuário"}), 400
    
    try:
        usuario.status = 'INATIVO'
        db.session.commit()
        return jsonify({"success": "Usuário desativado com sucesso"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao desativar usuário {id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500

@usuarios_bp.route("/bulk-action", methods=["POST"])
@login_required
def bulk_action():
    data = request.get_json()
    action = data.get('action')
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({"error": "Nenhum usuário selecionado"}), 400
    
    ids = [id for id in ids if int(id) != current_user.id]
    
    if not ids:
        return jsonify({"error": "Não é possível executar ação no próprio usuário"}), 400
    
    try:
        usuarios = Administrador.query.filter(Administrador.id.in_(ids)).all()
        
        if action == 'activate':
            for usuario in usuarios:
                usuario.status = 'ATIVO'
            message = f"{len(usuarios)} usuário(s) ativado(s) com sucesso"
        elif action == 'deactivate':
            for usuario in usuarios:
                usuario.status = 'INATIVO'
            message = f"{len(usuarios)} usuário(s) desativado(s) com sucesso"
        elif action == 'delete':
            for usuario in usuarios:
                db.session.delete(usuario)
            message = f"{len(usuarios)} usuário(s) excluído(s) com sucesso"
        else:
            return jsonify({"error": "Ação inválida"}), 400
        
        db.session.commit()
        return jsonify({"success": message}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro na ação em lote: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500