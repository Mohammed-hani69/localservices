from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

# User roles
ROLE_USER = 0
ROLE_SERVICE_PROVIDER = 1
ROLE_ADMIN = 2

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    role = db.Column(db.Integer, default=ROLE_USER)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships
    provider_profile = db.relationship('ServiceProvider', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='client', lazy='dynamic')
    payments = db.relationship('Payment', backref='client', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def is_provider(self):
        return self.role == ROLE_SERVICE_PROVIDER

class ServiceProvider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    logo = db.Column(db.String(200))
    website = db.Column(db.String(200))
    specialization = db.Column(db.String(50), default='أخرى')
    verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships
    services = db.relationship('Service', backref='provider', lazy='dynamic')
    meals = db.relationship('Meal', backref='provider', lazy='dynamic')
    table_reservations = db.relationship('TableReservation', backref='provider', lazy='dynamic')

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('service_provider.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer)  # Duration in minutes
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(200))  # لتخزين مسار الصورة
    service_type = db.Column(db.String(50))  # نوع الخدمة المحدد (مثل نوع التنظيف، نوع الصيانة، إلخ)
    additional_info = db.Column(db.Text)  # معلومات إضافية حسب نوع الخدمة
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships
    bookings = db.relationship('Booking', backref='service', lazy='dynamic')

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships
    payment = db.relationship('Payment', foreign_keys='Payment.booking_id', backref='booking', uselist=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)  # تغيير إلى nullable=True
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='SAR')
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships
    service = db.relationship('Service', backref=db.backref('reviews', lazy='dynamic'))
    user = db.relationship('User')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), default='info')  # info, success, warning, danger
    related_id = db.Column(db.Integer, nullable=True)  # ID of related object (booking, payment, etc.)
    related_type = db.Column(db.String(20), nullable=True)  # Type of related object (booking, payment, etc.)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    action_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='actions')
    booking = db.relationship('Booking', backref='actions')
    payment = db.relationship('Payment', backref='actions')

# نموذج الوجبات لمقدمي خدمات الطعام
class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('service_provider.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    meal_type = db.Column(db.String(50))  # فطور، غداء، عشاء، حلويات، مشروبات، وجبات سريعة، أخرى
    preparation_time = db.Column(db.Integer)  # وقت التحضير بالدقائق
    calories = db.Column(db.Integer, nullable=True)  # السعرات الحرارية
    is_vegetarian = db.Column(db.Boolean, default=False)  # وجبة نباتية
    is_vegan = db.Column(db.Boolean, default=False)  # وجبة نباتية صرفة
    is_gluten_free = db.Column(db.Boolean, default=False)  # خالية من الغلوتين
    image = db.Column(db.String(200))  # مسار صورة الوجبة
    is_available = db.Column(db.Boolean, default=True)  # متاحة أم لا
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    orders = db.relationship('MealOrder', backref='meal', lazy='dynamic')

# نموذج طلبات الوجبات
class MealOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    special_instructions = db.Column(db.Text)  # تعليمات خاصة للوجبة
    status = db.Column(db.String(20), default='pending')  # pending, preparing, ready, delivered, cancelled
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_address = db.Column(db.String(200), nullable=True)  # عنوان التوصيل إن وجد
    is_delivery = db.Column(db.Boolean, default=False)  # هل الطلب للتوصيل
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='meal_orders')

# نموذج حجز الطاولات في المطعم
class TableReservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('service_provider.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, nullable=False)  # تاريخ ووقت الحجز
    guests_number = db.Column(db.Integer, nullable=False)  # عدد الضيوف
    special_requests = db.Column(db.Text)  # طلبات خاصة
    contact_phone = db.Column(db.String(20), nullable=False)  # رقم الهاتف للتواصل
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='table_reservations')
