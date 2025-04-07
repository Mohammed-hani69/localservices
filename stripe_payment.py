import os
import stripe
from datetime import datetime
from flask import url_for
import uuid

from models import db, Payment, Booking, Service, User
from notifications import create_notification

# تكوين مفتاح API الخاص بـ Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def get_domain_url():
    """الحصول على مجال الموقع بناءً على المتغيرات البيئية"""
    if os.environ.get('REPLIT_DEPLOYMENT'):
        return os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
    elif os.environ.get('REPLIT_DOMAINS'):
        domains = os.environ.get('REPLIT_DOMAINS', '')
        if domains:
            return domains.split(',')[0]
    return 'localhost:5000'

def create_checkout_session(booking_id, user):
    """إنشاء جلسة دفع باستخدام Stripe"""
    booking = Booking.query.get(booking_id)
    if not booking:
        return None, "الحجز غير موجود"
    
    service = Service.query.get(booking.service_id)
    if not service:
        return None, "الخدمة غير موجودة"
    
    # التحقق من عدم وجود دفع مسبق لهذا الحجز
    existing_payment = Payment.query.filter_by(booking_id=booking_id).first()
    if existing_payment and existing_payment.status in ['completed', 'processing']:
        return None, f"يوجد بالفعل دفع لهذا الحجز بحالة: {existing_payment.status}"
    
    # إنشاء معرّف فريد للمعاملة
    transaction_id = str(uuid.uuid4())
    
    # حساب المبلغ بالهللات (Stripe يتطلب المبلغ بأصغر وحدة عملة)
    amount_in_cents = int(service.price * 100)  # تحويل الريال إلى هللة
    
    try:
        # إنشاء جلسة دفع جديدة
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'sar',
                        'product_data': {
                            'name': service.name,
                            'description': service.description[:255] if service.description else '',
                            'images': [f"https://{get_domain_url()}/static/uploads/{service.image}"] if service.image else [],
                        },
                        'unit_amount': amount_in_cents,
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                'booking_id': booking_id,
                'user_id': user.id,
                'service_id': service.id,
                'transaction_id': transaction_id
            },
            mode='payment',
            success_url=f"https://{get_domain_url()}{url_for('payment_success')}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"https://{get_domain_url()}{url_for('payment_cancel')}?booking_id={booking_id}",
        )
        
        # إنشاء سجل الدفع في قاعدة البيانات
        payment = Payment(
            booking_id=booking_id,
            user_id=user.id,
            amount=service.price,
            currency='SAR',
            status='processing',
            payment_method='stripe',
            transaction_id=transaction_id,
            created_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()
        
        # إرسال إشعار بالدفع
        create_notification(
            user.id,
            "بدء عملية الدفع",
            f"تم بدء عملية الدفع للخدمة {service.name}. يرجى إكمال العملية.",
            "info",
            payment.id,
            "payment"
        )
        
        return checkout_session, None
    except Exception as e:
        # في حالة حدوث خطأ
        return None, f"حدث خطأ أثناء إنشاء جلسة الدفع: {str(e)}"

def verify_payment_session(session_id):
    """التحقق من حالة الدفع باستخدام معرّف الجلسة"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
        
        transaction_id = session.metadata.get('transaction_id')
        booking_id = int(session.metadata.get('booking_id'))
        
        # تحديث سجل الدفع
        payment = Payment.query.filter_by(transaction_id=transaction_id).first()
        if not payment:
            return False, "لم يتم العثور على سجل الدفع"
        
        if payment_intent.status == 'succeeded':
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()
            
            # تحديث حالة الحجز
            booking = Booking.query.get(booking_id)
            if booking:
                booking.status = 'confirmed'
            
            # إنشاء إشعار بنجاح الدفع
            service = Service.query.get(booking.service_id)
            create_notification(
                payment.user_id,
                "تم الدفع بنجاح",
                f"تم دفع مبلغ {payment.amount} {payment.currency} مقابل الخدمة {service.name} بنجاح.",
                "success",
                payment.id,
                "payment"
            )
            
            # إرسال إشعار إلى مزود الخدمة
            provider_id = service.provider.user_id
            create_notification(
                provider_id,
                "تم استلام دفع جديد",
                f"تم استلام دفع جديد بقيمة {payment.amount} {payment.currency} لحجز الخدمة {service.name}.",
                "success",
                payment.id,
                "payment"
            )
            
            db.session.commit()
            return True, "تم التحقق من الدفع بنجاح"
        else:
            payment.status = 'failed'
            db.session.commit()
            return False, f"حالة الدفع: {payment_intent.status}"
    except Exception as e:
        return False, f"حدث خطأ أثناء التحقق من الدفع: {str(e)}"

def get_payment_status(payment_id):
    """الحصول على حالة الدفع من قاعدة البيانات"""
    payment = Payment.query.get(payment_id)
    if not payment:
        return None, "لم يتم العثور على سجل الدفع"
    
    return payment, None

def cancel_payment(payment_id):
    """إلغاء الدفع"""
    payment = Payment.query.get(payment_id)
    if not payment:
        return False, "لم يتم العثور على سجل الدفع"
    
    if payment.status in ['completed', 'refunded']:
        return False, "لا يمكن إلغاء دفع مكتمل أو مسترد"
    
    payment.status = 'cancelled'
    
    # تحديث حالة الحجز
    booking = Booking.query.get(payment.booking_id)
    if booking:
        booking.status = 'cancelled'
    
    # إشعار العميل بالإلغاء
    create_notification(
        payment.user_id,
        "تم إلغاء الدفع",
        "تم إلغاء عملية الدفع الخاصة بك.",
        "warning",
        payment.id,
        "payment"
    )
    
    db.session.commit()
    return True, "تم إلغاء الدفع بنجاح"