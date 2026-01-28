# -*- coding: utf-8 -*-
"""
Script para migrar o banco de dados existente para a nova estrutura
Execute este script após atualizar os modelos
"""

import logging
from . import create_app, db
from .models import Administrador, Equipamento

logger = logging.getLogger(__name__)

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            logger.info("Tabelas criadas com sucesso")
            print("Tabelas criadas!")
            
            # Verificar se já existe um administrador
            admin_exists = Administrador.query.first()
            if not admin_exists:
                # Criar usuário administrador padrão
                from werkzeug.security import generate_password_hash
                from sqlalchemy.exc import SQLAlchemyError
                
                admin = Administrador(
                    user_name="admin",
                    user_password=generate_password_hash("admin123"),
                    name_user="Administrador",
                    email="admin@sistema.com"
                )
                
                try:
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("Usuário administrador criado com sucesso")
                    print("Usuario administrador criado!")
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Erro ao criar administrador: {str(e)}", exc_info=True)
                    return False
            else:
                logger.info("Usuário administrador já existe")
                print("Usuario administrador ja existe.")
            
            logger.info("Banco SQLite configurado com sucesso")
            print("Banco SQLite configurado com sucesso!")
            return True
            
        except ImportError as e:
            logger.error(f"Erro de importacao: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Erro na configuracao: {str(e)}", exc_info=True)
            db.session.rollback()
            return False

if __name__ == "__main__":
    migrate_database()