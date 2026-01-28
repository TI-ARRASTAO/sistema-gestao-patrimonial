# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
import logging

from . import db
from .models import Notificacao, Emprestimo, Equipamento, Administrador

logger = logging.getLogger(__name__)

notificacoes_bp = Blueprint("notificacoes", __name__, template_folder="templates")

@notificacoes_bp.route("/", methods=["GET"])
@login_required
def index():
    """Lista todas as notificações do usuário atual"""
    try:
        # Buscar notificações não lidas primeiro, depois as lidas
        notificacoes_nao_lidas = Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).order_by(Notificacao.created_at.desc()).all()

        notificacoes_lidas = Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=True
        ).order_by(Notificacao.created_at.desc()).limit(50).all()

        notificacoes = notificacoes_nao_lidas + notificacoes_lidas

        # Estatísticas
        stats = {
            'total_nao_lidas': len(notificacoes_nao_lidas),
            'total_lidas': len(notificacoes_lidas),
            'total': len(notificacoes)
        }

        return render_template("dashboard/notificacoes.html",
                             notificacoes=notificacoes,
                             stats=stats)
    except Exception as e:
        logger.error(f"Erro ao listar notificações: {str(e)}", exc_info=True)
        flash("Erro ao carregar notificações", "error")
        return render_template("dashboard/notificacoes.html",
                             notificacoes=[],
                             stats={'total_nao_lidas': 0, 'total_lidas': 0, 'total': 0})

@notificacoes_bp.route("/marcar-lida/<int:id>", methods=["POST"])
@login_required
def marcar_lida(id):
    """Marca uma notificação como lida"""
    try:
        notificacao = Notificacao.query.filter_by(id=id, usuario_id=current_user.id).first()
        if not notificacao:
            return jsonify({"error": "Notificação não encontrada"}), 404

        notificacao.lida = True
        db.session.commit()

        return jsonify({"success": "Notificação marcada como lida"})
    except Exception as e:
        logger.error(f"Erro ao marcar notificação como lida: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500

@notificacoes_bp.route("/marcar-todas-lidas", methods=["POST"])
@login_required
def marcar_todas_lidas():
    """Marca todas as notificações do usuário como lidas"""
    try:
        Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).update({'lida': True})

        db.session.commit()
        return jsonify({"success": "Todas as notificações foram marcadas como lidas"})
    except Exception as e:
        logger.error(f"Erro ao marcar todas notificações como lidas: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500

@notificacoes_bp.route("/api/count", methods=["GET"])
@login_required
def get_notificacoes_count():
    """Retorna contagem de notificações não lidas (para AJAX)"""
    try:
        count = Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).count()

        return jsonify({"count": count})
    except Exception as e:
        logger.error(f"Erro ao contar notificações: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500

def criar_notificacao_emprestimo_atrasado():
    """Verifica empréstimos atrasados e cria notificações"""
    try:
        now_utc = datetime.now(timezone.utc)
        # Buscar empréstimos ativos com data de devolução vencida
        emprestimos_atrasados = Emprestimo.query.filter(
            Emprestimo.status == 'ATIVO',
            Emprestimo.data_prevista_devolucao < now_utc
        ).all()

        for emprestimo in emprestimos_atrasados:
            # Verificar se já existe notificação para este empréstimo
            notificacao_existente = Notificacao.query.filter_by(
                usuario_id=emprestimo.responsavel_id,
                relacionada_tabela='emprestimos',
                relacionada_id=emprestimo.id,
                titulo='Empréstimo Atrasado'
            ).first()

            if not notificacao_existente:
                # Buscar dados do equipamento e usuário
                equipamento = Equipamento.query.get(emprestimo.equipamento_id)
                usuario = Administrador.query.get(emprestimo.usuario_id)

                if equipamento and usuario:
                    # Converter data prevista para timezone-aware se necessário
                    data_prevista = emprestimo.data_prevista_devolucao
                    if data_prevista and data_prevista.tzinfo is None:
                        data_prevista = data_prevista.replace(tzinfo=timezone.utc)
                    
                    dias_atraso = (now_utc - data_prevista).days

                    notificacao = Notificacao(
                        usuario_id=emprestimo.responsavel_id,
                        titulo='Empréstimo Atrasado',
                        mensagem=f'O equipamento "{equipamento.name_response}" emprestado para {usuario.name_user} está atrasado há {dias_atraso} dias. Data prevista: {emprestimo.data_prevista_devolucao.strftime("%d/%m/%Y") if emprestimo.data_prevista_devolucao else "N/A"}',
                        tipo='WARNING',
                        relacionada_tabela='emprestimos',
                        relacionada_id=emprestimo.id,
                        expires_at=now_utc + timedelta(days=30)  # Expira em 30 dias
                    )

                    db.session.add(notificacao)

        db.session.commit()
        logger.info(f"Criadas notificações para {len(emprestimos_atrasados)} empréstimos atrasados")

    except Exception as e:
        logger.error(f"Erro ao criar notificações de empréstimos atrasados: {str(e)}", exc_info=True)
        db.session.rollback()

def criar_notificacao_emprestimo_vence_hoje():
    """Cria notificações para empréstimos que vencem hoje"""
    try:
        now_utc = datetime.now(timezone.utc)
        hoje = now_utc.date()
        emprestimos_hoje = Emprestimo.query.filter(
            Emprestimo.status == 'ATIVO',
            Emprestimo.data_prevista_devolucao.isnot(None),
            db.func.date(Emprestimo.data_prevista_devolucao) == hoje
        ).all()

        for emprestimo in emprestimos_hoje:
            # Verificar se já existe notificação
            notificacao_existente = Notificacao.query.filter_by(
                usuario_id=emprestimo.responsavel_id,
                relacionada_tabela='emprestimos',
                relacionada_id=emprestimo.id,
                titulo='Empréstimo Vence Hoje'
            ).first()

            if not notificacao_existente:
                equipamento = Equipamento.query.get(emprestimo.equipamento_id)
                usuario = Administrador.query.get(emprestimo.usuario_id)

                if equipamento and usuario:
                    notificacao = Notificacao(
                        usuario_id=emprestimo.responsavel_id,
                        titulo='Empréstimo Vence Hoje',
                        mensagem=f'O empréstimo do equipamento "{equipamento.name_response}" para {usuario.name_user} vence hoje.',
                        tipo='WARNING',
                        relacionada_tabela='emprestimos',
                        relacionada_id=emprestimo.id,
                        expires_at=now_utc + timedelta(days=1)
                    )

                    db.session.add(notificacao)

        db.session.commit()
        logger.info(f"Criadas notificações para {len(emprestimos_hoje)} empréstimos que vencem hoje")

    except Exception as e:
        logger.error(f"Erro ao criar notificações de empréstimos que vencem hoje: {str(e)}", exc_info=True)
        db.session.rollback()

def criar_notificacao_emprestimo_vence_amanha():
    """Cria notificações para empréstimos que vencem amanhã"""
    try:
        now_utc = datetime.now(timezone.utc)
        amanha = (now_utc + timedelta(days=1)).date()
        emprestimos_amanha = Emprestimo.query.filter(
            Emprestimo.status == 'ATIVO',
            Emprestimo.data_prevista_devolucao.isnot(None),
            db.func.date(Emprestimo.data_prevista_devolucao) == amanha
        ).all()

        for emprestimo in emprestimos_amanha:
            # Verificar se já existe notificação
            notificacao_existente = Notificacao.query.filter_by(
                usuario_id=emprestimo.responsavel_id,
                relacionada_tabela='emprestimos',
                relacionada_id=emprestimo.id,
                titulo='Empréstimo Vence Amanhã'
            ).first()

            if not notificacao_existente:
                equipamento = Equipamento.query.get(emprestimo.equipamento_id)
                usuario = Administrador.query.get(emprestimo.usuario_id)

                if equipamento and usuario:
                    notificacao = Notificacao(
                        usuario_id=emprestimo.responsavel_id,
                        titulo='Empréstimo Vence Amanhã',
                        mensagem=f'O empréstimo do equipamento "{equipamento.name_response}" para {usuario.name_user} vence amanhã ({emprestimo.data_prevista_devolucao.strftime("%d/%m/%Y")}).',
                        tipo='INFO',
                        relacionada_tabela='emprestimos',
                        relacionada_id=emprestimo.id,
                        expires_at=now_utc + timedelta(days=2)
                    )

                    db.session.add(notificacao)

        db.session.commit()
        logger.info(f"Criadas notificações para {len(emprestimos_amanha)} empréstimos que vencem amanhã")

    except Exception as e:
        logger.error(f"Erro ao criar notificações de empréstimos que vencem amanhã: {str(e)}", exc_info=True)
        db.session.rollback()

def limpar_notificacoes_expiradas():
    """Remove notificações expiradas"""
    try:
        now_utc = datetime.now(timezone.utc)
        notificacoes_expiradas = Notificacao.query.filter(
            Notificacao.expires_at.isnot(None),
            Notificacao.expires_at < now_utc
        ).delete()

        db.session.commit()
        if notificacoes_expiradas > 0:
            logger.info(f"Removidas {notificacoes_expiradas} notificações expiradas")

    except Exception as e:
        logger.error(f"Erro ao limpar notificações expiradas: {str(e)}", exc_info=True)
        db.session.rollback()

def executar_verificacoes_notificacoes():
    """Executa todas as verificações de notificações (chamada por scheduler)"""
    logger.info("Executando verificações de notificações...")

    criar_notificacao_emprestimo_atrasado()
    criar_notificacao_emprestimo_vence_hoje()
    criar_notificacao_emprestimo_vence_amanha()
    limpar_notificacoes_expiradas()

    logger.info("Verificações de notificações concluídas")