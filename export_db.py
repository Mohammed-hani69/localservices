import json
import os
from datetime import datetime
from models import User, ServiceProvider, Service, Booking, Payment, Review, Notification
from database import db

def export_database():
    """إنشاء نسخة احتياطية من قاعدة البيانات كملف JSON"""
    try:
        # إنشاء مجلد للنسخ الاحتياطية إذا لم يكن موجودًا
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        # إنشاء اسم الملف بناءً على التاريخ والوقت الحاليين
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backups/database_backup_{timestamp}.json"
        
        # جمع البيانات من قاعدة البيانات
        data = {
            'users': [],
            'service_providers': [],
            'services': [],
            'bookings': [],
            'payments': [],
            'reviews': [],
            'notifications': []
        }
        
        # استخراج بيانات المستخدمين (دون كلمات المرور)
        users = User.query.all()
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'address': user.address,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            data['users'].append(user_data)
        
        # استخراج بيانات مقدمي الخدمات
        providers = ServiceProvider.query.all()
        for provider in providers:
            provider_data = {
                'id': provider.id,
                'user_id': provider.user_id,
                'company_name': provider.company_name,
                'description': provider.description,
                'logo': provider.logo,
                'website': provider.website,
                'verified': provider.verified,
                'rating': provider.rating,
                'created_at': provider.created_at.isoformat() if provider.created_at else None
            }
            data['service_providers'].append(provider_data)
        
        # استخراج بيانات الخدمات
        services = Service.query.all()
        for service in services:
            service_data = {
                'id': service.id,
                'provider_id': service.provider_id,
                'name': service.name,
                'description': service.description,
                'price': service.price,
                'duration': service.duration,
                'category': service.category,
                'service_type': service.service_type,
                'is_active': service.is_active,
                'image': service.image,
                'additional_info': service.additional_info,
                'created_at': service.created_at.isoformat() if service.created_at else None
            }
            data['services'].append(service_data)
        
        # استخراج بيانات الحجوزات
        bookings = Booking.query.all()
        for booking in bookings:
            booking_data = {
                'id': booking.id,
                'client_id': booking.client_id,
                'service_id': booking.service_id,
                'booking_date': booking.booking_date.isoformat() if booking.booking_date else None,
                'status': booking.status,
                'notes': booking.notes,
                'created_at': booking.created_at.isoformat() if booking.created_at else None
            }
            data['bookings'].append(booking_data)
        
        # استخراج بيانات المدفوعات
        payments = Payment.query.all()
        for payment in payments:
            payment_data = {
                'id': payment.id,
                'booking_id': payment.booking_id,
                'user_id': payment.user_id,
                'amount': payment.amount,
                'currency': payment.currency,
                'status': payment.status,
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'created_at': payment.created_at.isoformat() if payment.created_at else None
            }
            data['payments'].append(payment_data)
        
        # استخراج بيانات التقييمات
        reviews = Review.query.all()
        for review in reviews:
            review_data = {
                'id': review.id,
                'service_id': review.service_id,
                'user_id': review.user_id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat() if review.created_at else None
            }
            data['reviews'].append(review_data)
        
        # استخراج بيانات الإشعارات
        notifications = Notification.query.all()
        for notification in notifications:
            notification_data = {
                'id': notification.id,
                'user_id': notification.user_id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'related_id': notification.related_id,
                'related_type': notification.related_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat() if notification.created_at else None
            }
            data['notifications'].append(notification_data)
        
        # حفظ البيانات المستخرجة إلى ملف JSON
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        return backup_file
    
    except Exception as e:
        print(f"حدث خطأ: {str(e)}")
        return None

if __name__ == "__main__":
    backup_file = export_database()
    if backup_file:
        print(f"تم إنشاء النسخة الاحتياطية بنجاح: {backup_file}")
    else:
        print("فشل إنشاء النسخة الاحتياطية")