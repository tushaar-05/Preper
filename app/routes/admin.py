"""
Admin dashboard routes with database integration
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import current_user
from app.extensions import db
from app.utils.decorators import admin_required
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, Resource, Payment, Mentor
)
from app.utils import admin_required, get_batch_status_color, get_interview_status_color
from datetime import datetime, timedelta
from sqlalchemy import func, or_

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@admin_required
def dashboard():
    admin = User.query.get(session.get('admin_id'))
    
    # Get statistics with proper error handling and default values
    try:
        total_payments = float(db.session.query(func.sum(Payment.amount)).scalar() or 0)
        
        # Get total students (all registered)
        total_students = Student.query.count() or 0
        
        # Get total paid students
        total_paid_students = db.session.query(Enrollment.student_id)\
            .filter(Enrollment.payment_status.in_(['completed', 'partial']))\
            .distinct().count() or 0
        
        # Get newly enrolled students (last 7 days)
        one_week_ago = datetime.utcnow().date() - timedelta(days=7)
        new_enrollments = db.session.query(Enrollment.student_id)\
            .filter(Enrollment.enrollment_date >= one_week_ago)\
            .distinct().count() or 0
            
        stats = {
            'total_students': total_students,
            'total_paid': total_paid_students,
            'new_enrollments': new_enrollments,
            'active_batches': Batch.query.filter_by(status='active').count() or 0,
            'pending_payments': Payment.query.filter_by(status='pending').count() or 0,
            'upcoming_interviews': Interview.query.filter(
                Interview.scheduled_date > datetime.utcnow()
            ).count() or 0,
            'total_revenue': total_payments,
            'enrollments_this_month': Enrollment.query.filter(
                func.extract('month', Enrollment.enrollment_date) == datetime.utcnow().month
            ).count() or 0
        }
    except Exception as e:
        # Use a safe way to log if current_app is not imported
        print(f"Error fetching dashboard stats: {str(e)}")
        stats = {
            'total_students': 0,
            'new_enrollments': 0,
            'active_batches': 0,
            'pending_payments': 0,
            'upcoming_interviews': 0,
            'total_revenue': 0.0,
            'enrollments_this_month': 0
        }
    # Fetch recent enrollments (all registrations)
    recent_enrollments = db.session.query(Enrollment, Student, Batch, User)\
        .join(Student, Enrollment.student_id == Student.id)\
        .join(Batch, Enrollment.batch_id == Batch.id)\
        .join(User, Student.user_id == User.id)\
        .order_by(Enrollment.enrollment_date.desc())\
        .limit(5).all()
        
    # Fetch top mentors (from the new Mentor table)
    mentors_list = Mentor.query.filter_by(is_active=True).limit(3).all()
        
    mentors = []
    for m in mentors_list:
        mentors.append({
            'name': m.full_name,
            'initial': m.full_name[0] if m.full_name else '?',
            'role': m.role,
            'rating': f"{m.rating:.1f}"
        })
    
    # Fallback to interviewers if no mentors in table yet
    if not mentors:
        mentors_data = db.session.query(Interview.interviewer_name).distinct()\
            .filter(Interview.interviewer_name != None)\
            .limit(3).all()
        for m in mentors_data:
            mentors.append({
                'name': m[0],
                'initial': m[0][0] if m[0] else '?',
                'role': 'Guide',
                'rating': '4.9'
            })

    return render_template('dashboard/admin/admin.html', 
                         admin=admin, 
                         stats=stats, 
                         recent_enrollments=recent_enrollments,
                         mentors=mentors)


@bp.route('/add_mentor', methods=['POST'])
@admin_required
def add_mentor():
    """Add a new mentor"""
    try:
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role = request.form.get('role', 'Guide')
        
        if not full_name:
            flash('Mentor name is required', 'error')
            return redirect(url_for('admin.dashboard'))
            
        new_mentor = Mentor(
            full_name=full_name,
            email=email,
            role=role,
            rating=5.0
        )
        
        db.session.add(new_mentor)
        db.session.commit()
        flash(f'Mentor {full_name} added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding mentor: {str(e)}")
        flash('Error adding mentor. Please try again.', 'error')
        
    return redirect(url_for('admin.dashboard'))


@bp.route('/students')
@admin_required
def students():
    """List all students"""
    # Get filter parameters
    search_query = request.args.get('q', '')
    batch_filter = request.args.get('batch', '')
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Base query joining Student, User, Enrollment and Batch
    query = db.session.query(Student, User, Enrollment, Batch)\
        .join(User, Student.user_id == User.id)\
        .outerjoin(Enrollment, Student.id == Enrollment.student_id)\
        .outerjoin(Batch, Enrollment.batch_id == Batch.id)
    
    # Apply search filter
    if search_query:
        query = query.filter(or_(
            Student.full_name.ilike(f'%{search_query}%'),
            User.email.ilike(f'%{search_query}%'),
            Student.phone.ilike(f'%{search_query}%')
        ))
    
    # Apply batch filter
    if batch_filter:
        query = query.filter(Batch.name.ilike(f'%{batch_filter}%'))
    
    # Apply status filter
    if status_filter == 'active':
        # Enrolled: has a payment status that indicates completion
        query = query.filter(Enrollment.payment_status.in_(['completed', 'partial']))
    elif status_filter == 'pending':
        # Not Enrolled: either no enrollment or payment is pending
        query = query.filter(or_(
            Enrollment.id == None,
            Enrollment.payment_status == 'pending'
        ))
    
    # Order by joined date
    query = query.order_by(Student.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Convert items to list for template
    students_list = []
    for student, user, enrollment, batch in pagination.items:
        # Determine if they are enrolled in any batch (paid)
        has_paid = enrollment and enrollment.payment_status in ['completed', 'partial']
        batch_name = batch.name if (batch and has_paid) else '-'
        status = 'Enrolled' if has_paid else 'Not Enrolled'
        
        students_list.append({
            'id': student.id,
            'name': student.full_name,
            'email': user.email,
            'phone': student.phone or 'N/A',
            'batch': batch_name,
            'status': status,
            'joined_date': student.created_at.strftime('%b %d, %Y'),
            'avatar_color': 'bg-violet-100 text-violet-600'
        })
    
    return render_template('dashboard/admin/students.html', 
                          students=students_list, 
                          pagination=pagination,
                          q=search_query,
                          selected_batch=batch_filter,
                          selected_status=status_filter)


@bp.route('/mentors')
@admin_required
def mentors():
    """List all mentors"""
    mentors_data = Mentor.query.order_by(Mentor.created_at.desc()).all()
    
    mentors_list = []
    for mentor in mentors_data:
        mentors_list.append({
            'id': mentor.id,
            'name': mentor.full_name,
            'email': mentor.email,
            'role': mentor.role,
            'rating': f"{mentor.rating:.1f}",
            'status': 'Active' if mentor.is_active else 'Inactive',
            'joined_date': mentor.created_at.strftime('%b %d, %Y'),
            'initial': mentor.full_name[0] if mentor.full_name else '?'
        })
    
    return render_template('dashboard/admin/mentors.html', mentors=mentors_list)


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
            'price': int(batch.discounted_price),
            'original_price': int(batch.original_price),
            'features': batch.features,
            'color': batch.color,
            'description': batch.description
        })
    
    return render_template('dashboard/admin/batches.html', batches=batches_list)

@bp.route('/batches/create', methods=['POST'])
@admin_required
def batches_create():
    """Create a new batch"""
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        original_price = float(request.form.get('original_price', 0))
        discounted_price = float(request.form.get('discounted_price', 0))
        max_students = int(request.form.get('max_students', 50))
        status = request.form.get('status', 'upcoming')
        color = request.form.get('color', 'violet')
        features = request.form.getlist('features[]')
        
        if not name:
            flash('Batch name is required', 'error')
            return redirect(url_for('admin.batches'))
            
        batch = Batch(
            name=name,
            description=description,
            original_price=original_price,
            discounted_price=discounted_price,
            max_students=max_students,
            status=status,
            color=color
        )
        batch.features = features if features else []
        
        db.session.add(batch)
        db.session.commit()
        flash(f'Batch "{name}" created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating batch: {str(e)}', 'error')
        
    return redirect(url_for('admin.batches'))

@bp.route('/batches/edit/<int:batch_id>', methods=['POST'])
@admin_required
def batches_edit(batch_id):
    """Edit an existing batch"""
    try:
        batch = Batch.query.get_or_404(batch_id)
        
        batch.name = request.form.get('name')
        batch.description = request.form.get('description')
        batch.original_price = float(request.form.get('original_price', 0))
        batch.discounted_price = float(request.form.get('discounted_price', 0))
        batch.max_students = int(request.form.get('max_students', 50))
        batch.status = request.form.get('status')
        batch.color = request.form.get('color')
        
        features = request.form.getlist('features[]')
        batch.features = features if features else []
        
        db.session.commit()
        flash(f'Batch "{batch.name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating batch: {str(e)}', 'error')
        
    return redirect(url_for('admin.batches'))

@bp.route('/batches/delete/<int:batch_id>', methods=['POST'])
@admin_required
def batches_delete(batch_id):
    """Delete a batch"""
    try:
        batch = Batch.query.get_or_404(batch_id)
        
        # Check if there are enrollments
        if batch.current_enrollment > 0:
            flash(f'Cannot delete batch "{batch.name}" because it has active enrollments.', 'error')
            return redirect(url_for('admin.batches'))
            
        db.session.delete(batch)
        db.session.commit()
        flash(f'Batch deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting batch: {str(e)}', 'error')
        
    return redirect(url_for('admin.batches'))


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
        # Improve type display
        type_display = interview.interview_type.replace('_', ' ').title()
        if interview.interview_type == 'personal':
            type_display = '1:1 Interview'
        elif interview.interview_type == 'meeting':
            type_display = 'Meeting'
            
        interviews_list.append({
            'id': interview.id,
            'student_name': student.full_name,
            'student_id': student.id,
            'type': type_display,
            'raw_type': interview.interview_type,
            'mentor': interview.interviewer_name or 'TBD',
            'date': interview.scheduled_date.strftime('%b %d, %Y'),
            'time': interview.scheduled_date.strftime('%I:%M %p'),
            'raw_date': interview.scheduled_date.strftime('%Y-%m-%d'),
            'raw_time': interview.scheduled_date.strftime('%H:%M'),
            'status': interview.status.title(),
            'raw_status': interview.status,
            'status_color': get_interview_status_color(interview.status),
            'title': interview.title,
            'description': interview.description,
            'feedback': interview.feedback,
            'rating': interview.rating
        })
    
    # Fetch students and mentors for scheduling modal
    all_students = Student.query.order_by(Student.full_name).all()
    all_mentors = Mentor.query.order_by(Mentor.full_name).all()
    
    return render_template('dashboard/admin/interviews.html', 
                          interviews=interviews_list,
                          students=all_students,
                          mentors=all_mentors)

@bp.route('/interviews/schedule', methods=['POST'])
@admin_required
def interviews_schedule():
    """Schedule a new interview or meeting"""
    try:
        student_id = request.form.get('student_id')
        mentor_id = request.form.get('mentor_id')
        interview_type = request.form.get('type')
        title = request.form.get('title')
        description = request.form.get('description')
        scheduled_date_str = request.form.get('date')
        scheduled_time_str = request.form.get('time')
        
        if not student_id or not scheduled_date_str or not scheduled_time_str:
            flash('Missing required fields for scheduling', 'error')
            return redirect(url_for('admin.interviews'))
            
        scheduled_datetime = datetime.strptime(f"{scheduled_date_str} {scheduled_time_str}", "%Y-%m-%d %H:%M")
        
        interviewer_name = None
        interviewer_email = None
        if mentor_id:
            mentor = Mentor.query.get(mentor_id)
            if mentor:
                interviewer_name = mentor.full_name
                interviewer_email = mentor.email
        
        interview = Interview(
            student_id=student_id,
            interview_type=interview_type,
            title=title or f"{interview_type.title()} with {interviewer_name or 'Mentor'}",
            description=description,
            scheduled_date=scheduled_datetime,
            interviewer_name=interviewer_name,
            interviewer_email=interviewer_email,
            status='scheduled'
        )
        
        db.session.add(interview)
        db.session.commit()
        flash('Interview scheduled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error scheduling interview: {str(e)}', 'error')
        
    return redirect(url_for('admin.interviews'))

@bp.route('/interviews/update/<int:interview_id>', methods=['POST'])
@admin_required
def interviews_update(interview_id):
    """Update an existing interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        
        interview.student_id = request.form.get('student_id')
        mentor_id = request.form.get('mentor_id')
        interview.interview_type = request.form.get('type')
        interview.title = request.form.get('title')
        interview.description = request.form.get('description')
        interview.status = request.form.get('status')
        interview.feedback = request.form.get('feedback')
        rating = request.form.get('rating')
        if rating:
            interview.rating = int(rating)
            
        scheduled_date_str = request.form.get('date')
        scheduled_time_str = request.form.get('time')
        
        if scheduled_date_str and scheduled_time_str:
            interview.scheduled_date = datetime.strptime(f"{scheduled_date_str} {scheduled_time_str}", "%Y-%m-%d %H:%M")
        
        if mentor_id:
            mentor = Mentor.query.get(mentor_id)
            if mentor:
                interview.interviewer_name = mentor.full_name
                interview.interviewer_email = mentor.email
        
        db.session.commit()
        flash('Interview updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating interview: {str(e)}', 'error')
        
    return redirect(url_for('admin.interviews'))

@bp.route('/interviews/delete/<int:interview_id>', methods=['POST'])
@admin_required
def interviews_delete(interview_id):
    """Delete an interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        db.session.delete(interview)
        db.session.commit()
        flash('Interview deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting interview: {str(e)}', 'error')
        
    return redirect(url_for('admin.interviews'))


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
