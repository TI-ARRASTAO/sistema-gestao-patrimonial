# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from .advanced_reports import ReportGenerator
from .audit import AuditManager
from datetime import datetime, timedelta
import json

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
def index():
    """Página principal de auditoria"""
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem acessar relatórios de auditoria.", "error")
        return redirect(url_for('dashboard.index'))
    
    # Resumo rápido dos últimos 7 dias
    summary = AuditManager.get_audit_summary(days=7)
    
    return render_template('audit/index.html', summary=summary)

@audit_bp.route('/reports/audit')
@login_required
def audit_report():
    """Relatório detalhado de auditoria"""
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Parâmetros de filtro
    days = request.args.get('days', 30, type=int)
    user_id = request.args.get('user_id', type=int)
    action_type = request.args.get('action_type')
    
    # Gerar relatório
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    report = ReportGenerator.generate_audit_report(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action_type=action_type
    )
    
    return jsonify(report)

@audit_bp.route('/reports/compliance')
@login_required
def compliance_report():
    """Relatório de compliance"""
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado'}), 403
    
    report = ReportGenerator.generate_compliance_report()
    return jsonify(report)

@audit_bp.route('/reports/lifecycle')
@login_required
def lifecycle_report():
    """Relatório de ciclo de vida dos equipamentos"""
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado'}), 403
    
    report = ReportGenerator.generate_equipment_lifecycle_report()
    return jsonify(report)

@audit_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard de auditoria com métricas em tempo real"""
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem acessar o dashboard de auditoria.", "error")
        return redirect(url_for('dashboard.index'))
    
    # Métricas para o dashboard
    metrics = {
        'last_24h': AuditManager.get_audit_summary(days=1),
        'last_7d': AuditManager.get_audit_summary(days=7),
        'last_30d': AuditManager.get_audit_summary(days=30)
    }
    
    # Compliance score
    compliance = ReportGenerator.generate_compliance_report()
    
    return render_template('audit/dashboard.html', 
                         metrics=metrics, 
                         compliance=compliance)

@audit_bp.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Exporta relatórios em diferentes formatos"""
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Registrar auditoria da exportação
    AuditManager.log_action('EXPORT', 'audit_reports', details={
        'report_type': report_type,
        'export_format': request.args.get('format', 'json')
    })
    
    if report_type == 'audit':
        report = ReportGenerator.generate_audit_report()
    elif report_type == 'compliance':
        report = ReportGenerator.generate_compliance_report()
    elif report_type == 'lifecycle':
        report = ReportGenerator.generate_equipment_lifecycle_report()
    else:
        return jsonify({'error': 'Tipo de relatório inválido'}), 400
    
    # Formato de exportação
    format_type = request.args.get('format', 'json')
    
    if format_type == 'json':
        response = jsonify(report)
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response
    
    # Adicionar outros formatos conforme necessário
    return jsonify({'error': 'Formato não suportado'}), 400