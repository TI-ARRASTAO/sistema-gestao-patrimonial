from flask import request, jsonify, g
from functools import wraps
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# Rate limiting simples em memória (use Redis em produção)
rate_limit_storage = defaultdict(deque)

def rate_limit(max_requests=100, window=3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if client_ip and ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            client_ip = client_ip or '0.0.0.0'
            current_time = time.time()
            
            # Limpar requests antigos
            requests = rate_limit_storage[client_ip]
            while requests and requests[0] < current_time - window:
                requests.popleft()
            
            # Verificar limite
            if len(requests) >= max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Adicionar request atual
            requests.append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(data, required_fields=None, max_lengths=None):
    """Validar dados de entrada"""
    if required_fields:
        for field in required_fields:
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                return False, f"Campo '{field}' é obrigatório"
    
    if max_lengths:
        for field, max_len in max_lengths.items():
            if data.get(field) and len(str(data.get(field))) > max_len:
                return False, f"Campo '{field}' excede o tamanho máximo de {max_len} caracteres"
    
    return True, None

def validate_password_strength(password):
    """Valida força da senha"""
    if not password or len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Senha deve conter maiúsculas, minúsculas e números"
    
    return True, None

def add_security_headers(response):
    """Adicionar headers de segurança"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    try:
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    except (RuntimeError, AttributeError) as e:
        logger.debug(f"Could not set HSTS header: {e}")
    
    return response