# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
import logging

from . import db
from .models import Emprestimo, Equipamento, Administrador

logger = logging.getLogger(__name__)

emprestimos_bp = Blueprint("emprestimos", __name__, template_folder="templates")

@emprestimos_bp.route("/", methods=["GET"])
@login_required
def list_emprestimos():
    try:
        emprestimos = Emprestimo.query.filter_by(status='ATIVO').all()
        
        now_utc = datetime.now(timezone.utc)
        
        # Função auxiliar para comparar datas com timezone-aware
        def make_aware(dt):
            if dt and dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        kpis = {
            "total_ativos": len(emprestimos),
            "atrasados": len([e for e in emprestimos if e.data_prevista_devolucao and make_aware(e.data_prevista_devolucao) < now_utc]),
            "hoje": len([e for e in emprestimos if e.data_prevista_devolucao and make_aware(e.data_prevista_devolucao).date() == now_utc.date()])
        }
        
        return render_template("dashboard/emprestimos.html", emprestimos=emprestimos, kpis=kpis)
    except Exception as e:
        logger.error(f"Erro ao listar empréstimos: {str(e)}", exc_info=True)
        flash("Erro ao carregar empréstimos", "error")
        return render_template("dashboard/emprestimos.html", emprestimos=[], kpis={"total_ativos": 0, "atrasados": 0, "hoje": 0})

@emprestimos_bp.route("/create", methods=["POST"])
@login_required
def create_emprestimo():
    data = request.get_json()
    
    try:
        equipamento = Equipamento.query.get_or_404(data['equipamento_id'])
        usuario = Administrador.query.get_or_404(data['usuario_id'])
        
        # Verificar se equipamento já está emprestado
        emprestimo_ativo = Emprestimo.query.filter_by(equipamento_id=equipamento.id, status='ATIVO').first()
        if emprestimo_ativo:
            return jsonify({"error": "Equipamento já está emprestado"}), 400
        
        data_prevista = datetime.strptime(data['data_prevista'], '%Y-%m-%d') if data.get('data_prevista') else datetime.now(timezone.utc) + timedelta(days=7)
        
        emprestimo = Emprestimo(
            equipamento_id=equipamento.id,
            usuario_id=usuario.id,
            responsavel_id=current_user.id,
            data_prevista_devolucao=data_prevista,
            observacoes=data.get('observacoes')
        )
        
        # Atualizar status do equipamento
        equipamento.emprestimo = 'SIM'
        
        db.session.add(emprestimo)
        db.session.commit()
        
        return jsonify({"success": "Empréstimo criado com sucesso"}), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao criar empréstimo: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500

@emprestimos_bp.route("/<int:id>/devolver", methods=["POST"])
@login_required
def devolver_emprestimo(id):
    try:
        emprestimo = Emprestimo.query.get_or_404(id)
        
        emprestimo.data_devolucao = datetime.now(timezone.utc)
        emprestimo.status = 'DEVOLVIDO'
        
        # Atualizar status do equipamento
        equipamento = Equipamento.query.get(emprestimo.equipamento_id)
        equipamento.emprestimo = 'NAO'
        
        db.session.commit()
        
        return jsonify({"success": "Equipamento devolvido com sucesso"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao devolver empréstimo {id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500