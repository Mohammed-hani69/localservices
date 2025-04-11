from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يجب تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'warning')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يجب تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('هذه الصفحة مخصصة للمشرفين فقط', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function