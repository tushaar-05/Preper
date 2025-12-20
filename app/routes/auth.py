from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from app.extensions import db
from app.models import User, Student, Batch, Enrollment

bp = Blueprint('auth', __name__)


# ---------------- STUDENT REGISTRATION ----------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Validate inputs
        if not email or not password or not full_name:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'danger')
            return render_template('register.html')

        try:
            # 1. Create User
            username = email.split('@')[0]
            # Make username unique
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User(username=username, email=email, role='student')
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # 2. Create Student profile
            student = Student(user_id=user.id, full_name=full_name, phone=phone)
            db.session.add(student)
            db.session.flush()

            # 3. Create Enrollment (Auto-enroll in default batch)
            # Find the batch by partial name match 'neumann' or just get first active
            batch = Batch.query.filter(Batch.name.ilike('%neumann%')).first()
            if not batch:
                batch = Batch.query.filter_by(status='active').first()
            
            if batch:
                enrollment = Enrollment(
                    student_id=student.id,
                    batch_id=batch.id,
                    total_amount=batch.discounted_price,
                    payment_status='pending'
                )
                db.session.add(enrollment)
            
            db.session.commit()
            flash('Registration successful! Please login to continue.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            print(f"Registration Error: {str(e)}")
            flash('An error occurred. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')

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
