# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import os
import shutil
import sqlite3
import logging
import zipfile
from pathlib import Path

from . import db
from .models import Backup, Administrador

logger = logging.getLogger(__name__)

backup_bp = Blueprint("backup", __name__, template_folder="templates")

# Diretório para armazenar backups
BACKUP_DIR = "backups"

def get_sqlite_path():
    """Resolve o caminho absoluto do arquivo de banco de dados SQLite"""
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return None

    db_path = db_uri.replace('sqlite:///', '')
    # Se o caminho não for absoluto, torná-lo relativo ao diretório do projeto (pai do app)
    if not os.path.isabs(db_path):
        instance_path = os.path.join(current_app.root_path, '..', 'instance', os.path.basename(db_path))
        db_path = os.path.normpath(instance_path)
    
    return os.path.normpath(db_path)

def create_backup_automatico():
    """Cria um backup automático do banco de dados (chamado pelo scheduler)"""
    try:
        logger.info("Iniciando backup automático")

        # Criar diretório se não existir
        backup_path = Path(current_app.root_path) / BACKUP_DIR
        backup_path.mkdir(exist_ok=True)

        # Nome do arquivo de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_auto_{timestamp}.db"
        backup_filepath = backup_path / backup_filename

        # Criar registro do backup
        backup = Backup(
            nome=f"Backup Automático - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            arquivo=str(backup_filepath),
            tamanho=0,  # Será atualizado após criação
            tipo='AUTOMATICO',
            status='EXECUTANDO',
            criado_por=None  # Backup automático não tem usuário específico
        )
        db.session.add(backup)
        db.session.commit()

        try:
            # Fazer backup do banco SQLite
            db_path = get_sqlite_path()
            if not db_path:
                raise Exception("Backup automático suportado apenas para SQLite")

            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")

            # Copiar arquivo do banco
            shutil.copy2(db_path, backup_filepath)

            # Verificar se o backup foi criado com sucesso
            if not backup_filepath.exists():
                raise Exception("Arquivo de backup não foi criado")

            # Atualizar informações do backup
            tamanho = backup_filepath.stat().st_size
            backup.tamanho = tamanho
            backup.status = 'SUCESSO'
            backup.concluido_at = datetime.now(timezone.utc)
            db.session.commit()

            logger.info(f"Backup automático criado com sucesso: {backup_filename} ({tamanho} bytes)")

        except Exception as e:
            # Marcar backup como falha
            backup.status = 'FALHA'
            backup.erro_mensagem = str(e)
            backup.concluido_at = datetime.now(timezone.utc)
            db.session.commit()

            logger.error(f"Erro ao criar backup automático: {str(e)}", exc_info=True)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro de banco ao criar backup automático: {str(e)}", exc_info=True)

@backup_bp.route("/", methods=["GET"])
@login_required
def list_backups():
    """Lista todos os backups realizados"""
    try:
        # Apenas ADMIN pode acessar backups
        if current_user.role != 'ADMIN':
            flash("Acesso negado. Apenas administradores podem gerenciar backups.", "error")
            return redirect(url_for("dashboard.index"))

        backups = Backup.query.order_by(Backup.created_at.desc()).all()

        # Estatísticas
        stats = {
            'total': len(backups),
            'sucesso': len([b for b in backups if b.status == 'SUCESSO']),
            'falha': len([b for b in backups if b.status == 'FALHA']),
            'executando': len([b for b in backups if b.status == 'EXECUTANDO'])
        }

        return render_template("dashboard/backup.html", backups=backups, stats=stats)
    except Exception as e:
        logger.error(f"Erro ao listar backups: {str(e)}", exc_info=True)
        flash("Erro ao carregar backups", "error")
        return render_template("dashboard/backup.html", backups=[], stats={'total': 0, 'sucesso': 0, 'falha': 0, 'executando': 0})

@backup_bp.route("/create", methods=["POST"])
@login_required
def create_backup():
    """Cria um novo backup do banco de dados"""
    try:
        # Apenas ADMIN pode criar backups
        if current_user.role != 'ADMIN':
            return jsonify({"error": "Acesso negado"}), 403

        # Criar diretório se não existir
        backup_path = Path(current_app.root_path) / BACKUP_DIR
        backup_path.mkdir(exist_ok=True)

        # Nome do arquivo de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_filepath = backup_path / backup_filename

        # Criar registro do backup
        backup = Backup(
            nome=f"Backup Manual - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            arquivo=str(backup_filepath),
            tamanho=0,  # Será atualizado após criação
            tipo='MANUAL',
            status='EXECUTANDO',
            criado_por=current_user.id
        )
        db.session.add(backup)
        db.session.commit()

        try:
            # Fazer backup do banco SQLite
            db_path = get_sqlite_path()
            if not db_path:
                raise Exception("Backup manual suportado apenas para SQLite")
            
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")

            # Copiar arquivo do banco
            shutil.copy2(db_path, backup_filepath)

            # Verificar se o backup foi criado com sucesso
            if not backup_filepath.exists():
                raise Exception("Arquivo de backup não foi criado")

            # Atualizar informações do backup
            tamanho = backup_filepath.stat().st_size
            backup.tamanho = tamanho
            backup.status = 'SUCESSO'
            backup.concluido_at = datetime.now(timezone.utc)
            db.session.commit()

            logger.info(f"Backup criado com sucesso: {backup_filename} ({tamanho} bytes)")
            flash(f"Backup criado com sucesso: {backup_filename}", "success")

        except Exception as e:
            # Marcar backup como falha
            backup.status = 'FALHA'
            backup.erro_mensagem = str(e)
            backup.concluido_at = datetime.now(timezone.utc)
            db.session.commit()

            logger.error(f"Erro ao criar backup: {str(e)}", exc_info=True)
            flash(f"Erro ao criar backup: {str(e)}", "error")

        return redirect(url_for("backup.list_backups"))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro de banco ao criar backup: {str(e)}", exc_info=True)
        flash("Erro interno do servidor", "error")
        return redirect(url_for("backup.list_backups"))

@backup_bp.route("/create-auto", methods=["POST"])
@login_required
def create_backup_auto():
    """Executa backup automático manualmente (para testes)"""
    try:
        # Apenas ADMIN pode criar backups
        if current_user.role != 'ADMIN':
            return jsonify({"error": "Acesso negado"}), 403

        # Executar backup automático
        create_backup_automatico()

        flash("Backup automático executado com sucesso", "success")
        return redirect(url_for("backup.list_backups"))

    except Exception as e:
        logger.error(f"Erro ao executar backup automático manual: {str(e)}", exc_info=True)
        flash("Erro ao executar backup automático", "error")
        return redirect(url_for("backup.list_backups"))

@backup_bp.route("/<int:id>/download", methods=["GET"])
@login_required
def download_backup(id):
    """Download de um arquivo de backup"""
    try:
        # Apenas ADMIN pode baixar backups
        if current_user.role != 'ADMIN':
            flash("Acesso negado", "error")
            return redirect(url_for("dashboard.index"))

        backup = Backup.query.get_or_404(id)

        if backup.status != 'SUCESSO':
            flash("Este backup não está disponível para download", "error")
            return redirect(url_for("backup.list_backups"))

        if not os.path.exists(backup.arquivo):
            flash("Arquivo de backup não encontrado", "error")
            return redirect(url_for("backup.list_backups"))

        return send_file(
            backup.arquivo,
            as_attachment=True,
            download_name=f"{backup.nome.replace(' ', '_')}.db"
        )

    except Exception as e:
        logger.error(f"Erro ao baixar backup {id}: {str(e)}", exc_info=True)
        flash("Erro ao baixar backup", "error")
        return redirect(url_for("backup.list_backups"))

@backup_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_backup(id):
    """Remove um backup"""
    try:
        # Apenas ADMIN pode deletar backups
        if current_user.role != 'ADMIN':
            return jsonify({"error": "Acesso negado"}), 403

        backup = Backup.query.get_or_404(id)

        # Remover arquivo físico se existir
        if os.path.exists(backup.arquivo):
            try:
                os.remove(backup.arquivo)
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo físico do backup {id}: {str(e)}")

        # Remover registro do banco
        db.session.delete(backup)
        db.session.commit()

        flash("Backup removido com sucesso", "success")
        return redirect(url_for("backup.list_backups"))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao remover backup {id}: {str(e)}", exc_info=True)
        flash("Erro ao remover backup", "error")
        return redirect(url_for("backup.list_backups"))

@backup_bp.route("/restore/<int:id>", methods=["POST"])
@login_required
def restore_backup(id):
    """Restaura um backup"""
    try:
        # Apenas ADMIN pode restaurar backups
        if current_user.role != 'ADMIN':
            return jsonify({"error": "Acesso negado"}), 403

        backup = Backup.query.get_or_404(id)

        if backup.status != 'SUCESSO':
            flash("Este backup não pode ser restaurado", "error")
            return redirect(url_for("backup.list_backups"))

        if not os.path.exists(backup.arquivo):
            flash("Arquivo de backup não encontrado", "error")
            return redirect(url_for("backup.list_backups"))

        # Caminho do banco atual
        db_path = get_sqlite_path()
        if not db_path:
            flash("Restauração suportada apenas para SQLite", "error")
            return redirect(url_for("backup.list_backups"))

        # Criar backup do estado atual antes de restaurar
        backup_atual_filename = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_atual_path = Path(current_app.root_path) / BACKUP_DIR / backup_atual_filename

        try:
            # Fazer backup do estado atual
            shutil.copy2(db_path, backup_atual_path)

            # Registrar backup de segurança
            backup_seguranca = Backup(
                nome=f"Backup de Segurança - Pré-restauração {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                arquivo=str(backup_atual_path),
                tamanho=backup_atual_path.stat().st_size,
                tipo='AUTOMATICO',
                status='SUCESSO',
                criado_por=current_user.id,
                concluido_at=datetime.now(timezone.utc)
            )
            db.session.add(backup_seguranca)
            db.session.commit()

        except Exception as e:
            logger.warning(f"Erro ao criar backup de segurança: {str(e)}")

        # Restaurar backup
        shutil.copy2(backup.arquivo, db_path)

        flash("Backup restaurado com sucesso! O sistema será reiniciado.", "success")
        logger.info(f"Backup {id} restaurado por {current_user.name_user}")

        # Nota: Em produção, seria necessário reiniciar a aplicação
        return redirect(url_for("backup.list_backups"))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao restaurar backup {id}: {str(e)}", exc_info=True)
        flash("Erro ao restaurar backup", "error")
        return redirect(url_for("backup.list_backups"))

@backup_bp.route("/cleanup", methods=["POST"])
@login_required
def cleanup_old_backups():
    """Remove backups antigos (mantém apenas os 10 mais recentes)"""
    try:
        # Apenas ADMIN pode limpar backups
        if current_user.role != 'ADMIN':
            return jsonify({"error": "Acesso negado"}), 403

        # Buscar todos os backups de sucesso ordenados por data
        backups = Backup.query.filter_by(status='SUCESSO').order_by(Backup.created_at.desc()).all()

        if len(backups) <= 10:
            flash("Não há backups antigos para remover", "info")
            return redirect(url_for("backup.list_backups"))

        # Manter apenas os 10 mais recentes
        backups_para_remover = backups[10:]

        removidos = 0
        for backup in backups_para_remover:
            # Remover arquivo físico
            if os.path.exists(backup.arquivo):
                try:
                    os.remove(backup.arquivo)
                    removidos += 1
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo físico do backup {backup.id}: {str(e)}")

            # Remover registro do banco
            db.session.delete(backup)

        db.session.commit()

        flash(f"{removidos} backups antigos removidos com sucesso", "success")
        return redirect(url_for("backup.list_backups"))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao limpar backups antigos: {str(e)}", exc_info=True)
        flash("Erro ao limpar backups antigos", "error")
        return redirect(url_for("backup.list_backups"))