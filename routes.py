import logging
import os
import secrets
import uuid
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, abort, g, send_file
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from app import app, db
from export_db import export_database
from notifications import send_review_notification, check_completed_bookings, create_notification
from models import User, ServiceProvider, Service, Booking, Payment, Review, Notification, ROLE_USER, ROLE_SERVICE_PROVIDER, ROLE_ADMIN
from forms import LoginForm, RegistrationForm, ServiceProviderForm, ServiceForm, BookingForm, PaymentForm, ReviewForm, SearchForm

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
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.is_admin():
                next_page = url_for('admin_dashboard')
            elif user.is_provider():
                next_page = url_for('dashboard')
            else:
                next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='تسجيل الدخول', form=form)

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
    return render_template('register.html', title='تسجيل حساب جديد', form=form)

# User Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    if current_user.is_provider():
        # Get provider's profile and services
        provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
        if not provider:
            return redirect(url_for('create_provider_profile'))
        
        services = Service.query.filter_by(provider_id=provider.id).all()
        bookings = []
        for service in services:
            service_bookings = Booking.query.filter_by(service_id=service.id).all()
            bookings.extend(service_bookings)
        
        return render_template('dashboard.html', title='لوحة التحكم', 
                              provider=provider, services=services, bookings=bookings)
    else:
        # Regular user dashboard
        bookings = Booking.query.filter_by(client_id=current_user.id).order_by(Booking.booking_date.desc()).all()
        payments = Payment.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', title='لوحة التحكم', 
                              bookings=bookings, payments=payments)

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
            website=form.website.data
        )
        db.session.add(provider)
        db.session.commit()
        flash('تم إنشاء ملف مقدم الخدمة بنجاح!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('profile.html', title='إنشاء ملف مقدم الخدمة', form=form)

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
    form = ServiceForm()
    # تهيئة النموذج للحصول على أنواع الخدمات
    types = form.service_types.get(category, [('', 'اختر نوع الخدمة')])
    return jsonify(types)

# Add Service
@app.route('/services/add', methods=['GET', 'POST'])
@login_required
def add_service():
    if not current_user.is_provider():
        flash('عذراً، هذه الصفحة مخصصة لمقدمي الخدمات فقط.', 'warning')
        return redirect(url_for('index'))
    
    provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
    if not provider:
        flash('الرجاء إكمال ملف مقدم الخدمة أولاً.', 'warning')
        return redirect(url_for('create_provider_profile'))
    
    form = ServiceForm()
    
    # تحديث اختيارات نوع الخدمة عند تغيير الفئة
    if request.method == 'GET' and request.args.get('category'):
        category = request.args.get('category')
        form.service_type.choices = form.service_types.get(category, [('', 'اختر نوع الخدمة')])
    
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
    
    return render_template('service_form.html', form=form)

# Edit Service
@app.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    provider = ServiceProvider.query.get(service.provider_id)
    
    # Verify ownership
    if provider.user_id != current_user.id and not current_user.is_admin():
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
        
        # تحديد حالة الدفع بناءً على طريقة الدفع المختارة
        payment_status = 'pending'
        if form.payment_method.data == 'cash':
            payment_status = 'awaiting_confirmation'
        
        # Create a payment record
        payment = Payment(
            booking_id=booking.id,
            user_id=current_user.id,
            amount=service.price,
            status=payment_status,
            payment_method=form.payment_method.data
        )
        
        # إذا كانت طريقة الدفع بالبطاقة، قم بتخزين تفاصيل البطاقة
        if form.payment_method.data in ['credit_card', 'debit_card']:
            # في بيئة الإنتاج الحقيقية، يجب استخدام خدمة دفع آمنة مثل Stripe بدلاً من تخزين تفاصيل البطاقة
            payment.transaction_id = f"TR-{uuid.uuid4().hex[:8]}"  # إنشاء معرف معاملة وهمي
            
            # في حالة نجاح الدفع، نقوم بتحديث حالة الدفع وتاريخه
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()
            
            # تحديث حالة الحجز إلى مؤكد
            booking.status = 'confirmed'
        
        db.session.add(payment)
        db.session.commit()
        
        # إنشاء إشعار للمستخدم
        create_notification(
            current_user.id,
            "تم إنشاء الحجز بنجاح",
            f"تم إنشاء حجز لخدمة {service.name} بتاريخ {booking.booking_date.strftime('%Y-%m-%d %H:%M')}",
            "success",
            booking.id,
            "booking"
        )
        
        # إنشاء إشعار لمقدم الخدمة
        provider = ServiceProvider.query.get(service.provider_id)
        create_notification(
            provider.user_id,
            "حجز جديد",
            f"لديك طلب حجز جديد لخدمة {service.name} من المستخدم {current_user.username}",
            "info",
            booking.id,
            "booking"
        )
        
        if payment.status == 'completed':
            flash('تم تأكيد الحجز وإتمام عملية الدفع بنجاح!', 'success')
            return redirect(url_for('dashboard'))
        elif payment.status == 'awaiting_confirmation':
            flash('تم إنشاء الحجز بنجاح! سيتم تأكيده بعد الدفع نقدًا عند الاستلام.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('تم إنشاء الحجز بنجاح! الرجاء إكمال عملية الدفع.', 'info')
            return redirect(url_for('payment', payment_id=payment.id))
    
    flash('حدث خطأ أثناء إنشاء الحجز. الرجاء المحاولة مرة أخرى.', 'danger')
    return redirect(url_for('services'))

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

# Add review
@app.route('/review', methods=['POST'])
@login_required
def add_review():
    form = ReviewForm()
    if form.validate_on_submit():
        service_id = form.service_id.data
        
        # Check if user has booked this service before
        user_bookings = Booking.query.filter_by(client_id=current_user.id, service_id=service_id).first()
        if not user_bookings:
            flash('يمكنك فقط تقييم الخدمات التي قمت بحجزها.', 'warning')
            return redirect(url_for('service_details', service_id=service_id))
        
        # Check if user has already reviewed this service
        existing_review = Review.query.filter_by(user_id=current_user.id, service_id=service_id).first()
        if existing_review:
            flash('لقد قمت بتقييم هذه الخدمة بالفعل.', 'warning')
            return redirect(url_for('service_details', service_id=service_id))
        
        review = Review(
            service_id=service_id,
            user_id=current_user.id,
            rating=form.rating.data,
            comment=form.comment.data
        )
        db.session.add(review)
        
        # Update service rating
        service = Service.query.get(service_id)
        all_reviews = Review.query.filter_by(service_id=service_id).all()
        total_rating = sum(r.rating for r in all_reviews) + form.rating.data
        new_rating = total_rating / (len(all_reviews) + 1)
        
        provider = ServiceProvider.query.get(service.provider_id)
        provider.rating = new_rating
        
        db.session.commit()
        flash('شكراً على تقييمك!', 'success')
        
    return redirect(url_for('service_details', service_id=form.service_id.data))

# Admin Dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))
    
    users_count = User.query.count()
    providers_count = ServiceProvider.query.count()
    services_count = Service.query.count()
    bookings_count = Booking.query.count()
    payments_count = Payment.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', title='لوحة تحكم المدير',
                          users_count=users_count, providers_count=providers_count,
                          services_count=services_count, bookings_count=bookings_count,
                          payments_count=payments_count, recent_users=recent_users,
                          recent_bookings=recent_bookings)

# Admin - Users
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/users.html', title='إدارة المستخدمين', users=users)

# Admin - Services
@app.route('/admin/services')
@login_required
def admin_services():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))
    
    services = Service.query.all()
    return render_template('admin/services.html', title='إدارة الخدمات', services=services)

# Admin - Bookings
@app.route('/admin/bookings')
@login_required
def admin_bookings():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))
    
    bookings = Booking.query.all()
    return render_template('admin/bookings.html', title='إدارة الحجوزات', bookings=bookings)

# Admin - Payments
@app.route('/admin/payments')
@login_required
def admin_payments():
    if not current_user.is_admin():
        flash('عذراً، هذه الصفحة مخصصة للمشرفين فقط.', 'warning')
        return redirect(url_for('index'))
    
    payments = Payment.query.all()
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
    
    # التحقق من أن المستخدم هو مزود الخدمة المرتبط بالحجز
    service = Service.query.get(booking.service_id)
    provider = ServiceProvider.query.get(service.provider_id)
    
    if provider.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية إدارة هذا الحجز'})
    
    # تنفيذ الإجراء المطلوب
    if action == 'confirm':
        booking.status = 'confirmed'
        message = 'تم تأكيد الحجز بنجاح'
        
        # إنشاء إشعار للعميل
        create_notification(
            booking.client_id,
            "تم تأكيد الحجز",
            f"تم تأكيد حجزك للخدمة {service.name} بتاريخ {booking.booking_date.strftime('%Y-%m-%d %H:%M')}",
            "success",
            booking.id,
            "booking"
        )
    
    elif action == 'cancel':
        booking.status = 'cancelled'
        message = 'تم إلغاء الحجز بنجاح'
        
        # إعادة تعيين حالة الدفع إذا كانت موجودة
        if booking.payment:
            booking.payment.status = 'cancelled'
        
        # إنشاء إشعار للعميل
        create_notification(
            booking.client_id,
            "تم إلغاء الحجز",
            f"تم إلغاء حجزك للخدمة {service.name} بتاريخ {booking.booking_date.strftime('%Y-%m-%d %H:%M')}",
            "danger",
            booking.id,
            "booking"
        )
    
    elif action == 'complete':
        booking.status = 'completed'
        message = 'تم تعليم الحجز كمكتمل'
        
        # إنشاء إشعار للعميل
        create_notification(
            booking.client_id,
            "تم إكمال الخدمة",
            f"تم إكمال تقديم الخدمة {service.name}. نأمل أن تكون راضياً عن الخدمة. يمكنك الآن تقييم الخدمة.",
            "info",
            booking.id,
            "booking"
        )
        
        # إرسال إشعار للتقييم
        send_review_notification(booking.id)
    
    else:
        return jsonify({'success': False, 'message': 'إجراء غير صالح'})
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': message,
        'status': booking.status
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
        payment.status = 'completed'
        payment.payment_date = datetime.utcnow()
        
        # تحديث حالة الحجز إلى مؤكد
        booking.status = 'confirmed'
        
        # إنشاء إشعار للعميل
        create_notification(
            booking.client_id,
            "تم تأكيد الدفع",
            f"تم تأكيد دفعك للخدمة {service.name} وتأكيد الحجز بنجاح",
            "success",
            payment.id,
            "payment"
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تأكيد استلام الدفع بنجاح',
            'status': payment.status
        })
    else:
        return jsonify({'success': False, 'message': 'لا يمكن تأكيد هذا الدفع في حالته الحالية'})

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
            mimetype='application/sql'
        )
    else:
        flash('حدث خطأ أثناء تصدير قاعدة البيانات. الرجاء المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('admin_dashboard'))

# =============== Mobile Application Routes =============== #

# Mobile Home Page
@app.route('/mobile/')
@app.route('/mobile/index')
def mobile_index():
    featured_services = Service.query.filter_by(is_active=True).order_by(Service.id.desc()).limit(6).all()
    recent_services = Service.query.filter_by(is_active=True).order_by(Service.created_at.desc()).limit(6).all()
    return render_template('mobile/index.html', featured_services=featured_services, recent_services=recent_services)

# Mobile Services Page
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
    review_form = ReviewForm()
    
    return render_template('mobile/service_details.html', service=service, review_form=review_form)

# Mobile Dashboard
@app.route('/mobile/dashboard')
@login_required
def mobile_dashboard():
    if current_user.is_provider():
        # Provider Dashboard
        provider = ServiceProvider.query.filter_by(user_id=current_user.id).first()
        if not provider:
            return redirect(url_for('create_provider_profile'))
        
        services = Service.query.filter_by(provider_id=provider.id).all()
        active_services_count = Service.query.filter_by(provider_id=provider.id, is_active=True).count()
        
        # Get provider bookings
        bookings = []
        for service in services:
            service_bookings = Booking.query.filter_by(service_id=service.id).all()
            bookings.extend(service_bookings)
            
        pending_bookings_count = sum(1 for b in bookings if b.status == 'pending')
        completed_bookings_count = sum(1 for b in bookings if b.status == 'completed')
        recent_bookings = sorted(bookings, key=lambda x: x.booking_date, reverse=True)[:5]
        provider_rating = provider.rating
        
        return render_template('mobile/dashboard.html',
                              provider=provider,
                              services=services,
                              bookings=bookings,
                              active_services_count=active_services_count,
                              pending_bookings_count=pending_bookings_count,
                              completed_bookings_count=completed_bookings_count,
                              recent_bookings=recent_bookings,
                              provider_rating=provider_rating,
                              review_form=ReviewForm())
    else:
        # User Dashboard
        bookings = Booking.query.filter_by(client_id=current_user.id).order_by(Booking.booking_date.desc()).all()
        pending_bookings_count = Booking.query.filter_by(client_id=current_user.id, status='pending').count()
        completed_bookings_count = Booking.query.filter_by(client_id=current_user.id, status='completed').count()
        recent_bookings = Booking.query.filter_by(client_id=current_user.id).order_by(Booking.booking_date.desc()).limit(5).all()
        reviews = Review.query.filter_by(user_id=current_user.id).all()
        
        return render_template('mobile/dashboard.html',
                              bookings=bookings,
                              pending_bookings_count=pending_bookings_count,
                              completed_bookings_count=completed_bookings_count,
                              recent_bookings=recent_bookings,
                              reviews=reviews,
                              review_form=ReviewForm())

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

