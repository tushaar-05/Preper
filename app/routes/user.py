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


@bp.route('/prepkit')
@student_required
def prepkit():
    """View resources/prep kit"""
    student = get_current_student()
    batch_ids = get_user_batch_ids(student.id)
    
    # Get accessible resources
    resources_query = Resource.query\
        .filter(Resource.is_active == True)\
        .filter(
            (Resource.access_level == 'free') |
            (Resource.target_batch_id.in_(batch_ids) if batch_ids else False)
        )\
        .order_by(Resource.created_at.desc())\
        .all()
    
    # Group resources by category
    resources = {}
    for resource in resources_query:
        category = resource.category.title()
        if category not in resources:
            resources[category] = []
        
        # Format file size
        if resource.file_size:
            size_mb = resource.file_size / (1024 * 1024)
            size = f'{size_mb:.1f} MB'
        else:
            size = 'N/A'
        
        resources[category].append({
            'title': resource.title,
            'type': resource.file_type.upper() if resource.file_type else 'Link',
            'size': size,
            'link': resource.file_url or resource.file_path or '#'
        })
    
    return render_template('dashboard/user/prepkit.html', resources=resources, student=student)


@bp.route('/interview')
@student_required
def interview():
    """View interviews"""
    student = get_current_student()
    
    # Check enrollment status for group interviews
    enrollments = db.session.query(Enrollment).filter_by(student_id=student.id).all()
    is_enrolled = any(e.payment_status in ['completed', 'partial'] for e in enrollments)
    
    # Build query for upcoming interviews
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
        .all()
    
    # Format for template
    upcoming = []
    for interview in upcoming_interviews:
        upcoming.append({
            'id': interview.id,
            'title': interview.title,
            'date': interview.scheduled_date.strftime('%b %d, %Y'),
            'time': interview.scheduled_date.strftime('%I:%M %p'),
            'mentor': interview.interviewer_name or 'TBD',
            'type': interview.interview_type.replace('_', ' ').title(),
            'image': interview.image_url or '/static/images/interview_default.png',
            'link': interview.meeting_link or '#'
        })
    
    # Get past interviews
    past_interviews = Interview.query\
        .filter(or_(*interview_filters))\
        .filter(
            (Interview.scheduled_date < datetime.utcnow()) |
            (Interview.status == 'completed')
        )\
        .order_by(Interview.scheduled_date.desc())\
        .all()
    
    # Format for template
    past = []
    for interview in past_interviews:
        past.append({
            'id': interview.id,
            'title': interview.title,
            'date': interview.scheduled_date.strftime('%b %d, %Y'),
            'mentor': interview.interviewer_name or 'TBD',
            'status': interview.status.title(),
            'feedback_link': '#'
        })
    
    return render_template('dashboard/user/interview.html', upcoming=upcoming, past=past, student=student)