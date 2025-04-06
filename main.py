import threading
import time
import logging
from app import app, db
from notifications import check_completed_bookings

# إعداد التسجيل للأخطاء
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# مهمة خلفية للتحقق من الحجوزات المكتملة وإرسال إشعارات التقييم
def notifications_background_task():
    with app.app_context():
        try:
            while True:
                logger.info("جاري التحقق من الحجوزات المكتملة...")
                check_completed_bookings()
                # انتظار ساعة قبل التحقق مرة أخرى (3600 ثانية)
                time.sleep(3600)
        except Exception as e:
            logger.error(f"خطأ في المهمة الخلفية للإشعارات: {str(e)}")

# بدء المهمة الخلفية
def start_background_tasks():
    notifications_thread = threading.Thread(target=notifications_background_task)
    notifications_thread.daemon = True  # سيتم إيقاف المهمة عند إيقاف التطبيق الرئيسي
    notifications_thread.start()
    logger.info("تم بدء المهمة الخلفية للإشعارات")

if __name__ == "__main__":
    # بدء المهام الخلفية
    start_background_tasks()
    # بدء تشغيل التطبيق
    app.run(host="0.0.0.0", port=5000, debug=True)
