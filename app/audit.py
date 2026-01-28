# -*- coding: utf-8 -*-
"""
Sistema de Auditoria Aprimorado
Registra todas as operações críticas do sistema para compliance e rastreabilidade
"""

from flask import request, session
from flask_login import current_user
from . import db
from .models import AuditLog, Equipamento, Administrador
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

class AuditManager:
    """Gerenciador central de auditoria"""
    
    @staticmethod
    def log_action(action, table_name, record_id=None, old_values=None, new_values=None, details=None):
        """
        Registra uma ação no log de auditoria
        """
        try:
            # Verificar se estamos em contexto de requisição
            user_id = None
            ip_address = None
            user_agent = None
            
            try:
                from flask_login import current_user
                from flask import request
                
                if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                    user_id = current_user.id
                
                if request:
                    ip_address = request.remote_addr
                    user_agent = request.headers.get('User-Agent', '')[:255]
            except:
                # Contexto fora de requisição (testes, scripts)
                pass
            
            # Preparar dados para JSON
            import json
            old_json = json.dumps(old_values, default=str) if old_values else None
            new_json = json.dumps(new_values, default=str) if new_values else None
            
            # Criar registro de auditoria
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                table_name=table_name,
                record_id=record_id,
                old_values=old_json,
                new_values=new_json,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            # Log crítico para ações sensíveis
            if action in ['DELETE', 'CLEAR_ALL', 'EXPORT', 'IMPORT']:
                logger.critical(f"AUDITORIA: {action} em {table_name} por usuário {user_id or 'SISTEMA'}")
            
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {str(e)}")
            # Não falhar a operação principal por erro de auditoria
    
    @staticmethod
    def _get_action_details(action, table_name, record_id):
        """Gera detalhes específicos da ação"""
        details = {
            'action_type': action,
            'target_table': table_name,
            'target_id': record_id
        }
        
        # Adicionar contexto específico por tipo de ação
        if action == 'LOGIN':
            details['login_method'] = 'web_interface'
        elif action == 'EXPORT':
            details['export_format'] = request.args.get('format', 'unknown') if request else 'unknown'
        elif action == 'CLEAR_ALL':
            details['severity'] = 'CRITICAL'
            details['data_loss'] = True
        
        return details
    
    @staticmethod
    def log_equipment_change(action, equipment, old_data=None):
        """Log específico para mudanças em equipamentos"""
        new_data = {
            'id': equipment.id,
            'name': equipment.name_response,
            'category': equipment.equipamento_category,
            'brand': equipment.marca_category,
            'sector': equipment.setor_category,
            'status': equipment.emprestimo,
            'shared': equipment.equipamento_compartilhado
        }
        
        AuditManager.log_action(
            action=action,
            table_name='equipamentos',
            record_id=equipment.id,
            old_values=old_data,
            new_values=new_data,
            details={
                'equipment_name': equipment.name_response,
                'equipment_category': equipment.equipamento_category
            }
        )
    
    @staticmethod
    def log_user_action(action, user_id=None, details=None):
        """Log específico para ações de usuário"""
        AuditManager.log_action(
            action=action,
            table_name='administrador',
            record_id=user_id,
            details=details
        )
    
    @staticmethod
    def get_audit_summary(days=30):
        """Retorna resumo de auditoria dos últimos N dias"""
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        logs = AuditLog.query.filter(AuditLog.created_at >= start_date).all()
        
        summary = {
            'total_actions': len(logs),
            'actions_by_type': {},
            'actions_by_user': {},
            'actions_by_table': {},
            'critical_actions': [],
            'recent_actions': []
        }
        
        for log in logs:
            # Contar por tipo
            summary['actions_by_type'][log.action] = summary['actions_by_type'].get(log.action, 0) + 1
            
            # Contar por usuário
            user_name = 'Sistema' if not log.user_id else f"User_{log.user_id}"
            if log.user_id:
                user = Administrador.query.get(log.user_id)
                if user:
                    user_name = user.name_user
            
            summary['actions_by_user'][user_name] = summary['actions_by_user'].get(user_name, 0) + 1
            
            # Contar por tabela
            summary['actions_by_table'][log.table_name] = summary['actions_by_table'].get(log.table_name, 0) + 1
            
            # Ações críticas
            if log.action in ['DELETE', 'CLEAR_ALL', 'EXPORT']:
                summary['critical_actions'].append({
                    'action': log.action,
                    'table': log.table_name,
                    'user': user_name,
                    'timestamp': log.created_at.isoformat(),
                    'ip': log.ip_address
                })
        
        # Ações recentes (últimas 10)
        recent = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
        for log in recent:
            user_name = 'Sistema' if not log.user_id else f"User_{log.user_id}"
            if log.user_id:
                user = Administrador.query.get(log.user_id)
                if user:
                    user_name = user.name_user
            
            summary['recent_actions'].append({
                'action': log.action,
                'table': log.table_name,
                'user': user_name,
                'timestamp': log.created_at.isoformat(),
                'record_id': log.record_id
            })
        
        return summary

# Decorador para auditoria automática
def audit_action(action, table_name):
    """Decorador para registrar automaticamente ações auditáveis"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                AuditManager.log_action(action, table_name)
                return result
            except Exception as e:
                AuditManager.log_action(f"{action}_FAILED", table_name, details={'error': str(e)})
                raise
        return wrapper
    return decorator