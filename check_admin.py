from app import app, db
from models import User, ROLE_ADMIN
from werkzeug.security import generate_password_hash, check_password_hash

def check_admin_password():
    # Check admin account
    with app.app_context():
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            print('Admin account does not exist.')
            return
        
        # Check password
        if check_password_hash(admin.password_hash, '12345678'):
            print('Admin account exists with the correct password.')
        else:
            print('Admin account exists but password is incorrect.')
            print('Updating password...')
            admin.password_hash = generate_password_hash('12345678')
            db.session.commit()
            print('Password updated successfully!')
        
        print(f'Username: {admin.username}')
        print(f'Email: {admin.email}')
        print(f'Role: {admin.role} (ADMIN={ROLE_ADMIN})')

check_admin_password()