from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, DateTimeField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from models import User
from wtforms.validators import URL


class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[DataRequired(), Length(min=10, max=20)])
    address = StringField('العنوان', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('نوع الحساب', choices=[(0, 'مستخدم'), (1, 'مقدم خدمة')], coerce=int, default=0)
    submit = SubmitField('تسجيل')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('هذا الاسم مستخدم بالفعل، الرجاء اختيار اسم آخر.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('هذا البريد الإلكتروني مسجل بالفعل، الرجاء استخدام بريد آخر.')

class ServiceProviderForm(FlaskForm):
    company_name = StringField('اسم الشركة أو المؤسسة', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('وصف الخدمات المقدمة', validators=[DataRequired()])
    specialization = SelectField('التخصص', choices=[
        ('صحة', 'صحة'), 
        ('تعليم', 'تعليم'), 
        ('صيانة', 'صيانة'), 
        ('تنظيف', 'تنظيف'), 
        ('طعام', 'طعام'),
        ('أخرى', 'أخرى')
    ], validators=[DataRequired()])
    website = StringField('الموقع الإلكتروني', validators=[Optional(), URL(message='الرجاء إدخال رابط صحيح')])
    submit = SubmitField('حفظ')

class BaseServiceForm(FlaskForm):
    """النموذج الأساسي للخدمات الذي ترث منه جميع النماذج المتخصصة"""
    name = StringField('اسم الخدمة', validators=[DataRequired()])
    description = TextAreaField('وصف الخدمة', validators=[DataRequired()])
    price = FloatField('السعر', validators=[DataRequired(), NumberRange(min=0)])
    duration = IntegerField('المدة (بالدقائق)', validators=[DataRequired(), NumberRange(min=5)])
    image = FileField('صورة الخدمة', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'يُسمح فقط بملفات الصور')
    ])
    additional_info = TextAreaField('معلومات إضافية')
    is_active = BooleanField('متاح', default=True)
    submit = SubmitField('إضافة الخدمة')

class ServiceForm(BaseServiceForm):
    """النموذج العام للخدمات الذي يستخدم عند عدم وجود نموذج متخصص"""
    category = SelectField('التصنيف', choices=[
        ('صيانة', 'صيانة'),
        ('تنظيف', 'تنظيف'),
        ('تعليم', 'تعليم'),
        ('صحة', 'صحة'),
        ('طعام', 'طعام'),
        ('أخرى', 'أخرى')
    ])
    service_type = SelectField('نوع الخدمة المحدد', choices=[])

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        # قائمة أنواع الخدمات حسب التصنيف
        self.service_types = {
            'صيانة': [
                ('', 'اختر نوع الخدمة'),
                ('كهرباء', 'صيانة كهربائية'),
                ('سباكة', 'صيانة سباكة'),
                ('تكييف', 'صيانة تكييف'),
                ('أجهزة', 'صيانة أجهزة منزلية'),
                ('حاسوب', 'صيانة حاسوب'),
                ('أخرى', 'أنواع أخرى')
            ],
            'تنظيف': [
                ('', 'اختر نوع الخدمة'),
                ('منزلي', 'تنظيف منزلي'),
                ('مكتبي', 'تنظيف مكاتب'),
                ('سجاد', 'تنظيف سجاد'),
                ('واجهات', 'تنظيف واجهات'),
                ('سيارات', 'تنظيف سيارات'),
                ('أخرى', 'أنواع أخرى')
            ],
            'تعليم': [
                ('', 'اختر نوع الخدمة'),
                ('لغات', 'تعليم لغات'),
                ('رياضيات', 'تعليم رياضيات'),
                ('علوم', 'تعليم علوم'),
                ('حاسوب', 'تعليم حاسوب'),
                ('موسيقى', 'تعليم موسيقى'),
                ('أخرى', 'أنواع أخرى')
            ],
            'صحة': [
                ('', 'اختر نوع الخدمة'),
                ('استشارات', 'استشارات طبية'),
                ('علاج طبيعي', 'علاج طبيعي'),
                ('تغذية', 'استشارات تغذية'),
                ('لياقة', 'تدريب لياقة'),
                ('تمريض', 'خدمات تمريض'),
                ('أخرى', 'أنواع أخرى')
            ],
            'طعام': [
                ('', 'اختر نوع الخدمة'),
                ('وجبات', 'إعداد وجبات'),
                ('حلويات', 'حلويات'),
                ('مشروبات', 'مشروبات'),
                ('طعام صحي', 'طعام صحي'),
                ('مناسبات', 'طعام مناسبات'),
                ('أخرى', 'أنواع أخرى')
            ],
            'أخرى': [
                ('', 'اختر نوع الخدمة'),
                ('تصميم', 'خدمات تصميم'),
                ('ترجمة', 'خدمات ترجمة'),
                ('قانون', 'استشارات قانونية'),
                ('سفر', 'خدمات سفر'),
                ('تجميل', 'خدمات تجميل'),
                ('أخرى', 'أنواع أخرى')
            ]
        }

        # تحديث اختيارات نوع الخدمة المحدد بناءً على التصنيف المحدد
        if 'category' in kwargs.get('data', {}) and kwargs['data']['category']:
            selected_category = kwargs['data']['category']
            self.service_type.choices = self.service_types.get(selected_category, [('', 'اختر نوع الخدمة')])

# نموذج خدمات الصيانة
class MaintenanceServiceForm(BaseServiceForm):
    category = HiddenField('التصنيف', default='صيانة')
    service_type = SelectField('نوع الخدمة', choices=[
        ('كهرباء', 'صيانة كهربائية'),
        ('سباكة', 'صيانة سباكة'),
        ('تكييف', 'صيانة تكييف'),
        ('أجهزة', 'صيانة أجهزة منزلية'),
        ('حاسوب', 'صيانة حاسوب'),
        ('أخرى', 'أنواع أخرى')
    ])
    tools_provided = BooleanField('توفير الأدوات', default=True)
    has_warranty = BooleanField('ضمان على الخدمة', default=True)
    warranty_period = IntegerField('مدة الضمان (بالأيام)', default=30, validators=[Optional(), NumberRange(min=0)])
    emergency_service = BooleanField('خدمة طوارئ', default=False)
    experience_years = IntegerField('سنوات الخبرة', validators=[Optional(), NumberRange(min=0)])

# نموذج خدمات التنظيف
class CleaningServiceForm(BaseServiceForm):
    category = HiddenField('التصنيف', default='تنظيف')
    service_type = SelectField('نوع الخدمة', choices=[
        ('منزلي', 'تنظيف منزلي'),
        ('مكتبي', 'تنظيف مكاتب'),
        ('سجاد', 'تنظيف سجاد'),
        ('واجهات', 'تنظيف واجهات'),
        ('سيارات', 'تنظيف سيارات'),
        ('أخرى', 'أنواع أخرى')
    ])
    materials_included = BooleanField('المواد مشمولة', default=True)
    equipment_provided = BooleanField('توفير المعدات', default=True)
    eco_friendly = BooleanField('منتجات صديقة للبيئة', default=False)
    min_area = IntegerField('الحد الأدنى للمساحة (م²)', validators=[Optional(), NumberRange(min=0)])
    max_area = IntegerField('الحد الأقصى للمساحة (م²)', validators=[Optional(), NumberRange(min=0)])

# نموذج خدمات التعليم
class EducationServiceForm(BaseServiceForm):
    category = HiddenField('التصنيف', default='تعليم')
    service_type = SelectField('نوع الخدمة', choices=[
        ('لغات', 'تعليم لغات'),
        ('رياضيات', 'تعليم رياضيات'),
        ('علوم', 'تعليم علوم'),
        ('حاسوب', 'تعليم حاسوب'),
        ('موسيقى', 'تعليم موسيقى'),
        ('أخرى', 'أنواع أخرى')
    ])
    education_level = SelectField('المستوى التعليمي', choices=[
        ('ابتدائي', 'ابتدائي'),
        ('متوسط', 'متوسط'),
        ('ثانوي', 'ثانوي'),
        ('جامعي', 'جامعي'),
        ('الكل', 'جميع المستويات')
    ])
    teaching_method = SelectField('طريقة التدريس', choices=[
        ('حضوري', 'تدريس حضوري'),
        ('اونلاين', 'تدريس عن بعد'),
        ('كلاهما', 'حضوري وعن بعد')
    ])
    group_class = BooleanField('دروس جماعية', default=False)
    max_students = IntegerField('الحد الأقصى للطلاب', validators=[Optional(), NumberRange(min=1)])
    has_certificate = BooleanField('توفير شهادة', default=False)

# نموذج الخدمات الصحية
class HealthServiceForm(BaseServiceForm):
    category = HiddenField('التصنيف', default='صحة')
    service_type = SelectField('نوع الخدمة', choices=[
        ('استشارات', 'استشارات طبية'),
        ('علاج طبيعي', 'علاج طبيعي'),
        ('تغذية', 'استشارات تغذية'),
        ('لياقة', 'تدريب لياقة'),
        ('تمريض', 'خدمات تمريض'),
        ('أخرى', 'أنواع أخرى')
    ])
    consultation_type = SelectField('نوع الاستشارة', choices=[
        ('حضوري', 'حضوري'),
        ('فيديو', 'عبر الفيديو'),
        ('هاتف', 'استشارة هاتفية'),
        ('كلاهما', 'حضوري وعن بعد')
    ])
    medical_specialty = StringField('التخصص الطبي')
    years_experience = IntegerField('سنوات الخبرة', validators=[Optional(), NumberRange(min=0)])
    home_visit = BooleanField('زيارات منزلية', default=False)
    accepts_insurance = BooleanField('قبول التأمين الصحي', default=False)
    medical_license = StringField('رقم الترخيص الطبي', validators=[Optional()])

# نموذج خدمات الطعام
class FoodServiceForm(BaseServiceForm):
    category = HiddenField('التصنيف', default='طعام')
    service_type = SelectField('نوع الخدمة', choices=[
        ('وجبات', 'إعداد وجبات'),
        ('حلويات', 'حلويات'),
        ('مشروبات', 'مشروبات'),
        ('طعام صحي', 'طعام صحي'),
        ('مناسبات', 'طعام مناسبات'),
        ('أخرى', 'أنواع أخرى')
    ])
    delivery_available = BooleanField('توصيل متاح', default=True)
    min_order_quantity = IntegerField('الحد الأدنى للطلب', validators=[Optional(), NumberRange(min=1)])
    preparation_time = IntegerField('وقت التحضير (بالدقائق)', validators=[Optional(), NumberRange(min=0)])
    menu_items = TextAreaField('عناصر القائمة')
    vegetarian_options = BooleanField('خيارات نباتية', default=False)
    vegan_options = BooleanField('خيارات نباتية صرفة', default=False)
    catering_service = BooleanField('خدمة توريد للمناسبات', default=False)
    dietary_info = TextAreaField('معلومات غذائية')

# نموذج الخدمات الأخرى
class OtherServiceForm(BaseServiceForm):
    category = HiddenField('التصنيف', default='أخرى')
    service_type = SelectField('نوع الخدمة', choices=[
        ('تصميم', 'خدمات تصميم'),
        ('ترجمة', 'خدمات ترجمة'),
        ('قانون', 'استشارات قانونية'),
        ('سفر', 'خدمات سفر'),
        ('تجميل', 'خدمات تجميل'),
        ('أخرى', 'أنواع أخرى')
    ])
    service_mode = SelectField('طريقة تقديم الخدمة', choices=[
        ('حضوري', 'حضوري'),
        ('اونلاين', 'عن بعد'),
        ('كلاهما', 'حضوري وعن بعد')
    ])
    custom_fields = TextAreaField('حقول مخصصة')

class BaseBookingForm(FlaskForm):
    """النموذج الأساسي للحجز الذي ترث منه جميع النماذج المتخصصة"""
    service_id = HiddenField('معرف الخدمة', validators=[DataRequired()])
    booking_date = DateTimeField('التاريخ والوقت', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    notes = TextAreaField('ملاحظات إضافية')
    payment_method = SelectField('طريقة الدفع', choices=[
        ('credit_card', 'بطاقة ائتمان'),
        ('debit_card', 'بطاقة مدين'),
        ('bank_transfer', 'تحويل بنكي'),
        ('cash', 'نقدًا عند الاستلام')
    ], validators=[DataRequired()])
    card_number = StringField('رقم البطاقة', validators=[Optional(), Length(min=16, max=16)])
    card_expiry = StringField('تاريخ الانتهاء (MM/YY)', validators=[Optional()])
    card_cvv = StringField('رمز التحقق CVV', validators=[Optional(), Length(min=3, max=4)])
    submit = SubmitField('تأكيد الحجز والدفع')

class BookingForm(BaseBookingForm):
    """النموذج العام للحجز"""
    pass

class MaintenanceBookingForm(BaseBookingForm):
    """نموذج حجز خدمات الصيانة"""
    problem_description = TextAreaField('وصف المشكلة', validators=[DataRequired()])
    location_details = StringField('تفاصيل الموقع', validators=[DataRequired()])
    preferred_time = SelectField('الوقت المفضل', choices=[
        ('morning', 'صباحًا (8 ص - 12 م)'),
        ('afternoon', 'ظهرًا (12 م - 4 م)'),
        ('evening', 'مساءً (4 م - 8 م)')
    ])
    is_emergency = BooleanField('حالة طارئة', default=False)
    has_pets = BooleanField('يوجد حيوانات أليفة', default=False)

class CleaningBookingForm(BaseBookingForm):
    """نموذج حجز خدمات التنظيف"""
    area_size = IntegerField('مساحة المكان (م²)', validators=[DataRequired(), NumberRange(min=1)])
    property_type = SelectField('نوع العقار', choices=[
        ('apartment', 'شقة'),
        ('house', 'منزل'),
        ('office', 'مكتب'),
        ('commercial', 'مبنى تجاري'),
        ('other', 'أخرى')
    ])
    number_of_rooms = IntegerField('عدد الغرف', validators=[DataRequired(), NumberRange(min=1)])
    supplies_provided = BooleanField('توفير مواد التنظيف', default=True)
    special_requirements = TextAreaField('متطلبات خاصة')

class EducationBookingForm(BaseBookingForm):
    """نموذج حجز خدمات التعليم"""
    student_name = StringField('اسم الطالب', validators=[DataRequired()])
    student_age = IntegerField('عمر الطالب', validators=[Optional(), NumberRange(min=3)])
    education_level = SelectField('المستوى التعليمي', choices=[
        ('elementary', 'ابتدائي'),
        ('middle', 'متوسط'),
        ('high', 'ثانوي'),
        ('university', 'جامعي'),
        ('adult', 'تعليم الكبار')
    ])
    learning_goals = TextAreaField('أهداف التعلم')
    preferred_language = SelectField('اللغة المفضلة', choices=[
        ('arabic', 'العربية'),
        ('english', 'الإنجليزية'),
        ('both', 'كلاهما')
    ])
    
class HealthBookingForm(BaseBookingForm):
    """نموذج حجز الخدمات الصحية"""
    patient_name = StringField('اسم المريض', validators=[DataRequired()])
    patient_age = IntegerField('عمر المريض', validators=[Optional(), NumberRange(min=0)])
    gender = SelectField('الجنس', choices=[
        ('male', 'ذكر'),
        ('female', 'أنثى')
    ])
    health_issues = TextAreaField('الحالة الصحية')
    has_medical_history = BooleanField('لديه سجل طبي سابق', default=False)
    medical_history = TextAreaField('السجل الطبي')
    has_insurance = BooleanField('لديه تأمين صحي', default=False)
    insurance_details = StringField('تفاصيل التأمين')
    is_first_visit = BooleanField('زيارة أولى', default=True)

class FoodBookingForm(BaseBookingForm):
    """نموذج حجز خدمات الطعام"""
    number_of_people = IntegerField('عدد الأشخاص', validators=[DataRequired(), NumberRange(min=1)])
    delivery_address = StringField('عنوان التوصيل')
    delivery_time = DateTimeField('وقت التوصيل', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    is_delivery = BooleanField('توصيل للمنزل', default=True)
    has_allergies = BooleanField('وجود حساسية من الطعام', default=False)
    allergies_details = TextAreaField('تفاصيل الحساسية')
    dietary_preferences = SelectField('التفضيلات الغذائية', choices=[
        ('none', 'لا توجد'),
        ('vegetarian', 'نباتي'),
        ('vegan', 'نباتي صرف'),
        ('gluten_free', 'خالي من الجلوتين'),
        ('low_carb', 'قليل الكربوهيدرات'),
        ('other', 'أخرى')
    ])
    special_requests = TextAreaField('طلبات خاصة')

class PaymentForm(FlaskForm):
    booking_id = HiddenField('معرف الحجز', validators=[DataRequired()])
    amount = HiddenField('المبلغ', validators=[DataRequired()])
    payment_method = SelectField('طريقة الدفع', choices=[
        ('credit_card', 'بطاقة ائتمان'),
        ('debit_card', 'بطاقة مدين'),
        ('bank_transfer', 'تحويل بنكي'),
        ('cash', 'نقدًا عند الاستلام')
    ])
    card_number = StringField('رقم البطاقة', validators=[Length(min=16, max=16)])
    card_expiry = StringField('تاريخ الانتهاء (MM/YY)')
    card_cvv = StringField('رمز التحقق CVV', validators=[Length(min=3, max=4)])
    submit = SubmitField('إتمام الدفع')

class ReviewForm(FlaskForm):
    service_id = HiddenField('معرف الخدمة', validators=[DataRequired()])
    rating = SelectField('التقييم', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('التعليق', validators=[DataRequired()])
    submit = SubmitField('إرسال التقييم')

class SearchForm(FlaskForm):
    query = StringField('بحث عن خدمة', validators=[DataRequired()])
    category = SelectField('التصنيف', choices=[
        ('', 'الكل'),
        ('صيانة', 'صيانة'),
        ('تنظيف', 'تنظيف'),
        ('تعليم', 'تعليم'),
        ('صحة', 'صحة'),
        ('طعام', 'طعام'),
        ('أخرى', 'أخرى')
    ])
    submit = SubmitField('بحث')

# نموذج إضافة وجبة لمقدمي خدمات الطعام
class MealForm(FlaskForm):
    name = StringField('اسم الوجبة', validators=[DataRequired()])
    description = TextAreaField('وصف الوجبة', validators=[DataRequired()])
    price = FloatField('السعر', validators=[DataRequired(), NumberRange(min=0)])
    meal_type = SelectField('نوع الوجبة', choices=[
        ('فطور', 'فطور'),
        ('غداء', 'غداء'),
        ('عشاء', 'عشاء'),
        ('حلويات', 'حلويات'),
        ('مشروبات', 'مشروبات'),
        ('وجبات سريعة', 'وجبات سريعة'),
        ('أخرى', 'أخرى')
    ])
    preparation_time = IntegerField('وقت التحضير (بالدقائق)', validators=[DataRequired(), NumberRange(min=1)])
    calories = IntegerField('السعرات الحرارية', validators=[Optional()])
    is_vegetarian = BooleanField('وجبة نباتية')
    is_vegan = BooleanField('وجبة نباتية صرفة')
    is_gluten_free = BooleanField('خالية من الغلوتين')
    image = FileField('صورة الوجبة', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'يُسمح فقط بملفات الصور')
    ])
    is_available = BooleanField('متاحة', default=True)
    submit = SubmitField('إضافة الوجبة')

# نموذج حجز طاولة في المطعم
class TableReservationForm(FlaskForm):
    reservation_date = DateTimeField('تاريخ ووقت الحجز', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    guests_number = IntegerField('عدد الضيوف', validators=[DataRequired(), NumberRange(min=1, max=20)])
    special_requests = TextAreaField('طلبات خاصة')
    contact_phone = StringField('رقم الهاتف للتواصل', validators=[DataRequired()])
    submit = SubmitField('تأكيد الحجز')