import os
import logging
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
from flask import request
from app import app, db
from models import Booking, User, Service, Notification

# تكوين متغيرات البيئة
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = 'no-reply@localservices.com'  # يمكن تغييره إلى بريد إلكتروني حقيقي

def create_notification(user_id, title, content, notification_type='info', related_id=None, related_type=None):
    """إنشاء إشعار جديد للمستخدم"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            related_id=related_id,
            related_type=related_type,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        logging.info(f"تم إنشاء إشعار جديد للمستخدم {user_id}: {title}")
        return notification
    except Exception as e:
        logging.error(f"خطأ في إنشاء الإشعار: {str(e)}")
        db.session.rollback()
        return None

def send_email(to_email, subject, html_content):
    """إرسال بريد إلكتروني باستخدام SendGrid"""
    try:
        if not SENDGRID_API_KEY:
            logging.error("مفتاح SendGrid API غير متوفر. تعذر إرسال البريد الإلكتروني.")
            return False
        
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code >= 200 and response.status_code < 300:
            logging.info(f"تم إرسال البريد الإلكتروني بنجاح إلى {to_email}")
            return True
        else:
            logging.error(f"فشل إرسال البريد الإلكتروني: {response.status_code}, {response.body}")
            return False
        
    except Exception as e:
        logging.error(f"خطأ في إرسال البريد الإلكتروني: {str(e)}")
        return False

def send_review_notification(booking_id):
    """إرسال إشعار للمستخدم لتقييم الخدمة بعد انتهاء الموعد"""
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            logging.error(f"الحجز رقم {booking_id} غير موجود.")
            return False
        
        # التحقق من انتهاء الموعد
        now = datetime.utcnow()
        if booking.booking_date + timedelta(minutes=booking.service.duration) > now:
            logging.info(f"الموعد رقم {booking_id} لم ينته بعد.")
            return False
        
        # التحقق من حالة الحجز - يجب أن يكون مؤكدًا أو مكتملًا
        if booking.status not in ['confirmed', 'completed']:
            logging.info(f"حالة الحجز {booking.status} غير مناسبة لإرسال إشعار التقييم.")
            return False
        
        user = User.query.get(booking.client_id)
        service = Service.query.get(booking.service_id)
        
        # التحقق مما إذا كان المستخدم قام بالتقييم بالفعل
        from models import Review
        existing_review = Review.query.filter_by(
            user_id=booking.client_id,
            service_id=booking.service_id
        ).first()
        
        if existing_review:
            logging.info(f"المستخدم {user.id} قام بالفعل بتقييم الخدمة {service.id}.")
            return False
        
        # إنشاء رابط التقييم - إما لصفحة التفاصيل أو للوحة التحكم
        dashboard_url = f"{request.host_url}dashboard"
        service_url = f"{request.host_url}services/{service.id}"
        
        # إنشاء إشعار داخلي في الموقع
        notification_title = f"🌟 قيّم تجربتك مع {service.name}"
        notification_content = (
            f"نأمل أن تكون قد استمتعت بخدمة {service.name}. "
            f"يمكنك الآن تقييم الخدمة من خلال الضغط على زر 'تقييم' في قائمة الحجوزات."
        )
        
        notification = create_notification(
            user_id=user.id,
            title=notification_title,
            content=notification_content,
            notification_type='info',
            related_id=booking.id,
            related_type='review_reminder'
        )
        
        if notification:
            logging.info(f"تم إنشاء إشعار تقييم بنجاح للمستخدم {user.id}، للحجز {booking_id}")
        
        # إنشاء محتوى البريد الإلكتروني
        subject = notification_title
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; direction: rtl; text-align: right; }}
                .container {{ padding: 20px; border: 1px solid #eee; border-radius: 10px; }}
                .header {{ color: #4361ee; font-size: 24px; margin-bottom: 20px; }}
                .button {{ background-color: #4361ee; color: white; padding: 10px 20px; text-decoration: none;
                        border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 15px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                .highlight {{ color: #4361ee; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">تقييم الخدمة</div>
                
                <p>مرحباً <span class="highlight">{user.username}</span>،</p>
                
                <p>نأمل أن تكون قد استمتعت بخدمة <strong>{service.name}</strong> التي حجزتها.</p>
                
                <p>تقييمك يساعدنا على تحسين خدماتنا ويساعد المستخدمين الآخرين على اتخاذ قرارات أفضل.</p>
                
                <p>يمكنك تقييم الخدمة بسهولة من خلال:</p>
                <ol>
                  <li>الدخول إلى صفحة الحجوزات الخاصة بك</li>
                  <li>البحث عن حجز خدمة {service.name}</li>
                  <li>النقر على زر "تقييم" الموجود أسفل بطاقة الحجز</li>
                </ol>
                
                <div style="text-align: center; margin: 20px 0;">
                  <a href="{dashboard_url}" class="button">الذهاب إلى لوحة التحكم</a>
                </div>
                
                <p>أو يمكنك زيارة صفحة الخدمة مباشرة والتقييم من هناك:</p>
                
                <div style="text-align: center; margin: 20px 0;">
                  <a href="{service_url}" class="button">عرض تفاصيل الخدمة</a>
                </div>
                
                <p>شكراً لثقتك بنا ولاستخدامك منصتنا!</p>
                
                <div class="footer">
                    هذا بريد إلكتروني تلقائي، يرجى عدم الرد عليه.
                </div>
            </div>
        </body>
        </html>
        """
        
        # إرسال البريد الإلكتروني إذا كان مفعلاً
        email_sent = send_email(user.email, subject, html_content)
        if email_sent:
            logging.info(f"تم إرسال بريد إلكتروني للمستخدم {user.id} لتقييم الخدمة {service.id}")
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في إرسال إشعار التقييم: {str(e)}")
        return False

def check_completed_bookings():
    """التحقق من الحجوزات المكتملة وإرسال إشعارات التقييم"""
    try:
        # البحث عن الحجوزات المؤكدة التي انتهت ولم يتم تقييمها بعد
        now = datetime.utcnow()
        completed_bookings = Booking.query.filter(
            Booking.status.in_(['confirmed', 'completed']),
            Booking.booking_date <= now
        ).all()
        
        notifications_sent = 0
        
        for booking in completed_bookings:
            # التحقق مما إذا كان وقت الخدمة قد انتهى
            service = Service.query.get(booking.service_id)
            end_time = booking.booking_date + timedelta(minutes=service.duration)
            
            if end_time <= now:
                # تغيير حالة الحجز إلى مكتملة إذا كان مؤكدًا
                if booking.status == 'confirmed':
                    booking.status = 'completed'
                    
                    # إنشاء إشعار للعميل بإكمال الخدمة
                    create_notification(
                        user_id=booking.client_id,
                        title="تم إكمال الخدمة",
                        content=f"تم إكمال خدمة {service.name} بنجاح. نشكرك على استخدام منصتنا.",
                        notification_type="success",
                        related_id=booking.id,
                        related_type="booking"
                    )
                    
                    # إنشاء إشعار لمزود الخدمة بإكمال الخدمة
                    provider = ServiceProvider.query.get(service.provider_id)
                    create_notification(
                        user_id=provider.user_id,
                        title="تم إكمال الخدمة",
                        content=f"تم إكمال خدمة {service.name} بنجاح للعميل.",
                        notification_type="success",
                        related_id=booking.id,
                        related_type="booking"
                    )
                    
                    notifications_sent += 2
                    db.session.commit()
                
                # التحقق مما إذا كان المستخدم قام بالتقييم بالفعل
                from models import Review
                existing_review = Review.query.filter_by(
                    user_id=booking.client_id,
                    service_id=booking.service_id
                ).first()
                
                if not existing_review:
                    # إرسال إشعار التقييم إذا لم يتم إرسال إشعار في الـ 24 ساعة الماضية
                    last_notification = Notification.query.filter_by(
                        user_id=booking.client_id,
                        related_id=booking.id,
                        related_type="review_reminder"
                    ).order_by(Notification.created_at.desc()).first()
                    
                    # التحقق إذا لم يسبق إرسال إشعار أو إذا كان الإشعار الأخير قبل أكثر من 24 ساعة
                    if not last_notification or (now - last_notification.created_at > timedelta(hours=24)):
                        send_review_notification(booking.id)
                        notifications_sent += 1
        
        logging.info(f"تم إرسال {notifications_sent} إشعارات لحجوزات مكتملة")
        return True
    except Exception as e:
        logging.error(f"خطأ في التحقق من الحجوزات المكتملة: {str(e)}")
        return False