# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from . import db
from .models import Equipamento, Administrador, Emprestimo, AuditLog
from .audit import AuditManager
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
import calendar

# Desabilitar CSRF para rotas de API
try:
    from flask_wtf.csrf import exempt
except ImportError:
    def exempt(f):
        return f

relatorios_bp = Blueprint(
    "relatorios",
    __name__,
    template_folder="templates"
)

@relatorios_bp.route("/", methods=["GET"])
@login_required
def index():
    try:
        # Aplicar filtro por setor se usuário não for ADMIN
        base_query = Equipamento.query
        if current_user.role != 'ADMIN' and current_user.setor:
            base_query = base_query.filter_by(setor_category=current_user.setor)
        
        # 1. Status dos Equipamentos
        total_equipamentos = base_query.count()
        em_uso = base_query.filter_by(emprestimo="EM_USO").count()
        quebrados = base_query.filter_by(emprestimo="QUEBRADO").count()
        disponivel = total_equipamentos - em_uso - quebrados
        
        if total_equipamentos == 0:
            status_data = {
                "labels": [],
                "data": [],
                "colors": []
            }
        else:
            status_data = {
                "labels": ["Disponível", "Em Uso", "Quebrado"],
                "data": [disponivel, em_uso, quebrados],
                "colors": ["#10b981", "#f59e0b", "#ef4444"]
            }
        
        # 2. Equipamentos por Categoria
        cats_query = db.session.query(
            Equipamento.equipamento_category,
            func.count(Equipamento.id)
        )
        if current_user.role != 'ADMIN' and current_user.setor:
            cats_query = cats_query.filter_by(setor_category=current_user.setor)
        cats = cats_query.group_by(Equipamento.equipamento_category).all()
        
        category_data = {
            "labels": [c[0] for c in cats if c[0]],
            "data": [c[1] for c in cats if c[0]]
        }
        
        if not category_data["data"] or sum(category_data["data"]) == 0:
            category_data = {
                "labels": [],
                "data": []
            }
        
        # 3. Movimentação Mensal (Últimos 6 meses)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Empréstimos por mês
        loans_query = db.session.query(
            extract('year', Emprestimo.data_emprestimo),
            extract('month', Emprestimo.data_emprestimo),
            func.count(Emprestimo.id)
        ).filter(Emprestimo.data_emprestimo >= start_date)\
         .group_by(extract('year', Emprestimo.data_emprestimo), 
                   extract('month', Emprestimo.data_emprestimo)).all()
        
        loans_dict = {f"{int(r[0]):04d}-{int(r[1]):02d}": r[2] for r in loans_query}
        
        # Devoluções por mês
        returns_query = db.session.query(
            extract('year', Emprestimo.data_devolucao),
            extract('month', Emprestimo.data_devolucao),
            func.count(Emprestimo.id)
        ).filter(Emprestimo.data_devolucao >= start_date)\
         .group_by(extract('year', Emprestimo.data_devolucao), 
                   extract('month', Emprestimo.data_devolucao)).all()
         
        returns_dict = {f"{int(r[0]):04d}-{int(r[1]):02d}": r[2] for r in returns_query}
        
        # Construir dados para o gráfico
        movement_labels = []
        loans_data = []
        returns_data = []
        
        # Gerar últimos 6 meses
        for i in range(5, -1, -1):
            # Calcular data aproximada para o mês
            d = end_date.replace(day=1) - timedelta(days=i*30)
            # Ajustar para o mês correto se necessário (simplificado)
            
            # Melhor abordagem para iterar meses:
            year = end_date.year
            month = end_date.month - i
            while month <= 0:
                month += 12
                year -= 1
            
            key = f"{year:04d}-{month:02d}"
            month_name = calendar.month_abbr[month]
            
            movement_labels.append(month_name)
            loans_data.append(loans_dict.get(key, 0))
            returns_data.append(returns_dict.get(key, 0))
            
        movement_data = {
            "labels": movement_labels,
            "loans": loans_data,
            "returns": returns_data
        }
        
        # Se não há dados de movimento, definir como vazio
        if all(x == 0 for x in loans_data) and all(x == 0 for x in returns_data):
            movement_data = {
                "labels": [],
                "loans": [],
                "returns": []
            }
        
        return render_template(
            "dashboard/relatorios.html",
            status_data=status_data,
            category_data=category_data,
            movement_data=movement_data
        )
    except Exception as e:
        import logging
        logging.error(f"Erro ao carregar relatórios: {str(e)}", exc_info=True)
        flash("Erro ao carregar relatórios", "error")
        return render_template(
            "dashboard/relatorios.html",
            status_data={"labels": [], "data": [], "colors": []},
            category_data={"labels": [], "data": []},
            movement_data={"labels": [], "loans": [], "returns": []}
        )

def _gerar_dados_equipamento(eq):
    """Helper para gerar dados de equipamento"""
    try:
        return {
            "id": eq.id or 0,
            "nome": eq.name_response or "N/A",
            "categoria": eq.equipamento_category or "N/A",
            "marca": eq.marca_category or "N/A",
            "status": "Em Uso" if eq.emprestimo == "EM_USO" else "Quebrado" if eq.emprestimo == "QUEBRADO" else "Disponível",
            "setor": eq.setor_category or "N/A"
        }
    except Exception as e:
        import logging
        logging.error(f"Erro ao gerar dados do equipamento {getattr(eq, 'id', 'N/A')}: {str(e)}")
        return {
            "id": getattr(eq, 'id', 0),
            "nome": "Erro ao carregar",
            "categoria": "N/A",
            "marca": "N/A",
            "status": "N/A",
            "setor": "N/A"
        }

@relatorios_bp.route("/gerar/localizacao/setor", methods=["POST", "GET"])
@login_required
def gerar_relatorio_setor():
    try:
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
        setor = request.json.get('setor') if request.is_json else request.args.get('setor')
        
        if not setor:
            return {"error": "Setor não especificado"}
        
        # Verificar se usuário pode acessar o setor solicitado
        if current_user.role != 'ADMIN' and hasattr(current_user, 'setor') and current_user.setor and setor != current_user.setor:
            return {"error": "Acesso negado. Você só pode gerar relatórios do seu setor."}
        
        equipamentos = Equipamento.query.filter_by(setor_category=setor).all()
        
        data = {
            "tipo": f"Relatório de Localização - Setor {setor}",
            "setor": setor,
            "total": len(equipamentos),
            "equipamentos": [{"id": eq.id, "nome": eq.name_response or "N/A", "categoria": eq.equipamento_category or "N/A", "marca": eq.marca_category or "N/A", "status": "Em Uso" if eq.emprestimo == "EM_USO" else "Quebrado" if eq.emprestimo == "QUEBRADO" else "Disponível", "setor": eq.setor_category or "N/A"} for eq in equipamentos],
            "data_geracao": data_geracao
        }
        
        return {"success": "Relatório gerado com sucesso", "data": data}
        
    except Exception as e:
        return {"error": str(e)}

@relatorios_bp.route("/teste")
def teste():
    return "Funcionando"

@relatorios_bp.route("/gerar/<tipo>", methods=["POST", "GET"])
@login_required
def gerar_relatorio(tipo):
    try:
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Aplicar filtro por setor se usuário não for ADMIN
        def get_query():
            query = Equipamento.query
            if current_user.role != 'ADMIN' and hasattr(current_user, 'setor') and current_user.setor:
                query = query.filter_by(setor_category=current_user.setor)
            return query
        
        if tipo == "inventario":
            equipamentos = get_query().all()
            titulo = "Inventário Geral"
            if current_user.role != 'ADMIN' and current_user.setor:
                titulo += f" - Setor {current_user.setor}"
            data = {
                "tipo": titulo,
                "total": len(equipamentos),
                "equipamentos": [{"id": eq.id, "nome": eq.name_response or "N/A", "categoria": eq.equipamento_category or "N/A", "marca": eq.marca_category or "N/A", "status": "Em Uso" if eq.emprestimo == "EM_USO" else "Quebrado" if eq.emprestimo == "QUEBRADO" else "Disponível", "setor": eq.setor_category or "N/A"} for eq in equipamentos],
                "data_geracao": data_geracao
            }
            
        elif tipo == "emprestimos":
            equipamentos = get_query().filter_by(emprestimo="EM_USO").all()
            titulo = "Relatório de Empréstimos"
            if current_user.role != 'ADMIN' and current_user.setor:
                titulo += f" - Setor {current_user.setor}"
            data = {
                "tipo": titulo,
                "total": len(equipamentos),
                "equipamentos": [{"id": eq.id, "nome": eq.name_response or "N/A", "categoria": eq.equipamento_category or "N/A", "marca": eq.marca_category or "N/A", "status": "Em Uso", "setor": eq.setor_category or "N/A"} for eq in equipamentos],
                "data_geracao": data_geracao
            }
            
        elif tipo == "auditoria":
            # Relatório de auditoria com dados reais
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            
            # Buscar logs de auditoria
            audit_logs = AuditLog.query.filter(
                AuditLog.created_at >= start_date
            ).order_by(AuditLog.created_at.desc()).limit(100).all()
            
            # Análise dos dados
            actions_by_type = {}
            actions_by_user = {}
            critical_actions = []
            
            for log in audit_logs:
                # Contar por tipo
                actions_by_type[log.action] = actions_by_type.get(log.action, 0) + 1
                
                # Contar por usuário
                user_name = 'Sistema' if not log.user_id else 'Usuário Desconhecido'
                if log.user_id:
                    user = Administrador.query.get(log.user_id)
                    if user:
                        user_name = user.name_user
                actions_by_user[user_name] = actions_by_user.get(user_name, 0) + 1
                
                # Ações críticas
                if log.action in ['DELETE', 'CLEAR_ALL', 'EXPORT']:
                    critical_actions.append({
                        'action': log.action,
                        'user': user_name,
                        'timestamp': log.created_at.strftime('%d/%m/%Y %H:%M'),
                        'table': log.table_name,
                        'record_id': log.record_id
                    })
            
            # Calcular score de compliance
            total_actions = len(audit_logs)
            compliance_score = min(100, max(0, 100 - len(critical_actions) * 5))
            
            titulo = "Relatório de Auditoria"
            if current_user.role != 'ADMIN' and current_user.setor:
                titulo += f" - Setor {current_user.setor}"
            
            data = {
                "tipo": titulo,
                "periodo": f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
                "total_acoes": total_actions,
                "acoes_criticas": len(critical_actions),
                "compliance_score": compliance_score,
                "acoes_por_tipo": actions_by_type,
                "acoes_por_usuario": actions_by_user,
                "acoes_criticas_detalhes": critical_actions[:10],
                "usuarios_ativos": len(actions_by_user),
                "data_geracao": data_geracao,
                "recomendacoes": [
                    "Monitorar ações críticas regularmente",
                    "Revisar acessos de usuários periodicamente",
                    "Implementar alertas automáticos para ações suspeitas"
                ] if compliance_score < 85 else [
                    "Sistema em conformidade adequada",
                    "Manter monitoramento contínuo"
                ]
            }
            
        elif tipo == "manutencao":
            titulo = "Relatório de Manutenção"
            if current_user.role != 'ADMIN' and current_user.setor:
                titulo += f" - Setor {current_user.setor}"
            data = {
                "tipo": titulo,
                "data_geracao": data_geracao,
                "message": "Relatório de manutenção disponível para exportação"
            }
            
        elif tipo == "financeiro":
            titulo = "Relatório Financeiro"
            if current_user.role != 'ADMIN' and current_user.setor:
                titulo += f" - Setor {current_user.setor}"
            
            data = {
                "tipo": titulo,
                "data_geracao": data_geracao,
                "message": "Relatório financeiro disponível para exportação em Excel"
            }
            
        elif tipo == "localizacao":
            # Para usuários não-admin, mostrar apenas seu setor
            if current_user.role != 'ADMIN' and current_user.setor:
                setores_disponiveis = [current_user.setor]
            else:
                setores_disponiveis = ['CJ', 'CCA', 'CEI', 'ADMINISTRATIVO', 'RH', 'TI', 'COMUNICACAO', 'SOCIAL', 'FINANCEIRO', 'BAZAR', 'ARRASTART', 'ENFERMARIA', 'COZINHA', 'MANUTENCAO', 'ADMINISTRADOR']
            
            data = {
                "tipo": "Seleção de Setor",
                "requer_setor": True,
                "setores_disponiveis": setores_disponiveis,
                "data_geracao": data_geracao
            }
            
        else:
            return {"error": "Tipo inválido"}
        
        return {"success": "Relatório gerado com sucesso", "data": data}
        
    except Exception as e:
        return {"error": str(e)}

@relatorios_bp.route("/exportar/<formato>", methods=["GET"])
@login_required
def exportar_relatorio(formato):
    from flask import send_file, make_response
    import io
    import csv
    from werkzeug.utils import secure_filename
    
    if formato not in ["pdf", "excel", "csv"]:
        return jsonify({"error": "Formato inválido"}), 400
    
    tipo = request.args.get('tipo', 'inventario')
    setor = request.args.get('setor')
    
    try:
        if tipo == 'financeiro':
            return _exportar_financeiro(formato)
        elif tipo == 'auditoria':
            return _exportar_auditoria(formato)
        elif tipo == 'manutencao':
            return _exportar_manutencao(formato)
        elif tipo == 'emprestimos':
            return _exportar_emprestimos(formato)
        elif tipo == 'localizacao' and setor:
            return _exportar_localizacao(formato, setor)
        else:
            return _exportar_inventario(formato)
            
    except Exception as e:
        import logging
        logging.error(f"Erro ao exportar relatório: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao exportar relatório"}), 500

def _exportar_financeiro(formato):
    """Export específico para relatório financeiro"""
    from flask import make_response
    import io, csv
    from werkzeug.utils import secure_filename
    
    query = Equipamento.query
    if current_user.role != 'ADMIN' and current_user.setor:
        query = query.filter_by(setor_category=current_user.setor)
    
    equipamentos = query.all()
    
    if formato == "excel":
        html = '''<html><head><meta charset="utf-8"><style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        .total-row { background-color: #e8f4fd; font-weight: bold; }
        .currency { text-align: right; }
        .status-disponivel { color: #10b981; }
        .status-em-uso { color: #f59e0b; }
        .status-quebrado { color: #ef4444; }
        </style></head><body>
        <h2>Relatório Financeiro - Patrimônio</h2>
        <p><strong>Gerado em:</strong> ''' + datetime.now().strftime("%d/%m/%Y %H:%M") + '''</p>
        <p><strong>Total de equipamentos:</strong> ''' + str(len(equipamentos)) + '''</p>
        <table>
        <tr><th>ID</th><th>Nome</th><th>Categoria</th><th>Marca</th><th>Setor</th><th>Valor Aquisição</th><th>Data Aquisição</th><th>Idade (anos)</th><th>Valor Atual</th><th>Depreciação</th><th>% Depreciação</th><th>Status</th></tr>'''
        
        total_aquisicao = 0
        total_atual = 0
        equipamentos_com_valor = 0
        equipamentos_sem_valor = 0
        
        for eq in equipamentos:
            # Usar valor real se disponível, senão estimar baseado na categoria
            if eq.valor_aquisicao and float(eq.valor_aquisicao) > 0:
                valor_aquisicao = float(eq.valor_aquisicao)
                equipamentos_com_valor += 1
            else:
                # Estimativas por categoria
                estimativas = {
                    'NOTEBOOK': 3500.0,
                    'DESKTOP': 2500.0,
                    'IMPRESSORA': 800.0,
                    'TABLET': 1200.0,
                    'TV': 2000.0,
                    'PROJETOR': 3000.0,
                    'CELULAR': 1500.0,
                    'ACCESS POINT': 300.0,
                    'ROTEADOR': 400.0,
                    'CAIXA DE SOM': 200.0,
                    'PERIFERICOS': 150.0
                }
                valor_aquisicao = estimativas.get(eq.equipamento_category, 1000.0)
                equipamentos_sem_valor += 1
            
            # Calcular idade e depreciação
            if eq.data_aquisicao:
                anos_uso = max(0, (datetime.now().date() - eq.data_aquisicao).days / 365.25)
                data_aquisicao_str = eq.data_aquisicao.strftime('%d/%m/%Y')
            else:
                anos_uso = 2.0  # Assumir 2 anos se não há data
                data_aquisicao_str = 'Não informado'
            
            # Depreciação: 20% ao ano, mínimo 10% do valor original
            taxa_depreciacao = min(0.9, anos_uso * 0.2)  # Máximo 90% de depreciação
            valor_atual = valor_aquisicao * (1 - taxa_depreciacao)
            valor_atual = max(valor_atual, valor_aquisicao * 0.1)  # Mínimo 10% do valor original
            depreciacao = valor_aquisicao - valor_atual
            percentual_depreciacao = (depreciacao / valor_aquisicao) * 100
            
            total_aquisicao += valor_aquisicao
            total_atual += valor_atual
            
            # Determinar classe CSS do status
            if eq.emprestimo == 'EM_USO':
                status_text = 'Em Uso'
                status_class = 'status-em-uso'
            elif eq.emprestimo == 'QUEBRADO':
                status_text = 'Quebrado'
                status_class = 'status-quebrado'
            else:
                status_text = 'Disponível'
                status_class = 'status-disponivel'
            
            # Indicar se o valor é estimado
            valor_display = f"R$ {valor_aquisicao:,.2f}"
            if not (eq.valor_aquisicao and float(eq.valor_aquisicao) > 0):
                valor_display += " (est.)"
            
            html += f'''<tr>
                <td>{eq.id}</td>
                <td>{eq.name_response or ''}</td>
                <td>{eq.equipamento_category or ''}</td>
                <td>{eq.marca_category or ''}</td>
                <td>{eq.setor_category or 'N/A'}</td>
                <td class="currency">{valor_display}</td>
                <td>{data_aquisicao_str}</td>
                <td>{anos_uso:.1f}</td>
                <td class="currency">R$ {valor_atual:,.2f}</td>
                <td class="currency">R$ {depreciacao:,.2f}</td>
                <td class="currency">{percentual_depreciacao:.1f}%</td>
                <td class="{status_class}">{status_text}</td>
            </tr>'''
        
        # Calcular estatísticas
        depreciacao_total = total_aquisicao - total_atual
        percentual_depreciacao_total = (depreciacao_total / total_aquisicao * 100) if total_aquisicao > 0 else 0
        
        html += f'''<tr class="total-row">
            <td colspan="5"><strong>TOTAIS</strong></td>
            <td class="currency"><strong>R$ {total_aquisicao:,.2f}</strong></td>
            <td>-</td>
            <td>-</td>
            <td class="currency"><strong>R$ {total_atual:,.2f}</strong></td>
            <td class="currency"><strong>R$ {depreciacao_total:,.2f}</strong></td>
            <td class="currency"><strong>{percentual_depreciacao_total:.1f}%</strong></td>
            <td>-</td>
        </tr></table>
        
        <h3>Resumo Financeiro</h3>
        <table style="width: 50%;">
            <tr><td><strong>Valor Total Investido:</strong></td><td class="currency"><strong>R$ {total_aquisicao:,.2f}</strong></td></tr>
            <tr><td><strong>Valor Atual do Patrimônio:</strong></td><td class="currency"><strong>R$ {total_atual:,.2f}</strong></td></tr>
            <tr><td><strong>Depreciação Total:</strong></td><td class="currency"><strong>R$ {depreciacao_total:,.2f}</strong></td></tr>
            <tr><td><strong>Percentual de Depreciação:</strong></td><td class="currency"><strong>{percentual_depreciacao_total:.1f}%</strong></td></tr>
            <tr><td>Equipamentos com valor informado:</td><td>{equipamentos_com_valor}</td></tr>
            <tr><td>Equipamentos com valor estimado:</td><td>{equipamentos_sem_valor}</td></tr>
        </table>
        
        <p><em>Nota: Valores marcados com "(est.)" são estimativas baseadas na categoria do equipamento. Para maior precisão, cadastre os valores reais de aquisição.</em></p>
        </body></html>'''
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        response.headers['Content-Disposition'] = 'attachment; filename=relatorio_financeiro.xls'
        return response
    
    return jsonify({"error": "Formato não suportado para relatório financeiro"}), 400

def _exportar_auditoria(formato):
    """Export específico para relatório de auditoria"""
    from flask import make_response
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    audit_logs = AuditLog.query.filter(
        AuditLog.created_at >= start_date
    ).order_by(AuditLog.created_at.desc()).limit(200).all()
    
    if formato == "excel":
        html = '''<html><head><meta charset="utf-8"></head><body>
        <h2>Relatório de Auditoria</h2>
        <p>Período: ''' + start_date.strftime("%d/%m/%Y") + ''' a ''' + end_date.strftime("%d/%m/%Y") + '''</p>
        <p>Total de ações: ''' + str(len(audit_logs)) + '''</p>
        <table border="1">
        <tr><th>Data/Hora</th><th>Usuário</th><th>Ação</th><th>Tabela</th><th>Registro ID</th><th>IP</th><th>Detalhes</th></tr>'''
        
        for log in audit_logs:
            user_name = 'Sistema'
            if log.user_id:
                user = Administrador.query.get(log.user_id)
                user_name = user.name_user if user else 'Usuário Desconhecido'
            
            html += f'''<tr>
                <td>{log.created_at.strftime('%d/%m/%Y %H:%M:%S')}</td>
                <td>{user_name}</td>
                <td>{log.action}</td>
                <td>{log.table_name}</td>
                <td>{log.record_id or 'N/A'}</td>
                <td>{log.ip_address or 'N/A'}</td>
                <td>{log.new_values[:100] if log.new_values else 'N/A'}...</td>
            </tr>'''
        
        html += '</table></body></html>'
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        response.headers['Content-Disposition'] = 'attachment; filename=relatorio_auditoria.xls'
        return response
    
    return jsonify({"error": "Formato não suportado para relatório de auditoria"}), 400

def _exportar_manutencao(formato):
    """Export específico para relatório de manutenção"""
    from flask import make_response
    
    query = Equipamento.query
    if current_user.role != 'ADMIN' and current_user.setor:
        query = query.filter_by(setor_category=current_user.setor)
    
    # Equipamentos quebrados que precisam de manutenção
    quebrados = query.filter_by(emprestimo='QUEBRADO').all()
    # Equipamentos antigos (mais de 3 anos) que podem precisar de manutenção preventiva
    data_limite = datetime.now().date() - timedelta(days=1095)  # 3 anos
    antigos = query.filter(Equipamento.data_aquisicao < data_limite).all()
    
    if formato == "excel":
        html = '''<html><head><meta charset="utf-8"></head><body>
        <h2>Relatório de Manutenção</h2>
        <p>Gerado em: ''' + datetime.now().strftime("%d/%m/%Y %H:%M") + '''</p>
        
        <h3>Equipamentos Quebrados (Manutenção Corretiva)</h3>
        <table border="1">
        <tr><th>ID</th><th>Nome</th><th>Categoria</th><th>Marca</th><th>Setor</th><th>Data Cadastro</th><th>Prioridade</th></tr>'''
        
        for eq in quebrados:
            dias_quebrado = (datetime.now().date() - eq.data_cadastro.date()).days if eq.data_cadastro else 0
            prioridade = "ALTA" if dias_quebrado > 7 else "MÉDIA" if dias_quebrado > 3 else "NORMAL"
            
            html += f'''<tr>
                <td>{eq.id}</td>
                <td>{eq.name_response or ''}</td>
                <td>{eq.equipamento_category or ''}</td>
                <td>{eq.marca_category or ''}</td>
                <td>{eq.setor_category or 'N/A'}</td>
                <td>{eq.data_cadastro.strftime('%d/%m/%Y') if eq.data_cadastro else 'N/A'}</td>
                <td>{prioridade}</td>
            </tr>'''
        
        html += '''</table>
        
        <h3>Equipamentos para Manutenção Preventiva (Mais de 3 anos)</h3>
        <table border="1">
        <tr><th>ID</th><th>Nome</th><th>Categoria</th><th>Marca</th><th>Setor</th><th>Data Aquisição</th><th>Idade (anos)</th><th>Status</th></tr>'''
        
        for eq in antigos:
            if eq.data_aquisicao:
                idade = (datetime.now().date() - eq.data_aquisicao).days / 365
                html += f'''<tr>
                    <td>{eq.id}</td>
                    <td>{eq.name_response or ''}</td>
                    <td>{eq.equipamento_category or ''}</td>
                    <td>{eq.marca_category or ''}</td>
                    <td>{eq.setor_category or 'N/A'}</td>
                    <td>{eq.data_aquisicao.strftime('%d/%m/%Y')}</td>
                    <td>{idade:.1f}</td>
                    <td>{'Em Uso' if eq.emprestimo == 'EM_USO' else 'Quebrado' if eq.emprestimo == 'QUEBRADO' else 'Disponível'}</td>
                </tr>'''
        
        html += f'''</table>
        <p><strong>Resumo:</strong></p>
        <ul>
            <li>Equipamentos quebrados: {len(quebrados)}</li>
            <li>Equipamentos para manutenção preventiva: {len(antigos)}</li>
            <li>Total que requer atenção: {len(quebrados) + len(antigos)}</li>
        </ul>
        </body></html>'''
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        response.headers['Content-Disposition'] = 'attachment; filename=relatorio_manutencao.xls'
        return response
    
    return jsonify({"error": "Formato não suportado para relatório de manutenção"}), 400

def _exportar_emprestimos(formato):
    """Export específico para relatório de empréstimos"""
    from flask import make_response
    
    query = Equipamento.query.filter_by(emprestimo="EM_USO")
    if current_user.role != 'ADMIN' and current_user.setor:
        query = query.filter_by(setor_category=current_user.setor)
    
    equipamentos = query.all()
    
    if formato == "excel":
        html = '''<html><head><meta charset="utf-8"></head><body>
        <h2>Relatório de Empréstimos</h2>
        <p>Gerado em: ''' + datetime.now().strftime("%d/%m/%Y %H:%M") + '''</p>
        <table border="1">
        <tr><th>ID</th><th>Nome</th><th>Categoria</th><th>Marca</th><th>Setor</th><th>Cargo</th><th>Compartilhado</th><th>AnyDesk</th><th>Observações</th></tr>'''
        
        for eq in equipamentos:
            html += f'''<tr>
                <td>{eq.id}</td>
                <td>{eq.name_response or ''}</td>
                <td>{eq.equipamento_category or ''}</td>
                <td>{eq.marca_category or ''}</td>
                <td>{eq.setor_category or 'N/A'}</td>
                <td>{eq.cargo_category or 'N/A'}</td>
                <td>{'Sim' if eq.equipamento_compartilhado == 'SIM' else 'Não'}</td>
                <td>{eq.numero_anydesk or 'N/A'}</td>
                <td>{eq.observacoes[:50] if eq.observacoes else 'N/A'}...</td>
            </tr>'''
        
        html += f'''</table>
        <p><strong>Total de equipamentos em uso: {len(equipamentos)}</strong></p>
        </body></html>'''
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        response.headers['Content-Disposition'] = 'attachment; filename=relatorio_emprestimos.xls'
        return response
    
    return jsonify({"error": "Formato não suportado para relatório de empréstimos"}), 400

def _exportar_localizacao(formato, setor):
    """Export específico para relatório de localização"""
    from flask import make_response
    
    if current_user.role != 'ADMIN' and current_user.setor and setor != current_user.setor:
        return jsonify({"error": "Acesso negado ao setor solicitado"}), 403
    
    equipamentos = Equipamento.query.filter_by(setor_category=setor).all()
    
    if formato == "excel":
        html = f'''<html><head><meta charset="utf-8"></head><body>
        <h2>Relatório de Localização - Setor {setor}</h2>
        <p>Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        <table border="1">
        <tr><th>ID</th><th>Nome</th><th>Categoria</th><th>Marca</th><th>Status</th><th>Cargo</th><th>Compartilhado</th><th>AnyDesk</th></tr>'''
        
        for eq in equipamentos:
            status = 'Em Uso' if eq.emprestimo == 'EM_USO' else 'Quebrado' if eq.emprestimo == 'QUEBRADO' else 'Disponível'
            html += f'''<tr>
                <td>{eq.id}</td>
                <td>{eq.name_response or ''}</td>
                <td>{eq.equipamento_category or ''}</td>
                <td>{eq.marca_category or ''}</td>
                <td>{status}</td>
                <td>{eq.cargo_category or 'N/A'}</td>
                <td>{'Sim' if eq.equipamento_compartilhado == 'SIM' else 'Não'}</td>
                <td>{eq.numero_anydesk or 'N/A'}</td>
            </tr>'''
        
        html += f'''</table>
        <p><strong>Total de equipamentos no setor {setor}: {len(equipamentos)}</strong></p>
        </body></html>'''
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        response.headers['Content-Disposition'] = f'attachment; filename=relatorio_localizacao_{setor}.xls'
        return response
    
    return jsonify({"error": "Formato não suportado para relatório de localização"}), 400

def _exportar_inventario(formato):
    """Export padrão para inventário geral"""
    from flask import make_response
    
    query = Equipamento.query
    if current_user.role != 'ADMIN' and current_user.setor:
        query = query.filter_by(setor_category=current_user.setor)
    
    equipamentos = query.all()
    
    if formato == "excel":
        html = '''<html><head><meta charset="utf-8"></head><body>
        <h2>Inventário Geral</h2>
        <p>Gerado em: ''' + datetime.now().strftime("%d/%m/%Y %H:%M") + '''</p>
        <table border="1">
        <tr><th>ID</th><th>Nome</th><th>Categoria</th><th>Marca</th><th>Status</th><th>Setor</th></tr>'''
        
        for eq in equipamentos:
            status = 'Em Uso' if eq.emprestimo == 'EM_USO' else 'Quebrado' if eq.emprestimo == 'QUEBRADO' else 'Disponível'
            html += f'''<tr>
                <td>{eq.id}</td>
                <td>{eq.name_response or ''}</td>
                <td>{eq.equipamento_category or ''}</td>
                <td>{eq.marca_category or ''}</td>
                <td>{status}</td>
                <td>{eq.setor_category or 'N/A'}</td>
            </tr>'''
        
        html += '</table></body></html>'
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        response.headers['Content-Disposition'] = 'attachment; filename=relatorio_inventario.xls'
        return response
    
    return jsonify({"error": "Formato não suportado para inventário"}), 400
