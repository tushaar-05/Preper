from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime, timedelta
from sqlalchemy import or_
from app.extensions import db, cache, IST
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, AnnouncementRead, Resource, Doubt, DoubtReply
)
from app.utils.decorators import student_required, paid_student_required
from app.utils.helpers import get_current_student, get_user_batch_ids
from app.utils.storage import get_download_url

bp = Blueprint('user', __name__)

@bp.context_processor
def inject_payment_status():
    student = get_current_student()
    return dict(is_paid=_check_payment_cached(student.id) if student else False)

@cache.memoize(timeout=60)
def _check_payment_cached(student_id):
    student = Student.query.get(student_id)
    return student.is_paid if student else False

@bp.route('/dashboard')
@student_required
def dashboard():
    student = get_current_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))

    batch_ids = get_user_batch_ids(student.id)
    enrollments = db.session.query(Enrollment, Batch).join(Batch).filter(Enrollment.student_id == student.id).all()

    # Announcements Logic
    ann_filter = (Announcement.target_audience.in_(['all', 'students'])) | (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False)
    unread_count = Announcement.query.filter(ann_filter, Announcement.is_published == True)\
        .outerjoin(AnnouncementRead, (AnnouncementRead.announcement_id == Announcement.id) & (AnnouncementRead.student_id == student.id))\
        .filter(AnnouncementRead.id == None).count()
    
    announcements = Announcement.query.filter(ann_filter, Announcement.is_published == True)\
        .order_by(Announcement.published_at.desc()).limit(5).all()

    # Interviews Logic
    interview_filters = [Interview.student_id == student.id, Interview.target_audience == 'all_registered']
    if student.is_paid:
        interview_filters.append(Interview.target_audience == 'all_enrolled')
        
    upcoming_interviews = Interview.query.filter(or_(*interview_filters), Interview.scheduled_date >= datetime.utcnow(), Interview.status.in_(['scheduled', 'confirmed']))\
        .order_by(Interview.scheduled_date).limit(3).all()

    formatted_interviews = [{
        'id': i.id, 'title': i.title, 'mentor': i.interviewer_name or 'TBD',
        'date': i.scheduled_date.strftime('%b %d, %Y'), 'time': i.scheduled_date.strftime('%I:%M %p'),
        'type': i.interview_type.replace('_', ' ').title(), 'image_url': i.image_url,
        'link': i.meeting_link or '#', 'status': i.status
    } for i in upcoming_interviews]
        
    # Calculate Statistics
    total_mocks = MockTest.query.filter(MockTest.is_active == True).filter(
        or_(MockTest.is_free == True, MockTest.batch_id.in_(batch_ids) if batch_ids else False, MockTest.batch_id == None)
    ).count()
    
    attempts = TestAttempt.query.filter_by(student_id=student.id, status='completed').count()
    interviews_done = Interview.query.filter_by(student_id=student.id, status='completed').count()
    pending_doubts = Doubt.query.filter_by(student_id=student.id, status='pending').count()
    
    # Simple readiness logic
    readiness = "Excellent" if attempts > 5 else "Good" if attempts > 0 else "Beginner"
    color = "green" if attempts > 5 else "blue" if attempts > 0 else "yellow"

    return render_template('dashboard/user/user.html',
        student=student, announcements=announcements, unread_announcements_count=unread_count,
        enrollments=enrollments, upcoming_interviews=formatted_interviews,
        stats={'total_mocks': total_mocks, 'attempted_mocks': attempts, 'interviews_done': interviews_done,
               'readiness': readiness, 'readiness_color': color, 'pending_doubts': pending_doubts}
    )

@bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    student = get_current_student()
    user = User.query.get(student.user_id)

    if request.method == 'POST':
        try:
            for field in ['full_name', 'phone', 'city', 'state', 'preferred_batch', 'education_level', 'institution_name']:
                setattr(student, field, request.form.get(field, getattr(student, field)))

            dob = request.form.get('date_of_birth')
            if dob:
                try: student.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
                except ValueError: pass

            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception:
            db.session.rollback()
            flash('Update failed', 'danger')

    profile_data = {
        'full_name': student.full_name, 'email': user.email if user else 'N/A', 'phone': student.phone or 'Not set',
        'date_of_birth': student.date_of_birth.strftime('%d %B %Y') if student.date_of_birth else 'Not set',
        'preferred_batch': student.preferred_batch or 'Not set',
        'member_since': student.created_at.strftime('%b %Y') if student.created_at else 'N/A',
        'batch_name': getattr(Enrollment.query.filter_by(student_id=student.id).first(), 'batch', None).name if Enrollment.query.filter_by(student_id=student.id).first() else 'Not enrolled',
        'city': student.city or 'Not set', 'state': student.state or 'Not set',
        'dob_for_input': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
        'education_level': student.education_level or 'Not set', 'institution_name': student.institution_name or 'Not set'
    }
    return render_template('dashboard/user/profile.html', student=student, user=user, profile=profile_data)

@bp.route('/announcement')
@paid_student_required
def announcement():
    """View announcements"""
    student = get_current_student()
    batch_ids = get_user_batch_ids(student.id)
    
    announcements_query = db.session.query(Announcement, AnnouncementRead.id.label('is_read'))\
        .filter((Announcement.target_audience.in_(['all', 'students'])) | (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False))\
        .filter(Announcement.is_published == True)\
        .outerjoin(AnnouncementRead, (AnnouncementRead.announcement_id == Announcement.id) & (AnnouncementRead.student_id == student.id))\
        .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc()).all()
        
    announcements_data = [{
        'id': ann.id, 'title': ann.title, 'description': ann.content[:100] + '...' if len(ann.content) > 100 else ann.content,
        'content': ann.content, 'date': ann.published_at.strftime('%b %d, %Y'),
        'category': 'Important' if ann.priority == 'urgent' else 'Academic' if ann.priority == 'high' else 'System',
        'priority': ann.priority, 'unread': read_id is None
    } for ann, read_id in announcements_query]
    
    return render_template('dashboard/user/announcement.html', announcements=announcements_data, student=student)

@bp.route('/announcement/mark-read/<int:ann_id>', methods=['POST'])
@student_required
def mark_announcement_read(ann_id):
    student = get_current_student()
    if not AnnouncementRead.query.filter_by(student_id=student.id, announcement_id=ann_id).first():
        db.session.add(AnnouncementRead(student_id=student.id, announcement_id=ann_id))
        db.session.commit()
    return {"status": "success"}

@bp.route('/announcement/mark-all-read', methods=['POST'])
@student_required
def mark_all_announcements_read():
    student, batch_ids = get_current_student(), get_user_batch_ids(get_current_student().id)
    unread = Announcement.query.filter((Announcement.target_audience.in_(['all', 'students'])) | (Announcement.target_batch_id.in_(batch_ids) if batch_ids else False))\
        .filter(Announcement.is_published == True)\
        .outerjoin(AnnouncementRead, (AnnouncementRead.announcement_id == Announcement.id) & (AnnouncementRead.student_id == student.id))\
        .filter(AnnouncementRead.id == None).all()
    
    for ann in unread: db.session.add(AnnouncementRead(student_id=student.id, announcement_id=ann.id))
    db.session.commit()
    return {"status": "success"}

@bp.route('/prepkit')
@paid_student_required
def prepkit():
    student, batch_ids = get_current_student(), get_user_batch_ids(get_current_student().id)
    resources_query = Resource.query.filter(Resource.is_active == True).filter((Resource.access_level == 'free') | (Resource.target_batch_id.in_(batch_ids) if batch_ids else False)).order_by(Resource.created_at.desc()).all()
    
    resources = {}
    for res in resources_query:
        category = res.category.title()
        if category not in resources: resources[category] = []
        
        link = res.file_url or res.file_path or '#'
        if link and 'cloudinary.com' in link and res.file_type == 'pdf': link = get_download_url(link)

        resources[category].append({
            'title': res.title, 'description': res.description, 'type': res.file_type.upper() if res.file_type else 'Link',
            'size': f'{res.file_size / (1024*1024):.1f} MB' if res.file_size else 'N/A', 'link': link
        })
    return render_template('dashboard/user/prepkit.html', resources=resources, student=student)

@bp.route('/interview')
@student_required
def interview():
    student = get_current_student()
    is_enrolled = student.is_paid
    filters = [Interview.student_id == student.id, Interview.target_audience == 'all_registered']
    if is_enrolled: filters.append(Interview.target_audience == 'all_enrolled')
        
    upcoming = [{
        'id': i.id, 'title': i.title, 'date': i.scheduled_date.strftime('%b %d, %Y'), 'time': i.scheduled_date.strftime('%I:%M %p'),
        'mentor': i.interviewer_name or 'TBD', 'type': i.interview_type.replace('_', ' ').title(),
        'image': i.image_url or '/static/images/interview_default.png', 'link': i.meeting_link or '#'
    } for i in Interview.query.filter(or_(*filters), Interview.scheduled_date >= datetime.utcnow(), Interview.status.in_(['scheduled', 'confirmed'])).order_by(Interview.scheduled_date).all()]
    
    past = [{
        'id': i.id, 'title': i.title, 'date': i.scheduled_date.strftime('%b %d, %Y'), 'mentor': i.interviewer_name or 'TBD',
        'status': i.status.title(), 'feedback_link': '#'
    } for i in Interview.query.filter(or_(*filters)).filter((Interview.scheduled_date < datetime.utcnow()) | (Interview.status == 'completed')).order_by(Interview.scheduled_date.desc()).all()]
    
    return render_template('dashboard/user/interview.html', upcoming=upcoming, past=past, student=student)

@bp.route('/doubts')
@paid_student_required
def doubts():
    student = get_current_student()
    doubts_list = []
    for d in Doubt.query.order_by(Doubt.created_at.desc()).all():
        diff = datetime.utcnow() - d.created_at
        ts = f"{diff.days} days ago" if diff.days > 0 else f"{diff.seconds // 3600} hours ago" if diff.seconds >= 3600 else f"{max(1, diff.seconds // 60)} mins ago"
        doubts_list.append({
            'id': d.id, 'title': d.title, 'content': d.content, 'author': d.student.full_name, 'timestamp': ts,
            'replies': d.replies.count(), 'views': d.views, 'category': d.category, 'student_id': d.student_id
        })
    return render_template('dashboard/user/doubts.html', doubts=doubts_list, student=student)

@bp.route('/post_doubt', methods=['POST'])
@student_required
def post_doubt():
    student = get_current_student()
    title, content = request.form.get('title'), request.form.get('content')
    if not title or not content:
        flash('Title and description required', 'danger')
        return redirect(url_for('user.doubts'))
    try:
        db.session.add(Doubt(student_id=student.id, title=title, category=request.form.get('category', 'General Query'), content=content, status='pending'))
        db.session.commit()
        flash('Doubt posted!', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to post', 'danger')
    return redirect(url_for('user.doubts'))

@bp.route('/doubts/<int:doubt_id>')
@student_required
def doubt_detail(doubt_id):
    student, doubt = get_current_student(), Doubt.query.get_or_404(doubt_id)
    if doubt_id not in session.get('viewed_doubts', []):
        doubt.views += 1
        session.setdefault('viewed_doubts', []).append(doubt_id)
        db.session.commit()
    
    diff = datetime.utcnow() - doubt.created_at
    ts = f"{diff.days} days ago" if diff.days > 0 else f"{diff.seconds // 3600} hours ago" if diff.seconds >= 3600 else f"{max(1, diff.seconds // 60)} mins ago"
    
    replies = []
    for r in doubt.replies.order_by(DoubtReply.created_at.asc()).all():
        r_diff = datetime.utcnow() - r.created_at
        r_ts = f"{r_diff.days} days ago" if r_diff.days > 0 else f"{r_diff.seconds // 3600} hours ago" if r_diff.seconds >= 3600 else f"{max(1, r_diff.seconds // 60)} mins ago"
        replies.append({
            'id': r.id, 'content': r.content, 'author': User.query.get(r.user_id).email.split('@')[0], 'is_staff': r.is_staff_reply, 'timestamp': r_ts
        })
    return render_template('dashboard/user/doubt_detail.html', doubt={'id': doubt.id, 'title': doubt.title, 'content': doubt.content, 'category': doubt.category, 'status': doubt.status, 'author': doubt.student.full_name, 'timestamp': ts, 'views': doubt.views, 'replies_count': doubt.replies.count()}, replies=replies, student=student)

@bp.route('/doubts/<int:doubt_id>/reply', methods=['POST'])
@student_required
def post_reply(doubt_id):
    content = request.form.get('content')
    if not content: return redirect(url_for('user.doubt_detail', doubt_id=doubt_id))
    try:
        db.session.add(DoubtReply(doubt_id=doubt_id, user_id=get_current_student().user_id, content=content, is_staff_reply=False))
        db.session.commit()
        flash('Reply posted!', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to reply', 'danger')
    return redirect(url_for('user.doubt_detail', doubt_id=doubt_id))

@bp.route('/doubts/delete/<int:doubt_id>', methods=['POST'])
@student_required
def delete_doubt(doubt_id):
    doubt = Doubt.query.get_or_404(doubt_id)
    if doubt.student_id == get_current_student().id:
        db.session.delete(doubt)
        db.session.commit()
        flash('Doubt deleted', 'success')
    return redirect(url_for('user.doubts'))

@bp.route('/mock')
@paid_student_required
def mock():
    student, batch_ids = get_current_student(), get_user_batch_ids(get_current_student().id)
    tests = MockTest.query.filter(MockTest.is_active == True).filter(or_(MockTest.is_free == True, MockTest.batch_id.in_(batch_ids) if batch_ids else False, MockTest.batch_id == None)).order_by(MockTest.available_from.desc()).all()
    
    now = datetime.now(IST).replace(tzinfo=None)
    formatted = []
    for t in tests:
        attempt = TestAttempt.query.filter_by(student_id=student.id, mock_test_id=t.id, status='completed').first()
        status = 'Live' if t.is_anytime or (t.available_from and t.available_from <= now and (not t.available_until or now <= t.available_until)) else 'Upcoming' if t.available_from and now < t.available_from else 'Ended'
        formatted.append({
            'id': t.id, 'title': t.title, 'date': t.available_from.strftime('%b %d, %Y') if t.available_from else 'Anytime',
            'time': t.available_from.strftime('%I:%M %p') if t.available_from else 'Flexible',
            'duration': f"{t.duration_minutes} mins", 'questions': t.total_questions, 'status': status, 'attempted': attempt is not None, 'attempt_id': attempt.id if attempt else None
        })
    return render_template('dashboard/user/mock.html', tests=formatted, student=student)

@bp.route('/mock/<int:test_id>/start')
@student_required
def mock_start(test_id):
    student, test = get_current_student(), MockTest.query.get_or_404(test_id)
    attempt = TestAttempt.query.filter_by(student_id=student.id, mock_test_id=test.id, status='completed').first()
    if attempt: return redirect(url_for('user.mock_result', attempt_id=attempt.id))
    return render_template('dashboard/user/mock_start.html', test=test, student=student)

@bp.route('/mock/<int:test_id>/take')
@student_required
def mock_take(test_id):
    student, test = get_current_student(), MockTest.query.get_or_404(test_id)
    attempt = TestAttempt.query.filter_by(student_id=student.id, mock_test_id=test.id, status='in_progress').first()
    now = datetime.now(IST).replace(tzinfo=None)
    
    if attempt and (now - attempt.started_at).total_seconds() / 60 > test.duration_minutes:
        return redirect(url_for('user.mock_submit', test_id=test.id))
    if not attempt:
        attempt = TestAttempt(student_id=student.id, mock_test_id=test.id, status='in_progress', started_at=now)
        db.session.add(attempt); db.session.commit()
    
    questions = test.questions.order_by(Question.question_number).all()
    q_data, counts = [], {}
    for q in questions: counts[q.section] = counts.get(q.section, 0) + 1
    
    curr_indices = {}
    for i, q in enumerate(questions):
        idx = curr_indices.get(q.section, 0) + 1
        curr_indices[q.section] = idx
        d = q.to_dict()
        d.update({'abs_index': i, 'rel_index': idx, 'section_total': counts[q.section]})
        q_data.append(d)
        
    return render_template('dashboard/user/mock_take.html', test=test, attempt=attempt, questions=q_data, remaining_seconds=int(max(0, test.duration_minutes - (now - attempt.started_at).total_seconds() / 60) * 60), student=student)

@bp.route('/mock/<int:test_id>/submit', methods=['POST'])
@student_required
def mock_submit(test_id):
    student, test = get_current_student(), MockTest.query.get_or_404(test_id)
    attempt = TestAttempt.query.filter_by(student_id=student.id, mock_test_id=test.id, status='in_progress').first()
    if not attempt: return redirect(url_for('user.mock'))
    
    answers = {k.split('_')[1]: v for k, v in request.form.items() if k.startswith('q_')}
    attempt.answers, attempt.submitted_at, attempt.status = answers, datetime.now(IST).replace(tzinfo=None), 'completed'
    
    correct, wrong, score = 0, 0, 0.0
    for q in test.questions.all():
        ans = answers.get(str(q.id))
        if ans == q.correct_answer: correct +=1; score += (q.marks or 1)
        elif ans: wrong += 1; score -= (q.negative_marks or 0)
            
    attempt.correct_answers, attempt.wrong_answers, attempt.score = correct, wrong, score
    attempt.unanswered = test.total_questions - (correct + wrong)
    attempt.total_marks, attempt.percentage = test.total_marks, (score / test.total_marks * 100) if test.total_marks > 0 else 0
    attempt.time_taken_minutes = (attempt.submitted_at - attempt.started_at).seconds // 60
    db.session.commit()
    return redirect(url_for('user.mock_result', attempt_id=attempt.id))

@bp.route('/mock/result/<int:attempt_id>')
@student_required
def mock_result(attempt_id):
    student, attempt = get_current_student(), TestAttempt.query.get_or_404(attempt_id)
    if attempt.student_id != student.id: return redirect(url_for('user.mock'))
    return render_template('dashboard/user/mock_result.html', attempt=attempt, test=attempt.mock_test, questions=attempt.mock_test.questions.order_by(Question.question_number).all(), answers=attempt.answers, student=student)

@bp.route('/enrollment-required')
@student_required
def enrollment_required_page():
    return render_template('dashboard/user/enrollment_required.html', student=get_current_student())
