from flask import Blueprint, render_template, jsonify, request
from . import db
from .models import Equipamento, Administrador
from flask_login import login_required, current_user
from sqlalchemy import func, case
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")

CATEGORIAS = ['NOTEBOOK', 'DESKTOP', 'ACCESS POINT', 'ROTEADOR', 'IMPRESSORA', 
              'TABLET', 'TV', 'PROJETOR', 'CELULAR', 'CAIXA DE SOM', 'PERIFERICOS']
SETORES = ['CJ', 'CCA', 'CEI', 'ADMINISTRATIVO', 'RH', 'TI', 'COMUNICACAO', 
           'SOCIAL', 'FINANCEIRO', 'BAZAR', 'ARRASTART', 'ENFERMARIA', 'COZINHA', 'MANUTENCAO', 'ADMINISTRADOR']
CARGOS = ['GERENTE', 'COORDENADOR', 'ASSISTENTE', 'AUXILIAR', 'ANALISTA', 
          'EDUCADOR', 'DIRETORIA', 'ENFERMEIRA', 'RH']

@dashboard_bp.route("/")
@login_required
def index():
    try:
        # Base query para equipamentos
        base_query = Equipamento.query
        
        # Aplicar filtro por setor se usuário não for ADMIN
        if current_user.role != 'ADMIN' and current_user.setor:
            base_query = base_query.filter_by(setor_category=current_user.setor)
        
        # KPIs básicos
        kpis = {
            "total": 0,
            "disponiveis": 0,
            "em_uso": 0,
            "manutencao": 0,
            "usuarios_total": Administrador.query.count(),
            "usuarios_ativos": Administrador.query.filter_by(status='ATIVO').count(),
            "categorias_counts": {}
        }
        
        equipamentos = []
        
        # Apenas administradores podem ver dados de equipamentos
        if current_user.role == 'ADMIN':
            # Tentar obter dados dos equipamentos
            try:
                kpis["total"] = base_query.count()
                kpis["disponiveis"] = base_query.filter_by(emprestimo='DISPONIVEL').count()
                kpis["em_uso"] = base_query.filter_by(emprestimo='EM_USO').count()
                kpis["quebrados"] = base_query.filter_by(emprestimo='QUEBRADO').count()
                equipamentos = base_query.limit(10).all()
            except:
                equipamentos = []
        
        return render_template(
            "dashboard/index.html", 
            kpis=kpis, 
            equipamentos=equipamentos,
            categorias=CATEGORIAS,
            setores=SETORES,
            cargos=CARGOS,
            user=current_user
        )
    except Exception as e:
        logger.error(f"Erro no dashboard: {str(e)}", exc_info=True)
        return render_template(
            "dashboard/index.html", 
            kpis={"total": 0, "disponiveis": 0, "em_uso": 0, "manutencao": 0, "usuarios_total": 0, "usuarios_ativos": 0, "categorias_counts": {}},
            equipamentos=[],
            categorias=CATEGORIAS,
            setores=SETORES,
            cargos=CARGOS,
            user=current_user
        )

@dashboard_bp.route("/api/equipamentos/<int:id>")
@login_required
def get_equipamento_api(id):
    """API endpoint para obter dados de um equipamento específico"""
    # Verificar se o usuário tem permissão para acessar equipamentos
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado. Apenas administradores podem acessar equipamentos.'}), 403
    try:
        equipamento = Equipamento.query.get_or_404(id)
        
        return jsonify({
            'id': equipamento.id,
            'name_response': equipamento.name_response,
            'marca_category': equipamento.marca_category,
            'serial_number': equipamento.serial_number or '',
            'equipamento_category': equipamento.equipamento_category,
            'setor_category': equipamento.setor_category,
            'cargo_category': equipamento.cargo_category,
            'emprestimo': equipamento.emprestimo,
            'data_aquisicao': equipamento.data_aquisicao.isoformat() if equipamento.data_aquisicao else None,
            'valor_aquisicao': float(equipamento.valor_aquisicao) if equipamento.valor_aquisicao else 0,
            'observacoes': equipamento.observacoes or ''
        })
    except Exception as e:
        logger.error(f"Erro ao buscar equipamento {id}: {str(e)}")
        return jsonify({'error': 'Equipamento não encontrado'}), 404

@dashboard_bp.route("/api/equipamentos/<int:id>/update", methods=['POST'])
@login_required
def update_equipamento_api(id):
    """API endpoint para atualizar um equipamento"""
    # Verificar se o usuário tem permissão para acessar equipamentos
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado. Apenas administradores podem acessar equipamentos.'}), 403
    try:
        equipamento = Equipamento.query.get_or_404(id)
        data = request.get_json()
        
        # Atualizar campos
        if 'name_response' in data:
            equipamento.name_response = data['name_response']
        if 'marca_category' in data:
            equipamento.marca_category = data['marca_category']
        if 'serial_number' in data:
            equipamento.serial_number = data['serial_number']
        if 'equipamento_category' in data:
            equipamento.equipamento_category = data['equipamento_category']
        if 'setor_category' in data:
            equipamento.setor_category = data['setor_category']
        if 'cargo_category' in data:
            equipamento.cargo_category = data['cargo_category']
        if 'emprestimo' in data:
            equipamento.emprestimo = data['emprestimo']
        if 'valor_aquisicao' in data:
            equipamento.valor_aquisicao = data['valor_aquisicao']
        if 'observacoes' in data:
            equipamento.observacoes = data['observacoes']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Equipamento atualizado com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar equipamento {id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar equipamento'
        }), 500

@dashboard_bp.route("/api/search")
@login_required
def search_equipamentos():
    """API para busca em tempo real"""
    # Verificar se o usuário tem permissão para acessar equipamentos
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado. Apenas administradores podem acessar equipamentos.'}), 403
    try:
        query = request.args.get('q', '').strip()
        categoria = request.args.get('categoria', '')
        status = request.args.get('status', '')
        
        equipamentos_query = Equipamento.query
        
        # Aplicar filtro por setor se usuário não for ADMIN
        if current_user.role != 'ADMIN' and current_user.setor:
            equipamentos_query = equipamentos_query.filter_by(setor_category=current_user.setor)
        
        if query:
            search_term = f'%{query}%'
            equipamentos_query = equipamentos_query.filter(
                db.or_(
                    Equipamento.name_response.ilike(search_term),
                    Equipamento.marca_category.ilike(search_term),
                    Equipamento.equipamento_category.ilike(search_term)
                )
            )
        
        if categoria:
            equipamentos_query = equipamentos_query.filter(Equipamento.equipamento_category == categoria)
        
        if status:
            equipamentos_query = equipamentos_query.filter(Equipamento.emprestimo == status)
        
        equipamentos = equipamentos_query.limit(20).all()
        
        return jsonify({
            'success': True,
            'equipamentos': [{
                'id': eq.id,
                'name_response': eq.name_response,
                'marca_category': eq.marca_category,
                'equipamento_category': eq.equipamento_category,
                'setor_category': eq.setor_category or '-',
                'cargo_category': eq.cargo_category or '-',
                'emprestimo': eq.emprestimo
            } for eq in equipamentos]
        })
    except Exception as e:
        logger.error(f"Erro na busca: {str(e)}")
        return jsonify({'success': False, 'error': 'Erro na busca'}), 500

@dashboard_bp.route("/api/analytics")
@login_required
def get_analytics():
    """API para dados de gráficos"""
    try:
        # Verificar se há equipamentos no banco
        total_equipamentos = Equipamento.query.count()
        
        # Se não há equipamentos, retornar dados vazios
        if total_equipamentos == 0:
            response = jsonify({
                'success': True,
                'categorias': [],
                'status': [],
                'setores': []
            })
            # Headers para evitar cache
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        
        # Base query para equipamentos
        base_query = Equipamento.query
        
        # Aplicar filtro por setor se usuário não for ADMIN
        if current_user.role != 'ADMIN' and current_user.setor:
            base_query = base_query.filter_by(setor_category=current_user.setor)
        
        # Equipamentos por categoria
        categorias = db.session.query(
            Equipamento.equipamento_category,
            func.count(Equipamento.id).label('total')
        )
        if current_user.role != 'ADMIN' and current_user.setor:
            categorias = categorias.filter_by(setor_category=current_user.setor)
        categorias = categorias.group_by(Equipamento.equipamento_category).all()
        
        # Status dos equipamentos
        status_data = db.session.query(
            Equipamento.emprestimo,
            func.count(Equipamento.id).label('total')
        )
        if current_user.role != 'ADMIN' and current_user.setor:
            status_data = status_data.filter_by(setor_category=current_user.setor)
        status_data = status_data.group_by(Equipamento.emprestimo).all()
        
        # Equipamentos por setor (apenas para ADMIN)
        setores = []
        if current_user.role == 'ADMIN':
            setores = db.session.query(
                Equipamento.setor_category,
                func.count(Equipamento.id).label('total')
            ).filter(Equipamento.setor_category.isnot(None)).group_by(Equipamento.setor_category).all()
        
        response = jsonify({
            'success': True,
            'categorias': [{'name': cat[0], 'value': cat[1]} for cat in categorias],
            'status': [{
                'name': 'Disponível' if st[0] == 'DISPONIVEL' else 'Em Uso' if st[0] == 'EM_USO' else 'Quebrado',
                'value': st[1]
            } for st in status_data],
            'setores': [{'name': set[0], 'value': set[1]} for set in setores[:5]]
        })
        
        # Headers para evitar cache
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"Erro ao obter analytics: {str(e)}")
        return jsonify({'success': False, 'error': 'Erro ao carregar dados'}), 500