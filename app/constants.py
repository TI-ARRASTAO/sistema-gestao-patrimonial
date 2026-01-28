# -*- coding: utf-8 -*-
"""
Constantes do sistema
"""

# Configurações de paginação
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Status de equipamentos
STATUS_EMPRESTADO = "SIM"
STATUS_DISPONIVEL = "NAO"

# Mensagens de erro
MSG_ERRO_GENERICO = "Erro interno do servidor"
MSG_DADOS_INVALIDOS = "Dados inválidos"
MSG_CAMPOS_OBRIGATORIOS = "Preencha todos os campos obrigatórios"
MSG_EMAIL_INVALIDO = "Formato de email inválido"
MSG_EMAIL_DUPLICADO = "Email já cadastrado"
MSG_USUARIO_EXISTE = "Usuário já existe"
MSG_LOGIN_INVALIDO = "Usuário ou senha inválidos"
MSG_ACESSO_NEGADO = "Acesso negado"

# Mensagens de sucesso
MSG_SUCESSO_CRIAR = "Criado com sucesso"
MSG_SUCESSO_ATUALIZAR = "Atualizado com sucesso"
MSG_SUCESSO_REMOVER = "Removido com sucesso"

# Configurações de senha
MIN_PASSWORD_LENGTH = 8
DEFAULT_PASSWORD_LENGTH = 12

# Regex patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Formatos de arquivo permitidos
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
