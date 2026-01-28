#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de inicialização para produção (Render)
"""

import os
from app import create_app

# Criar aplicação
app = create_app()

# Configurar para produção
if os.environ.get('RENDER'):
    # Forçar SQLite para evitar problemas com PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key-change-me')
    
    # Criar tabelas se não existirem
    with app.app_context():
        from app import db
        try:
            print("Configurando banco SQLite...")
            db.create_all()
            print("Tabelas criadas com sucesso!")
            
            # Criar usuário admin padrão se não existir
            from app.models import Administrador
            from werkzeug.security import generate_password_hash
            
            admin = Administrador.query.filter_by(user_name='admin').first()
            if not admin:
                admin = Administrador(
                    user_name='admin',
                    user_password=generate_password_hash('admin123'),
                    name_user='Administrador',
                    email='admin@sistema.com',
                    role='ADMIN',
                    status='ATIVO'
                )
                db.session.add(admin)
                db.session.commit()
                print("Usuário admin criado: admin/admin123")
            else:
                print("Usuário admin já existe.")
                
        except Exception as e:
            print(f"Erro ao configurar banco: {e}")
            raise e

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)