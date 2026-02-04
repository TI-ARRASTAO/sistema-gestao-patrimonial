#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a página de equipamentos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Administrador, Equipamento

def test_equipamentos_page():
    """Testa se a página de equipamentos está funcionando"""
    app = create_app()
    
    with app.app_context():
        print("=== TESTE DA PAGINA DE EQUIPAMENTOS ===")
        print()
        
        # Verificar se há usuário admin
        admin = Administrador.query.filter_by(user_name='admin').first()
        if not admin:
            print("ERRO: Usuario admin nao encontrado!")
            return False
        
        print(f"OK: Usuario admin encontrado: {admin.name_user}")
        
        # Verificar se há equipamentos
        equipamentos = Equipamento.query.all()
        print(f"OK: Total de equipamentos: {len(equipamentos)}")
        
        # Testar rota de equipamentos
        with app.test_client() as client:
            # Fazer login
            login_response = client.post('/admin/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            if login_response.status_code == 200:
                print("OK: Login realizado com sucesso")
                
                # Testar página de equipamentos
                equipamentos_response = client.get('/equipamentos/')
                
                if equipamentos_response.status_code == 200:
                    print("OK: Pagina de equipamentos carregou com sucesso")
                    print(f"OK: Tamanho da resposta: {len(equipamentos_response.data)} bytes")
                    
                    # Verificar se contém elementos esperados
                    content = equipamentos_response.data.decode('utf-8')
                    if 'Equipamentos' in content:
                        print("OK: Titulo 'Equipamentos' encontrado")
                    if 'table' in content.lower():
                        print("OK: Tabela encontrada no HTML")
                    if 'Novo' in content:
                        print("OK: Botao 'Novo' encontrado")
                    
                    return True
                else:
                    print(f"ERRO: Pagina de equipamentos retornou status {equipamentos_response.status_code}")
                    print(f"Resposta: {equipamentos_response.data.decode('utf-8')[:500]}...")
                    return False
            else:
                print(f"ERRO: Login falhou com status {login_response.status_code}")
                return False

if __name__ == "__main__":
    success = test_equipamentos_page()
    if success:
        print("\nSUCESSO: Pagina de equipamentos esta funcionando!")
    else:
        print("\nFALHA: Ha problemas na pagina de equipamentos!")