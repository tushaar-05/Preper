from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from app.extensions import db
from app.models import User, Student

bp = Blueprint('auth', __name__)

# ---------------- STUDENT LOGIN ----------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, role='student').first()

        if not user or not user.check_password(password):
            flash('Invalid credentials', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('Account disabled', 'danger')
            return render_template('login.html')

        session['student_id'] = user.id
        user.last_login = datetime.utcnow()
        db.session.commit()

        return redirect(url_for('user.dashboard'))

    return render_template('login.html')


# ---------------- ADMIN LOGIN ----------------
@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        admin = User.query.filter_by(email=email, role='admin').first()

        if not admin or not admin.check_password(password):
            flash('Invalid admin credentials', 'danger')
            return render_template('admin_login.html')

        if not admin.is_active:
            flash('Account disabled', 'danger')
            return render_template('admin_login.html')

        session['admin_id'] = admin.id
        admin.last_login = datetime.utcnow()
        db.session.commit()

        return redirect(url_for('admin.dashboard'))

    return render_template('admin_login.html')


# ---------------- LOGOUT ----------------
@bp.route('/logout')
def logout():
    session.pop('student_id', None)
    session.pop('admin_id', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.index'))
