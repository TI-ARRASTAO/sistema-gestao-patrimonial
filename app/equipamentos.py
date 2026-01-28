# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response
from . import db
from .models import Equipamento
from .audit import AuditManager
from flask_login import login_required, current_user
from sqlalchemy import or_, func, case
from sqlalchemy.exc import SQLAlchemyError
from io import BytesIO, StringIO
import csv
from datetime import datetime
from werkzeug.utils import secure_filename
import logging
import os

# Configurar logging
logger = logging.getLogger(__name__)

equipamentos_bp = Blueprint(
    "equipamentos",
    __name__,
    template_folder="templates"
)

# =====================================================
# LISTAGEM + BUSCA + FILTROS + PAGINAÇÃO + KPIs
# =====================================================
@equipamentos_bp.route("/", methods=["GET"])
@login_required
def list_equipamentos():
    try:
        logger.info(f"Usuário atual: {current_user.name_user if current_user.is_authenticated else 'Não autenticado'}")
        logger.info(f"Role do usuário: {current_user.role if current_user.is_authenticated else 'N/A'}")
        
        if not current_user.is_authenticated:
            logger.error("Usuário não autenticado")
            flash("Você precisa fazer login para acessar esta página.", "error")
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'ADMIN':
            logger.warning(f"Acesso negado para usuário {current_user.name_user} com role {current_user.role}")
            flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
            return redirect(url_for('dashboard.index'))
        
        logger.info(f"Carregando equipamentos para usuário: {current_user.name_user}")
        
        # Obter parâmetros de filtro
        search_query = request.args.get('q', '').strip()
        status_filter = request.args.get('status', '').strip()
        categoria_filter = request.args.get('categoria', '').strip()
        setor_filter = request.args.get('setor', '').strip()
        marca_filter = request.args.get('marca', '').strip()
        
        # Construir query base
        query = Equipamento.query
        
        # Aplicar filtros
        if search_query:
            query = query.filter(
                or_(
                    Equipamento.name_response.ilike(f'%{search_query}%'),
                    Equipamento.marca_category.ilike(f'%{search_query}%'),
                    Equipamento.equipamento_category.ilike(f'%{search_query}%')
                )
            )
        
        if status_filter:
            query = query.filter(Equipamento.emprestimo == status_filter)
        
        if categoria_filter:
            query = query.filter(Equipamento.equipamento_category == categoria_filter)
        
        if setor_filter:
            query = query.filter(Equipamento.setor_category == setor_filter)
        
        if marca_filter:
            query = query.filter(Equipamento.marca_category.ilike(f'%{marca_filter}%'))
        
        # Buscar equipamentos filtrados
        equipamentos_list = query.all()
        logger.info(f"Encontrados {len(equipamentos_list)} equipamentos após filtros")
        
        # Calcular KPIs (sempre com todos os equipamentos)
        all_equipamentos = Equipamento.query.all()
        total = len(all_equipamentos)
        em_uso = sum(1 for eq in all_equipamentos if eq.emprestimo == 'EM_USO')
        quebrados = sum(1 for eq in all_equipamentos if eq.emprestimo == 'QUEBRADO')
        kpis = {
            "total": total,
            "em_uso": em_uso,
            "quebrados": quebrados,
            "disponiveis": total - em_uso - quebrados
        }
        
        # Estrutura de dados para o template
        equipamentos_data = {
            'items': equipamentos_list,
            'pages': 1,
            'page': 1,
            'total': len(equipamentos_list),
            'has_prev': False,
            'has_next': False
        }
        
        # Converter para objeto simples
        class SimpleEquipamentos:
            def __init__(self, data):
                self.items = data['items']
                self.pages = data['pages']
                self.page = data['page']
                self.total = data['total']
                self.has_prev = data['has_prev']
                self.has_next = data['has_next']
        
        logger.info("Renderizando template equipamentos.html")
        return render_template(
            "dashboard/equipamentos.html",
            equipamentos=SimpleEquipamentos(equipamentos_data),
            kpis=kpis
        )
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO ao carregar equipamentos: {str(e)}", exc_info=True)
        flash("Erro interno do servidor ao carregar equipamentos", "error")
        return redirect(url_for('dashboard.index'))


# =====================================================
# PÁGINA DE CRIAÇÃO
# =====================================================
@equipamentos_bp.route("/create", methods=["GET"])
@login_required
def create_page():
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    return render_template("dashboard/create.html")

# =====================================================
# CRIAR EQUIPAMENTO
# =====================================================
@equipamentos_bp.route("/create", methods=["POST"])
@login_required
def create_equipamento():
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    
    logger.info(f"Tentativa de criar equipamento por {current_user.name_user}")
    
    data = request.form if request.form else request.get_json()
    if not data:
        logger.error("Dados não recebidos")
        flash("Dados inválidos", "error")
        return redirect(url_for("equipamentos.list_equipamentos"))

    logger.info(f"Dados recebidos: {dict(data)}")

    try:
        nome = data.get("nome", "").strip()
        categoria = data.get("categoria", "").strip()
        marca = data.get("marca", "").strip()
        
        logger.info(f"Nome: {nome}, Categoria: {categoria}, Marca: {marca}")
        
        # Validar dados obrigatórios
        if not nome or not categoria:
            logger.error(f"Campos obrigatórios vazios - Nome: {nome}, Categoria: {categoria}")
            flash("Nome e categoria são obrigatórios", "error")
            return redirect(url_for("equipamentos.list_equipamentos"))
        
        # Verificar se já existe equipamento com esse nome
        existing = Equipamento.query.filter_by(name_response=nome).first()
        if existing:
            logger.error(f"Equipamento já existe: {nome}")
            flash(f"Já existe um equipamento com o nome '{nome}'", "error")
            return redirect(url_for("equipamentos.list_equipamentos"))
        
        eq = Equipamento(
            name_response=nome,
            setor_category=data.get("setor"),
            cargo_category=data.get("cargo"),
            equipamento_category=categoria,
            marca_category=marca or "Sem marca",
            equipamento_compartilhado=data.get("compartilhado", "NAO"),
            emprestimo=data.get("emprestimo", "DISPONIVEL"),
            numero_anydesk=data.get("anydesk", "").strip() or None,
            observacoes=data.get("observacoes", "").strip() or None,
            created_by=current_user.id,
            updated_by=current_user.id
        )

        logger.info(f"Criando equipamento: {eq.name_response}")
        db.session.add(eq)
        db.session.commit()
        
        # Registrar auditoria
        AuditManager.log_equipment_change('CREATE', eq)
        
        logger.info(f"Equipamento criado com sucesso - ID: {eq.id}")

        flash("Equipamento cadastrado com sucesso", "success")
        return redirect(url_for("equipamentos.list_equipamentos"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao cadastrar equipamento: {str(e)}", exc_info=True)
        flash("Erro interno do servidor", "error")
        return redirect(url_for("equipamentos.list_equipamentos"))


# =====================================================
# EDITAR EQUIPAMENTO
# =====================================================
@equipamentos_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
def edit_equipamento_form(id):
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    eq = Equipamento.query.get_or_404(id)
    return render_template(
        "dashboard/edit_equipamento.html",
        equipamento=eq
    )

@equipamentos_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
def edit_equipamento(id):
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    eq = Equipamento.query.get_or_404(id)
    
    try:
        form = request.form
        novo_nome = form.get("nome")
        
        if novo_nome != eq.name_response:
            if Equipamento.query.filter_by(name_response=novo_nome).first():
                flash(f"Já existe um equipamento com o nome '{novo_nome}'", "error")
                return redirect(url_for("equipamentos.edit_equipamento_form", id=id))

        # Capturar dados antigos para auditoria
        old_data = {
            'name': eq.name_response,
            'category': eq.equipamento_category,
            'brand': eq.marca_category,
            'sector': eq.setor_category,
            'status': eq.emprestimo,
            'shared': eq.equipamento_compartilhado
        }
        
        eq.name_response = novo_nome
        eq.setor_category = form.get("setor")
        eq.cargo_category = form.get("cargo")
        eq.equipamento_category = form.get("categoria")
        eq.marca_category = form.get("marca")
        eq.equipamento_compartilhado = form.get("compartilhado", "NAO")
        eq.emprestimo = form.get("emprestimo", "DISPONIVEL")
        eq.numero_anydesk = form.get("anydesk")
        eq.observacoes = form.get("observacoes")
        eq.updated_by = current_user.id

        db.session.commit()
        
        # Registrar auditoria
        AuditManager.log_equipment_change('UPDATE', eq, old_data)
        flash("Equipamento atualizado com sucesso", "success")
        return redirect(url_for("equipamentos.list_equipamentos"))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar equipamento {id}: {str(e)}", exc_info=True)
        flash("Erro interno do servidor", "error")
        return redirect(url_for("equipamentos.edit_equipamento_form", id=id))


# =====================================================
# VISUALIZAR E EDITAR EQUIPAMENTO (API para modais)
# =====================================================
@equipamentos_bp.route("/<int:id>/view", methods=["GET"])
@login_required
def view_equipamento(id):
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado'}), 403
    
    eq = Equipamento.query.get_or_404(id)
    return jsonify({
        'id': eq.id,
        'name_response': eq.name_response,
        'equipamento_category': eq.equipamento_category,
        'marca_category': eq.marca_category,
        'setor_category': eq.setor_category or 'N/A',
        'cargo_category': eq.cargo_category or 'N/A',
        'emprestimo': eq.emprestimo,
        'equipamento_compartilhado': eq.equipamento_compartilhado,
        'numero_anydesk': eq.numero_anydesk or 'N/A',
        'observacoes': eq.observacoes or 'Nenhuma observação',
        'data_cadastro': eq.data_cadastro.strftime('%d/%m/%Y %H:%M') if eq.data_cadastro else 'N/A'
    })

@equipamentos_bp.route("/<int:id>/edit-data", methods=["GET"])
@login_required
def get_edit_data(id):
    if current_user.role != 'ADMIN':
        return jsonify({'error': 'Acesso negado'}), 403
    
    eq = Equipamento.query.get_or_404(id)
    return jsonify({
        'id': eq.id,
        'name_response': eq.name_response,
        'equipamento_category': eq.equipamento_category,
        'marca_category': eq.marca_category,
        'setor_category': eq.setor_category,
        'cargo_category': eq.cargo_category,
        'emprestimo': eq.emprestimo,
        'equipamento_compartilhado': eq.equipamento_compartilhado,
        'numero_anydesk': eq.numero_anydesk or '',
        'observacoes': eq.observacoes or ''
    })

@equipamentos_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_equipamento(id):
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    eq = Equipamento.query.get_or_404(id)

    try:
        db.session.delete(eq)
        db.session.commit()
        flash("Equipamento removido com sucesso", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao remover equipamento {id}: {str(e)}", exc_info=True)
        flash("Erro interno do servidor", "error")

    return redirect(url_for("equipamentos.list_equipamentos"))


# =====================================================
# EXPORT EQUIPAMENTOS
# =====================================================
@equipamentos_bp.route("/export/<format>")
@login_required
def export_equipamentos(format):
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    return export_data(format)

@equipamentos_bp.route("/export-data/<format>")
@login_required
def export_data(format):
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    if format == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['ID', 'Nome', 'Categoria', 'Marca', 'Setor', 'Cargo', 'Emprestimo', 'Compartilhado', 'AnyDesk', 'Observacoes'])
        
        for eq in Equipamento.query.yield_per(100):
            writer.writerow([
                eq.id, eq.name_response, eq.equipamento_category, eq.marca_category,
                eq.setor_category or '', eq.cargo_category or '', eq.emprestimo,
                eq.equipamento_compartilhado, eq.numero_anydesk or '', eq.observacoes or ''
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=equipamentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response
    
    flash("Formato não suportado", "error")
    return redirect(url_for("equipamentos.list_equipamentos"))


# =====================================================
# IMPORT EQUIPAMENTOS
# =====================================================
def _validate_import_file(request):
    """Valida o arquivo de importação"""
    if 'file' not in request.files:
        return None, "Nenhum arquivo selecionado"
    
    file = request.files['file']
    if not file or file.filename == '':
        return None, "Nenhum arquivo selecionado"
    
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        return None, "Selecione um arquivo CSV ou Excel válido"
    
    return file, None

def _process_csv_row(row, row_num):
    """Processa uma linha do CSV e retorna equipamento ou erro"""
    nome = row.get('Nome', '').strip()
    if not nome:
        return None, f"Linha {row_num}: Nome é obrigatório"
    
    eq = Equipamento(
        name_response=nome,
        equipamento_category=row.get('Categoria', 'NOTEBOOK'),
        marca_category=row.get('Marca', 'Sem marca'),
        setor_category=row.get('Setor') or None,
        cargo_category=row.get('Cargo') or None,
        emprestimo=row.get('Emprestimo', 'NAO'),
        equipamento_compartilhado=row.get('Compartilhado', 'NAO'),
        numero_anydesk=row.get('AnyDesk') or None,
        observacoes=row.get('Observacoes') or None,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    return eq, None

@equipamentos_bp.route("/import", methods=["POST"])
@login_required
def import_equipamentos():
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    file, error = _validate_import_file(request)
    if error:
        flash(error, "error")
        return redirect(url_for("equipamentos.list_equipamentos"))
    
    try:
        imported_count = 0
        errors = []
        batch_size = 100
        
        # Processar arquivo baseado na extensão
        if file.filename.lower().endswith('.csv'):
            # Processar CSV
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            reader = csv.DictReader(stream)
            rows = list(reader)
        else:
            # Processar Excel
            try:
                import pandas as pd
                df = pd.read_excel(file.stream, engine='openpyxl')
                rows = df.to_dict('records')
            except ImportError:
                flash("Biblioteca pandas não instalada. Use arquivo CSV", "error")
                return redirect(url_for("equipamentos.list_equipamentos"))
            except Exception as e:
                flash(f"Erro ao ler arquivo Excel: {str(e)}", "error")
                return redirect(url_for("equipamentos.list_equipamentos"))
        
        for row_num, row in enumerate(rows, start=2):
            eq, error = _process_csv_row(row, row_num)
            if error:
                errors.append(error)
                continue
            
            try:
                db.session.add(eq)
                imported_count += 1
                
                if imported_count % batch_size == 0:
                    db.session.commit()
            except SQLAlchemyError as e:
                errors.append(f"Linha {row_num}: {str(e)}")
                db.session.rollback()
        
        if imported_count % batch_size != 0:
            db.session.commit()
        
        if imported_count > 0:
            flash(f"{imported_count} equipamentos importados com sucesso", "success")
        
        for error in errors[:5]:
            flash(error, "warning")
        
    except UnicodeDecodeError:
        flash("Erro ao ler arquivo: encoding inválido. Use UTF-8", "error")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao importar equipamentos: {str(e)}", exc_info=True)
        flash("Erro ao processar arquivo", "error")
    
    return redirect(url_for("equipamentos.list_equipamentos"))

@equipamentos_bp.route("/clear-all", methods=["POST"])
@login_required
def clear_all_equipamentos():
    """Apaga TODOS os dados do patrimônio - OPERAÇÃO PERIGOSA"""
    
    if current_user.role != 'ADMIN':
        flash("Acesso negado. Apenas administradores podem gerenciar equipamentos.", "error")
        return redirect(url_for('dashboard.index'))
    
    # Verificação de segurança - palavra de confirmação
    confirmation = request.form.get('confirmation', '').strip().upper()
    if confirmation != 'APAGAR TUDO':
        flash("Confirmação inválida. Digite exatamente: APAGAR TUDO", "error")
        return redirect(url_for("equipamentos.list_equipamentos"))
    
    try:
        # Importar todos os modelos necessários
        from .models import Equipamento, AuditLog, Emprestimo
        
        # Contar todos os dados antes de apagar
        equipamentos_count = Equipamento.query.count()
        emprestimos_count = Emprestimo.query.count()
        audit_count = AuditLog.query.count() if hasattr(db.Model, 'AuditLog') else 0
        
        total_records = equipamentos_count + emprestimos_count + audit_count
        
        if total_records == 0:
            flash("Não há dados para apagar", "warning")
            return redirect(url_for("equipamentos.list_equipamentos"))
        
        # Apagar TODOS os dados do patrimônio
        deleted_items = []
        
        # 1. Apagar logs de auditoria
        if audit_count > 0:
            AuditLog.query.delete()
            deleted_items.append(f"{audit_count} logs de auditoria")
        
        # 2. Apagar todos os empréstimos (antes dos equipamentos por causa das chaves estrangeiras)
        if emprestimos_count > 0:
            Emprestimo.query.delete()
            deleted_items.append(f"{emprestimos_count} empréstimos")
        
        # 3. Apagar todos os equipamentos
        if equipamentos_count > 0:
            Equipamento.query.delete()
            deleted_items.append(f"{equipamentos_count} equipamentos")
        
        # Resetar sequências de ID (SQLite)
        try:
            db.session.execute("DELETE FROM sqlite_sequence WHERE name='equipamentos'")
            db.session.execute("DELETE FROM sqlite_sequence WHERE name='emprestimos'")
            db.session.execute("DELETE FROM sqlite_sequence WHERE name='audit_logs'")
        except:
            pass  # Ignorar se não for SQLite
        
        db.session.commit()
        
        # Log da operação crítica
        logger.critical(f"🚨 OPERAÇÃO CRÍTICA: Usuário {current_user.name_user} (ID: {current_user.id}) ZEROU TODO O PATRIMÔNIO - Removidos: {', '.join(deleted_items)}")
        
        flash(f"PATRIMÔNIO ZERADO! Removidos: {', '.join(deleted_items)}", "success")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao zerar patrimônio: {str(e)}", exc_info=True)
        flash("Erro ao apagar dados", "error")
    
    return redirect(url_for("equipamentos.list_equipamentos"))
