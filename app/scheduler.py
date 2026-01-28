# -*- coding: utf-8 -*-
import time
import threading
from datetime import datetime, time as dt_time
import logging

logger = logging.getLogger(__name__)

class SystemScheduler:
    """Scheduler para executar tarefas automáticas do sistema (notificações e backups)"""

    def __init__(self, app):
        self.app = app
        self.running = False
        self.thread = None

    def start(self):
        """Inicia o scheduler em uma thread separada"""
        if self.running:
            logger.warning("Scheduler já está rodando")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Scheduler do sistema iniciado")

    def stop(self):
        """Para o scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler do sistema parado")

    def _run_scheduler(self):
        """Loop principal do scheduler"""
        while self.running:
            try:
                now = datetime.now()

                # Executar verificações de notificações a cada hora
                self._executar_verificacoes_notificacoes()

                # Executar backup automático diariamente às 2:00 AM
                if now.hour == 2 and now.minute == 0:
                    self._executar_backup_automatico()
                    # Aguardar alguns segundos para evitar múltiplas execuções no mesmo minuto
                    time.sleep(60)

                # Aguardar 1 minuto antes da próxima verificação
                time.sleep(60)

            except Exception as e:
                logger.error(f"Erro no scheduler do sistema: {str(e)}", exc_info=True)
                # Em caso de erro, aguardar 5 minutos antes de tentar novamente
                time.sleep(300)

    def _executar_verificacoes_notificacoes(self):
        """Executa as verificações de notificações"""
        try:
            with self.app.app_context():
                from .notificacoes import executar_verificacoes_notificacoes
                executar_verificacoes_notificacoes()
                logger.info("Verificações de notificações executadas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao executar verificações de notificações: {str(e)}", exc_info=True)

    def _executar_backup_automatico(self):
        """Executa backup automático diário"""
        try:
            with self.app.app_context():
                from .backup import create_backup_automatico
                create_backup_automatico()
                logger.info("Backup automático executado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao executar backup automático: {str(e)}", exc_info=True)

    def executar_backup_agora(self):
        """Executa backup imediatamente (para testes)"""
        try:
            with self.app.app_context():
                from .backup import create_backup_automatico
                create_backup_automatico()
                logger.info("Backup automático executado manualmente")
        except Exception as e:
            logger.error(f"Erro ao executar backup manual: {str(e)}", exc_info=True)

    def executar_notificacoes_agora(self):
        """Executa verificações de notificações imediatamente (para testes)"""
        try:
            with self.app.app_context():
                from .notificacoes import executar_verificacoes_notificacoes
                executar_verificacoes_notificacoes()
                logger.info("Verificações de notificações executadas manualmente")
        except Exception as e:
            logger.error(f"Erro ao executar verificações manuais: {str(e)}", exc_info=True)