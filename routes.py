
import logging
import os
import secrets
import uuid
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, abort, g, send_file
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from wtforms.validators import ValidationError
from app import app
from database import db
from export_db import export_database
from notifications import send_review_notification, check_completed_bookings, create_notification
from models import User, ServiceProvider, Service, Booking, Payment, Review, Notification, Meal, MealOrder, TableReservation, ROLE_USER, ROLE_SERVICE_PROVIDER, ROLE_ADMIN
from forms import LoginForm, RegistrationForm, ServiceProviderForm, ServiceForm, BookingForm, PaymentForm, ReviewForm, SearchForm, MealForm, TableReservationForm
from stripe_payment import create_checkout_session, verify_payment_session, get_payment_status, cancel_payment
from auth import require_role

# Set up date context for all requests
@app.before_request
def before_request():
    g.now = datetime.now()

    # اضافة عدد الإشعارات غير المقروءة للمستخدم
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        g.unread_notifications_count = unread_count
    else:
        g.unread_notifications_count = 0

# تحقق من حالة المستخدم قبل كل طلب
@app.before_request
def check_user_status():
    if current_user.is_authenticated:
        # استثناء صفحات تسجيل الخروج والصفحة الرئيسية
        if request.endpoint not in ['logout', 'index', 'static']:
            if not current_user.is_active:
                logout_user()
                flash('تم تعطيل حسابك. يرجى التواصل مع الإدارة.', 'danger')
                return redirect(url_for('index'))

# Make variables available to templates
@app.context_processor
def inject_now():
    return {
        'now': g.now,
        'unread_notifications_count': g.unread_notifications_count if hasattr(g, 'unread_notifications_count') else 0
    }

# Home page
@app.route('/')
@app.route('/index')
def index():
    # Check if the user is requesting from a mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent

    # Query services for display
    featured_services = Service.query.filter_by(is_active=True).order_by(Service.id.desc()).limit(6).all()
    recent_services = Service.query.filter_by(is_active=True).order_by(Service.created_at.desc()).limit(6).all()
    search_form = SearchForm()

    if is_mobile and request.args.get('view') != 'desktop':
        return render_template('mobile/index.html',
                              featured_services=featured_services,
                              recent_services=recent_services)

    return render_template('index.html', title='الصفحة الرئيسية', services=featured_services, search_form=search_form)

# About page
@app.route('/about')
def about():
    # Check if the user is requesting from a mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent

    if is_mobile and request.args.get('view') != 'desktop':
        return render_template('mobile/about.html', title='عن منصتنا')

    return render_template('about.html', title='عن منصتنا')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('بريد إلكتروني أو كلمة مرور غير صحيحة', 'danger')
            return redirect(url_for('login'))

        # التحقق من حالة المستخدم
        if not user.is_active:
            flash('تم تعطيل حسابك. يرجى التواصل مع الإدارة.', 'danger')
            return redirect(url_for('login'))

        # Move login_user here after all checks pass
        login_user(user, remember=form.remember_me.data)
        
        # Get next page or default to dashboard
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
            
        # Check if mobile device and redirect accordingly  
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
        if is_mobile:
            next_page = url_for('mobile_dashboard')
            
        return redirect(next_page)

    # Choose appropriate template for GET requests
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
    template = 'mobile/login.html' if is_mobile else 'login.html'
    
    return render_template(template, title='تسجيل الدخول', form=form)

# Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                    phone=form.phone.data, address=form.address.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # If registering as service provider, redirect to complete provider profile
        if form.role.data == ROLE_SERVICE_PROVIDER:
            login_user(user)
            flash('تم تسجيل حسابك بنجاح! الرجاء إكمال بيانات مقدم الخدمة.', 'success')
            return redirect(url_for('create_provider_profile'))

        flash('تم تسجيل حسابك بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('login'))

    # التحقق من نوع الجهاز
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or request.args.get('mobile')

    # اختيار القالب المناسب
    template = 'mobile/register.html' if is_mobile else 'register.html'
    return render_template(template, title='تسجيل حساب جديد', form=form)

# User Dashboard
@app.route('/dashboard')
@login_required
@require_role(ROLE_USER, ROLE_SERVICE_PROVIDER, ROLE_ADMIN)
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))

    # Check if mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or request.args.get('mobile')

    # Get provider profile if exists
    provider = None
    if current_user.is_provider():
        provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()

        if provider:
            services = Service.query.filter_by(provider_id=provider.id).all()
            bookings = []
            for service in services:
                service_bookings = Booking.query.filter_by(service_id=service.id).all()
                bookings.extend(service_bookings)

            active_services_count = sum(1 for s in services if s.is_active)
            pending_bookings_count = sum(1 for b in bookings if b.status == 'pending')

            # توجيه مقدم الخدمة إلى لوحة التحكم المخصصة حسب تخصصه
            if is_mobile:
                if provider.specialization == 'صحة':
                    return render_template('mobile/provider/dashboard_health.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'تعليم':
                    return render_template('mobile/provider/dashboard_education.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'صيانة':
                    return render_template('mobile/provider/dashboard_maintenance.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'تنظيف':
                    return render_template('mobile/provider/dashboard_cleaning.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'طعام':
                    return render_template('mobile/provider/dashboard_food.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count,
                                        meals=provider.meals.all(),
                                        table_reservations=provider.table_reservations.all())
                else:
                    return render_template('mobile/provider/dashboard.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
            else:
                if provider.specialization == 'صحة':
                    return render_template('provider/dashboard_health.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'تعليم':
                    return render_template('provider/dashboard_education.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'صيانة':
                    return render_template('provider/dashboard_maintenance.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'تنظيف':
                    return render_template('provider/dashboard_cleaning.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
                elif provider.specialization == 'طعام':
                    return render_template('provider/dashboard_food.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count,
                                        meals=provider.meals.all(),
                                        meal_orders=MealOrder.query.join(Meal).filter(Meal.provider_id == provider.id).all(),
                                        table_reservations=provider.table_reservations.all())
                else:
                    return render_template('provider/dashboard.html',
                                        provider=provider,
                                        services=services,
                                        bookings=bookings,
                                        active_services_count=active_services_count,
                                        pending_bookings_count=pending_bookings_count)
        else:
            return redirect(url_for('create_provider_profile'))

    # Regular user dashboard
    bookings = Booking.query.filter_by(client_id=current_user.id).order_by(Booking.created_at.desc()).all()
    reviews = Review.query.filter_by(user_id=current_user.id).all()

    return render_template('dashboard.html', 
                         bookings=bookings,
                         reviews=reviews)

# Create Service Provider Profile
@app.route('/provider/create', methods=['GET', 'POST'])
@login_required
def create_provider_profile():
    if not current_user.is_provider():
        flash('عذراً، هذه الصفحة مخصصة لمقدمي الخدمات فقط.', 'warning')
        return redirect(url_for('index'))

    # Check if provider profile already exists
    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if provider:
        return redirect(url_for('dashboard'))

    form = ServiceProviderForm()
    if form.validate_on_submit():
        provider = ServiceProvider(
            user_id=current_user.id,
            company_name=form.company_name.data,
            description=form.description.data,
            website=form.website.data,
            specialization=form.specialization.data
        )
        db.session.add(provider)
        db.session.commit()
        flash('تم إنشاء ملف مقدم الخدمة بنجاح!', 'success')
        return redirect(url_for('dashboard'))

    # التحقق من نوع الجهاز
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or request.args.get('mobile')

    # اختيار القالب المناسب
    template = 'mobile/provider/create.html' if is_mobile else 'profile.html'
    return render_template(template, title='إنشاء ملف مقدم الخدمة', form=form)

# Edit User Profile
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_user_profile():
    user = User.query.get(current_user.id)

    # Create a partial registration form with only user fields
    from forms import RegistrationForm
    form = RegistrationForm(obj=user)
    # Don't validate email uniqueness when it's the current user's email
    def validate_email(form, field):
        user = User.query.filter_by(email=field.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل. الرجاء استخدام بريد إلكتروني آخر.')

    # Replace the original validate_email with our custom one
    form.validate_email = validate_email

    # Don't validate username uniqueness when it's the current user's username
    def validate_username(form, field):
        user = User.query.filter_by(username=field.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('هذا الاسم مستخدم بالفعل. الرجاء اختيار اسم آخر.')

    # Replace the original validate_username with our custom one
    form.validate_username = validate_username

    # Remove password validation when updating profile
    form.password.validators = []
    form.password2.validators = []

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.address = form.address.data

        # Only update password if provided
        if form.password.data and form.password.data == form.password2.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash('تم تحديث معلومات حسابك بنجاح!', 'success')

        # Redirect to the appropriate dashboard based on where the request came from
        if 'mobile' in request.referrer or 'mobile' in request.headers.get('Referer', ''):
            return redirect(url_for('mobile_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    # For GET requests, don't show passwords
    form.password.data = ''
    form.password2.data = ''

    # Determine which template to use based on the request
    if 'mobile' in request.headers.get('Referer', '') or request.args.get('mobile'):
        return render_template('mobile/edit_profile.html', title='تعديل بيانات الحساب', form=form)
    else:
        return render_template('edit_profile.html', title='تعديل بيانات الحساب', form=form)

# Edit Service Provider Profile
@app.route('/provider/edit', methods=['GET', 'POST'])
@login_required
def edit_provider_profile():
    if not current_user.is_provider():
        flash('عذراً، هذه الصفحة مخصصة لمقدمي الخدمات فقط.', 'warning')
        return redirect(url_for('index'))

    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        return redirect(url_for('create_provider_profile'))

    form = ServiceProviderForm(obj=provider)
    if form.validate_on_submit():
        provider.company_name = form.company_name.data
        provider.description = form.description.data
        provider.website = form.website.data
        db.session.commit()
        flash('تم تحديث ملف مقدم الخدمة بنجاح!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('profile.html', title='تعديل ملف مقدم الخدمة', form=form)

# وظيفة حفظ الصورة
def save_image(file):
    if not file:
        return None
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(file.filename)
    filename = random_hex + file_extension.lower()  # تحويل امتداد الملف إلى أحرف صغيرة

    # التأكد من وجود مجلد الصور
    upload_folder = os.path.join(app.root_path, 'static/uploads/services')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return 'uploads/services/' + filename

# واجهة لتحديث اختيارات نوع الخدمة بناءً على الفئة
@app.route('/api/service-types/<category>')
def get_service_types(category):
    service_types = {
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
        ]
    }

    return jsonify(service_types.get(category, []))

# Add Service
@app.route('/services/add', methods=['GET', 'POST'])
@login_required
def add_service():
    if not current_user.is_provider():
        flash('عذراً، هذه الصفحة مخصصة لمقدمي الخدمات فقط.', 'warning')
        return redirect(url_for('index'))

    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        flash('يجب إنشاء ملف مقدم الخدمة أولاً.', 'warning')
        return redirect(url_for('create_provider_profile'))

    form = ServiceForm()
    
    # تثبيت التصنيف بناءً على تخصص مقدم الخدمة
    form.category.data = provider.specialization
    form.category.render_kw = {'readonly': True, 'disabled': 'disabled'}
    
    if form.validate_on_submit():
        # معالجة تحميل الصورة إن وجدت
        image_path = None
        if form.image.data:
            image_path = save_image(form.image.data)

        service = Service(
            provider_id=provider.id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            duration=form.duration.data,
            category=form.category.data,
            service_type=form.service_type.data,
            additional_info=form.additional_info.data,
            image=image_path,
            is_active=form.is_active.data
        )
        db.session.add(service)
        db.session.commit()
        flash('تمت إضافة الخدمة بنجاح!', 'success')
        return redirect(url_for('dashboard'))
        
    # التحقق من أن المستخدم هو مقدم خدمة
    if not current_user.is_provider():
        flash('عذراً، هذه الصفحة مخصصة لمقدمي الخدمات فقط.', 'warning')
        return redirect(url_for('index'))

    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        flash('الرجاء إكمال ملف مقدم الخدمة أولاً.', 'warning')
        return redirect(url_for('create_provider_profile'))

    # تحديث اختيارات نوع الخدمة بناءً على الفئة المحددة
    if form.category.data:
        service_types = {
            'صيانة': [('كهرباء', 'كهرباء'), ('سباكة', 'سباكة'), ('تكييف', 'تكييف'),
                    ('أجهزة', 'أجهزة'), ('حاسوب', 'حاسوب')],
            'تنظيف': [('منزلي', 'منزلي'), ('مكتبي', 'مكتبي'), ('سجاد', 'سجاد'),
                    ('واجهات', 'واجهات'), ('سيارات', 'سيارات')],
            'تعليم': [('لغات', 'لغات'), ('رياضيات', 'رياضيات'), ('علوم', 'علوم'),
                    ('حاسوب', 'حاسوب'), ('موسيقى', 'موسيقى')],
            'صحة': [('استشارات', 'استشارات'), ('علاج طبيعي', 'علاج طبيعي'),
                   ('تغذية', 'تغذية'), ('لياقة', 'لياقة'), ('تمريض', 'تمريض')],
            'طعام': [('وجبات', 'وجبات'), ('حلويات', 'حلويات'), ('مشروبات', 'مشروبات'),
                   ('طعام صحي', 'طعام صحي'), ('مناسبات', 'مناسبات')]
        }
        form.service_type.choices = service_types.get(form.category.data, [])

    if form.validate_on_submit():
        # معالجة تحميل الصورة إن وجدت
        image_path = None
        if form.image.data:
            image_path = save_image(form.image.data)

        service = Service(
            provider_id=provider.id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            duration=form.duration.data,
            category=form.category.data,
            service_type=form.service_type.data,
            additional_info=form.additional_info.data,
            image=image_path,
            is_active=form.is_active.data
        )
        db.session.add(service)
        db.session.commit()
        flash('تمت إضافة الخدمة بنجاح!', 'success')
        return redirect(url_for('dashboard'))

    # التحقق من نوع الجهاز
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or request.args.get('mobile')

    # اختيار القالب المناسب
    template = 'mobile/service_form.html' if is_mobile else 'service_form.html'
    return render_template(template, form=form)

# Edit Service
@app.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    provider = ServiceProvider.query.get(service.provider_id)

    # التحقق من أن المستخدم هو مقدم الخدمة الأصلي فقط
    if provider.user_id != current_user.id:
        flash('ليس لديك صلاحية تعديل هذه الخدمة.', 'danger')
        return redirect(url_for('dashboard'))

    form = ServiceForm(obj=service)

    # تحديث اختيارات نوع الخدمة حسب الفئة المحددة حالياً
    if service.category:
        form.service_type.choices = form.service_types.get(service.category, [('', 'اختر نوع الخدمة')])

    # تحديث اختيارات نوع الخدمة عند تغيير الفئة
    if request.method == 'GET' and request.args.get('category'):
        category = request.args.get('category')
        form.service_type.choices = form.service_types.get(category, [('', 'اختر نوع الخدمة')])

    if form.validate_on_submit():
        service.name = form.name.data
        service.description = form.description.data
        service.price = form.price.data
        service.duration = form.duration.data
        service.category = form.category.data
        service.service_type = form.service_type.data
        service.additional_info = form.additional_info.data
        service.is_active = form.is_active.data

        # تحديث الصورة إذا تم تحميل صورة جديدة
        if form.image.data:
            service.image = save_image(form.image.data)

        db.session.commit()
        flash('تم تحديث الخدمة بنجاح!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('service_form.html', form=form, service=service)

# View all services
@app.route('/services')
def services():
    search_form = SearchForm()
    query = request.args.get('query', '')
    category = request.args.get('category', '')

    services_query = Service.query.filter_by(is_active=True)

    if query:
        services_query = services_query.filter(Service.name.contains(query) |
                                              Service.description.contains(query))

    if category:
        services_query = services_query.filter_by(category=category)

    services = services_query.all()

    return render_template('services.html', title='الخدمات المتاحة',
                          services=services, search_form=search_form,
                          query=query, category=category)

# View service details
@app.route('/services/<int:service_id>')
def service_details(service_id):
    service = Service.query.get_or_404(service_id)
    provider = ServiceProvider.query.get(service.provider_id)
    reviews = Review.query.filter_by(service_id=service_id).all()

    # Get similar services from the same category
    similar_services = Service.query.filter_by(category=service.category).filter(Service.id != service_id).limit(5).all()

    booking_form = BookingForm()
    booking_form.service_id.data = service_id

    review_form = None
    if current_user.is_authenticated:
        # Check if user has booked this service before
        user_bookings = Booking.query.filter_by(client_id=current_user.id, service_id=service_id).all()
        if user_bookings:
            # Check if user has already reviewed this service
            user_review = Review.query.filter_by(user_id=current_user.id, service_id=service_id).first()
            if not user_review:
                review_form = ReviewForm()
                review_form.service_id.data = service_id

    return render_template('service_details.html', title=service.name,
                          service=service, provider=provider,
                          booking_form=booking_form, review_form=review_form,
                          reviews=reviews, similar_services=similar_services)

# Book service - get form
@app.route('/booking/<int:service_id>', methods=['GET'])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)

    # Check if user is eligible to book
    if current_user.id == service.provider.user_id or current_user.is_admin() or not service.is_active:
        flash('عذراً، لا يمكنك حجز هذه الخدمة.', 'warning')
        return redirect(url_for('service_details', service_id=service_id))

    booking_form = BookingForm()
    booking_form.service_id.data = service_id

    # Calculate the minimum date for booking (today)
    min_date = datetime.now().strftime('%Y-%m-%dT%H:%M')

    return render_template('booking.html', title='حجز موعد',
                          service=service, booking_form=booking_form,
                          min_date=min_date)

# Process booking
@app.route('/booking/process', methods=['POST'])
@login_required
def process_booking():
    """Process booking for both mobile and desktop views"""
    form = BookingForm()
    if form.validate_on_submit():
        service = Service.query.get_or_404(form.service_id.data)
        
        booking = Booking(
            client_id=current_user.id,
            service_id=service.id,
            booking_date=form.booking_date.data,
            notes=form.notes.data,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()

        # Create payment record
        payment = Payment(
            booking_id=booking.id,
            user_id=current_user.id,
            amount=service.price,
            status='pending',
            payment_method=form.payment_method.data
        )
        db.session.add(payment)
        
        # Update payment status based on payment method
        if payment.payment_method == 'cash':
            payment.status = 'awaiting_confirmation'
            booking.status = 'pending'
        
        db.session.commit()

        # Create notification for service provider
        create_notification(
            service.provider.user_id,
            "حجز جديد",
            f"لديك حجز جديد للخدمة {service.name}",
            "info",
            booking.id,
            "booking"
        )

        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'redirect_url': url_for('mobile_dashboard' if 'mobile' in request.referrer else 'dashboard')
            })
        
        # Regular form submission redirect
        flash('تم إنشاء الحجز بنجاح!', 'success')
        if 'mobile' in request.referrer:
            return redirect(url_for('mobile_dashboard'))
        return redirect(url_for('dashboard'))

    # Handle validation errors
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في معالجة النموذج'
        })
    
    flash('حدث خطأ أثناء إنشاء الحجز. الرجاء المحاولة مرة أخرى.', 'danger')
    return redirect(url_for('mobile_services' if 'mobile' in request.referrer else 'services'))

# Payment
@app.route('/payment/<int:payment_id>', methods=['GET', 'POST'])
@login_required
def payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)

    # Verify ownership
    if payment.user_id != current_user.id and not current_user.is_admin():
        flash('ليس لديك صلاحية الوصول إلى صفحة الدفع هذه.', 'danger')
        return redirect(url_for('dashboard'))

    booking = Booking.query.get(payment.booking_id)
    service = Service.query.get(booking.service_id)

    form = PaymentForm()
    form.booking_id.data = booking.id
    form.amount.data = payment.amount

    if form.validate_on_submit():
        payment.payment_method = form.payment_method.data
        payment.status = 'completed'
        payment.payment_date = datetime.utcnow()
        payment.transaction_id = f"TR-{payment.id}-{int(datetime.utcnow().timestamp())}"

        # Update booking status
        booking.status = 'confirmed'

        db.session.commit()
        flash('تمت عملية الدفع بنجاح!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('payment.html', title='إتمام الدفع',
                          payment=payment, booking=booking,
                          service=service, form=form)

@app.route('/mobile/payment/<int:payment_id>')
@login_required
def mobile_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    booking = Booking.query.get(payment.booking_id)
    service = Service.query.get(booking.service_id)

    # Verify ownership
    if payment.user_id != current_user.id and not current_user.is_admin():
        flash('ليس لديك صلاحية الوصول إلى صفحة الدفع هذه.', 'danger')
        return redirect(url_for('mobile_dashboard'))

    return render_template('mobile/payment.html', 
                         payment=payment,
                         booking=booking,
                         service=service)

# Add review
@app.route('/review', methods=['POST'])
@login_required
def add_review():
    form = ReviewForm()
    if form.validate_on_submit():
        service_id = form.service_id.data
        service = Service.query.get_or_404(service_id)

        # التحقق من وجود حجز مكتمل للخدمة
        user_bookings = Booking.query.filter_by(
            client_id=current_user.id, 
            service_id=service_id,
            status='completed'
        ).first()
        
        if not user_bookings:
            flash('يمكنك فقط تقييم الخدمات التي قمت بحجزها وتم إكمالها.', 'warning')
            return redirect(url_for('service_details', service_id=service_id))

        # التحقق من عدم وجود تقييم سابق
        existing_review = Review.query.filter_by(user_id=current_user.id, service_id=service_id).first()
        if existing_review:
            flash('لقد قمت بتقييم هذه الخدمة بالفعل.', 'warning')
            return redirect(url_for('service_details', service_id=service_id))

        # التحقق من صحة التقييم
        try:
            rating = int(form.rating.data)
            if rating < 1 or rating > 5:
                flash('التقييم يجب أن يكون بين 1 و 5 نجوم.', 'warning')
                return redirect(url_for('service_details', service_id=service_id))
        except:
            flash('التقييم يجب أن يكون رقماً صحيحاً.', 'warning')
            return redirect(url_for('service_details', service_id=service_id))

        # التحقق من صحة التعليق
        comment = form.comment.data.strip()
        if len(comment) < 10:
            flash('يرجى كتابة تعليق أطول (10 أحرف على الأقل).', 'warning')
            return redirect(url_for('service_details', service_id=service_id))

        # إنشاء التقييم الجديد
        review = Review(
            service_id=service_id,
            user_id=current_user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)

        # تحديث متوسط تقييم الخدمة
        service_reviews = Review.query.filter_by(service_id=service_id).all()
        if service_reviews:
            service_avg_rating = sum(r.rating for r in service_reviews) / len(service_reviews)
            # يمكن إضافة حقل متوسط التقييم إلى جدول الخدمات إذا لزم الأمر
        
        # تحديث متوسط تقييم مزود الخدمة
        provider = ServiceProvider.query.get(service.provider_id)
        provider_services = Service.query.filter_by(provider_id=provider.id).all()
        all_provider_reviews = []
        
        for srv in provider_services:
            service_reviews = Review.query.filter_by(service_id=srv.id).all()
            all_provider_reviews.extend(service_reviews)
            
        if all_provider_reviews:
            provider.rating = sum(r.rating for r in all_provider_reviews) / len(all_provider_reviews)
        
        # إنشاء إشعار لمزود الخدمة
        create_notification(
            provider.user_id,
            "تقييم جديد",
            f"قام {current_user.username} بتقييم خدمة {service.name} بتقييم {rating} نجوم",
            "info",
            service_id,
            "review"
        )

        # حفظ التغييرات
        db.session.commit()
        
        # إظهار رسالة نجاح
        flash('شكراً على مشاركة تقييمك! سيساعد ذلك الآخرين في اختيار الخدمة المناسبة.', 'success')
        
        # التوجيه إلى الصفحة المناسبة
        referer = request.headers.get('Referer', '')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'تم إضافة التقييم بنجاح',
                'redirect': url_for('mobile_dashboard' if 'mobile' in referer else 'dashboard')
            })
        elif 'mobile' in referer:
            return redirect(url_for('mobile_dashboard'))
        elif 'service_details' in referer:
            return redirect(url_for('service_details', service_id=service_id))
        else:
            return redirect(url_for('dashboard'))

    else:
        # معالجة أخطاء التحقق من النموذج
        errors = []
        for field, error_messages in form.errors.items():
            for error in error_messages:
                errors.append(f"خطأ في حقل {field}: {error}")
        
        error_message = "حدث خطأ في تقديم التقييم. " + " ".join(errors)
        flash(error_message, 'warning')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': error_message
            })
        
        return redirect(url_for('service_details', service_id=form.service_id.data))
        
    return redirect(url_for('service_details', service_id=form.service_id.data))

# إضافة وجبة جديدة (لمقدمي خدمات الطعام)
@app.route('/meals/add', methods=['GET', 'POST'])
@login_required
def add_meal():
    # التحقق من أن المستخدم مقدم خدمة طعام
    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider or provider.specialization != 'طعام':
        flash('عذراً، هذه الصفحة مخصصة لمقدمي خدمات الطعام فقط.', 'warning')
        return redirect(url_for('dashboard'))

    form = MealForm()
    if form.validate_on_submit():
        # معالجة تحميل الصورة إن وجدت
        image_path = None
        if form.image.data:
            image_path = save_image(form.image.data)

        meal = Meal(
            provider_id=provider.id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            meal_type=form.meal_type.data,
            preparation_time=form.preparation_time.data,
            calories=form.calories.data,
            is_vegetarian=form.is_vegetarian.data,
            is_vegan=form.is_vegan.data,
            is_gluten_free=form.is_gluten_free.data,
            image=image_path,
            is_available=form.is_available.data
        )
        db.session.add(meal)
        db.session.commit()

        # تسجيل الإجراء
        log_action(
            user_id=current_user.id,
            action_type='add_meal',
            action_details=f'تمت إضافة وجبة جديدة: {meal.name}'
        )

        flash('تمت إضافة الوجبة بنجاح!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('meal_form.html', form=form, title='إضافة وجبة جديدة')

# تعديل وجبة
@app.route('/meals/edit/<int:meal_id>', methods=['GET', 'POST'])
@login_required
def edit_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    provider = ServiceProvider.query.get(meal.provider_id)

    # التحقق من ملكية الوجبة
    if provider.user_id != current_user.id and not current_user.is_admin():
        flash('ليس لديك صلاحية تعديل هذه الوجبة.', 'danger')
        return redirect(url_for('dashboard'))

    form = MealForm(obj=meal)
    if form.validate_on_submit():
        meal.name = form.name.data
        meal.description = form.description.data
        meal.price = form.price.data
        meal.meal_type = form.meal_type.data
        meal.preparation_time = form.preparation_time.data
        meal.calories = form.calories.data
        meal.is_vegetarian = form.is_vegetarian.data
        meal.is_vegan = form.is_vegan.data
        meal.is_gluten_free = form.is_gluten_free.data
        meal.is_available = form.is_available.data

        # تحديث الصورة إذا تم تحميل صورة جديدة
        if form.image.data:
            meal.image = save_image(form.image.data)

        db.session.commit()

        # تسجيل الإجراء
        log_action(
            user_id=current_user.id,
            action_type='edit_meal',
            action_details=f'تم تعديل وجبة: {meal.name}'
        )

        flash('تم تحديث الوجبة بنجاح!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('meal_form.html', form=form, meal=meal, title='تعديل وجبة')

# حجز طاولة فيالمطعم
@app.route('/restaurant/<int:provider_id>/reserve-table', methods=['GET', 'POST'])
@login_required
def reserve_table(provider_id):
    provider = ServiceProvider.query.get_or_404(provider_id)

    # التحقق من أن مقدم الخدمة متخصص في الطعام
    if provider.specialization != 'طعام':
        flash('عذراً، لا يمكن حجز طاولة إلا في المطاعم.', 'warning')
        return redirect(url_for('index'))

    form = TableReservationForm()
    if form.validate_on_submit():
        reservation = TableReservation(
            provider_id=provider_id,
            user_id=current_user.id,
            reservation_date=form.reservation_date.data,
            guests_number=form.guests_number.data,
            special_requests=form.special_requests.data,
            contact_phone=form.contact_phone.data,
            status='pending'
        )
        db.session.add(reservation)
        db.session.commit()

        # إنشاء إشعار لمقدم الخدمة
        create_notification(
            user_id=provider.user_id,
            title='حجز طاولة جديد',
            content=f'لديك حجز طاولة جديد من {current_user.username} بتاريخ {reservation.reservation_date.strftime("%Y-%m-%d %H:%M")}',
            notification_type='info',
            related_id=reservation.id,
            related_type='table_reservation'
        )

        # تسجيل الإجراء
        log_action(
            user_id=current_user.id,
            action_type='reserve_table',
            action_details=f'تم حجز طاولة في {provider.company_name} بتاريخ {reservation.reservation_date.strftime("%Y-%m-%d %H:%M")}'
        )

        flash('تم حجز الطاولة بنجاح! سيتم التواصل معك لتأكيد الحجز.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('table_reservation.html', form=form, provider=provider, title='حجز طاولة')

# Admin Dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))
        
    # Check if the user is requesting from a mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent

    users_count = User.query.count()
    providers_count = ServiceProvider.query.count()
    services_count = Service.query.count()
    bookings_count = Booking.query.count()
    payments_count = Payment.query.count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    if is_mobile and request.args.get('view') != 'desktop':
        return render_template('mobile/admin/dashboard.html',
                             title='لوحة تحكم المدير',
                             users_count=users_count,
                             providers_count=providers_count,
                             services_count=services_count,
                             bookings_count=bookings_count,
                             payments_count=payments_count,
                             recent_users=recent_users,
                             recent_bookings=recent_bookings)

    return render_template('admin/dashboard.html', title='لوحة تحكم المدير',
                          users_count=users_count, providers_count=providers_count,
                          services_count=services_count, bookings_count=bookings_count,
                          payments_count=payments_count, recent_users=recent_users,
                          recent_bookings=recent_bookings)

@app.route('/mobile/admin/dashboard')
@login_required
def mobile_admin_dashboard():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('mobile_index'))

    users_count = User.query.count()
    providers_count = ServiceProvider.query.count()
    services_count = Service.query.count()
    bookings_count = Booking.query.count()
    payments_count = Payment.query.count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    return render_template('mobile/admin/dashboard.html',
                         title='لوحة تحكم المدير',
                         users_count=users_count,
                         providers_count=providers_count,
                         services_count=services_count,
                         bookings_count=bookings_count,
                         payments_count=payments_count,
                         recent_users=recent_users,
                         recent_bookings=recent_bookings)

# Admin Reports
@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))

    # التحقق من نوع الجهاز
    is_mobile = request.args.get('mobile') or 'mobile' in request.headers.get('User-Agent', '').lower()

    # استخراج إحصائيات المستخدمين
    total_users = User.query.count()
    total_providers = ServiceProvider.query.count()
    total_regular_users = User.query.filter_by(role=ROLE_USER).count()
    verified_providers = ServiceProvider.query.filter_by(verified=True).count()
    unverified_providers = total_providers - verified_providers  # إضافة هذا المتغير

    # استخراج إحصائيات الخدمات
    total_services = Service.query.count()
    active_services = Service.query.filter_by(is_active=True).count()

    # توزيع الخدمات حسب الفئات
    categories = db.session.query(Service.category, db.func.count(Service.id)).group_by(Service.category).all()
    category_labels = [category[0] for category in categories]
    category_data = [category[1] for category in categories]

    # إحصائيات الحجوزات
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    confirmed_bookings = Booking.query.filter_by(status='confirmed').count()
    completed_bookings = Booking.query.filter_by(status='completed').count()
    cancelled_bookings = Booking.query.filter_by(status='cancelled').count()

    # إحصائيات المدفوعات
    total_payments = Payment.query.count()
    completed_payments = Payment.query.filter_by(status='completed').count()
    payment_amounts = db.session.query(Payment.status, db.func.sum(Payment.amount)).group_by(Payment.status).all()

    # إجمالي المبيعات
    total_sales = 0
    for payment in payment_amounts:
        if payment[0] == 'completed':
            total_sales = payment[1] if payment[1] else 0

    # استخراج إحصائيات الحجوزات الشهرية
    monthly_bookings = []
    current_year = datetime.now().year
    for month in range(1, 13):
        start_date = datetime(current_year, month, 1)
        if month == 12:
            end_date = datetime(current_year + 1, 1, 1)
        else:
            end_date = datetime(current_year, month + 1, 1)
        count = Booking.query.filter(
            Booking.created_at >= start_date,
            Booking.created_at < end_date
        ).count()
        monthly_bookings.append(count)

    # استخراج إحصائيات التقييمات
    avg_rating = db.session.query(db.func.avg(Review.rating)).scalar() or 0
    rating_distribution = db.session.query(Review.rating, db.func.count(Review.id)).group_by(Review.rating).all()
    rating_data = [0, 0, 0, 0, 0]  # تمثل التقييمات من 1 إلى 5
    for rating in rating_distribution:
        if 1 <= rating[0] <= 5:
            rating_data[rating[0]-1] = rating[1]

    # تقرير أفضل مزودي الخدمة
    top_providers = db.session.query(
        ServiceProvider.id,
        ServiceProvider.company_name,
        ServiceProvider.rating,
        db.func.count(Service.id).label('service_count'),
        db.func.count(Booking.id).label('booking_count')
    ).join(Service, ServiceProvider.id == Service.provider_id, isouter=True)\
     .join(Booking, Service.id == Booking.service_id, isouter=True)\
     .group_by(ServiceProvider.id)\
     .order_by(ServiceProvider.rating.desc())\
     .limit(5).all()

    if is_mobile:
        return render_template('mobile/admin/reports.html', 
                             title='تقارير النظام',
                             total_users=total_users,
                             total_providers=total_providers,
                             total_regular_users=total_regular_users,
                             verified_providers=verified_providers,
                             unverified_providers=unverified_providers,  # إضافة هذا المتغير
                             total_services=total_services,
                             active_services=active_services,
                             category_labels=category_labels,
                             category_data=category_data,
                             total_bookings=total_bookings,
                             pending_bookings=pending_bookings,
                             confirmed_bookings=confirmed_bookings,
                             completed_bookings=completed_bookings,
                             cancelled_bookings=cancelled_bookings,
                             total_payments=total_payments,
                             completed_payments=completed_payments,
                             total_sales=total_sales,
                             monthly_bookings=monthly_bookings,
                             avg_rating=avg_rating,
                             rating_data=rating_data,
                             top_providers=top_providers)

    return render_template('admin/reports.html', title='تقارير النظام',
                          total_users=total_users,
                          total_providers=total_providers,
                          total_regular_users=total_regular_users,
                          verified_providers=verified_providers,
                          unverified_providers=unverified_providers,  # إضافة هذا المتغير
                          total_services=total_services,
                          active_services=active_services,
                          category_labels=category_labels,
                          category_data=category_data,
                          total_bookings=total_bookings,
                          pending_bookings=pending_bookings,
                          confirmed_bookings=confirmed_bookings,
                          completed_bookings=completed_bookings,
                          cancelled_bookings=cancelled_bookings,
                          total_payments=total_payments,
                          completed_payments=completed_payments,
                          total_sales=total_sales,
                          monthly_bookings=monthly_bookings,
                          avg_rating=avg_rating,
                          rating_data=rating_data,
                          top_providers=top_providers)

# Admin - Users
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))

    # التحقق من نوع الجهاز
    is_mobile = request.args.get('mobile') or 'mobile' in request.headers.get('User-Agent', '').lower()
    
    users = User.query.all()
    
    # اختيار القالب المناسب حسب نوع الجهاز
    template = 'mobile/admin/users.html' if is_mobile else 'admin/users.html'
    return render_template(template, title='إدارة المستخدمين', users=users)

# Admin - Services
@app.route('/admin/services')
@login_required
def admin_services():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))

    services = Service.query.all()
    return render_template('admin/services.html', title='إدارة الخدمات', services=services)

@app.route('/mobile/admin/services')
@login_required
def mobile_admin_services():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('mobile_index'))

    services = Service.query.all()
    return render_template('mobile/admin/services.html', 
                         title='إدارة الخدمات',
                         services=services)

# Admin - Bookings
@app.route('/admin/bookings')
@login_required
def admin_bookings():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))

    # التحقق من نوع الجهاز
    is_mobile = request.args.get('mobile') or 'mobile' in request.headers.get('User-Agent', '').lower()

    bookings = Booking.query.all()
    
    if is_mobile:
        return render_template('mobile/admin/bookings.html', title='إدارة الحجوزات', bookings=bookings)
    
    return render_template('admin/bookings.html', title='إدارة الحجوزات', bookings=bookings)

# Admin - Payments
@app.route('/admin/payments')
@login_required
def admin_payments():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))

    # التحقق من نوع الجهاز
    is_mobile = request.args.get('mobile') or 'mobile' in request.headers.get('User-Agent', '').lower()

    payments = Payment.query.all()
    
    if is_mobile:
        return render_template('mobile/admin/payments.html', title='إدارة المدفوعات', payments=payments)
    
    return render_template('admin/payments.html', title='إدارة المدفوعات', payments=payments)

# Toggle user active status
@app.route('/admin/users/<int:user_id>/toggle_active', methods=['POST'])
@login_required
def toggle_user_active(user_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'غير مصرح بهذه العملية'})

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'active': user.is_active,
        'message': f'تم تغيير حالة المستخدم بنجاح إلى {"مفعل" if user.is_active else "معطل"}'
    })

# Toggle service active status
@app.route('/admin/services/<int:service_id>/toggle_active', methods=['POST'])
@login_required
def toggle_service_active(service_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'غير مصرح بهذه العملية'})

    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'active': service.is_active,
        'message': f'تم تغيير حالة الخدمة بنجاح إلى {"متاحة" if service.is_active else "غير متاحة"}'
    })

# تغيير حالة الحجز (للمزودين)
@app.route('/booking/<int:booking_id>/<action>', methods=['POST'])
@login_required
def manage_booking(booking_id, action):
    # التحقق من الحجز
    booking = Booking.query.get_or_404(booking_id)
    service = Service.query.get(booking.service_id)
    provider = ServiceProvider.query.get(service.provider_id)

    # التحقق من الصلاحيات - السماح للعميل ومزود الخدمة والمشرف
    is_authorized = (booking.client_id == current_user.id or 
                    provider.user_id == current_user.id or 
                    current_user.is_admin())
    
    if not is_authorized:
        return jsonify({
            'success': False,
            'message': 'ليس لديك صلاحية إدارة هذا الحجز'
        })

    # تنفيذ الإجراء المطلوب
    if action == 'confirm':
        if provider.user_id != current_user.id and not current_user.is_admin():
            return jsonify({
                'success': False,
                'message': 'فقط مزود الخدمة يمكنه تأكيد الحجز'
            })
            
        booking.status = 'confirmed'
        message = 'تم تأكيد الحجز بنجاح'

        # إنشاء إشعار للعميل
        create_notification(
            booking.client_id,
            "تم تأكيد الحجز",
            f"تم تأكيد حجزك للخدمة {service.name}",
            "success",
            booking.id,
            "booking"
        )

    elif action == 'cancel':
        # التحقق من حالة الحجز
        if booking.status not in ['pending', 'confirmed']:
            return jsonify({
                'success': False,
                'message': 'لا يمكن إلغاء هذا الحجز في حالته الحالية'
            })

        # حذف الدفع المرتبط إن وجد
        if booking.payment:
            db.session.delete(booking.payment)

        # إلغاء الحجز
        booking.status = 'cancelled'
        message = 'تم إلغاء الحجز بنجاح'

        # تحديد من سيتلقى الإشعار
        notify_user_id = provider.user_id if current_user.id == booking.client_id else booking.client_id
        notifier_name = "العميل" if current_user.id == booking.client_id else "مزود الخدمة"
        
        create_notification(
            notify_user_id,
            "تم إلغاء الحجز",
            f"قام {notifier_name} بإلغاء الحجز للخدمة {service.name}",
            "danger",
            None,
            "booking"
        )

    elif action == 'complete':
        if provider.user_id != current_user.id and not current_user.is_admin():
            return jsonify({
                'success': False,
                'message': 'فقط مزود الخدمة يمكنه إكمال الحجز'
            })
            
        booking.status = 'completed'
        message = 'تم إكمال الحجز بنجاح'

        # إنشاء إشعار للعميل
        create_notification(
            booking.client_id,
            "تم إكمال الخدمة",
            f"تم إكمال تقديم الخدمة {service.name}. يمكنك الآن تقييم الخدمة",
            "info",
            booking.id,
            "booking"
        )

        # إرسال إشعار للتقييم
        send_review_notification(booking.id)

    else:
        return jsonify({
            'success': False,
            'message': 'إجراء غير صالح'
        })

    try:
        db.session.commit()
        # تسجيل الإجراء
        log_action(
            current_user.id,
            f'{action}_booking',
            f'تم {message} رقم {booking_id}',
            booking_id=booking_id
        )
        
        return jsonify({
            'success': True,
            'message': message,
            'status': booking.status
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in {action} booking {booking_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء {message}'
        })

# تغيير حالة الدفع (للمزودين)
@app.route('/payment/<int:payment_id>/confirm-payment', methods=['POST'])
@login_required
def confirm_payment(payment_id):
    # التحقق من الدفع
    payment = Payment.query.get_or_404(payment_id)
    booking = Booking.query.get(payment.booking_id)

    # التحقق من أن المستخدم هو مزود الخدمة المرتبط بالحجز
    service = Service.query.get(booking.service_id)
    provider = ServiceProvider.query.get(service.provider_id)

    if provider.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية تأكيد هذا الدفع'})

    # تأكيد الدفع
    if payment.status == 'awaiting_confirmation':
        try:
            # تحديث حالة الدفع
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()

            # تحديث حالة الحجز إلى مؤكد
            booking.status = 'confirmed'

            # تحديث إجمالي المبيعات لمقدم الخدمة
            provider.total_sales = (provider.total_sales or 0) + payment.amount

            # إنشاء إشعار للعميل
            create_notification(
                booking.client_id,
                "تم تأكيد الدفع",
                f"تم تأكيد دفعك للخدمة {service.name} وتأكيد الحجز بنجاح",
                "success",
                payment.id,
                "payment"
            )

            # إنشاء إشعار لمقدم الخدمة
            create_notification(
                provider.user_id,
                "تم تأكيد الدفع",
                f"تم تأكيد استلام الدفع للحجز رقم {booking.id}",
                "success",
                payment.id,
                "payment"
            )

            # تسجيل الإجراء
            log_action(
                current_user.id,
                'confirm_payment',
                f'تم تأكيد الدفع للحجز رقم {booking.id}',
                booking_id=booking.id,
                payment_id=payment_id
            )

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'تم تأكيد استلام الدفع بنجاح',
                'data': {
                    'payment_status': 'completed',
                    'booking_status': 'confirmed',
                    'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
                    'total_amount': f"{payment.amount:.2f}"
                }
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'حدث خطأ أثناء تأكيد الدفع: {str(e)}'
            })
    else:
        return jsonify({
            'success': False,
            'message': 'لا يمكن تأكيد هذا الدفع في حالته الحالية'
        })

# إرسال إشعارات التقييم يدويًا (للاختبار)
@app.route('/admin/send-review-notifications')
@login_required
def admin_send_review_notifications():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))

    try:
        result = check_completed_bookings()
        if result:
            flash('تم إرسال إشعارات التقييم بنجاح!', 'success')
        else:
            flash('حدث خطأ أثناء إرسال إشعارات التقييم.', 'danger')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))

# تصدير قاعدة البيانات (للمشرفين)
@app.route('/admin/export-database')
@login_required
def admin_export_database():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))

    backup_file = export_database()

    if backup_file and os.path.exists(backup_file):
        # إنشاء إشعار للمشرف
        create_notification(
            current_user.id,
            "تم تصدير قاعدة البيانات",
            f"تم تصدير قاعدة البيانات بنجاح إلى: {backup_file}",
            "success"
        )

        # تقديم الملف للتحميل
        return send_file(
            backup_file,
            as_attachment=True,
            download_name=os.path.basename(backup_file),
            mimetype='application/json'
        )
    else:
        flash('حدث خطأ أثناء تصدير قاعدة البيانات. الرجاء المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('admin_dashboard'))

# =============== Stripe Payment Routes =============== #

# بدء عملية الدفع باستخدام Stripe
@app.route('/stripe/checkout/<int:booking_id>', methods=['POST'])
@login_required
def stripe_checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # التحقق من أن المستخدم هو صاحب الحجز
    if booking.client_id != current_user.id:
        flash('ليس لديك صلاحية الوصول إلى هذا الحجز.', 'danger')
        return redirect(url_for('dashboard'))

    # التحقق من حالة الحجز
    if booking.status not in ['pending', 'awaiting_payment']:
        flash('هذا الحجز غير مؤهل للدفع، ربما تم الدفع مسبقاً أو تم إلغاؤه.', 'warning')
        return redirect(url_for('dashboard'))

    # إنشاء جلسة دفع Stripe
    checkout_session, error = create_checkout_session(booking_id, current_user)

    if error:
        flash(f'حدث خطأ أثناء إعداد عملية الدفع: {error}', 'danger')
        return redirect(url_for('dashboard'))

    # تحديث حالة الحجز
    booking.status = 'awaiting_payment'
    db.session.commit()

    # إعادة التوجيه إلى صفحة الدفع الخاصة بـ Stripe
    return redirect(checkout_session.url, code=303)

# صفحة نجاح الدفع
@app.route('/payment/success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    if not session_id:
        flash('معرّف جلسة الدفع غير متوفر.', 'danger')
        return redirect(url_for('dashboard'))

    # التحقق من حالة الدفع
    success, message = verify_payment_session(session_id)

    if success:
        flash('تم اكتمال عملية الدفع بنجاح!', 'success')
    else:
        flash(f'حدث خطأ أثناء التحقق من الدفع: {message}', 'warning')

    return redirect(url_for('dashboard'))

# صفحة إلغاء الدفع
@app.route('/payment/cancel')
@login_required
def payment_cancel():
    booking_id = request.args.get('booking_id')
    if not booking_id:
        flash('معرّف الحجز غير متوفر.', 'danger')
        return redirect(url_for('dashboard'))

    booking = Booking.query.get_or_404(booking_id)

    # التحقق من أن المستخدم هو صاحب الحجز
    if booking.client_id != current_user.id:
        flash('ليس لديك صلاحية الوصول إلى هذا الحجز.', 'danger')
        return redirect(url_for('dashboard'))

    # التحقق من وجود دفع قيد المعالجة
    payment = Payment.query.filter_by(booking_id=booking_id, status='processing').first()
    if payment:
        # إلغاء الدفع
        cancel_payment(payment.id)

    flash('تم إلغاء عملية الدفع.', 'info')
    return redirect(url_for('dashboard'))

# عرض تفاصيل الدفع (صفحة جديدة)
@app.route('/stripe/payment-details/<int:payment_id>')
@login_required
def stripe_payment_details(payment_id):
    payment, error = get_payment_status(payment_id)

    if error:
        flash(error, 'danger')
        return redirect(url_for('dashboard'))

    # التحقق من صلاحية الوصول
    booking = Booking.query.get(payment.booking_id)
    service = Service.query.get(booking.service_id)
    provider = ServiceProvider.query.get(service.provider_id)

    # التحقق من أن المستخدم هو صاحب الدفع أو مزود الخدمة أو المدير
    if payment.user_id != current_user.id and provider.user_id != current_user.id and not current_user.is_admin():
        flash('ليس لديك صلاحية الوصول إلى تفاصيل هذا الدفع.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('payment_details.html', title='تفاصيل الدفع',
                          payment=payment, booking=booking, service=service)

# =============== Mobile Application Routes =============== #

# Mobile Home Page
@app.route('/mobile/')
@app.route('/mobile/index')
def mobile_index():
    featured_services = Service.query.filter_by(is_active=True).order_by(Service.id.desc()).limit(6).all()
    recent_services = Service.query.filter_by(is_active=True).order_by(Service.created_at.desc()).limit(6).all()
    return render_template('mobile/index.html', featured_services=featured_services, recent_services=recent_services)

@app.route('/mobile/services')
def mobile_services():
    query = request.args.get('query', '')
    category = request.args.get('category', '')

    services_query = Service.query.filter_by(is_active=True)

    if query:
        services_query = services_query.filter(Service.name.contains(query) |
                                           Service.description.contains(query))

    if category:
        services_query = services_query.filter_by(category=category)

    services = services_query.all()
    return render_template('mobile/services.html', services=services, category=category)

# Mobile Service Details
@app.route('/mobile/services/<int:service_id>')
def mobile_service_details(service_id):
    service = Service.query.get_or_404(service_id)
    provider = ServiceProvider.query.get(service.provider_id)
    reviews = Review.query.filter_by(service_id=service_id).all()
    
    # Get similar services from the same category
    similar_services = Service.query.filter_by(category=service.category).filter(Service.id != service_id).limit(5).all()
    
    booking_form = BookingForm()
    booking_form.service_id.data = service_id
    
    review_form = None
    if current_user.is_authenticated:
        # Check if user has booked this service before
        user_bookings = Booking.query.filter_by(client_id=current_user.id, service_id=service_id).all()
        if user_bookings:
            # Check if user has already reviewed this service
            user_review = Review.query.filter_by(user_id=current_user.id, service_id=service_id).first()
            if not user_review:
                review_form = ReviewForm()
                review_form.service_id.data = service_id

    return render_template('mobile/service_details.html', 
                          service=service, 
                          provider=provider,
                          reviews=reviews, 
                          booking_form=booking_form,
                          review_form=review_form,
                          similar_services=similar_services)

# Mobile Dashboard
@app.route('/mobile/dashboard')
@login_required
def mobile_dashboard():
    # الحصول على بيانات المستخدم الحالي
    current_user_data = User.query.get(current_user.id)

    # الحصول على حجوزات المستخدم
    bookings = Booking.query.filter_by(client_id=current_user.id)\
        .order_by(Booking.booking_date.desc()).all()

    # مقدم خدمة؟
    provider = None
    active_services_count = 0
    pending_bookings_count = 0
    services_offered = None

    if current_user.is_provider():
        provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
        if provider:
            services = Service.query.filter_by(provider_id=provider.id).all()
            active_services_count = sum(1 for s in services if s.is_active)

            # الحصول على حجوزات الخدمات الخاصة بالمزود
            provider_bookings = []
            for service in services:
                service_bookings = Booking.query.filter_by(service_id=service.id, status='pending').all()
                provider_bookings.extend(service_bookings)

            pending_bookings_count = len(provider_bookings)
            services_offered = ", ".join([service.name for service in services])

    completed_bookings = [b for b in bookings if b.status == 'completed']
    review_form = ReviewForm()

    return render_template('mobile/dashboard.html', 
                          user=current_user_data, 
                          bookings=bookings,
                          completed_bookings=completed_bookings,
                          active_services_count=active_services_count,
                          pending_bookings_count=pending_bookings_count,
                          review_form=review_form,
                          provider=provider,
                          services_offered=services_offered)

@app.route('/mobile/about')
def mobile_about():
    return render_template('mobile/about.html')

# Mobile Booking Page
@app.route('/mobile/booking/<int:service_id>')
@login_required
def mobile_booking(service_id):
    if current_user.is_provider():
        flash('لا يمكن لمقدمي الخدمات حجز خدمات أخرى', 'warning')
        return redirect(url_for('mobile_dashboard'))

    service = Service.query.get_or_404(service_id)
    booking_form = BookingForm()
    booking_form.service_id.data = service_id

    # Calculate the minimum date for booking (today)
    min_date = datetime.now().strftime('%Y-%m-%dT%H:%M')

    return render_template('mobile/booking.html', service=service, booking_form=booking_form, min_date=min_date)

# Helper functions for mobile templates
@app.template_filter('get_status_color')
def get_status_color(status):
    status_colors = {
        'pending': 'warning',
        'confirmed': 'info',
        'completed': 'success',
        'cancelled': 'danger'
    }
    return status_colors.get(status, 'secondary')

@app.context_processor
def utility_processor():
    def has_review(service_id, user_id):
        return Review.query.filter_by(service_id=service_id, user_id=user_id).first() is not None

    def get_status_color(status):
        status_colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(status, 'secondary')

    return {'has_review': has_review, 'get_status_color': get_status_color}

# Notifications
@app.route('/notifications')
@login_required
def notifications():
    """عرض الإشعارات للمستخدم الحالي"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # جلب الإشعارات وترتيبها حسب الأحدث أولاً
    notifications_query = Notification.query.filter_by(user_id=current_user.id)
    notifications_pagination = notifications_query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=per_page)
    notifications = notifications_pagination.items

    # تحديث حالة الإشعارات غير المقروءة
    unread_notifications = notifications_query.filter_by(is_read=False).all()
    for notification in unread_notifications:
        notification.is_read = True

    db.session.commit()

    return render_template('notifications.html', title='الإشعارات',
                          notifications=notifications,
                          pagination=notifications_pagination)

# تعليم إشعار كمقروء
@app.route('/notifications/mark-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    """تعليم إشعار معين كمقروء"""
    notification = Notification.query.get_or_404(notification_id)

    # التأكد من أن الإشعار للمستخدم الحالي
    if notification.user_id != current_user.id:
        flash('ليس لديك صلاحية الوصول إلى هذا الإشعار.', 'danger')
        return redirect(url_for('notifications'))

    notification.is_read = True
    db.session.commit()

    # إذا تم تحديد عنوان URL للعودة، عد إليه
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)

    # وإلا عد إلى صفحة الإشعارات
    return redirect(url_for('notifications'))

# حذف إشعار
@app.route('/notifications/delete/<int:notification_id>')
@login_required
def delete_notification(notification_id):
    """حذف إشعار معين"""
    notification = Notification.query.get_or_404(notification_id)

    # التأكد من أن الإشعار للمستخدم الحالي
    if notification.user_id != current_user.id:
        flash('ليس لديك صلاحية حذف هذا الإشعار.', 'danger')
        return redirect(url_for('notifications'))

    db.session.delete(notification)
    db.session.commit()

    flash('تم حذف الإشعار بنجاح.', 'success')
    return redirect(url_for('notifications'))

# حذف جميع الإشعارات للمستخدم الحالي
@app.route('/notifications/delete-all', methods=['POST'])
@login_required
def delete_all_notifications():
    """حذف جميع إشعارات المستخدم الحالي"""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('تم حذف جميع الإشعارات بنجاح.', 'success')
    return redirect(url_for('notifications'))

# الإشعارات للتطبيق الجوال
@app.route('/mobile/notifications')
@login_required
def mobile_notifications():
    """عرض الإشعارات في واجهة الهاتف المحمول"""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()

    # تحديث حالة الإشعارات غير المقروءة
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in unread_notifications:
        notification.is_read = True

    db.session.commit()

    return render_template('mobile/notifications.html', title='الإشعارات', notifications=notifications)

# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

def log_action(user_id, action_type, action_details, booking_id=None, payment_id=None):
    """تسجيل إجراء في قاعدة البيانات"""
    from models import ActionLog
    action = ActionLog(
        user_id=user_id,
        booking_id=booking_id,
        payment_id=payment_id,
        action_type=action_type,
        action_details=action_details
    )
    db.session.add(action)
    db.session.commit()

# Delete Service
@app.route('/admin/services/<int:service_id>/delete', methods=['POST'])
@login_required
def delete_service(service_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'غير مصرح بهذه العملية'})

    service = Service.query.get_or_404(service_id)
    try:
        db.session.delete(service)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم حذف الخدمة بنجاح'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف الخدمة'
        })

@app.route('/api/check_completed_booking/<int:service_id>')
@login_required
def check_completed_booking(service_id):
    """التحقق من إمكانية تقييم خدمة معينة"""
    # التحقق مما إذا كان المستخدم لديه حجز مكتمل لهذه الخدمة
    completed_booking = Booking.query.filter_by(
        client_id=current_user.id, 
        service_id=service_id, 
        status='completed'
    ).first()
    
    # التحقق مما إذا كان المستخدم لديه مراجعة لهذه الخدمة
    has_review = Review.query.filter_by(
        user_id=current_user.id,
        service_id=service_id
    ).first() is not None
    
    # التحقق من التفاصيل الإضافية للحجز
    booking_details = {}
    if completed_booking:
        service = Service.query.get(service_id)
        booking_details = {
            'service_name': service.name,
            'booking_date': completed_booking.booking_date.strftime('%Y-%m-%d %H:%M'),
            'completion_date': completed_booking.updated_at.strftime('%Y-%m-%d') if completed_booking.updated_at else None
        }
    
    return jsonify({
        'has_completed': completed_booking is not None,
        'has_review': has_review,
        'booking_details': booking_details
    })
