import sqlite3

def add_specialization_column():
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect('instance/local_services.db')
        cursor = conn.cursor()
        
        # التحقق من وجود العمود
        cursor.execute("PRAGMA table_info(service_provider)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # إضافة العمود إذا لم يكن موجوداً
        if 'specialization' not in column_names:
            cursor.execute("ALTER TABLE service_provider ADD COLUMN specialization TEXT DEFAULT 'أخرى'")
            conn.commit()
            print("تم إضافة عمود التخصص بنجاح!")
        else:
            print("عمود التخصص موجود بالفعل.")
        
        # إغلاق الاتصال
        conn.close()
        return True
    except Exception as e:
        print(f"حدث خطأ: {str(e)}")
        return False

if __name__ == "__main__":
    add_specialization_column()
