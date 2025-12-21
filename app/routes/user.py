# """
# Student/User dashboard routes with database integration
# """

# from flask import Blueprint, render_template, redirect, url_for, flash, request
# from flask import session
# from app.extensions import db
# from app.models import (
#     User, Student, Batch, Enrollment, Interview,
#     MockTest, TestAttempt, Announcement, Resource
# )
# from app.utils import (
#     student_required, get_current_student,
#     get_user_batch_ids, get_user_batches
# )
# from datetime import datetime

# bp = Blueprint('user', __name__)


# @bp.route('/me')
# @bp.route('/dashboard')
# @student_required
# def dashboard():
#     """Student dashboard"""
#     student = get_current_student()
    
#     if not student:
#         flash('Student profile not found. Please complete your profile.', 'warning')
#         return redirect(url_for('user.profile'))
    
#     # Get enrollments with batch info
#     enrollments = db.session.query(Enrollment, Batch)\
#         .join(Batch, Enrollment.batch_id == Batch.id)\
#         .filter(Enrollment.student_id == student.id)\
#         .all()
    
#     # Get upcoming interviews
#     upcoming_interviews = Interview.query\
#         .filter_by(student_id=student.id)\
#         .filter(Interview.scheduled_date >= datetime.utcnow())\
#         .filter(Interview.status.in_(['scheduled', 'confirmed']))\
#         .order_by(Interview.scheduled_date)\
#         .limit(3)\
#         .all()
    
#     # Get recent announcements
#     batch_ids = get_user_batch_ids(student.id)
#     announcements = Announcement.query\
#         .filter(
#             (Announcement.target_audience == 'all') |
#             (Announcement.target_audience == 'students') |
#             (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
#         )\
#         .filter(Announcement.is_published == True)\
#         .order_by(Announcement.published_at.desc())\
#         .limit(5)\
#         .all()
    
#     # Get available mock tests
#     available_tests = MockTest.query\
#         .filter_by(is_active=True)\
#         .filter(
#             (MockTest.available_from <= datetime.utcnow()) |
#             (MockTest.available_from == None)
#         )\
#         .filter(
#             (MockTest.available_until >= datetime.utcnow()) |
#             (MockTest.available_until == None)
#         )\
#         .limit(3)\
#         .all()
    
#     return render_template('dashboard/user/user.html',
#                          student=student,
#                          enrollments=enrollments,
#                          upcoming_interviews=upcoming_interviews,
#                          announcements=announcements,
#                          available_tests=available_tests)


# @bp.route('/profile', methods=['GET', 'POST'])
# @student_required
# def profile():
#     """View and edit student profile"""
#     student = get_current_student()
    
#     if request.method == 'POST':
#         # Update profile
#         try:
#             student.full_name = request.form.get('full_name', student.full_name)
#             student.phone = request.form.get('phone', student.phone)
#             student.city = request.form.get('city', student.city)
#             student.state = request.form.get('state', student.state)
#             student.education_level = request.form.get('education_level', student.education_level)
#             student.institution_name = request.form.get('institution_name', student.institution_name)
            
#             # Update user email if changed
#             new_email = request.form.get('email')
#             if new_email and new_email != current_user.email:
#                 # Check if email is already taken
#                 existing_user = User.query.filter_by(email=new_email).first()
#                 if existing_user and existing_user.id != current_user.id:
#                     flash('Email already in use.', 'danger')
#                 else:
#                     current_user.email = new_email
            
#             db.session.commit()
#             flash('Profile updated successfully!', 'success')
            
#         except Exception as e:
#             db.session.rollback()
#             flash('Error updating profile. Please try again.', 'danger')
#             print(f"Profile update error: {e}")
    
#     return render_template('dashboard/user/profile.html', student=student, user=current_user)


# @bp.route('/announcement')
# @student_required
# def announcement():
#     """View announcements"""
#     student = get_current_student()
#     batch_ids = get_user_batch_ids(student.id)
    
#     # Get all relevant announcements
#     announcements = Announcement.query\
#         .filter(
#             (Announcement.target_audience == 'all') |
#             (Announcement.target_audience == 'students') |
#             (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
#         )\
#         .filter(Announcement.is_published == True)\
#         .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())\
#         .all()
    
#     return render_template('dashboard/user/announcement.html', announcements=announcements)


# @bp.route('/interview')
# @student_required
# def interview():
#     """View interviews"""
#     student = get_current_student()
    
#     # Get upcoming interviews
#     upcoming_interviews = Interview.query\
#         .filter_by(student_id=student.id)\
#         .filter(Interview.scheduled_date >= datetime.utcnow())\
#         .filter(Interview.status.in_(['scheduled', 'confirmed']))\
#         .order_by(Interview.scheduled_date)\
#         .all()
    
#     # Format for template
#     upcoming = []
#     for interview in upcoming_interviews:
#         upcoming.append({
#             'id': interview.id,
#             'title': interview.title,
#             'date': interview.scheduled_date.strftime('%b %d, %Y'),
#             'time': interview.scheduled_date.strftime('%I:%M %p'),
#             'mentor': interview.interviewer_name or 'TBD',
#             'type': interview.interview_type.replace('_', ' ').title(),
#             'image': '/static/images/interview_default.png',
#             'link': interview.meeting_link or '#'
#         })
    
#     # Get past interviews
#     past_interviews = Interview.query\
#         .filter_by(student_id=student.id)\
#         .filter(
#             (Interview.scheduled_date < datetime.utcnow()) |
#             (Interview.status == 'completed')
#         )\
#         .order_by(Interview.scheduled_date.desc())\
#         .all()
    
#     # Format for template
#     past = []
#     for interview in past_interviews:
#         past.append({
#             'id': interview.id,
#             'title': interview.title,
#             'date': interview.scheduled_date.strftime('%b %d, %Y'),
#             'mentor': interview.interviewer_name or 'TBD',
#             'status': interview.status.title(),
#             'feedback_link': '#'
#         })
    
#     return render_template('dashboard/user/interview.html', upcoming=upcoming, past=past)


# @bp.route('/mock')
# @student_required
# def mock():
#     """View available mock tests"""
#     student = get_current_student()
    
#     # Get all active mock tests
#     mock_tests = MockTest.query\
#         .filter_by(is_active=True)\
#         .order_by(MockTest.created_at.desc())\
#         .all()
    
#     tests = []
#     for test in mock_tests:
#         # Determine status
#         now = datetime.utcnow()
#         if test.available_from and now < test.available_from:
#             status = 'Upcoming'
#         elif test.available_until and now > test.available_until:
#             status = 'Ended'
#         else:
#             status = 'Live'
        
#         # Check if student has attempted
#         attempt = TestAttempt.query\
#             .filter_by(student_id=student.id, mock_test_id=test.id)\
#             .first()
        
#         tests.append({
#             'id': test.id,
#             'title': test.title,
#             'date': test.available_from.strftime('%b %d, %Y') if test.available_from else 'Available Now',
#             'time': f"{test.available_from.strftime('%I:%M %p')} - {test.available_until.strftime('%I:%M %p')}" if test.available_from and test.available_until else 'Available All Day',
#             'duration': f'{test.duration_minutes // 60} Hour{"s" if test.duration_minutes >= 120 else ""}' if test.duration_minutes >= 60 else f'{test.duration_minutes} Minutes',
#             'questions': test.total_questions,
#             'status': status,
#             'attempted': attempt is not None,
#             'score': f'{attempt.percentage:.0f}%' if attempt and attempt.status == 'completed' else None,
#             'syllabus_link': '#'
#         })
    
#     return render_template('dashboard/user/mock.html', tests=tests)


# @bp.route('/prepkit')
# @student_required
# def prepkit():
#     """View resources/prep kit"""
#     student = get_current_student()
#     batch_ids = get_user_batch_ids(student.id)
    
#     # Get accessible resources
#     resources_query = Resource.query\
#         .filter(Resource.is_active == True)\
#         .filter(
#             (Resource.access_level == 'free') |
#             (Resource.target_batch_id.in_(batch_ids) if batch_ids else False)
#         )\
#         .order_by(Resource.created_at.desc())\
#         .all()
    
#     # Group resources by category
#     resources = {}
#     for resource in resources_query:
#         category = resource.category.title()
#         if category not in resources:
#             resources[category] = []
        
#         # Format file size
#         if resource.file_size:
#             size_mb = resource.file_size / (1024 * 1024)
#             size = f'{size_mb:.1f} MB'
#         else:
#             size = 'N/A'
        
#         resources[category].append({
#             'title': resource.title,
#             'type': resource.file_type.upper() if resource.file_type else 'Link',
#             'size': size,
#             'link': resource.file_url or resource.file_path or '#'
#         })
    
#     return render_template('dashboard/user/prepkit.html', resources=resources)


# @bp.route('/doubts')
# @student_required
# def doubts():
#     """Doubt forum (placeholder with sample data)"""
#     # This is a placeholder - can be enhanced with a proper doubt forum system
#     sample_doubts = [
#         {
#             'id': 1,
#             'title': 'How to solve this math problem?',
#             'content': 'I\'m having trouble understanding how to approach this calculus problem...',
#             'author': 'John Doe',
#             'timestamp': '2025-12-19 14:30',
#             'replies': 3,
#             'views': 24
#         },
#         {
#             'id': 2,
#             'title': 'Physics concept clarification needed',
#             'content': 'Can someone explain the concept of quantum entanglement in simple terms?',
#             'author': 'Jane Smith',
#             'timestamp': '2025-12-18 10:15',
#             'replies': 5,
#             'views': 42
#         }
#     ]
    
#     return render_template('dashboard/user/doubts.html', doubts=sample_doubts)




from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime
from app.extensions import db
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, TestAttempt, Announcement, Resource
)
from app.utils.decorators import student_required
from app.utils.helpers import get_current_student, get_user_batch_ids

bp = Blueprint('user', __name__)

@bp.route('/dashboard')
@student_required
def dashboard():
    student = get_current_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))

    enrollments = db.session.query(Enrollment, Batch)\
        .join(Batch, Enrollment.batch_id == Batch.id)\
        .filter(Enrollment.student_id == student.id)\
        .all()

    batch_ids = get_user_batch_ids(student.id)

    announcements = Announcement.query\
        .filter(
            (Announcement.target_audience == 'all') |
            (Announcement.target_audience == 'students') |
            (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
        )\
        .filter(Announcement.is_published == True)\
        .order_by(Announcement.published_at.desc())\
        .limit(5)\
        .all()

    # Determine enrollment status for group interviews
    is_enrolled = False
    for enrollment, batch in enrollments:
        if enrollment.payment_status in ['completed', 'partial']:
            is_enrolled = True
            break

    # Fetch queries
    from sqlalchemy import or_
    
    interview_filters = [Interview.student_id == student.id, Interview.target_audience == 'all_registered']
    if is_enrolled:
        interview_filters.append(Interview.target_audience == 'all_enrolled')
        
    upcoming_interviews = Interview.query\
        .filter(or_(*interview_filters))\
        .filter(Interview.scheduled_date >= datetime.utcnow())\
        .filter(Interview.status.in_(['scheduled', 'confirmed']))\
        .order_by(Interview.scheduled_date)\
        .limit(3)\
        .all()

    # Format upcoming interviews
    formatted_interviews = []
    for interview in upcoming_interviews:
        formatted_interviews.append({
            'id': interview.id,
            'title': interview.title,
            'date': interview.scheduled_date.strftime('%b %d, %Y'),
            'time': interview.scheduled_date.strftime('%I:%M %p'),
            'mentor': interview.interviewer_name or 'TBD',
            'type': interview.interview_type.replace('_', ' ').title(),
            'image_url': interview.image_url,  # New field
            'link': interview.meeting_link or '#',
            'status': interview.status
        })
        
    # Calculate Statistics
    total_mocks_count = MockTest.query.filter_by(is_active=True).count()
    attempted_mocks_count = TestAttempt.query.filter_by(student_id=student.id).count()
    
    interviews_done_count = Interview.query.filter_by(student_id=student.id, status='completed').count()
    
    # Simple readiness logic
    if attempted_mocks_count > 5:
        interview_readiness = "Excellent"
        readiness_color = "green"
    elif attempted_mocks_count > 0:
        interview_readiness = "Good"
        readiness_color = "blue"
    else:
        interview_readiness = "Beginner"
        readiness_color = "yellow"

    return render_template(
        'dashboard/user/user.html',
        student=student,
        announcements=announcements,
        enrollments=enrollments,
        upcoming_interviews=formatted_interviews,
        stats={
            'total_mocks': total_mocks_count,
            'attempted_mocks': attempted_mocks_count,
            'interviews_done': interviews_done_count,
            'readiness': interview_readiness,
            'readiness_color': readiness_color,
            'pending_doubts': 0
        }
    )


@bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    student = get_current_student()
    user = User.query.get(student.user_id)

    if request.method == 'POST':
        try:
            student.full_name = request.form.get('full_name', student.full_name)
            student.phone = request.form.get('phone', student.phone)

            new_email = request.form.get('email')
            if new_email and new_email != user.email:
                if User.query.filter_by(email=new_email).first():
                    flash('Email already exists', 'danger')
                else:
                    user.email = new_email

            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Update failed', 'danger')
            print(e)

    return render_template('dashboard/user/profile.html', student=student, user=user)


@bp.route('/announcement')
@student_required
def announcement():
    """View announcements"""
    student = get_current_student()
    batch_ids = get_user_batch_ids(student.id)
    
    # Get all relevant announcements
    announcements_query = Announcement.query\
        .filter(
            (Announcement.target_audience == 'all') |
            (Announcement.target_audience == 'students') |
            (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
        )\
        .filter(Announcement.is_published == True)\
        .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())\
        .all()
        
    # Serialize for frontend
    announcements_data = []
    for ann in announcements_query:
        announcements_data.append({
            'id': ann.id,
            'title': ann.title,
            'description': ann.content[:100] + '...' if len(ann.content) > 100 else ann.content,
            'content': ann.content,
            'date': ann.published_at.strftime('%b %d, %Y'),
            'category': 'System' if ann.priority == 'medium' else 'Academic' if ann.priority == 'high' else 'Important',
            'priority': ann.priority,
            'unread': True # Logic for unread status can be added later
        })
    
    return render_template('dashboard/user/announcement.html', announcements=announcements_data)
