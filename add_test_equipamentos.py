#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para adicionar equipamentos de teste
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Equipamento, Administrador

def add_test_equipamentos():
    """Adiciona equipamentos de teste"""
    app = create_app()
    
    with app.app_context():
        print("=== ADICIONANDO EQUIPAMENTOS DE TESTE ===")
        print()
        
        # Verificar se já existem equipamentos
        existing = Equipamento.query.count()
        if existing > 0:
            print(f"Ja existem {existing} equipamentos no banco.")
            return
        
        # Buscar usuário admin para usar como created_by
        admin = Administrador.query.filter_by(user_name='admin').first()
        if not admin:
            print("ERRO: Usuario admin nao encontrado!")
            return
        
        # Equipamentos de teste
        equipamentos_teste = [
            {
                'name_response': 'Notebook Dell Inspiron 01',
                'equipamento_category': 'NOTEBOOK',
                'marca_category': 'Dell',
                'setor_category': 'TI',
                'cargo_category': 'ANALISTA',
                'emprestimo': 'DISPONIVEL',
                'equipamento_compartilhado': 'NAO'
            },
            {
                'name_response': 'Desktop HP Compaq 01',
                'equipamento_category': 'DESKTOP',
                'marca_category': 'HP',
                'setor_category': 'ADMINISTRATIVO',
                'cargo_category': 'ASSISTENTE',
                'emprestimo': 'EM_USO',
                'equipamento_compartilhado': 'NAO'
            },
            {
                'name_response': 'Impressora Canon Pixma',
                'equipamento_category': 'IMPRESSORA',
                'marca_category': 'Canon',
                'setor_category': 'FINANCEIRO',
                'cargo_category': 'GERENTE',
                'emprestimo': 'QUEBRADO',
                'equipamento_compartilhado': 'SIM'
            },
            {
                'name_response': 'Tablet Samsung Galaxy Tab',
                'equipamento_category': 'TABLET',
                'marca_category': 'Samsung',
                'setor_category': 'CJ',
                'cargo_category': 'EDUCADOR',
                'emprestimo': 'DISPONIVEL',
                'equipamento_compartilhado': 'SIM'
            },
            {
                'name_response': 'Projetor Epson PowerLite',
                'equipamento_category': 'PROJETOR',
                'marca_category': 'Epson',
                'setor_category': 'CCA',
                'cargo_category': 'COORDENADOR',
                'emprestimo': 'EM_USO',
                'equipamento_compartilhado': 'SIM'
            }
        ]
        
        try:
            for eq_data in equipamentos_teste:
                eq = Equipamento(
                    name_response=eq_data['name_response'],
                    equipamento_category=eq_data['equipamento_category'],
                    marca_category=eq_data['marca_category'],
                    setor_category=eq_data['setor_category'],
                    cargo_category=eq_data['cargo_category'],
                    emprestimo=eq_data['emprestimo'],
                    equipamento_compartilhado=eq_data['equipamento_compartilhado'],
                    created_by=admin.id,
                    updated_by=admin.id
                )
                db.session.add(eq)
                print(f"Adicionado: {eq_data['name_response']}")
            
            db.session.commit()
            print(f"\\nSUCESSO: {len(equipamentos_teste)} equipamentos de teste adicionados!")
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO ao adicionar equipamentos: {e}")

if __name__ == "__main__":
    add_test_equipamentos()