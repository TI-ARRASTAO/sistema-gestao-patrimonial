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
    # Usar PostgreSQL se DATABASE_URL estiver disponível, senão SQLite
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Corrigir URL do PostgreSQL se necessário
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key')
    
    # Criar tabelas se não existirem
    with app.app_context():
        from app import db
        try:
            # Testar conexão
            db.engine.connect()
            print("Conexão com banco estabelecida!")
            
            # Criar tabelas
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
                print("Usuário admin criado!")
            else:
                print("Usuário admin já existe.")
                
        except Exception as e:
            print(f"Erro ao configurar banco: {e}")
            # Em caso de erro, usar SQLite como fallback
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
            try:
                db.create_all()
                print("Fallback para SQLite realizado.")
            except Exception as e2:
                print(f"Erro crítico: {e2}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)