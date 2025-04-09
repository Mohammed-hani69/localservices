from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from forms import ServiceForm
import os

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/local_services.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إنشاء قاعدة البيانات
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# إعداد مدير تسجيل الدخول
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# تعريف أنواع الخدمات حسب الفئة
SERVICE_TYPES = {
    'صيانة': [
        ('كهرباء', 'كهرباء'),
        ('سباكة', 'سباكة'),
        ('تكييف', 'تكييف'),
        ('أجهزة', 'أجهزة'),
        ('حاسوب', 'حاسوب')
    ],
    'تنظيف': [
        ('منزلي', 'منزلي'),
        ('مكتبي', 'مكتبي'),
        ('سجاد', 'سجاد'),
        ('واجهات', 'واجهات'),
        ('سيارات', 'سيارات')
    ],
    'تعليم': [
        ('لغات', 'لغات'),
        ('رياضيات', 'رياضيات'),
        ('علوم', 'علوم'),
        ('حاسوب', 'حاسوب'),
        ('موسيقى', 'موسيقى')
    ],
    'صحة': [
        ('استشارات', 'استشارات'),
        ('علاج طبيعي', 'علاج طبيعي'),
        ('تغذية', 'تغذية'),
        ('لياقة', 'لياقة'),
        ('تمريض', 'تمريض')
    ],
    'طعام': [
        ('وجبات', 'وجبات'),
        ('حلويات', 'حلويات'),
        ('مشروبات', 'مشروبات'),
        ('طعام صحي', 'طعام صحي'),
        ('مناسبات', 'مناسبات')
    ],
    'أخرى': [
        ('أخرى', 'أخرى')
    ]
}

@app.route('/get_service_types/<category>')
def get_service_types(category):
    """الحصول على أنواع الخدمة بناءً على الفئة"""
    return jsonify(SERVICE_TYPES.get(category, []))

@app.route('/fix_service_form')
def fix_service_form():
    """إصلاح نموذج إضافة الخدمة"""
    form = ServiceForm()
    
    # تحديث اختيارات نوع الخدمة
    if form.category.data:
        form.service_type.choices = SERVICE_TYPES.get(form.category.data, [])
    else:
        form.service_type.choices = [('', 'اختر التصنيف أولاً')]
    
    return render_template('service_form.html', form=form, title='إضافة خدمة جديدة')

if __name__ == '__main__':
    app.run(debug=True)
