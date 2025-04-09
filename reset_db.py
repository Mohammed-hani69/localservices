import os
import shutil
from app import app, db
from models import User, ROLE_ADMIN
from werkzeug.security import generate_password_hash

def reset_database():
    with app.app_context():
        # Remove existing database
        if os.path.exists('local_services.db'):
            os.remove('local_services.db')
            print("Removed existing database.")

        # Remove migrations folder
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if os.path.exists(migrations_dir):
            shutil.rmtree(migrations_dir)
            print("Removed migrations folder.")

        # Create new tables
        db.create_all()
        print("Created new database tables.")

        # Create admin user
        admin = User(
            username='admin',
            email='admin@gmail.com',
            role=ROLE_ADMIN,
            is_active=True,
            phone='0000000000',
            address='Admin Address'
        )
        admin.password_hash = generate_password_hash('12345678')
        db.session.add(admin)
        db.session.commit()
        
        print("Database reset completed successfully!")

if __name__ == "__main__":
    reset_database()
