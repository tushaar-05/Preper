from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime
from app.extensions import db
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, AnnouncementRead, Resource
)
from app.utils.decorators import student_required, paid_student_required
from app.utils.helpers import get_current_student, get_user_batch_ids

bp = Blueprint('user', __name__)

@bp.context_processor
def inject_payment_status():
    student = get_current_student()
    is_paid = False
    if student:
        enrollment = Enrollment.query.filter_by(student_id=student.id)\
            .filter(Enrollment.payment_status.in_(['completed', 'partial']))\
            .first()
        if enrollment:
            is_paid = True
    return dict(is_paid=is_paid)

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

    # Get batch IDs
    batch_ids = get_user_batch_ids(student.id)

    # Get unread announcements count
    unread_announcements_count = Announcement.query\
        .filter(
            (Announcement.target_audience == 'all') |
            (Announcement.target_audience == 'students') |
            (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
        )\
        .filter(Announcement.is_published == True)\
        .outerjoin(AnnouncementRead, (AnnouncementRead.announcement_id == Announcement.id) & (AnnouncementRead.student_id == student.id))\
        .filter(AnnouncementRead.id == None)\
        .count()

    # Get latest announcements for dashboard display
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
    from sqlalchemy import or_
    total_mocks_count = MockTest.query.filter(
        MockTest.is_active == True
    ).filter(
        or_(
            MockTest.is_free == True,
            MockTest.batch_id.in_(batch_ids) if batch_ids else False,
            MockTest.batch_id == None
        )
    ).count()
    
    attempted_mocks_count = TestAttempt.query.filter_by(
        student_id=student.id,
        status='completed'
    ).count()
    
    interviews_done_count = Interview.query.filter_by(student_id=student.id, status='completed').count()
    
    # Calculate pending doubts
    from app.models.doubt import Doubt
    pending_doubts = Doubt.query.filter_by(student_id=student.id, status='pending').count()
    
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
        unread_announcements_count=unread_announcements_count,
        enrollments=enrollments,
        upcoming_interviews=formatted_interviews,
        stats={
            'total_mocks': total_mocks_count,
            'attempted_mocks': attempted_mocks_count,
            'interviews_done': interviews_done_count,
            'readiness': interview_readiness,
            'readiness_color': readiness_color,
            'pending_doubts': pending_doubts
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

    # Format date of birth
    dob_formatted = student.date_of_birth.strftime('%d %B %Y') if student.date_of_birth else 'Not set'
    
    # Format member since
    member_since = student.created_at.strftime('%b %Y') if student.created_at else 'N/A'
    
    # Get enrollment info - check if student is actually enrolled
    enrollment = Enrollment.query.filter_by(student_id=student.id).first()
    if enrollment and enrollment.batch:
        batch_name = enrollment.batch.name
    else:
        batch_name = 'Not enrolled'
    
    # Display campus preference with proper capitalization
    if student.preferred_batch:
        preferred_campus = student.preferred_batch.capitalize()
    else:
        preferred_campus = 'Not set'
    
    profile_data = {
        'full_name': student.full_name,
        'email': user.email if user else 'N/A',
        'phone': student.phone or 'Not set',
        'date_of_birth': dob_formatted,
        'city': f"{student.city}, {student.state}" if student.city and student.state else student.city or student.state or 'Not set',
        'preferred_batch': preferred_campus,
        'member_since': member_since,
        'batch_name': batch_name,
        'education_level': student.education_level or 'Not set',
        'institution_name': student.institution_name or 'Not set'
    }

    return render_template('dashboard/user/profile.html', student=student, user=user, profile=profile_data)


@bp.route('/announcement')
@paid_student_required
def announcement():
    """View announcements"""
    student = get_current_student()
    batch_ids = get_user_batch_ids(student.id)
    
    # Get all relevant announcements with read status
    announcements_query = db.session.query(Announcement, AnnouncementRead.id.label('is_read'))\
        .filter(
            (Announcement.target_audience == 'all') |
            (Announcement.target_audience == 'students') |
            (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
        )\
        .filter(Announcement.is_published == True)\
        .outerjoin(AnnouncementRead, (AnnouncementRead.announcement_id == Announcement.id) & (AnnouncementRead.student_id == student.id))\
        .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())\
        .all()
        
    # Serialize for frontend
    announcements_data = []
    for ann, read_id in announcements_query:
        announcements_data.append({
            'id': ann.id,
            'title': ann.title,
            'description': ann.content[:100] + '...' if len(ann.content) > 100 else ann.content,
            'content': ann.content,
            'date': ann.published_at.strftime('%b %d, %Y'),
            'category': 'System' if ann.priority == 'medium' else 'Academic' if ann.priority == 'high' else 'Important',
            'priority': ann.priority,
            'unread': read_id is None
        })
    
    return render_template('dashboard/user/announcement.html', announcements=announcements_data, student=student)


@bp.route('/announcement/mark-read/<int:ann_id>', methods=['POST'])
@student_required
def mark_announcement_read(ann_id):
    """Mark a single announcement as read"""
    student = get_current_student()
    if not student:
        return {"error": "Unauthorized"}, 401
    
    # Check if a record already exists
    existing = AnnouncementRead.query.filter_by(student_id=student.id, announcement_id=ann_id).first()
    if not existing:
        new_read = AnnouncementRead(student_id=student.id, announcement_id=ann_id)
        db.session.add(new_read)
        db.session.commit()
    
    return {"status": "success"}


@bp.route('/announcement/mark-all-read', methods=['POST'])
@student_required
def mark_all_announcements_read():
    """Mark all relevant announcements as read for the student"""
    student = get_current_student()
    if not student:
        return {"error": "Unauthorized"}, 401
    
    batch_ids = get_user_batch_ids(student.id)
    
    # Get all unread relevant announcements
    unread_announcements = Announcement.query\
        .filter(
            (Announcement.target_audience == 'all') |
            (Announcement.target_audience == 'students') |
            (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
        )\
        .filter(Announcement.is_published == True)\
        .outerjoin(AnnouncementRead, (AnnouncementRead.announcement_id == Announcement.id) & (AnnouncementRead.student_id == student.id))\
        .filter(AnnouncementRead.id == None)\
        .all()
    
    for ann in unread_announcements:
        read_record = AnnouncementRead(student_id=student.id, announcement_id=ann.id)
        db.session.add(read_record)
    
    db.session.commit()
    return {"status": "success"}


@bp.route('/prepkit')
@paid_student_required
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
        
        link = resource.file_url or resource.file_path or '#'
        if link and 'cloudinary.com' in link and resource.file_type and resource.file_type.lower() == 'pdf':
            if '/upload/' in link and '/fl_attachment' not in link:
                link = link.replace('/upload/', '/upload/fl_attachment/')

        resources[category].append({
            'title': resource.title,
            'type': resource.file_type.upper() if resource.file_type else 'Link',
            'size': size,
            'link': link
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


@bp.route('/doubts')
@paid_student_required
def doubts():
    """View doubts forum"""
    from app.models.doubt import Doubt, DoubtReply
    student = get_current_student()
    
    # Fetch all doubts from database
    doubts_query = Doubt.query.order_by(Doubt.created_at.desc()).all()
    
    # Format doubts for template
    doubts_list = []
    for doubt in doubts_query:
        # Calculate time ago
        time_diff = datetime.utcnow() - doubt.created_at
        if time_diff.days > 0:
            timestamp = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            timestamp = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = max(1, time_diff.seconds // 60)
            timestamp = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        doubts_list.append({
            'id': doubt.id,
            'title': doubt.title,
            'content': doubt.content,
            'author': doubt.student.full_name,
            'timestamp': timestamp,
            'replies': doubt.replies.count(),
            'views': doubt.views,
            'category': doubt.category
        })
    
    return render_template('dashboard/user/doubts.html', doubts=doubts_list, student=student)


@bp.route('/post_doubt', methods=['POST'])
@student_required
def post_doubt():
    """Handle posting a new doubt"""
    from app.models.doubt import Doubt
    student = get_current_student()
    
    # Get form data
    title = request.form.get('title')
    category = request.form.get('category', 'General Query')
    content = request.form.get('content')
    
    # Validate input
    if not title or not content:
        flash('Please provide both a title and description for your doubt.', 'danger')
        return redirect(url_for('user.doubts'))
    
    try:
        # Create new doubt
        new_doubt = Doubt(
            student_id=student.id,
            title=title,
            category=category,
            content=content,
            status='pending'
        )
        
        db.session.add(new_doubt)
        db.session.commit()
        
        flash('Your doubt has been posted successfully! Our team will respond soon.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to post doubt. Please try again.', 'danger')
        print(f"Error posting doubt: {e}")
    
    return redirect(url_for('user.doubts'))


@bp.route('/doubts/<int:doubt_id>')
@student_required
def doubt_detail(doubt_id):
    """View individual doubt with replies"""
    from app.models.doubt import Doubt, DoubtReply
    student = get_current_student()
    
    # Get the doubt
    doubt = Doubt.query.get_or_404(doubt_id)
    
    # Increment view count only once per session
    viewed_doubts = session.get('viewed_doubts', [])
    if doubt_id not in viewed_doubts:
        doubt.views += 1
        viewed_doubts.append(doubt_id)
        session['viewed_doubts'] = viewed_doubts
        db.session.commit()
    
    # Calculate time ago for doubt
    time_diff = datetime.utcnow() - doubt.created_at
    if time_diff.days > 0:
        doubt_timestamp = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
    elif time_diff.seconds >= 3600:
        hours = time_diff.seconds // 3600
        doubt_timestamp = f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        minutes = max(1, time_diff.seconds // 60)
        doubt_timestamp = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    # Format doubt data
    doubt_data = {
        'id': doubt.id,
        'title': doubt.title,
        'content': doubt.content,
        'category': doubt.category,
        'status': doubt.status,
        'author': doubt.student.full_name,
        'timestamp': doubt_timestamp,
        'created_at': doubt.created_at.strftime('%B %d, %Y at %I:%M %p'),
        'views': doubt.views,
        'replies_count': doubt.replies.count()
    }
    
    # Get all replies
    replies_query = doubt.replies.order_by(DoubtReply.created_at.asc()).all()
    replies_list = []
    for reply in replies_query:
        # Calculate time ago for reply
        reply_time_diff = datetime.utcnow() - reply.created_at
        if reply_time_diff.days > 0:
            reply_timestamp = f"{reply_time_diff.days} day{'s' if reply_time_diff.days > 1 else ''} ago"
        elif reply_time_diff.seconds >= 3600:
            reply_hours = reply_time_diff.seconds // 3600
            reply_timestamp = f"{reply_hours} hour{'s' if reply_hours > 1 else ''} ago"
        else:
            reply_minutes = max(1, reply_time_diff.seconds // 60)
            reply_timestamp = f"{reply_minutes} minute{'s' if reply_minutes > 1 else ''} ago"
        
        # Get user info
        user = User.query.get(reply.user_id)
        author_name = user.email.split('@')[0] if user else 'Unknown'
        
        replies_list.append({
            'id': reply.id,
            'content': reply.content,
            'author': author_name,
            'is_staff': reply.is_staff_reply,
            'timestamp': reply_timestamp,
            'created_at': reply.created_at.strftime('%B %d, %Y at %I:%M %p')
        })
    
    return render_template('dashboard/user/doubt_detail.html', 
                         doubt=doubt_data, 
                         replies=replies_list,
                         student=student)


@bp.route('/doubts/<int:doubt_id>/reply', methods=['POST'])
@student_required
def post_reply(doubt_id):
    """Post a reply to a doubt"""
    from app.models.doubt import Doubt, DoubtReply
    student = get_current_student()
    
    # Get form data
    content = request.form.get('content')
    
    # Validate input
    if not content:
        flash('Please provide a reply.', 'danger')
        return redirect(url_for('user.doubt_detail', doubt_id=doubt_id))
    
    try:
        # Get the doubt
        doubt = Doubt.query.get_or_404(doubt_id)
        
        # Create new reply
        new_reply = DoubtReply(
            doubt_id=doubt_id,
            user_id=student.user_id,
            content=content,
            is_staff_reply=False
        )
        
        db.session.add(new_reply)
        db.session.commit()
        
        flash('Your reply has been posted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to post reply. Please try again.', 'danger')
        print(f"Error posting reply: {e}")
    
    return redirect(url_for('user.doubt_detail', doubt_id=doubt_id))
@bp.route('/mock')
@paid_student_required
def mock():
    """View available mock tests"""
    student = get_current_student()
    batch_ids = get_user_batch_ids(student.id)
    
    # Filter tests: either free or assigned to student's batches
    # Filter for active tests only
    from sqlalchemy import or_
    tests_query = MockTest.query.filter(
        MockTest.is_active == True
    ).filter(
        or_(
            MockTest.is_free == True,
            MockTest.batch_id.in_(batch_ids) if batch_ids else False,
            MockTest.batch_id == None
        )
    ).order_by(MockTest.available_from.desc()).all()
    
    formatted_tests = []
    now = datetime.now()
    
    for test in tests_query:
        # Check if attempt already exists
        attempt = TestAttempt.query.filter_by(
            student_id=student.id, 
            mock_test_id=test.id,
            status='completed'
        ).first()
        
        # Determine status
        status = 'Live'
        if test.available_from and test.available_until:
            if now < test.available_from:
                status = 'Upcoming'
            elif now > test.available_until:
                status = 'Ended'
            else:
                status = 'Live'
        elif test.available_from:
            status = 'Live' if now >= test.available_from else 'Upcoming'
        elif test.available_until:
            status = 'Live' if now <= test.available_until else 'Ended'
        else:
            status = 'Live'
            
        formatted_tests.append({
            'id': test.id,
            'title': test.title,
            'date': test.available_from.strftime('%b %d, %Y') if test.available_from else 'Anytime',
            'time': test.available_from.strftime('%I:%M %p') if test.available_from else 'Flexible',
            'duration': f"{test.duration_minutes} mins",
            'questions': test.total_questions,
            'status': status,
            'attempted': attempt is not None,
            'attempt_id': attempt.id if attempt else None,
            'syllabus_link': '#' # Can be added to model if needed
        })
        
    return render_template('dashboard/user/mock.html', tests=formatted_tests, student=student)


@bp.route('/mock/<int:test_id>/start')
@student_required
def mock_start(test_id):
    """View test instructions before starting"""
    student = get_current_student()
    test = MockTest.query.get_or_404(test_id)
    
    # Check if already attempted
    attempt = TestAttempt.query.filter_by(
        student_id=student.id, 
        mock_test_id=test.id,
        status='completed'
    ).first()
    
    if attempt:
        flash('You have already completed this test.', 'info')
        return redirect(url_for('user.mock_result', attempt_id=attempt.id))
        
    return render_template('dashboard/user/mock_start.html', test=test, student=student)


@bp.route('/mock/<int:test_id>/take')
@student_required
def mock_take(test_id):
    """The actual test taking interface"""
    student = get_current_student()
    test = MockTest.query.get_or_404(test_id)
    
    # Check if already attempted completed
    existing_attempt = TestAttempt.query.filter_by(
        student_id=student.id, 
        mock_test_id=test.id,
        status='completed'
    ).first()
    
    if existing_attempt:
        flash('You have already completed this test.', 'info')
        return redirect(url_for('user.mock_result', attempt_id=existing_attempt.id))
    
    attempt = TestAttempt.query.filter_by(
        student_id=student.id, 
        mock_test_id=test.id,
        status='in_progress'
    ).first()
    
    if not attempt:
        attempt = TestAttempt(
            student_id=student.id,
            mock_test_id=test.id,
            status='in_progress',
            started_at=datetime.now()
        )
        db.session.add(attempt)
        db.session.commit()
    
    # Calculate remaining time
    now = datetime.now()
    elapsed = (now - attempt.started_at).total_seconds() / 60
    remaining_minutes = max(0, test.duration_minutes - elapsed)
    
    if remaining_minutes <= 0:
        flash('Time limit exceeded for this test.', 'warning')
        return redirect(url_for('user.mock'))
        
    # Get questions
    questions = test.questions.order_by(Question.question_number).all()
    questions_data = [q.to_dict() for q in questions]
    
    return render_template('dashboard/user/mock_take.html', 
                         test=test, 
                         attempt=attempt, 
                         questions=questions_data,
                         remaining_seconds=int(remaining_minutes * 60),
                         student=student)


@bp.route('/mock/<int:test_id>/submit', methods=['POST'])
@student_required
def mock_submit(test_id):
    """Process test submission"""
    student = get_current_student()
    test = MockTest.query.get_or_404(test_id)
    
    attempt = TestAttempt.query.filter_by(
        student_id=student.id, 
        mock_test_id=test.id,
        status='in_progress'
    ).first()
    
    if not attempt:
        flash('No active attempt found for this test.', 'danger')
        return redirect(url_for('user.mock'))
        
    # Process answers from form
    user_answers = {}
    for key, value in request.form.items():
        if key.startswith('q_'):
            q_id = key.split('_')[1]
            user_answers[q_id] = value
            
    attempt.answers = user_answers
    attempt.submitted_at = datetime.now()
    attempt.status = 'completed'
    
    # Grading logic
    correct_count = 0
    wrong_count = 0
    total_score = 0.0
    questions = test.questions.all()
    
    for q in questions:
        ans = user_answers.get(str(q.id))
        if ans == q.correct_answer:
            correct_count += 1
            total_score += q.marks if q.marks else 1
        elif ans:
            wrong_count += 1
            total_score -= q.negative_marks if q.negative_marks else 0
            
    attempt.correct_answers = correct_count
    attempt.wrong_answers = wrong_count
    attempt.unanswered = len(questions) - (correct_count + wrong_count)
    attempt.score = total_score
    attempt.total_marks = test.total_marks
    attempt.percentage = (total_score / test.total_marks * 100) if test.total_marks > 0 else 0
    
    # Calculate time taken
    time_taken = (attempt.submitted_at - attempt.started_at).seconds // 60
    attempt.time_taken_minutes = time_taken
    
    db.session.commit()
    
    flash('Test submitted successfully! Here are your results.', 'success')
    return redirect(url_for('user.mock_result', attempt_id=attempt.id))


@bp.route('/mock/result/<int:attempt_id>')
@student_required
def mock_result(attempt_id):
    """View test attempt results"""
    student = get_current_student()
    attempt = TestAttempt.query.get_or_404(attempt_id)
    
    if attempt.student_id != student.id:
        flash('Unauthorized access to test results.', 'danger')
        return redirect(url_for('user.mock'))
        
    test = attempt.mock_test
    questions = test.questions.order_by(Question.question_number).all()
    
    # Map answers for easy lookup in template
    answers = attempt.answers
    
    return render_template('dashboard/user/mock_result.html', 
                         attempt=attempt, 
                         test=test, 
                         questions=questions, 
                         answers=answers,
                         student=student)

@bp.route('/enrollment-required')
@student_required
def enrollment_required_page():
    """Show page asking user to enroll"""
    student = get_current_student()
    return render_template('dashboard/user/enrollment_required.html', student=student)
