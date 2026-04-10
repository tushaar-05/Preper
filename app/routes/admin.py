from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from sqlalchemy import func, or_
import os
from datetime import datetime, timedelta
from app.extensions import db, IST
from app.utils.decorators import admin_required
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, Resource, Payment, Mentor,
    SiteConfig, TeamMember
)
from app.utils.helpers import get_batch_status_color, get_interview_status_color, handle_image_upload
from app.utils.storage import delete_file

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@admin_required
def dashboard():
    admin = User.query.get(session.get('admin_id'))
    try:
        revenue = db.session.query(func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
        total_st = Student.query.count()
        paid_st = db.session.query(Enrollment.student_id).filter(Enrollment.payment_status.in_(['completed', 'partial'])).distinct().count()
        one_week = datetime.utcnow().date() - timedelta(days=7)
        new_en = db.session.query(Enrollment.student_id).filter(Enrollment.enrollment_date >= one_week, Enrollment.payment_status.in_(['completed', 'partial'])).distinct().count()
        
        stats = {
            'total_students': total_st, 'total_paid': paid_st, 'new_enrollments': new_en,
            'active_batches': Batch.query.filter_by(status='active').count(),
            'pending_payments': Payment.query.filter_by(status='pending').count(),
            'upcoming_interviews': Interview.query.filter(Interview.scheduled_date > datetime.utcnow()).count(),
            'total_revenue': float(revenue),
            'enrollments_this_month': Enrollment.query.filter(func.extract('month', Enrollment.enrollment_date) == datetime.utcnow().month).count()
        }
    except Exception as e:
        print(f"Stats Error: {e}")
        stats = {k: 0 for k in ['total_students', 'total_paid', 'new_enrollments', 'active_batches', 'pending_payments', 'upcoming_interviews', 'enrollments_this_month']}
        stats['total_revenue'] = 0.0

    recent = db.session.query(Enrollment, Student, Batch, User).join(Student).join(Batch).join(User).filter(Enrollment.payment_status.in_(['completed', 'partial'])).order_by(Enrollment.enrollment_date.desc()).limit(5).all()
    mentors = Mentor.query.filter_by(is_active=True).limit(3).all()
    fm = [{'name': m.full_name, 'initial': m.full_name[0], 'role': m.role, 'rating': f"{m.rating:.1f}"} for m in mentors]
    if not fm:
        backup = db.session.query(Interview.interviewer_name).distinct().filter(Interview.interviewer_name != None).limit(3).all()
        fm = [{'name': m[0], 'initial': m[0][0], 'role': 'Guide', 'rating': '4.9'} for m in backup]

    return render_template('dashboard/admin/admin.html', admin=admin, stats=stats, recent_enrollments=recent, mentors=fm)

@bp.route('/add_mentor', methods=['POST'])
@admin_required
def add_mentor():
    try:
        name = request.form.get('full_name')
        if not name: flash('Name required', 'error'); return redirect(url_for('admin.mentors'))
        db.session.add(Mentor(full_name=name, email=request.form.get('email'), role=request.form.get('role', 'Guide'), rating=5.0, image_url=handle_image_upload(request.files.get('image'), 'mentors'), description=request.form.get('description')))
        db.session.commit(); flash(f'Mentor {name} added!', 'success')
    except Exception as e: db.session.rollback(); flash('Error adding mentor', 'error')
    return redirect(url_for('admin.mentors'))

@bp.route('/students')
@admin_required
def students():
    q, batch, status = request.args.get('q', ''), request.args.get('batch', ''), request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    query = db.session.query(Student, User, Enrollment, Batch).join(User).outerjoin(Enrollment).outerjoin(Batch)
    if q: query = query.filter(or_(Student.full_name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'), Student.phone.ilike(f'%{q}%')))
    if batch: query = query.filter(Batch.name.ilike(f'%{batch}%'))
    if status == 'active': query = query.filter(Enrollment.payment_status.in_(['completed', 'partial']))
    elif status == 'pending': query = query.filter(or_(Enrollment.id == None, Enrollment.payment_status == 'pending'))
    
    pagination = query.order_by(Student.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    sl = [{'id': s.id, 'name': s.full_name, 'email': u.email, 'phone': s.phone or 'N/A', 'batch': b.name if (b and e and e.payment_status in ['completed', 'partial']) else 'Not Enrolled', 'status': 'Enrolled' if (e and e.payment_status in ['completed', 'partial']) else 'Not Enrolled', 'joined_date': s.created_at.strftime('%b %d, %Y'), 'avatar_color': 'bg-violet-100 text-violet-600'} for s, u, e, b in pagination.items]
    return render_template('dashboard/admin/students.html', students=sl, pagination=pagination, q=q, selected_batch=batch, selected_status=status)

@bp.route('/sync-db')
@admin_required
def sync_db():
    try:
        from sqlalchemy import text
        db.session.execute(text('ALTER TABLE mentors ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)'))
        db.session.execute(text('ALTER TABLE mentors ADD COLUMN IF NOT EXISTS description TEXT'))
        db.create_all()
        db.session.commit(); flash('Database synced!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Sync notice: {e}', 'info')
    return redirect(url_for('admin.mentors'))

@bp.route('/mentors')
@admin_required
def mentors():
    admin = User.query.get(session.get('admin_id'))
    try:
        ml = [{'id': m.id, 'name': m.full_name, 'email': m.email, 'role': m.role, 'rating': f"{m.rating:.1f}", 'status': 'Active' if m.is_active else 'Inactive', 'joined_date': m.created_at.strftime('%b %d, %Y'), 'initial': m.full_name[0], 'image_url': m.image_url, 'description': m.description} for m in Mentor.query.order_by(Mentor.created_at.desc()).all()]
        return render_template('dashboard/admin/mentors.html', mentors=ml, admin=admin)
    except Exception: return render_template('dashboard/admin/mentors.html', mentors=[], db_error=True, admin=admin)

@bp.route('/mentors/edit/<int:mentor_id>', methods=['POST'])
@admin_required
def edit_mentor(mentor_id):
    try:
        m = Mentor.query.get_or_404(mentor_id)
        for f in ['full_name', 'email', 'role', 'description']: setattr(m, f, request.form.get(f))
        m.is_active = request.form.get('status') == 'active'
        img = handle_image_upload(request.files.get('image'), 'mentors')
        if img: m.image_url = img
        db.session.commit(); flash('Mentor updated!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.mentors'))

@bp.route('/mentors/delete/<int:mentor_id>', methods=['POST'])
@admin_required
def delete_mentor(mentor_id):
    try:
        m = Mentor.query.get_or_404(mentor_id); db.session.delete(m); db.session.commit(); flash('Mentor deleted!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.mentors'))

@bp.route('/team')
@admin_required
def team():
    admin = User.query.get(session.get('admin_id'))
    try:
        tl = [{'id': m.id, 'name': m.full_name, 'role': m.role, 'description': m.description, 'image_url': m.image_url, 'status': 'Active' if m.is_active else 'Inactive', 'initial': m.full_name[0], 'display_order': m.display_order} for m in TeamMember.query.order_by(TeamMember.display_order.asc()).all()]
        return render_template('dashboard/admin/team.html', team=tl, admin=admin)
    except Exception: return render_template('dashboard/admin/team.html', team=[], db_error=True, admin=admin)

@bp.route('/team/add', methods=['POST'])
@admin_required
def add_team_member():
    try:
        name, role = request.form.get('full_name'), request.form.get('role')
        if not name or not role: flash('Name/Role required', 'error'); return redirect(url_for('admin.team'))
        db.session.add(TeamMember(full_name=name, role=role, description=request.form.get('description'), image_url=handle_image_upload(request.files.get('image'), 'team'), display_order=request.form.get('display_order', 0)))
        db.session.commit(); flash('Team member added!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.team'))

@bp.route('/team/edit/<int:member_id>', methods=['POST'])
@admin_required
def edit_team_member(member_id):
    try:
        m = TeamMember.query.get_or_404(member_id)
        for f in ['full_name', 'role', 'description', 'display_order']: setattr(m, f, request.form.get(f))
        m.is_active = request.form.get('status') == 'active'
        img = handle_image_upload(request.files.get('image'), 'team')
        if img: m.image_url = img
        db.session.commit(); flash('Updated!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.team'))

@bp.route('/team/delete/<int:member_id>', methods=['POST'])
@admin_required
def delete_team_member(member_id):
    try:
        m = TeamMember.query.get_or_404(member_id); db.session.delete(m); db.session.commit(); flash('Deleted!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.team'))

@bp.route('/batches')
@admin_required
def batches():
    bl = [{'id': b.id, 'name': b.name, 'status': b.status.title(), 'status_color': get_batch_status_color(b.status), 'students_count': b.current_enrollment, 'max_students': b.max_students, 'price': int(b.discounted_price), 'original_price': int(b.original_price), 'features': b.features, 'color': b.color, 'description': b.description} for b in Batch.query.order_by(Batch.created_at.desc()).all()]
    return render_template('dashboard/admin/batches.html', batches=bl)

@bp.route('/batches/create', methods=['POST'])
@admin_required
def batches_create():
    try:
        name = request.form.get('name')
        if not name: flash('Name required', 'error'); return redirect(url_for('admin.batches'))
        b = Batch(name=name, description=request.form.get('description'), original_price=float(request.form.get('original_price', 0)), discounted_price=float(request.form.get('discounted_price', 0)), max_students=int(request.form.get('max_students', 50)), status=request.form.get('status', 'upcoming'), color=request.form.get('color', 'violet'))
        b.features = request.form.getlist('features[]') or []
        db.session.add(b); db.session.commit(); flash('Batch created!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.batches'))

@bp.route('/batches/edit/<int:batch_id>', methods=['POST'])
@admin_required
def batches_edit(batch_id):
    try:
        b = Batch.query.get_or_404(batch_id)
        for f in ['name', 'description', 'status', 'color']: setattr(b, f, request.form.get(f))
        b.original_price, b.discounted_price = float(request.form.get('original_price', 0)), float(request.form.get('discounted_price', 0))
        b.max_students, b.features = int(request.form.get('max_students', 50)), request.form.getlist('features[]') or []
        db.session.commit(); flash('Updated!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.batches'))

@bp.route('/batches/delete/<int:batch_id>', methods=['POST'])
@admin_required
def batches_delete(batch_id):
    try:
        b = Batch.query.get_or_404(batch_id)
        if b.current_enrollment > 0: flash('Batch has enrollments!', 'error'); return redirect(url_for('admin.batches'))
        db.session.delete(b); db.session.commit(); flash('Deleted!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.batches'))

@bp.route('/interviews')
@admin_required
def interviews():
    data = db.session.query(Interview, Student, User).outerjoin(Student).outerjoin(User).order_by(Interview.scheduled_date.desc()).all()
    il = [{'id': i.id, 'student_name': s.full_name if s else None, 'student_id': s.id if s else None, 'target_audience': i.target_audience, 'type': i.interview_type.replace('_', ' ').title(), 'raw_type': i.interview_type, 'mentor': i.interviewer_name or 'TBD', 'date': i.scheduled_date.strftime('%b %d, %Y'), 'time': i.scheduled_date.strftime('%I:%M %p'), 'raw_date': i.scheduled_date.strftime('%Y-%m-%d'), 'raw_time': i.scheduled_date.strftime('%H:%M'), 'status': i.status.title(), 'raw_status': i.status, 'status_color': get_interview_status_color(i.status), 'title': i.title, 'description': i.description, 'meeting_link': i.meeting_link, 'meeting_platform': i.meeting_platform, 'image_url': i.image_url} for i, s, u in data]
    return render_template('dashboard/admin/interviews.html', interviews=il, students=Student.query.all(), mentors=Mentor.query.all())

@bp.route('/interviews/schedule', methods=['POST'])
@admin_required
def interviews_schedule():
    try:
        dt, tm = request.form.get('date'), request.form.get('time')
        if not dt or not tm: flash('Date/Time required', 'error'); return redirect(url_for('admin.interviews'))
        sched_dt = datetime.strptime(f"{dt} {tm}", "%Y-%m-%d %H:%M")
        mentor = Mentor.query.get(request.form.get('mentor_id'))
        img = handle_image_upload(request.files.get('image'), 'interviews')
        
        target = 'all_registered' if request.form.get('all_registered') == '1' else 'all_enrolled' if request.form.get('all_enrolled') == '1' else 'individual'
        students = Student.query.all() if target == 'all_registered' else Student.query.join(Enrollment).filter(Enrollment.payment_status.in_(['completed', 'partial'])).all() if target == 'all_enrolled' else [Student.query.get(request.form.get('student_id'))]
        
        if not students or not any(students): flash('No students found', 'warning'); return redirect(url_for('admin.interviews'))
        
        if target != 'individual':
            db.session.add(Interview(student_id=None, target_audience=target, interview_type=request.form.get('type'), title=request.form.get('title'), description=request.form.get('description'), scheduled_date=sched_dt, interviewer_name=mentor.full_name if mentor else None, interviewer_email=mentor.email if mentor else None, status='scheduled', meeting_link=request.form.get('meeting_link'), meeting_platform=request.form.get('meeting_platform'), image_url=img))
        else:
            for s in students: db.session.add(Interview(student_id=s.id, target_audience='individual', interview_type=request.form.get('type'), title=request.form.get('title'), description=request.form.get('description'), scheduled_date=sched_dt, interviewer_name=mentor.full_name if mentor else None, interviewer_email=mentor.email if mentor else None, status='scheduled', meeting_link=request.form.get('meeting_link'), meeting_platform=request.form.get('meeting_platform'), image_url=img))
        
        db.session.commit(); flash('Scheduled!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.interviews'))

@bp.route('/interviews/update/<int:interview_id>', methods=['POST'])
@admin_required
def interviews_update(interview_id):
    try:
        i = Interview.query.get_or_404(interview_id)
        i.title, i.description, i.status, i.feedback = request.form.get('title'), request.form.get('description'), request.form.get('status'), request.form.get('feedback')
        dt, tm = request.form.get('date'), request.form.get('time')
        if dt and tm: i.scheduled_date = datetime.strptime(f"{dt} {tm}", "%Y-%m-%d %H:%M")
        mentor = Mentor.query.get(request.form.get('mentor_id'))
        if mentor: i.interviewer_name, i.interviewer_email = mentor.full_name, mentor.email
        img = handle_image_upload(request.files.get('image'), 'interviews')
        if img: i.image_url = img
        db.session.commit(); flash('Updated!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.interviews'))

@bp.route('/interviews/delete/<int:interview_id>', methods=['POST'])
@admin_required
def interviews_delete(interview_id):
    i = Interview.query.get_or_404(interview_id); db.session.delete(i); db.session.commit(); flash('Deleted!', 'success'); return redirect(url_for('admin.interviews'))

@bp.route('/interviews/delete_all', methods=['POST'])
@admin_required
def interviews_delete_all():
    Interview.query.delete(); db.session.commit(); flash('All deleted!', 'success'); return redirect(url_for('admin.interviews'))

def _update_mock_total_marks(mock_id):
    m = MockTest.query.get(mock_id)
    if m: m.total_marks = int(db.session.query(func.sum(Question.marks)).filter_by(mock_test_id=mock_id).scalar() or 0); db.session.commit()

@bp.route('/mocks/<int:mock_id>/questions/add', methods=['POST'])
@admin_required
def mock_questions_add(mock_id):
    try:
        q_txt, ans = request.form.get('question_text'), request.form.get('correct_answer')
        q_img = handle_image_upload(request.files.get('question_image'), 'mocks/questions')
        opts, i = [], 1
        while request.form.get(f'option_{i}_text'):
            opts.append({'text': request.form.get(f'option_{i}_text'), 'image': handle_image_upload(request.files.get(f'option_{i}_image'), 'mocks/options')})
            i += 1
        last_q = Question.query.filter_by(mock_test_id=mock_id).order_by(Question.question_number.desc()).first()
        db.session.add(Question(mock_test_id=mock_id, section=request.form.get('section'), question_text=q_txt, question_image_url=q_img, options=opts, correct_answer=ans, explanation=request.form.get('explanation'), question_number=(last_q.question_number + 1 if last_q else 1), marks=int(request.form.get('marks', 1))))
        db.session.commit(); _update_mock_total_marks(mock_id); flash('Question added!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.mock_questions', mock_id=mock_id))

@bp.route('/mocks/<int:mock_id>/questions/<int:question_id>/edit', methods=['POST'])
@admin_required
def mock_questions_edit(mock_id, question_id):
    try:
        q = Question.query.get_or_404(question_id)
        for f in ['section', 'question_text', 'correct_answer', 'explanation']: setattr(q, f, request.form.get(f))
        q.marks = int(request.form.get('marks', 1))
        img = handle_image_upload(request.files.get('question_image'), 'mocks/questions')
        if img: q.question_image_url = img
        opts, i = [], 1
        while request.form.get(f'option_{i}_text'):
            existing_img = q.options[i-1].get('image') if len(q.options) >= i else None
            new_img = handle_image_upload(request.files.get(f'option_{i}_image'), 'mocks/options')
            opts.append({'text': request.form.get(f'option_{i}_text'), 'image': new_img or existing_img})
            i += 1
        q.options = opts; db.session.commit(); _update_mock_total_marks(mock_id); flash('Updated!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.mock_questions', mock_id=mock_id))

@bp.route('/mocks/<int:mock_id>/questions/<int:question_id>/delete', methods=['POST'])
@admin_required
def mock_questions_delete(mock_id, question_id):
    q = Question.query.get_or_404(question_id); db.session.delete(q); db.session.commit(); _update_mock_total_marks(mock_id); flash('Deleted!', 'success'); return redirect(url_for('admin.mock_questions', mock_id=mock_id))

@bp.route('/mocks/<int:mock_id>/delete', methods=['POST'])
@admin_required
def mocks_delete(mock_id):
    m = MockTest.query.get_or_404(mock_id); db.session.delete(m); db.session.commit(); flash('Deleted!', 'success'); return redirect(url_for('admin.mocks'))

@bp.route('/announcements')
@admin_required
def announcements():
    al = []
    for a in Announcement.query.order_by(Announcement.published_at.desc()).all():
        if a.priority == 'urgent': lbl, clr = 'Important', 'bg-red-100 text-red-700'
        elif a.priority == 'high': lbl, clr = 'Academic', 'bg-violet-100 text-violet-700'
        else: lbl, clr = 'System', 'bg-gray-100 text-gray-700'
        target = 'All Users' if a.target_audience == 'all' else Batch.query.get(a.target_batch_id).name if a.target_batch_id else a.target_audience.title()
        al.append({'id': a.id, 'title': a.title, 'date': a.published_at.strftime('%b %d, %Y'), 'target': target, 'content': a.content[:100]+'...', 'full_content': a.content, 'priority': a.priority, 'type': lbl, 'type_color': clr, 'raw_target_audience': a.target_audience, 'raw_target_batch_id': a.target_batch_id})
    return render_template('dashboard/admin/announcements.html', announcements=al, batches=Batch.query.filter(Batch.status.in_(['active', 'upcoming'])).all())

@bp.route('/announcements/update/<int:announcement_id>', methods=['POST'])
@admin_required
def announcements_update(announcement_id):
    try:
        a = Announcement.query.get_or_404(announcement_id)
        for f in ['title', 'content', 'priority', 'target_audience']: setattr(a, f, request.form.get(f))
        a.target_batch_id = request.form.get('target_batch_id') if a.target_audience == 'specific_batch' else None
        db.session.commit(); flash('Updated!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.announcements'))

@bp.route('/announcements/create', methods=['POST'])
@admin_required
def announcements_create():
    try:
        a = Announcement(title=request.form.get('title'), content=request.form.get('content'), priority=request.form.get('priority', 'medium'), target_audience=request.form.get('target_audience', 'all'), target_batch_id=request.form.get('target_batch_id') if request.form.get('target_audience') == 'specific_batch' else None, created_by=session.get('admin_id'), published_at=datetime.utcnow(), is_published=True)
        db.session.add(a); db.session.commit(); flash('Published!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.announcements'))

@bp.route('/announcements/delete/<int:announcement_id>', methods=['POST'])
@admin_required
def announcements_delete(announcement_id):
    a = Announcement.query.get_or_404(announcement_id); db.session.delete(a); db.session.commit(); flash('Deleted!', 'success'); return redirect(url_for('admin.announcements'))

@bp.route('/resources')
@admin_required
def resources():
    cat, bid = request.args.get('category'), request.args.get('batch_id')
    q = Resource.query
    if cat: q = q.filter_by(category=cat)
    if bid: q = q.filter_by(target_batch_id=bid)
    rl = []
    for r in q.order_by(Resource.created_at.desc()).all():
        rl.append({'id': r.id, 'title': r.title, 'category': r.category, 'batch': Batch.query.get(r.target_batch_id).name if r.target_batch_id else 'All Batches', 'uploaded_date': r.created_at.strftime('%b %d, %Y'), 'file_size': f'{r.file_size/(1024*1024):.1f} MB' if r.file_size else 'N/A', 'downloads': r.download_count, 'type': r.file_type.upper() if r.file_type else 'LINK', 'file_url': r.file_url, 'description': r.description, 'access_level': r.access_level, 'target_batch_id': r.target_batch_id, 'resource_type': r.resource_type})
    return render_template('dashboard/admin/resources.html', resources=rl, batches=Batch.query.filter(Batch.status.in_(['active', 'upcoming'])).all())

@bp.route('/resources/create', methods=['POST'])
@admin_required
def resources_create():
    try:
        r = Resource(title=request.form.get('title'), description=request.form.get('description'), category=request.form.get('category'), resource_type=request.form.get('resource_type', 'file'), access_level=request.form.get('access_level', 'free'), target_batch_id=request.form.get('target_batch_id') if request.form.get('access_level') == 'batch_specific' else None, uploaded_by=session.get('admin_id'))
        if r.resource_type == 'file' and 'resource_file' in request.files:
            f = request.files['resource_file']
            if f and f.filename:
                from app.utils.storage import upload_file
                res = upload_file(f, folder='resources', resource_type='raw' if f.filename.lower().endswith('.pdf') else 'auto')
                r.file_url, r.file_size, r.file_type = res.get('secure_url'), res.get('bytes', 0), res.get('format', f.filename.split('.')[-1].lower())
        else: r.file_url, r.file_type = request.form.get('file_url'), 'LINK'
        db.session.add(r); db.session.commit(); flash('Uploaded!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.resources'))

@bp.route('/resources/edit/<int:resource_id>', methods=['POST'])
@admin_required
def resources_edit(resource_id):
    try:
        r = Resource.query.get_or_404(resource_id)
        for f in ['title', 'description', 'category', 'access_level']: setattr(r, f, request.form.get(f))
        r.target_batch_id = request.form.get('target_batch_id') if r.access_level == 'batch_specific' else None
        db.session.commit(); flash('Updated!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.resources'))

@bp.route('/resources/delete/<int:resource_id>', methods=['POST'])
@admin_required
def resources_delete(resource_id):
    r = Resource.query.get_or_404(resource_id); db.session.delete(r); db.session.commit(); flash('Deleted!', 'success'); return redirect(url_for('admin.resources'))
