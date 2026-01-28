import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object("app.config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"

    from .auth import auth_bp
    from .equipamentos import equipamentos_bp
    from .dashboard import dashboard_bp
    from .usuarios import usuarios_bp
    from .relatorios import relatorios_bp
    from .main import main_bp
    from .exports import exports_bp
    from .notificacoes import notificacoes_bp
    from .backup import backup_bp
    from .manutencao import manutencao_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/admin")
    app.register_blueprint(equipamentos_bp, url_prefix="/equipamentos")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(relatorios_bp, url_prefix="/relatorios")
    
    # Desabilitar CSRF para rotas de relatórios
    csrf.exempt(relatorios_bp)
    app.register_blueprint(exports_bp, url_prefix="/exports")
    app.register_blueprint(notificacoes_bp, url_prefix="/notificacoes")
    app.register_blueprint(backup_bp, url_prefix="/backup")
    app.register_blueprint(manutencao_bp)

    @app.after_request
    def apply_security_headers(response):
        from .security import add_security_headers
        return add_security_headers(response)

    with app.app_context():
        # Verificar se as tabelas já existem antes de criar
        # Isso evita overhead desnecessário em cada inicialização
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            db.create_all()

    return app
