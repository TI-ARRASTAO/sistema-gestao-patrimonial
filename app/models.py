from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("administrador.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(db.Text, nullable=True)
    new_values = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Administrador(UserMixin, db.Model):
    __tablename__ = "administrador"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    name_user = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    status = db.Column(db.Enum('ATIVO', 'INATIVO'), default='ATIVO')
    role = db.Column(db.Enum('ADMIN', 'GERENTE', 'USUARIO', 'VISUALIZADOR'), default='USUARIO')
    setor = db.Column(db.String(50))
    cargo = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)

    def get_id(self):
        return str(self.id) if self.id is not None else None
    
    @property
    def is_active(self):
        return self.status == 'ATIVO'
    
    def has_permission(self, action):
        permissions = {
            'ADMIN': ['create', 'read', 'update', 'delete', 'manage_users'],
            'GERENTE': ['create', 'read', 'update', 'delete'],
            'USUARIO': ['create', 'read', 'update'],
            'VISUALIZADOR': ['read']
        }
        return action in permissions.get(self.role, [])
    
    def can_access_setor(self, setor):
        """Verifica se o usuário pode acessar um setor específico"""
        if self.role == 'ADMIN':
            return True
        return self.setor == setor if self.setor else False
    
    def get_accessible_setores(self):
        """Retorna lista de setores que o usuário pode acessar"""
        if self.role == 'ADMIN':
            return ['CJ', 'CCA', 'CEI', 'ADMINISTRATIVO', 'RH', 'TI', 'COMUNICACAO', 'SOCIAL', 'FINANCEIRO', 'BAZAR', 'ARRASTART', 'ENFERMARIA', 'COZINHA', 'MANUTENCAO', 'ADMINISTRADOR']
        elif self.setor:
            return [self.setor]  # Todos os outros perfis só veem seu próprio setor
        return []

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.user_password, password)

@login_manager.user_loader
def load_user(user_id):
    try:
        return Administrador.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


class Equipamento(db.Model):
    __tablename__ = "equipamentos"
    id = db.Column(db.Integer, primary_key=True)

    name_response = db.Column(db.String(100), unique=True, nullable=False)

    setor_category = db.Column(db.Enum(
        'CJ', 'CCA', 'CEI', 'ADMINISTRATIVO', 'RH', 'TI',
        'COMUNICACAO', 'SOCIAL', 'FINANCEIRO', 'BAZAR',
        'ARRASTART', 'ENFERMARIA', 'COZINHA', 'MANUTENCAO', 'ADMINISTRADOR'
    ), nullable=True)

    cargo_category = db.Column(db.Enum(
        'GERENTE', 'COORDENADOR', 'ASSISTENTE', 'AUXILIAR',
        'ANALISTA', 'EDUCADOR', 'DIRETORIA', 'ENFERMEIRA', 'RH'
    ), nullable=True)

    equipamento_category = db.Column(db.Enum(
        'NOTEBOOK', 'DESKTOP', 'ACCESS POINT', 'ROTEADOR',
        'IMPRESSORA', 'TABLET', 'TV', 'PROJETOR', 'CELULAR',
        'CAIXA DE SOM', 'PERIFERICOS'
    ), nullable=False)

    marca_category = db.Column(db.String(255), nullable=False)

    equipamento_compartilhado = db.Column(db.Enum('SIM','NAO'), default='NAO')
    emprestimo = db.Column(db.Enum('DISPONIVEL','EM_USO','QUEBRADO'), default='DISPONIVEL')

    serial_number = db.Column(db.String(100))
    data_aquisicao = db.Column(db.Date)
    valor_aquisicao = db.Column(db.Numeric(10, 2))

    numero_anydesk = db.Column(db.String(20))
    observacoes = db.Column(db.Text)

    # Campos adicionais
    data_cadastro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    created_by = db.Column(db.Integer, db.ForeignKey("administrador.id", ondelete="SET NULL"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("administrador.id", onupdate="CASCADE"), nullable=True)

class Emprestimo(db.Model):
    __tablename__ = "emprestimos"
    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey("equipamentos.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("administrador.id"), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey("administrador.id"), nullable=False)
    data_emprestimo = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    data_prevista_devolucao = db.Column(db.DateTime)
    data_devolucao = db.Column(db.DateTime)
    status = db.Column(db.Enum('ATIVO', 'DEVOLVIDO', 'ATRASADO'), default='ATIVO')
    observacoes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Notificacao(db.Model):
    __tablename__ = "notificacoes"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("administrador.id"), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.Enum('INFO', 'WARNING', 'ERROR', 'SUCCESS'), default='INFO')
    lida = db.Column(db.Boolean, default=False)
    relacionada_tabela = db.Column(db.String(50))  # 'emprestimos', 'equipamentos', etc.
    relacionada_id = db.Column(db.Integer)  # ID do registro relacionado
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)  # Data de expiração da notificação
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    usuario = db.relationship("Administrador", backref="notificacoes")

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'mensagem': self.mensagem,
            'tipo': self.tipo,
            'lida': self.lida,
            'relacionada_tabela': self.relacionada_tabela,
            'relacionada_id': self.relacionada_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class Backup(db.Model):
    __tablename__ = "backups"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    arquivo = db.Column(db.String(255), nullable=False)  # Caminho do arquivo
    tamanho = db.Column(db.Integer, nullable=False)  # Tamanho em bytes
    tipo = db.Column(db.Enum('MANUAL', 'AUTOMATICO'), default='MANUAL')
    status = db.Column(db.Enum('SUCESSO', 'FALHA', 'EXECUTANDO'), default='EXECUTANDO')
    criado_por = db.Column(db.Integer, db.ForeignKey("administrador.id"), nullable=True)
    erro_mensagem = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    concluido_at = db.Column(db.DateTime, nullable=True)

    # Relacionamento
    administrador = db.relationship("Administrador", backref="backups")

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'arquivo': self.arquivo,
            'tamanho': self.tamanho,
            'tipo': self.tipo,
            'status': self.status,
            'criado_por': self.criado_por,
            'erro_mensagem': self.erro_mensagem,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'concluido_at': self.concluido_at.isoformat() if self.concluido_at else None
        }

class Manutencao(db.Model):
    """Modelo para gestão de manutenção preventiva"""
    __tablename__ = "manutencao"

    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey("equipamentos.id"), nullable=False)

    # Tipo de manutenção
    tipo_manutencao = db.Column(db.Enum(
        'PREVENTIVA', 'CORRETIVA', 'PREDITIVA', 'CALIBRACAO',
        'LIMPEZA', 'ATUALIZACAO', 'SUBSTITUICAO', 'OUTROS'
    ), nullable=False)

    # Descrição e detalhes
    descricao = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)

    # Datas
    data_manutencao = db.Column(db.Date, nullable=False)
    data_conclusao = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Custos
    custo_estimado = db.Column(db.Numeric(10, 2), default=0)
    custo_real = db.Column(db.Numeric(10, 2))

    # Responsável e status
    responsavel = db.Column(db.String(100))
    status = db.Column(db.Enum(
        'AGENDADA', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA'
    ), default='AGENDADA')

    # Controle de criação/modificação
    created_by = db.Column(db.Integer, db.ForeignKey("administrador.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("administrador.id"))

    # Relacionamentos
    equipamento = db.relationship("Equipamento", backref="manutencoes")
    criador = db.relationship("Administrador", foreign_keys=[created_by], backref="manutencoes_criadas")
    atualizador = db.relationship("Administrador", foreign_keys=[updated_by], backref="manutencoes_atualizadas")

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'equipamento_id': self.equipamento_id,
            'equipamento_nome': self.equipamento.name_response if self.equipamento else None,
            'tipo_manutencao': self.tipo_manutencao,
            'descricao': self.descricao,
            'observacoes': self.observacoes,
            'data_manutencao': self.data_manutencao.isoformat() if self.data_manutencao else None,
            'data_conclusao': self.data_conclusao.isoformat() if self.data_conclusao else None,
            'custo_estimado': float(self.custo_estimado) if self.custo_estimado else 0,
            'custo_real': float(self.custo_real) if self.custo_real else 0,
            'responsavel': self.responsavel,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }

    def __repr__(self):
        return f'<Manutencao {self.id} - {self.tipo_manutencao} - {self.status}>'