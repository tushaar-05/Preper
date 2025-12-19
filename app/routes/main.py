from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login')
def login():
    return render_template('login.html')

@bp.route('/register')
def register():
    return render_template('register.html')

@bp.route('/admin')
def admin():
    return render_template('dashboard/admin/admin.html')

@bp.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@bp.route('/me')
def me():
    return render_template('dashboard/user/user.html')

@bp.route('/profile')
def profile():
    return render_template('dashboard/user/profile.html')

@bp.route('/announcement')
def announcement():
    return render_template('dashboard/user/announcement.html')