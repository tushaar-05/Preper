"""
Admin dashboard routes with database integration
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import current_user
from app.extensions import db
from app.utils.decorators import admin_required
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, Resource, Payment
)
from app.utils import admin_required, get_batch_status_color, get_interview_status_color
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@admin_required
def dashboard():
    admin = User.query.get(session.get('admin_id'))
    
    # Get statistics with proper error handling and default values
    try:
        total_payments = float(db.session.query(func.sum(Payment.amount)).scalar() or 0)
        stats = {
            'total_students': Student.query.count() or 0,
            'active_batches': Batch.query.filter_by(status='ongoing').count() or 0,
            'pending_payments': Payment.query.filter_by(status='pending').count() or 0,
            'upcoming_interviews': Interview.query.filter(
                Interview.scheduled_date > datetime.utcnow().date()
            ).count() or 0,
            'total_payments': total_payments,
            'total_revenue': total_payments,  # Added this line to match the template
            'enrollments_this_month': Enrollment.query.filter(
                func.extract('month', Enrollment.enrollment_date) == datetime.utcnow().month
            ).count() or 0
        }
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {str(e)}")
        # Provide default values in case of any error
        stats = {
            'total_students': 0,
            'active_batches': 0,
            'pending_payments': 0,
            'upcoming_interviews': 0,
            'total_payments': 0.0,
            'enrollments_this_month': 0
        }
    
    return render_template('dashboard/admin/admin.html', admin=admin, stats=stats)


@bp.route('/students')
@admin_required
def students():
    """List all students"""
    # Query students with their user info and enrollments
    students_data = db.session.query(Student, User)\
        .join(User, Student.user_id == User.id)\
        .order_by(Student.created_at.desc())\
        .all()
    
    # Get enrollment info for each student
    students_list = []
    for student, user in students_data:
        # Get student's batch
        enrollment = Enrollment.query.filter_by(student_id=student.id)\
            .join(Batch)\
            .first()
        
        batch_name = enrollment.batch.name if enrollment else 'Not Enrolled'
        
        students_list.append({
            'id': student.id,
            'name': student.full_name,
            'email': user.email,
            'batch': batch_name,
            'status': student.enrollment_status.title(),
            'joined_date': student.created_at.strftime('%b %d, %Y'),
            'avatar_color': 'bg-violet-100 text-violet-600'  # Can be randomized
        })
    
    return render_template('dashboard/admin/students.html', students=students_list)


@bp.route('/batches')
@admin_required
def batches():
    """List all batches"""
    batches_data = Batch.query.order_by(Batch.created_at.desc()).all()
    
    batches_list = []
    for batch in batches_data:
        batches_list.append({
            'id': batch.id,
            'name': batch.name,
            'status': batch.status.title(),
            'status_color': get_batch_status_color(batch.status),
            'students_count': batch.current_enrollment,
            'max_students': batch.max_students,
            'price': batch.discounted_price,
            'original_price': batch.original_price,
            'features': batch.features,
            'color': batch.color
        })
    
    return render_template('dashboard/admin/batches.html', batches=batches_list)


@bp.route('/interviews')
@admin_required
def interviews():
    """List all interviews"""
    interviews_data = db.session.query(Interview, Student, User)\
        .join(Student, Interview.student_id == Student.id)\
        .join(User, Student.user_id == User.id)\
        .order_by(Interview.scheduled_date.desc())\
        .all()
    
    interviews_list = []
    for interview, student, user in interviews_data:
        interviews_list.append({
            'id': interview.id,
            'student_name': student.full_name,
            'type': interview.interview_type.replace('_', ' ').title(),
            'mentor': interview.interviewer_name or 'TBD',
            'date': interview.scheduled_date.strftime('%b %d, %Y'),
            'time': interview.scheduled_date.strftime('%I:%M %p'),
            'status': interview.status.title(),
            'status_color': get_interview_status_color(interview.status)
        })
    
    return render_template('dashboard/admin/interviews.html', interviews=interviews_list)


@bp.route('/mocks')
@admin_required
def mocks():
    """List all mock tests"""
    mocks_data = MockTest.query.order_by(MockTest.created_at.desc()).all()
    
    mocks_list = []
    for mock in mocks_data:
        # Get attempt statistics
        attempts_count = TestAttempt.query.filter_by(mock_test_id=mock.id).count()
        avg_score = db.session.query(func.avg(TestAttempt.percentage))\
            .filter_by(mock_test_id=mock.id)\
            .filter(TestAttempt.status == 'completed')\
            .scalar()
        
        # Determine status based on availability
        now = datetime.utcnow()
        if mock.available_from and now < mock.available_from:
            status = 'Scheduled'
            status_color = 'bg-blue-100 text-blue-700'
        elif mock.available_until and now > mock.available_until:
            status = 'Ended'
            status_color = 'bg-gray-100 text-gray-600'
        else:
            status = 'Live'
            status_color = 'bg-green-100 text-green-700'
        
        mocks_list.append({
            'id': mock.id,
            'title': mock.title,
            'batch': 'All Batches',  # Can be enhanced with batch filtering
            'date': mock.available_from.strftime('%b %d, %Y') if mock.available_from else 'N/A',
            'attempts': attempts_count,
            'avg_score': f'{avg_score:.0f}%' if avg_score else '-',
            'status': status,
            'status_color': status_color
        })
    
    return render_template('dashboard/admin/mocks.html', mocks=mocks_list)


@bp.route('/announcements')
@admin_required
def announcements():
    """List all announcements"""
    announcements_data = Announcement.query\
        .order_by(Announcement.published_at.desc())\
        .all()
    
    announcements_list = []
    for announcement in announcements_data:
        # Determine type based on priority
        if announcement.priority == 'urgent':
            type_label = 'Important'
            type_color = 'bg-red-100 text-red-700'
        elif announcement.priority == 'high':
            type_label = 'Academic'
            type_color = 'bg-violet-100 text-violet-700'
        else:
            type_label = 'System'
            type_color = 'bg-gray-100 text-gray-700'
        
        # Get target
        if announcement.target_audience == 'all':
            target = 'All Users'
        elif announcement.target_batch_id:
            batch = Batch.query.get(announcement.target_batch_id)
            target = batch.name if batch else 'Specific Batch'
        else:
            target = announcement.target_audience.title()
        
        announcements_list.append({
            'id': announcement.id,
            'title': announcement.title,
            'date': announcement.published_at.strftime('%b %d, %Y'),
            'target': target,
            'content': announcement.content[:100] + '...' if len(announcement.content) > 100 else announcement.content,
            'type': type_label,
            'type_color': type_color
        })
    
    return render_template('dashboard/admin/announcements.html', announcements=announcements_list)


@bp.route('/resources')
@admin_required
def resources():
    """List all resources"""
    resources_data = Resource.query\
        .order_by(Resource.created_at.desc())\
        .all()
    
    resources_list = []
    for resource in resources_data:
        # Get batch name if batch-specific
        if resource.target_batch_id:
            batch = Batch.query.get(resource.target_batch_id)
            batch_name = batch.name if batch else 'Specific Batch'
        else:
            batch_name = 'All Batches'
        
        # Format file size
        if resource.file_size:
            size_mb = resource.file_size / (1024 * 1024)
            file_size = f'{size_mb:.1f} MB'
        else:
            file_size = 'N/A'
        
        resources_list.append({
            'id': resource.id,
            'title': resource.title,
            'category': resource.category.title(),
            'batch': batch_name,
            'uploaded_date': resource.created_at.strftime('%b %d, %Y'),
            'file_size': file_size,
            'downloads': resource.download_count,
            'type': resource.file_type.upper() if resource.file_type else 'Link'
        })
    
    return render_template('dashboard/admin/resources.html', resources=resources_list)


@bp.route('/settings')
@admin_required
def settings():
    """Platform settings page"""
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
