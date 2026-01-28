# -*- coding: utf-8 -*-
"""
Validadores reutilizáveis
"""

import re
from .constants import EMAIL_PATTERN, MIN_PASSWORD_LENGTH


def validate_email(email):
    """
    Valida formato de email
    
    Args:
        email (str): Email a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not email or not isinstance(email, str):
        return False
    
    stripped = email.strip()
    is_valid = bool(re.match(EMAIL_PATTERN, stripped))
    
    # Log para debug
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Validating email: '{email}' -> stripped: '{stripped}' -> valid: {is_valid}")
    
    return is_valid


def validate_password(password):
    """
    Valida senha
    
    Args:
        password (str): Senha a ser validada
        
    Returns:
        tuple: (bool, str) - (válido, mensagem de erro)
    """
    if not password:
        return False, "Senha é obrigatória"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"
    
    return True, None


def validate_required_fields(data, fields):
    """
    Valida campos obrigatórios
    
    Args:
        data (dict): Dados a serem validados
        fields (list): Lista de campos obrigatórios
        
    Returns:
        tuple: (bool, str) - (válido, campo faltante)
    """
    for field in fields:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            return False, field
    
    return True, None


def sanitize_string(value, max_length=1000):
    """
    Sanitiza string removendo espaços e limitando tamanho
    
    Args:
        value (str): String a ser sanitizada
        max_length (int): Tamanho máximo
        
    Returns:
        str: String sanitizada ou None
    """
    if not value:
        return None
    
    if isinstance(value, str):
        sanitized = value.strip()
        return sanitized[:max_length] if sanitized else None
    
    return None
