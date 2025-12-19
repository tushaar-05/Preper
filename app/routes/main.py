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

@bp.route('/payment')
def payment():
    # Sample payment data
    subscription = {
        'status': 'Active',
        'plan': 'Batch NEUMANN',
        'amount': '₹499',
        'next_billing': 'Lifetime Access',
        'card_last4': '4242'
    }
    
    transactions = [
        {
            'id': 'TXN_123456789',
            'date': 'Dec 15, 2025',
            'description': 'Batch NEUMANN Subscription',
            'amount': '₹499',
            'status': 'Success',
            'invoice_url': '#'
        }
    ]
    return render_template('dashboard/user/payment.html', subscription=subscription, transactions=transactions)

@bp.route('/prepkit')
def prepkit():
    resources = {
        'Interview Questions': [
            {'title': 'Top 50 NST Interview Questions', 'type': 'PDF', 'size': '2.4 MB', 'link': '#'},
            {'title': 'HR Behavioural Q&A Guide', 'type': 'PDF', 'size': '1.8 MB', 'link': '#'},
            {'title': 'Technical Round Cheat Sheet', 'type': 'PDF', 'size': '3.1 MB', 'link': '#'},
        ],
        'Study Notes': [
            {'title': 'Physics Formula Sheet', 'type': 'PDF', 'size': '4.2 MB', 'link': '#'},
            {'title': 'Mathematics Quick Revision', 'type': 'PDF', 'size': '5.5 MB', 'link': '#'},
            {'title': 'Logical Reasoning Tricks', 'type': 'DOC', 'size': '1.2 MB', 'link': '#'},
        ],
        'Practice Sets': [
            {'title': 'Mock Test Series 1 - Solutions', 'type': 'PDF', 'size': '8.4 MB', 'link': '#'},
            {'title': 'Previous Year Papers (2020-2024)', 'type': 'Zip', 'size': '42 MB', 'link': '#'},
        ]
    }
    return render_template('dashboard/user/prepkit.html', resources=resources)

@bp.route('/interview')
def interview():
    upcoming_interviews = [
        {
            'id': 1,
            'title': 'Crack your NSAT exam',
            'date': 'Dec 21, 2025',
            'time': '4:00 PM',
            'mentor': 'Tushar R Singh',
            'type': 'NSAT Guide',
            'image': '/static/images/nsat_poster.png',
            'link': '#'
        },
        {
            'id': 2,
            'title': 'Choose your campus',
            'date': 'Dec 24, 2025',
            'time': '11:00 AM',
            'mentor': 'Divyam',
            'type': 'Campus Guide',
            'image': '/static/images/campus_poster.png',
            'link': '#'
        }
    ]
    
    past_interviews = [
        {
            'id': 101,
            'title': '1:1 Interview #1',
            'date': 'Dec 14, 2025',
            'mentor': 'Devansh',
            'status': 'Completed',
            'feedback_link': '#'
        },
        {
            'id': 100,
            'title': '1:1 Interview #2',
            'date': 'Dec 07, 2025',
            'mentor': 'Devansh',
            'status': 'Completed',
            'feedback_link': '#'
        }
    ]
    return render_template('dashboard/user/interview.html', upcoming=upcoming_interviews, past=past_interviews)