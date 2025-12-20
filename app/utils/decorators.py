from functools import wraps
from flask import session, redirect, url_for, flash
from app.models import Student, Enrollment

def student_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please login as student', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin login required', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return wrapper


def enrollment_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        student_id = session.get('student_id')
        student = Student.query.filter_by(user_id=student_id).first()

        if not student:
            flash('Student profile not found', 'danger')
            return redirect(url_for('user.dashboard'))

        if not Enrollment.query.filter_by(student_id=student.id).first():
            flash('You are not enrolled in any batch', 'warning')
            return redirect(url_for('user.dashboard'))

        return f(*args, **kwargs)
    return wrapper
