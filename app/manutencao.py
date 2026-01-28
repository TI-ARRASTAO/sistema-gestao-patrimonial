"""
SISTEMA DE MANUTENÇÃO PREVENTIVA
Funcionalidade avançada para gestão de manutenção de equipamentos
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import db
from .models import Equipamento, Manutencao, Administrador
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
import logging

logger = logging.getLogger(__name__)

manutencao_bp = Blueprint('manutencao', __name__, url_prefix='/manutencao')

class ManutencaoService:
    """Serviço para gestão de manutenção preventiva"""

    @staticmethod
    def calcular_proxima_manutencao(equipamento):
        """Calcula a próxima data de manutenção baseada em regras"""
        if not equipamento.data_aquisicao:
            return None

        # Regras básicas de manutenção preventiva
        regras_manutencao = {
            'COMPUTADOR': 180,  # 6 meses
            'NOTEBOOK': 180,
            'IMPRESSORA': 90,   # 3 meses
            'PROJETOR': 120,    # 4 meses
            'TELEFONE': 365,    # 1 ano
            'MONITOR': 365,
            'SERVIDOR': 90,     # 3 meses
        }

        categoria = equipamento.equipamento_category.upper()
        dias_manutencao = regras_manutencao.get(categoria, 365)  # Default 1 ano

        # Verificar última manutenção
        ultima_manutencao = Manutencao.query.filter_by(
            equipamento_id=equipamento.id
        ).order_by(Manutencao.data_manutencao.desc()).first()

        if ultima_manutencao:
            proxima_data = ultima_manutencao.data_manutencao + timedelta(days=dias_manutencao)
        else:
            proxima_data = equipamento.data_aquisicao + timedelta(days=dias_manutencao)

        return proxima_data

    @staticmethod
    def verificar_manutencoes_vencidas():
        """Verifica equipamentos com manutenção vencida"""
        hoje = datetime.now().date()

        equipamentos = Equipamento.query.all()
        vencidos = []

        for equip in equipamentos:
            proxima_data = ManutencaoService.calcular_proxima_manutencao(equip)
            if proxima_data and proxima_data <= hoje:
                dias_atraso = (hoje - proxima_data).days
                vencidos.append({
                    'equipamento': equip,
                    'proxima_manutencao': proxima_data,
                    'dias_atraso': dias_atraso
                })

        return vencidos

    @staticmethod
    def verificar_manutencoes_proximas(dias=30):
        """Verifica equipamentos com manutenção próxima"""
        hoje = datetime.now().date()
        data_limite = hoje + timedelta(days=dias)

        equipamentos = Equipamento.query.all()
        proximas = []

        for equip in equipamentos:
            proxima_data = ManutencaoService.calcular_proxima_manutencao(equip)
            if proxima_data and hoje <= proxima_data <= data_limite:
                dias_restantes = (proxima_data - hoje).days
                proximas.append({
                    'equipamento': equip,
                    'proxima_manutencao': proxima_data,
                    'dias_restantes': dias_restantes
                })

        return proximas

@manutencao_bp.route('/')
@login_required
def index():
    """Página principal de manutenção"""
    # Verificar permissões
    if current_user.role not in ['ADMIN', 'GERENTE']:
        flash('Acesso negado. Permissões insuficientes.', 'error')
        return redirect(url_for('dashboard.index'))

    # Estatísticas de manutenção
    total_equipamentos = Equipamento.query.count()
    total_manutencoes = Manutencao.query.count()

    # Manutenções vencidas
    manutencoes_vencidas = ManutencaoService.verificar_manutencoes_vencidas()

    # Manutenções próximas (30 dias)
    manutencoes_proximas = ManutencaoService.verificar_manutencoes_proximas(30)

    # Manutenções por mês (últimos 6 meses)
    seis_meses_atras = datetime.now() - timedelta(days=180)
    manutencoes_por_mes = db.session.query(
        func.strftime('%Y-%m', Manutencao.data_manutencao).label('mes'),
        func.count(Manutencao.id).label('total')
    ).filter(Manutencao.data_manutencao >= seis_meses_atras)\
     .group_by(func.strftime('%Y-%m', Manutencao.data_manutencao))\
     .order_by(func.strftime('%Y-%m', Manutencao.data_manutencao))\
     .all()

    return render_template('manutencao/index.html',
                         total_equipamentos=total_equipamentos,
                         total_manutencoes=total_manutencoes,
                         manutencoes_vencidas=manutencoes_vencidas,
                         manutencoes_proximas=manutencoes_proximas,
                         manutencoes_por_mes=manutencoes_por_mes)

@manutencao_bp.route('/agendar/<int:equipamento_id>', methods=['GET', 'POST'])
@login_required
def agendar_manutencao(equipamento_id):
    """Agendar nova manutenção"""
    if current_user.role not in ['ADMIN', 'GERENTE']:
        flash('Acesso negado. Permissões insuficientes.', 'error')
        return redirect(url_for('manutencao.index'))

    equipamento = Equipamento.query.get_or_404(equipamento_id)

    if request.method == 'POST':
        try:
            # Criar nova manutenção
            data_str = request.form.get('data_manutencao')
            if not data_str:
                raise ValueError("Data de manutenção é obrigatória")

            nova_manutencao = Manutencao(
                equipamento_id=equipamento.id,
                tipo_manutencao=request.form.get('tipo_manutencao'),
                descricao=request.form.get('descricao'),
                data_manutencao=datetime.strptime(data_str, '%Y-%m-%d'),
                custo_estimado=float(request.form.get('custo_estimado') or 0),
                responsavel=request.form.get('responsavel'),
                status='AGENDADA',
                observacoes=request.form.get('observacoes'),
                created_by=current_user.id
            )

            db.session.add(nova_manutencao)
            db.session.commit()

            flash('Manutenção agendada com sucesso!', 'success')
            logger.info(f'Manutenção agendada para equipamento {equipamento.id} por {current_user.name_user}')

            return redirect(url_for('manutencao.equipamento', equipamento_id=equipamento.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao agendar manutenção: {str(e)}', 'error')
            logger.error(f'Erro ao agendar manutenção: {str(e)}')

    return render_template('manutencao/agendar.html', equipamento=equipamento)

@manutencao_bp.route('/equipamento/<int:equipamento_id>')
@login_required
def equipamento(equipamento_id):
    """Histórico de manutenção de um equipamento"""
    equipamento = Equipamento.query.get_or_404(equipamento_id)

    # Verificar permissões
    if current_user.role not in ['ADMIN', 'GERENTE'] and equipamento.setor_category != current_user.setor:
        flash('Acesso negado. Você só pode ver equipamentos do seu setor.', 'error')
        return redirect(url_for('manutencao.index'))

    # Histórico de manutenções
    manutencoes = Manutencao.query.filter_by(equipamento_id=equipamento_id)\
                                  .order_by(Manutencao.data_manutencao.desc())\
                                  .all()

    # Próxima manutenção
    proxima_manutencao = ManutencaoService.calcular_proxima_manutencao(equipamento)

    # Status da manutenção
    status_manutencao = 'EM_DIA'
    if proxima_manutencao:
        hoje = datetime.now().date()
        if proxima_manutencao < hoje:
            status_manutencao = 'VENCIDA'
        elif (proxima_manutencao - hoje).days <= 30:
            status_manutencao = 'PROXIMA'

    return render_template('manutencao/equipamento.html',
                         equipamento=equipamento,
                         manutencoes=manutencoes,
                         proxima_manutencao=proxima_manutencao,
                         status_manutencao=status_manutencao)

@manutencao_bp.route('/registrar/<int:manutencao_id>', methods=['POST'])
@login_required
def registrar_manutencao(manutencao_id):
    """Registrar conclusão de manutenção"""
    if current_user.role not in ['ADMIN', 'GERENTE']:
        return jsonify({'success': False, 'message': 'Acesso negado'})

    manutencao = Manutencao.query.get_or_404(manutencao_id)

    try:
        # Atualizar manutenção
        manutencao.status = 'CONCLUIDA'
        manutencao.custo_real = float(request.form.get('custo_real') or 0)
        manutencao.observacoes = (manutencao.observacoes or "") + f"\n\nCONCLUSÃO: {request.form.get('observacoes_conclusao', '')}"
        manutencao.data_conclusao = datetime.now()

        db.session.commit()

        flash('Manutenção registrada como concluída!', 'success')
        logger.info(f'Manutenção {manutencao.id} concluída por {current_user.name_user}')

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao registrar manutenção: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@manutencao_bp.route('/api/calendario')
@login_required
def calendario_api():
    """API para dados do calendário de manutenções"""
    # Manutenções agendadas
    manutencoes_agendadas = Manutencao.query.filter(
        and_(
            Manutencao.status.in_(['AGENDADA', 'EM_ANDAMENTO']),
            Manutencao.data_manutencao >= datetime.now().date()
        )
    ).all()

    eventos = []
    for manutencao in manutencoes_agendadas:
        equipamento = Equipamento.query.get(manutencao.equipamento_id)
        eventos.append({
            'id': manutencao.id,
            'title': f'{manutencao.tipo_manutencao} - {equipamento.name_response}',
            'start': manutencao.data_manutencao.isoformat(),
            'backgroundColor': '#f59e0b' if manutencao.status == 'AGENDADA' else '#3b82f6',
            'extendedProps': {
                'equipamento': equipamento.name_response,
                'tipo': manutencao.tipo_manutencao,
                'status': manutencao.status
            }
        })

    return jsonify(eventos)

@manutencao_bp.route('/relatorio')
@login_required
def relatorio():
    """Relatório de manutenções"""
    if current_user.role not in ['ADMIN', 'GERENTE']:
        flash('Acesso negado. Permissões insuficientes.', 'error')
        return redirect(url_for('manutencao.index'))

    # Filtros
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    tipo_manutencao = request.args.get('tipo_manutencao')
    status = request.args.get('status')

    query = Manutencao.query.join(Equipamento)

    if data_inicio:
        query = query.filter(Manutencao.data_manutencao >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        query = query.filter(Manutencao.data_manutencao <= datetime.strptime(data_fim, '%Y-%m-%d'))
    if tipo_manutencao:
        query = query.filter(Manutencao.tipo_manutencao == tipo_manutencao)
    if status:
        query = query.filter(Manutencao.status == status)

    manutencoes = query.order_by(Manutencao.data_manutencao.desc()).all()

    # Estatísticas
    total_manutencoes = len(manutencoes)
    custo_total = sum(m.custo_real or m.custo_estimado or 0 for m in manutencoes)
    manutencoes_concluidas = len([m for m in manutencoes if m.status == 'CONCLUIDA'])

    return render_template('manutencao/relatorio.html',
                         manutencoes=manutencoes,
                         total_manutencoes=total_manutencoes,
                         custo_total=custo_total,
                         manutencoes_concluidas=manutencoes_concluidas,
                         filtros=request.args)