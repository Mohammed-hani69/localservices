import os
import subprocess
from datetime import datetime

def export_database():
    """إنشاء نسخة احتياطية من قاعدة البيانات كملف SQL"""
    # الحصول على متغيرات البيئة لقاعدة البيانات
    db_host = os.environ.get('PGHOST')
    db_port = os.environ.get('PGPORT')
    db_name = os.environ.get('PGDATABASE')
    db_user = os.environ.get('PGUSER')
    db_password = os.environ.get('PGPASSWORD')
    
    # إنشاء مجلد للنسخ الاحتياطية إذا لم يكن موجودًا
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # إنشاء اسم الملف بناءً على التاريخ والوقت الحاليين
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backups/database_backup_{timestamp}.sql"
    
    # استخدام pg_dump لإنشاء نسخة احتياطية
    try:
        # تعيين متغير بيئة كلمة المرور لـ pg_dump
        env = os.environ.copy()
        if db_password is not None:
            env['PGPASSWORD'] = db_password
        
        # التأكد من وجود جميع متغيرات البيئة اللازمة
        if not all([db_host, db_port, db_user, db_name]):
            print("بعض متغيرات البيئة المطلوبة غير موجودة!")
            return None
            
        # تنفيذ أمر pg_dump
        command = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '-f', backup_file,
            '--format=p',  # نص عادي
            '--no-owner'   # لا تضمين معلومات المالك
        ]
        
        process = subprocess.run(command, env=env, check=True, capture_output=True)
        
        # إذا نجحت العملية، أعد مسار الملف
        if process.returncode == 0:
            return backup_file
        else:
            print("خطأ أثناء إنشاء النسخة الاحتياطية:")
            print(process.stderr.decode())
            return None
            
    except Exception as e:
        print(f"حدث خطأ: {str(e)}")
        return None

if __name__ == "__main__":
    backup_file = export_database()
    if backup_file:
        print(f"تم إنشاء النسخة الاحتياطية بنجاح: {backup_file}")
    else:
        print("فشل إنشاء النسخة الاحتياطية")