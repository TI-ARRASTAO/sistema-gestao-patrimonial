# Sistema de Gestão Patrimonial

Sistema completo para gerenciamento de patrimônio institucional desenvolvido em Flask.

## Funcionalidades

- **Dashboard** - Visão geral com KPIs e estatísticas
- **Equipamentos** - Cadastro, edição e controle de equipamentos
- **Usuários** - Gerenciamento de usuários e permissões
- **Relatórios** - Geração de relatórios e análises
- **Empréstimos** - Sistema completo de empréstimo/devolução
- **Notificações** - Alertas automáticos para empréstimos atrasados e pendentes
- **Auditoria** - Logs completos de todas as operações
- **Modo Escuro** - Interface adaptável
- **Responsivo** - Funciona em desktop e mobile

## Instalação e Configuração

### 1. Atualizar Banco de Dados MySQL

**Opção A: Automática (Recomendado)**
```bash
# Configure o .env com suas credenciais MySQL
# Depois execute:
python update_database.py
```

**Opção B: Manual**
```sql
-- Execute o arquivo database_update.sql no seu MySQL
mysql -u root -p patrimonio_db < database_update.sql
```

### 2. Instalar e Executar Sistema

```bash
# 1. Instalar dependências
python install.py

# 2. Configurar .env com suas credenciais MySQL
# DB_USER=root
# DB_PASS=sua_senha
# DB_HOST=localhost
# DB_NAME=patrimonio_db

# 3. Executar sistema
python run.py
```

### Credenciais Padrão
- **Usuário:** admin
- **Senha:** admin123
- **URL:** http://localhost:5000

## Estrutura do Projeto

```
app/
├── templates/
│   ├── dashboard/
│   │   ├── index.html          # Dashboard principal
│   │   ├── equipamentos.html   # Lista de equipamentos
│   │   ├── create.html         # Cadastro de equipamentos
│   │   ├── usuarios.html       # Gerenciamento de usuários
│   │   ├── relatorios.html     # Relatórios e análises
│   │   ├── emprestimos.html    # Gestão de empréstimos
│   │   ├── notificacoes.html   # Sistema de notificações
│   │   └── ...
│   ├── login.html              # Página de login
│   └── register.html           # Página de registro
├── static/
│   └── css/
│       └── style.css
├── __init__.py                 # Configuração da aplicação
├── models.py                   # Modelos do banco de dados
├── auth.py                     # Autenticação
├── dashboard.py                # Rotas do dashboard
├── equipamentos.py             # Rotas de equipamentos
├── usuarios.py                 # Rotas de usuários
├── relatorios.py               # Rotas de relatórios
├── emprestimos.py              # Rotas de empréstimos
├── notificacoes.py             # Sistema de notificações
├── scheduler.py                # Scheduler de tarefas automáticas
├── main.py                     # Rotas principais
├── migrate_db.py               # Script de migração
└── ...

## Uso

1. **Primeiro Acesso**: Registre um administrador em `/admin/register`
2. **Login**: Acesse `/admin/login` com suas credenciais
3. **Dashboard**: Visualize estatísticas em `/dashboard/`
4. **Equipamentos**: Gerencie equipamentos em `/equipamentos/`
5. **Usuários**: Controle usuários em `/usuarios/`
6. **Relatórios**: Gere relatórios em `/relatorios/`

## Recursos Técnicos

- **Backend**: Flask + SQLAlchemy
- **Frontend**: HTML5 + TailwindCSS + JavaScript
- **Banco**: SQLite (configurável)
- **Autenticação**: Flask-Login
- **Responsivo**: Design mobile-first
- **Modo Escuro**: Suporte completo

## Modelos de Dados

### Administrador (Usuários)
- ID, nome, email, username, senha
- Perfil (ADMIN, GERENTE, USUARIO, VISUALIZADOR)
- Setor, cargo, status
- Controle de acesso e auditoria

### Empréstimo
- Controle completo de empréstimos e devoluções
- Datas de empréstimo e devolução prevista/real
- Status: ATIVO, DEVOLVIDO, ATRASADO
- Observações e responsável pelo empréstimo

### Notificação
- Sistema de alertas automáticos
- Tipos: INFO, WARNING, ERROR, SUCCESS
- Controle de leitura e expiração
- Relacionamento com empréstimos e equipamentos

## Sistema de Notificações

O sistema possui um **sistema avançado de notificações** que alerta automaticamente sobre:

### Tipos de Notificação
- **🔴 Empréstimos Atrasados** - Alertas quando empréstimos ultrapassam a data prevista
- **🟡 Empréstimos Vencem Hoje** - Lembretes para devoluções do dia
- **🔵 Empréstimos Vencem Amanhã** - Antecipação de devoluções pendentes
- **✅ Confirmações de Sucesso** - Feedback de operações concluídas

### Funcionalidades
- **Notificações em Tempo Real** - Atualização automática a cada hora
- **Contador no Menu** - Badge vermelho mostra quantidade de notificações não lidas
- **Categorização por Tipo** - Cores e ícones para diferentes tipos de alerta
- **Marcação como Lida** - Controle individual ou marcar todas de uma vez
- **Expiração Automática** - Notificações antigas são removidas automaticamente
- **Interface Responsiva** - Funciona perfeitamente em mobile e desktop

### Como Usar
1. **Acesse o Menu** - Clique em "Notificações" na barra lateral
2. **Visualize Alertas** - Veja todas as notificações organizadas por data
3. **Marque como Lida** - Clique no botão para confirmar leitura
4. **Ações Rápidas** - "Marcar Todas como Lidas" para limpar rapidamente

### Benefícios
- **Redução de Perdas** - Evita empréstimos esquecidos
- **Melhor Controle** - Antecipação de problemas
- **Aumento da Produtividade** - Lembretes automáticos
- **Transparência** - Todos ficam informados sobre o status dos equipamentos