from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from app.extensions import db
from app.models import User, Student, Batch, Enrollment
from app.utils.email_service import send_mojoauth_otp, verify_mojoauth_otp, send_welcome_email

bp = Blueprint('auth', __name__)


# ---------------- STUDENT REGISTRATION ----------------
# ---------------- STUDENT REGISTRATION ----------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        campus_pref = request.form.get('campus_pref')
        
        # Validate inputs
        if not email or not password or not full_name:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'danger')
            return render_template('register.html')

        # Check existing phone
        if Student.query.filter_by(phone=phone).first():
            flash('Phone number already registered.', 'danger')
            return render_template('register.html')

        # Send OTP via MojoAuth
        state_id = send_mojoauth_otp(email)
        
        if state_id:
            # Store registration data in session
            session['registration_data'] = {
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'password': password,
                'campus_pref': campus_pref,
                'state_id': state_id, # Store MojoAuth State ID instead of OTP
                'otp_created_at': datetime.utcnow().timestamp()
            }
            flash('Verification code sent to your email.', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Failed to send verification email. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    # Determine context (Registration or Login)
    if 'registration_data' in session:
        context = 'register'
        data = session['registration_data']
    elif 'login_data' in session:
        context = 'login'
        data = session['login_data']
    else:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Check for OTP expiration (10 minutes = 600 seconds)
    if datetime.utcnow().timestamp() - data.get('otp_created_at', 0) > 600:
        flash('OTP has expired. Please request a new one.', 'warning')
        return render_template('otp_verify.html', email=data.get('email'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        state_id = data.get('state_id')
        
        if verify_mojoauth_otp(state_id, entered_otp):
            
            if context == 'login':
                # LOGIN FLOW
                user = User.query.filter_by(email=data['email']).first()
                if user:
                    session['student_id'] = user.id
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                    # Clear session data
                    session.pop('login_data', None)
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('user.dashboard'))
                else:
                    flash('User not found.', 'danger')
                    return redirect(url_for('auth.login'))
            
            else:
                # REGISTRATION FLOW
                reg_data = data
                # OTP Verified - Create User
                try:
                    # 1. Create User
                    username = reg_data['email'].split('@')[0]
                    base_username = username
                    counter = 1
                    while User.query.filter_by(username=username).first():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    user = User(username=username, email=reg_data['email'], role='student')
                    user.set_password(reg_data['password'])
                    db.session.add(user)
                    db.session.flush()

                    # 2. Create Student profile
                    student = Student(
                        user_id=user.id, 
                        full_name=reg_data['full_name'], 
                        phone=reg_data['phone'],
                        preferred_batch=reg_data['campus_pref'] if reg_data['campus_pref'] else None
                    )
                    db.session.add(student)
                    db.session.flush()

                    # 3. Create Enrollment (Auto-enroll in default batch)
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
                    
                    # Send welcome email
                    send_welcome_email(user.email, student.full_name)
                    
                    # Clear session registration data
                    session.pop('registration_data', None)
                    
                    # Log the user in
                    session['student_id'] = user.id
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                    
                    flash('Registration successful! Welcome to PREPER.', 'success')
                    return redirect(url_for('user.dashboard'))

                except Exception as e:
                    db.session.rollback()
                    print(f"Registration Error: {str(e)}")
                    flash('An error occurred during registration. Please try again.', 'danger')
                    return redirect(url_for('auth.register'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    if context == 'login':
        return render_template('otp_login_verify.html', email=data.get('email'))

    return render_template('otp_verify.html', email=data.get('email'))

@bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'registration_data' in session:
        data = session['registration_data']
        session_key = 'registration_data'
    elif 'login_data' in session:
        data = session['login_data']
        session_key = 'login_data'
    else:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Resend via MojoAuth
    state_id = send_mojoauth_otp(data['email'])
    
    if state_id:
        data['state_id'] = state_id
        data['otp_created_at'] = datetime.utcnow().timestamp()
        session[session_key] = data
        flash('New verification code sent.', 'success')
    else:
        flash('Failed to resend email.', 'danger')
        
    return redirect(url_for('auth.verify_otp'))

@bp.route('/edit-registration')
def edit_registration():
    if 'registration_data' not in session:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('auth.register'))
        
    data = session['registration_data']
    return render_template('register.html', form_data=data)

# ---------------- STUDENT LOGIN ----------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')

        # 1. Check if user exists
        user = User.query.filter_by(email=email, role='student').first()

        if not user:
            flash('No account found with this email.', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('Account disabled', 'danger')
            return render_template('login.html')

        # 2. Send OTP via MojoAuth
        state_id = send_mojoauth_otp(email)
        
        if state_id:
            # Store login data in session
            session['login_data'] = {
                'email': email,
                'state_id': state_id,
                'otp_created_at': datetime.utcnow().timestamp()
            }
            flash('Login verification code sent to your email.', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Failed to send verification email. Please try again.', 'danger')
            return render_template('login.html')

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
