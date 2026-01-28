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
    # Configurações específicas do Render
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/patrimonio.db')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key')
    
    # Criar tabelas se não existirem
    with app.app_context():
        from app import db
        try:
            db.create_all()
            print("Tabelas criadas com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)