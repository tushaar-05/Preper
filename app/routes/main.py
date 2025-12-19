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

@bp.route('/doubts')
def doubts():
    # In a real application, you would fetch actual doubts from the database here
    # For now, we'll use sample data
    sample_doubts = [
        {
            'id': 1,
            'title': 'How to solve this math problem?',
            'content': 'I\'m having trouble understanding how to approach this calculus problem...',
            'author': 'John Doe',
            'timestamp': '2025-12-19 14:30',
            'replies': 3,
            'views': 24
        },
        {
            'id': 2,
            'title': 'Physics concept clarification needed',
            'content': 'Can someone explain the concept of quantum entanglement in simple terms?',
            'author': 'Jane Smith',
            'timestamp': '2025-12-18 10:15',
            'replies': 5,
            'views': 42
        }
    ]
    return render_template('dashboard/user/doubts.html', doubts=sample_doubts)