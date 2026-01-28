from app import create_app, db
from app.models import Administrador
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    db.create_all()
    
    admin = Administrador.query.filter_by(user_name='admin').first()
    if not admin:
        admin = Administrador(
            user_name='admin',
            user_password=generate_password_hash('admin123'),
            name_user='Administrador',
            email='admin@sistema.com',
            role='ADMIN'
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin criado: admin/admin123')
    else:
        if admin.role != 'ADMIN':
            admin.role = 'ADMIN'
            db.session.commit()
            print('Admin existente atualizado para role ADMIN')
        print('Admin já existe')
