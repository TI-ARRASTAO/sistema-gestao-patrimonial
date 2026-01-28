#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar o sistema de gestão patrimonial
"""

import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Tentar importar o script de atualização de schema se existir
try:
    from app import create_app
    from app.migrate_db import migrate_database
except ImportError as e:
    print(f"Erro de importacao: {e}")
    print("Execute primeiro: python install.py")
    sys.exit(1)

try:
    from update_equipamentos_schema import update_equipamentos_table
except ImportError:
    update_equipamentos_table = None

def setup_database():
    """Configura o banco de dados se necessário"""
    print("Configurando banco SQLite...")
    try:
        result = migrate_database()
        if result:
            print("Banco SQLite pronto!")
            return True
        else:
            print("Falha na configuracao do banco.")
            return False
    except ImportError as e:
        logger.error(f"Erro de importacao: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro ao configurar banco: {e}", exc_info=True)
        return False
app = create_app()

if __name__ == "__main__":
    try:
        # Executar migrações e verificações iniciais
        # A verificação WERKZEUG_RUN_MAIN garante que rode apenas no processo principal do reloader
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            print("Sistema de Gestao Patrimonial")
            print("========================================")
            
            # Configurar banco se necessário
            setup_database()
            
            # Iniciar scheduler do sistema (notificações + backups)
            from app.scheduler import SystemScheduler
            scheduler = SystemScheduler(app)
            scheduler.start()
            
            # 2. Atualização de schema (adicionar colunas novas se faltarem)
            if update_equipamentos_table:
                print("Verificando schema de equipamentos...")
                update_equipamentos_table()
            
            print("\nSistema iniciado com sucesso!")
            print("Acesse: http://localhost:5000")
            print("Login padrao: admin / admin123")
            print("Pressione Ctrl+C para parar\n")
            
        app.run(host="0.0.0.0", port=5000, debug=True)
        
    except KeyboardInterrupt:
        logger.info("Servidor encerrado pelo usuario.")
        # Parar scheduler antes de sair
        if 'scheduler' in locals():
            scheduler.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicacao: {e}", exc_info=True)
        # Parar scheduler em caso de erro
        if 'scheduler' in locals():
            scheduler.stop()
        sys.exit(1)