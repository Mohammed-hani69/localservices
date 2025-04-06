from app import app, db
from models import User, ROLE_ADMIN
from werkzeug.security import generate_password_hash

def create_admin_user():
    # Check if admin account already exists
    admin = User.query.filter_by(email='admin@gmail.com').first()
    if admin:
        print('Admin account already exists.')
        return
    
    # Create admin account
    admin_user = User(
        username='admin',
        email='admin@gmail.com',
        role=ROLE_ADMIN,
        is_active=True,
        phone='0000000000',
        address='Admin Address'
    )
    admin_user.password_hash = generate_password_hash('12345678')
    
    # Add to database
    db.session.add(admin_user)
    db.session.commit()
    print('Admin account created successfully!')
    print('Email: admin@gmail.com')
    print('Password: 12345678')

# Run the function with app context
with app.app_context():
    create_admin_user()