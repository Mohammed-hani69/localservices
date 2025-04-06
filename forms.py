from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, DateTimeField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User

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
    company_name = StringField('اسم الشركة/المؤسسة', validators=[DataRequired()])
    description = TextAreaField('وصف الخدمات', validators=[DataRequired()])
    website = StringField('الموقع الإلكتروني')
    submit = SubmitField('حفظ المعلومات')

class ServiceForm(FlaskForm):
    name = StringField('اسم الخدمة', validators=[DataRequired()])
    description = TextAreaField('وصف الخدمة', validators=[DataRequired()])
    price = FloatField('السعر', validators=[DataRequired(), NumberRange(min=0)])
    duration = IntegerField('المدة (بالدقائق)', validators=[DataRequired(), NumberRange(min=5)])
    category = SelectField('التصنيف', choices=[
        ('صيانة', 'صيانة'),
        ('تنظيف', 'تنظيف'),
        ('تعليم', 'تعليم'),
        ('صحة', 'صحة'),
        ('طعام', 'طعام'),
        ('أخرى', 'أخرى')
    ])
    service_type = SelectField('نوع الخدمة المحدد', choices=[])
    image = FileField('صورة الخدمة', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'يُسمح فقط بملفات الصور')
    ])
    additional_info = TextAreaField('معلومات إضافية')
    is_active = BooleanField('متاح', default=True)
    submit = SubmitField('إضافة الخدمة')
    
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

class BookingForm(FlaskForm):
    service_id = HiddenField('معرف الخدمة', validators=[DataRequired()])
    booking_date = DateTimeField('التاريخ والوقت', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    notes = TextAreaField('ملاحظات إضافية')
    submit = SubmitField('حجز موعد')

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
