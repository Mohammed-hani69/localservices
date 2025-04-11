
import os
import shutil
from flask import Flask
from database import db
from models import User, ROLE_ADMIN
from werkzeug.security import generate_password_hash

def reset_database():
    # تهيئة تطبيق Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local_services.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # حذف قاعدة البيانات الحالية
        if os.path.exists('instance/local_services.db'):
            os.remove('instance/local_services.db')
            print("تم حذف قاعدة البيانات الحالية.")

        # إنشاء الجداول الجديدة
        db.create_all()
        print("تم إنشاء جداول قاعدة البيانات الجديدة.")

        # إنشاء مستخدم مدير
        admin = User(
            username='admin',
            email='admin@example.com',
            role=ROLE_ADMIN,
            is_active=True,
            phone='0000000000',
            address='عنوان المشرف'
        )
        admin.set_password('12345678')
        db.session.add(admin)
        db.session.commit()
        
        print("تم إعادة ضبط قاعدة البيانات بنجاح!")

if __name__ == "__main__":
    reset_database()
