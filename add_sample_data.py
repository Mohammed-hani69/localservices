from app import app, db
from models import User, ServiceProvider, Service
from werkzeug.security import generate_password_hash
import json

def create_sample_data():
    # إنشاء مستخدمين ومقدمي خدمات
    providers_data = [
        {
            "username": "maintenance_pro",
            "email": "maintenance@example.com",
            "password": "Pass123!",
            "phone": "0501234567",
            "address": "الرياض - حي النزهة",
            "provider": {
                "company_name": "شركة الصيانة المتكاملة",
                "description": "نقدم خدمات صيانة متكاملة للمنازل والمكاتب",
                "specialization": "صيانة",
                "website": "www.maintenance-pro.com"
            },
            "services": [
                {
                    "name": "صيانة أجهزة التكييف",
                    "description": "صيانة وإصلاح جميع أنواع المكيفات",
                    "price": 150.0,
                    "duration": 60,
                    "category": "صيانة",
                    "service_type": "تكييف",
                    "is_active": True,
                    "additional_info": json.dumps({
                        "tools_provided": True,
                        "has_warranty": True,
                        "warranty_period": "3 شهور",
                        "emergency_service": True,
                        "experience_years": 5
                    })
                },
                {
                    "name": "صيانة الأجهزة المنزلية",
                    "description": "إصلاح الثلاجات والغسالات وغيرها",
                    "price": 100.0,
                    "duration": 45,
                    "category": "صيانة",
                    "service_type": "أجهزة",
                    "is_active": True,
                    "additional_info": json.dumps({
                        "tools_provided": True,
                        "has_warranty": True,
                        "warranty_period": "شهر",
                        "emergency_service": False,
                        "experience_years": 3
                    })
                }
            ]
        },
        {
            "username": "clean_expert",
            "email": "cleaning@example.com",
            "password": "Pass123!",
            "phone": "0502345678",
            "address": "الرياض - حي الملز",
            "provider": {
                "company_name": "شركة النظافة المثالية",
                "description": "خدمات تنظيف احترافية للمنازل والمكاتب",
                "specialization": "تنظيف",
                "website": "www.clean-expert.com"
            },
            "services": [
                {
                    "name": "تنظيف منازل شامل",
                    "description": "تنظيف شامل للمنازل مع التعقيم",
                    "price": 300.0,
                    "duration": 180,
                    "category": "تنظيف",
                    "service_type": "منزلي",
                    "is_active": True,
                    "additional_info": json.dumps({
                        "materials_included": True,
                        "equipment_provided": True,
                        "eco_friendly": True,
                        "min_area": 100,
                        "max_area": 500
                    })
                }
            ]
        },
        {
            "username": "edu_teacher",
            "email": "education@example.com",
            "password": "Pass123!",
            "phone": "0503456789",
            "address": "الرياض - حي السليمانية",
            "provider": {
                "company_name": "مركز التعليم المتميز",
                "description": "دروس خصوصية في جميع المواد",
                "specialization": "تعليم",
                "website": "www.edu-teacher.com"
            },
            "services": [
                {
                    "name": "دروس رياضيات",
                    "description": "دروس خصوصية في الرياضيات لجميع المراحل",
                    "price": 100.0,
                    "duration": 60,
                    "category": "تعليم",
                    "service_type": "رياضيات",
                    "is_active": True,
                    "additional_info": json.dumps({
                        "education_level": "جميع المراحل",
                        "teaching_method": "حضوري وأونلاين",
                        "years_experience": 5,
                        "max_students": 3
                    })
                }
            ]
        },
        {
            "username": "health_care",
            "email": "health@example.com",
            "password": "Pass123!",
            "phone": "0504567890",
            "address": "الرياض - حي الورود",
            "provider": {
                "company_name": "عيادة الصحة والعافية",
                "description": "خدمات صحية متكاملة",
                "specialization": "صحة",
                "website": "www.health-care.com"
            },
            "services": [
                {
                    "name": "استشارات طبية عامة",
                    "description": "استشارات طبية عامة مع طبيب متخصص",
                    "price": 200.0,
                    "duration": 30,
                    "category": "صحة",
                    "service_type": "استشارات",
                    "is_active": True,
                    "additional_info": json.dumps({
                        "specialization": "طب عام",
                        "medical_license": "12345",
                        "consultation_type": "حضوري وعن بعد",
                        "languages": ["العربية", "الإنجليزية"]
                    })
                }
            ]
        },
        {
            "username": "food_master",
            "email": "food@example.com",
            "password": "Pass123!",
            "phone": "0505678901",
            "address": "الرياض - حي العليا",
            "provider": {
                "company_name": "مطبخ الذواقة",
                "description": "نقدم ألذ المأكولات والحلويات",
                "specialization": "طعام",
                "website": "www.food-master.com"
            },
            "services": [
                {
                    "name": "وجبات منزلية",
                    "description": "تحضير وجبات منزلية صحية",
                    "price": 80.0,
                    "duration": 60,
                    "category": "طعام",
                    "service_type": "وجبات",
                    "is_active": True,
                    "additional_info": json.dumps({
                        "delivery_available": True,
                        "min_order_quantity": 1,
                        "preparation_time": "60 دقيقة",
                        "vegetarian_options": True,
                        "vegan_options": False,
                        "catering_service": True,
                        "dietary_info": "متوفر خيارات صحية"
                    })
                }
            ]
        }
    ]

    with app.app_context():
        # إضافة البيانات
        for provider_data in providers_data:
            # إنشاء المستخدم
            user = User(
                username=provider_data["username"],
                email=provider_data["email"],
                password_hash=generate_password_hash(provider_data["password"]),
                phone=provider_data["phone"],
                address=provider_data["address"],
                role=1  # مقدم خدمة
            )
            db.session.add(user)
            db.session.flush()  # للحصول على user.id

            # إنشاء مقدم الخدمة
            provider = ServiceProvider(
                user_id=user.id,
                company_name=provider_data["provider"]["company_name"],
                description=provider_data["provider"]["description"],
                specialization=provider_data["provider"]["specialization"],
                website=provider_data["provider"]["website"]
            )
            db.session.add(provider)
            db.session.flush()  # للحصول على provider.id

            # إضافة الخدمات
            for service_data in provider_data["services"]:
                service = Service(
                    provider_id=provider.id,
                    **service_data
                )
                db.session.add(service)

        db.session.commit()
        print("تم إضافة البيانات التجريبية بنجاح!")

if __name__ == "__main__":
    create_sample_data()