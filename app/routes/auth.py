from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from app.extensions import db
from app.models import User, Student, Batch, Enrollment
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from app.utils.email_service import send_mojoauth_otp, verify_mojoauth_otp, send_welcome_email, send_password_reset_email
from authlib.integrations.flask_client import OAuth
from flask import current_app
import secrets

bp = Blueprint('auth', __name__)

# Initialize OAuth
oauth = OAuth()


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

        # Normalize email
        email = email.strip().lower()

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
    if 'registration_data' not in session:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('auth.register'))
        
    reg_data = session['registration_data']
    
    # Check for OTP expiration (10 minutes = 600 seconds)
    # Check for OTP expiration (10 minutes = 600 seconds)
    if datetime.utcnow().timestamp() - reg_data.get('otp_created_at', 0) > 600:
        flash('OTP has expired. Please request a new one.', 'warning')
        return render_template('otp_verify.html', email=reg_data.get('email'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        state_id = reg_data.get('state_id')
        
        if verify_mojoauth_otp(state_id, entered_otp):
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
    
    return render_template('otp_verify.html', email=reg_data.get('email'))

@bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'registration_data' not in session:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('auth.register'))
    
    reg_data = session['registration_data']
    
    # Resend via MojoAuth
    state_id = send_mojoauth_otp(reg_data['email'])
    
    if state_id:
        reg_data['state_id'] = state_id
        reg_data['otp_created_at'] = datetime.utcnow().timestamp()
        session['registration_data'] = reg_data
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
    if request.method == 'GET':
        # Redirect if already logged in
        if 'student_id' in session:
            return redirect(url_for('user.dashboard'))
        # Clear stale flash messages from other tabs
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Normalize email
        email = email.strip().lower()

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
    if request.method == 'GET':
        # Clear stale flash messages
        session.pop('_flashes', None)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Normalize email
        email = email.strip().lower()

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


# ---------------- GOOGLE OAUTH ----------------
def init_oauth(app):
    """Initialize OAuth with app context"""
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

@bp.route('/google/login')
def google_login():
    """Initiate Google OAuth flow"""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            flash('Failed to get user information from Google.', 'danger')
            return redirect(url_for('auth.login'))
        
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('sub')
        
        if not email:
            flash('Email not provided by Google.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Normalize email (strip whitespace and convert to lowercase)
        email = email.strip().lower()
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # User exists - log them in
            print(f"[Google OAuth] Existing user found: {email} (User ID: {user.id})")
            if user.role != 'student':
                flash('This account is not a student account.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Get student profile
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                session['student_id'] = user.id
                flash(f'Welcome back, {student.full_name}!', 'success')
                return redirect(url_for('user.dashboard'))
            else:
                flash('Student profile not found.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            # New user - create account
            print(f"[Google OAuth] Creating new account for: {email}")
            try:
                # Generate unique username
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create user with random password (OAuth users don't need it)
                user = User(username=username, email=email, role='student')
                random_password = secrets.token_urlsafe(32)
                user.set_password(random_password)
                db.session.add(user)
                db.session.flush()
                
                # Create student profile
                student = Student(
                    user_id=user.id,
                    full_name=name or email.split('@')[0],
                    phone=None  # Phone is optional for OAuth users
                )
                db.session.add(student)
                db.session.flush()
                
                db.session.commit()
                
                # Send welcome email
                try:
                    send_welcome_email(email, name or email.split('@')[0])
                except Exception as e:
                    print(f"Failed to send welcome email: {e}")
                
                # Log them in
                session['student_id'] = user.id
                flash(f'Welcome to NST Prep, {student.full_name}!', 'success')
                return redirect(url_for('user.dashboard'))
                
            except Exception as e:
                db.session.rollback()
                print(f"Error creating user from Google OAuth: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
                return redirect(url_for('auth.register'))
    
    except Exception as e:
        print(f"Google OAuth error: {e}")
        flash('Authentication failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

# ---------------- FORGOT PASSWORD ----------------
@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please provide an email address.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        
        # Security: Always look like it worked to prevent email enumeration
        if user:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(email, salt='password-reset-salt')
            send_password_reset_email(email, token)
        
        flash('If an account exists for that email, we have sent a password reset link.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600) # 1 hour expiration
    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    except Exception:
        flash('Invalid password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return render_template('reset_password.html')
            
        if password != confirm_password:
             flash('Passwords do not match.', 'danger')
             return render_template('reset_password.html')
             
        if len(password) < 6:
             flash('Password must be at least 6 characters.', 'danger')
             return render_template('reset_password.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been reset. You can now login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))
            
    return render_template('reset_password.html')
