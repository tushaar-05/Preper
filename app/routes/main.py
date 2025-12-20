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

@bp.route('/mock')
def mock():
    mock_tests = [
        {
            'id': 1,
            'title': 'NSAT Full Length Mock 1',
            'date': 'Dec 25, 2025',
            'time': '10:00 AM - 1:00 PM',
            'duration': '3 Hours',
            'questions': 90,
            'status': 'Upcoming',
            'syllabus_link': '#'
        },
        {
            'id': 2,
            'title': 'Logical Reasoning Sectional',
            'date': 'Dec 28, 2025',
            'time': '2:00 PM - 3:30 PM',
            'duration': '1.5 Hours',
            'questions': 45,
            'status': 'Upcoming',
            'syllabus_link': '#'
        },
        {
            'id': 3,
            'title': 'Quantitative Aptitude Drill',
            'date': 'Dec 30, 2025',
            'time': 'Available All Day',
            'duration': '1 Hour',
            'questions': 30,
            'status': 'Live',
            'syllabus_link': '#'
        }
    ]
    return render_template('dashboard/user/mock.html', tests=mock_tests)

@bp.route('/payment-pending')
def payment_pending():
    batches = [
        {
            'id': 'neumann',
            'name': 'Batch NEUMANN',
            'price': 499,
            'features': ['1:1 Mentorship', 'Live Doubt Support', 'Mock Tests Series', 'Prep Kit (PYQs)']
        }
    ]
    return render_template('dashboard/user/payment-pending.html', batches=batches)

@bp.route('/admin/students')
def admin_students():
    students = [
        {
            'id': 1,
            'name': 'Arjun Verma',
            'email': 'arjun.v@example.com',
            'batch': 'Batch NEUMANN',
            'status': 'Active',
            'joined_date': 'Dec 20, 2025',
            'avatar_color': 'bg-violet-100 text-violet-600'
        },
        {
            'id': 2,
            'name': 'Sneha Gupta',
            'email': 'sneha.g@example.com',
            'batch': 'Batch NEUMANN',
            'status': 'Active',
            'joined_date': 'Dec 19, 2025',
            'avatar_color': 'bg-pink-100 text-pink-600'
        },
        {
            'id': 3,
            'name': 'Rahul Kumar',
            'email': 'rahul.k@example.com',
            'batch': 'Batch NEUMANN',
            'status': 'Pending Payment',
            'joined_date': 'Dec 19, 2025',
            'avatar_color': 'bg-blue-100 text-blue-600'
        },
        {
            'id': 4,
            'name': 'Priya Singh',
            'email': 'priya.s@example.com',
            'batch': 'Batch NEUMANN',
            'status': 'Active',
            'joined_date': 'Dec 18, 2025',
            'avatar_color': 'bg-green-100 text-green-600'
        },
        {
            'id': 5,
            'name': 'Aditya Roy',
            'email': 'aditya.r@example.com',
            'batch': 'Batch NEUMANN',
            'status': 'Inactive',
            'joined_date': 'Dec 15, 2025',
            'avatar_color': 'bg-yellow-100 text-yellow-600'
        }
    ]
    return render_template('dashboard/admin/students.html', students=students)

@bp.route('/admin/batches')
def admin_batches():
    batches = [
        {
            'id': 1,
            'name': 'Batch NEUMANN',
            'status': 'Active',
            'status_color': 'bg-green-100 text-green-700',
            'students_count': 24,
            'max_students': 50,
            'price': 499,
            'original_price': 999,
            'features': ['Daily Live Classes', 'Doubt Support', 'Mock Tests', 'Personal Mentorship'],
            'color': 'violet'
        }
    ]
    return render_template('dashboard/admin/batches.html', batches=batches)

@bp.route('/admin/interviews')
def admin_interviews():
    interviews = [
        {
            'id': 1,
            'student_name': 'Arjun Verma',
            'type': 'Mock HR',
            'mentor': 'Tushar R Singh',
            'date': 'Dec 22, 2025',
            'time': '10:00 AM',
            'status': 'Scheduled',
            'status_color': 'bg-blue-100 text-blue-700'
        },
        {
            'id': 2,
            'student_name': 'Sneha Gupta',
            'type': 'Technical Round',
            'mentor': 'Divyam',
            'date': 'Dec 22, 2025',
            'time': '2:00 PM',
            'status': 'Confirmed',
            'status_color': 'bg-green-100 text-green-700'
        },
        {
            'id': 3,
            'student_name': 'Rahul Kumar',
            'type': '1:1 Mentorship',
            'mentor': 'Devansh',
            'date': 'Dec 21, 2025',
            'time': '11:00 AM',
            'status': 'Completed',
            'status_color': 'bg-gray-100 text-gray-600'
        }
    ]
    return render_template('dashboard/admin/interviews.html', interviews=interviews)

@bp.route('/admin/mocks')
def admin_mocks():
    mocks = [
        {
            'id': 1,
            'title': 'NST Full Mock Test 01',
            'batch': 'All Batches',
            'date': 'Dec 25, 2025',
            'attempts': 0,
            'avg_score': '-',
            'status': 'Scheduled',
            'status_color': 'bg-blue-100 text-blue-700'
        },
        {
            'id': 2,
            'title': 'Physics Chapter Test: Mechanics',
            'batch': 'Batch NEUMANN',
            'date': 'Dec 18, 2025',
            'attempts': 22,
            'avg_score': '76%',
            'status': 'Live',
            'status_color': 'bg-green-100 text-green-700'
        },
        {
            'id': 3,
            'title': 'Mathematics Speed Test',
            'batch': 'Batch NEWTON',
            'date': 'Dec 15, 2025',
            'attempts': 15,
            'avg_score': '82%',
            'status': 'Ended',
            'status_color': 'bg-gray-100 text-gray-600'
        }
    ]
    return render_template('dashboard/admin/mocks.html', mocks=mocks)

@bp.route('/admin/announcements')
def admin_announcements():
    announcements = [
        {
            'id': 1,
            'title': 'System Maintenance Update',
            'date': 'Dec 20, 2025',
            'target': 'All Users',
            'content': 'The portal will be down for maintenance from 2 AM to 4 AM tomorrow.',
            'type': 'System',
            'type_color': 'bg-gray-100 text-gray-700'
        },
        {
            'id': 2,
            'title': 'New Physics Module Released',
            'date': 'Dec 19, 2025',
            'target': 'Batch NEUMANN',
            'content': 'The new Mechanics module is now live in your Resource Center.',
            'type': 'Academic',
            'type_color': 'bg-violet-100 text-violet-700'
        },
        {
            'id': 3,
            'title': 'Mock Test Schedule Change',
            'date': 'Dec 18, 2025',
            'target': 'All Batches',
            'content': 'The upcoming Full Mock Test has been rescheduled to Dec 25th.',
            'type': 'Important',
            'type_color': 'bg-red-100 text-red-700'
        }
    ]
    return render_template('dashboard/admin/announcements.html', announcements=announcements)

@bp.route('/admin/resources')
def admin_resources():
    resources = [
        {
            'id': 1,
            'title': 'Physics Chapter 1: Mechanics - Complete Notes',
            'category': 'Notes',
            'batch': 'All Batches',
            'uploaded_date': 'Dec 20, 2025',
            'file_size': '2.4 MB',
            'downloads': 45,
            'type': 'PDF'
        },
        {
            'id': 2,
            'title': 'NST Previous Year Questions 2024',
            'category': 'PYQs',
            'batch': 'Batch NEUMANN',
            'uploaded_date': 'Dec 18, 2025',
            'file_size': '5.1 MB',
            'downloads': 38,
            'type': 'PDF'
        },
        {
            'id': 3,
            'title': 'Mathematics Formula Sheet',
            'category': 'Reference',
            'batch': 'All Batches',
            'uploaded_date': 'Dec 15, 2025',
            'file_size': '1.2 MB',
            'downloads': 52,
            'type': 'PDF'
        }
    ]
    return render_template('dashboard/admin/resources.html', resources=resources)

@bp.route('/admin/settings')
def admin_settings():
    settings = {
        'platform': {
            'name': 'NST Prep',
            'email': 'admin@nstprep.com',
            'phone': '+91 98765 43210',
            'timezone': 'Asia/Kolkata'
        },
        'features': {
            'registrations_open': True,
            'mock_tests_enabled': True,
            'interview_booking': True,
            'doubt_forum': True
        },
        'notifications': {
            'email_notifications': True,
            'sms_notifications': False,
            'push_notifications': True
        }
    }
    return render_template('dashboard/admin/settings.html', settings=settings)