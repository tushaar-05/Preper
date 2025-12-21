"""
Admin dashboard routes with database integration
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from app.extensions import db
from app.utils.decorators import admin_required
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, Resource, Payment, Mentor,
    SiteConfig
)
from app.utils import admin_required, get_batch_status_color, get_interview_status_color
from datetime import datetime, timedelta
from sqlalchemy import func, or_
import os
from werkzeug.utils import secure_filename

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
        .outerjoin(Student, Interview.student_id == Student.id)\
        .outerjoin(User, Student.user_id == User.id)\
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
            'student_name': student.full_name if student else None,
            'student_id': student.id if student else None,
            'target_audience': interview.target_audience,
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
            'rating': interview.rating,
            'meeting_link': interview.meeting_link,
            'meeting_platform': interview.meeting_platform,
            'image_url': interview.image_url
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
        
        # Check for bulk flags
        all_registered = request.form.get('all_registered') == '1'
        all_enrolled = request.form.get('all_enrolled') == '1'
        
        # Validate required fields (date, time, title are always required)
        if not scheduled_date_str or not scheduled_time_str:
            flash('Date and time are required for scheduling', 'error')
            return redirect(url_for('admin.interviews'))
            
        # Validate student selection
        if not student_id and not all_registered and not all_enrolled:
            flash('Please select a student or a group of students', 'error')
            return redirect(url_for('admin.interviews'))
            
        scheduled_datetime = datetime.strptime(f"{scheduled_date_str} {scheduled_time_str}", "%Y-%m-%d %H:%M")
        
        interviewer_name = None
        interviewer_email = None
        if mentor_id:
            mentor = Mentor.query.get(mentor_id)
            if mentor:
                interviewer_name = mentor.full_name
                interviewer_email = mentor.email
        
        # Handle Image Upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(f"interview_{datetime.now().timestamp()}_{file.filename}")
                upload_path = os.path.join('app', 'static', 'uploads', 'interviews', filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                
                file.save(upload_path)
                image_url = url_for('static', filename=f'uploads/interviews/{filename}')

        # Determine target list of students
        target_students = []
        
        if all_registered:
            target_students = Student.query.all()
        elif all_enrolled:
            # Get students with completed or partial payments
            target_students = db.session.query(Student)\
                .join(Enrollment, Student.id == Enrollment.student_id)\
                .filter(Enrollment.payment_status.in_(['completed', 'partial']))\
                .distinct().all()
        else:
            # Single student
            student = Student.query.get(student_id)
            if student:
                target_students = [student]
        
        if not target_students:
            flash('No students found for the selected criteria', 'warning')
            return redirect(url_for('admin.interviews'))
            
        # Create single interview for group OR individual
        target_audience = None
        if all_registered:
            target_audience = 'all_registered'
        elif all_enrolled:
            target_audience = 'all_enrolled'
        else:
            target_audience = 'individual'

        # If it's a group interview, we create ONE record with student_id=None
        if target_audience != 'individual':
            interview = Interview(
                student_id=None,
                target_audience=target_audience,
                interview_type=interview_type,
                title=title or f"{interview_type.title()} with {interviewer_name or 'Mentor'}",
                description=description,
                scheduled_date=scheduled_datetime,
                interviewer_name=interviewer_name,
                interviewer_email=interviewer_email,
                status='scheduled',
                meeting_link=request.form.get('meeting_link'),
                meeting_platform=request.form.get('meeting_platform'),
                image_url=image_url
            )
            db.session.add(interview)
            count = len(target_students) # Just for display purposes
        else:
            # Individual - create one record
            # We can still loop if for some reason multiple students were passed, but here it's usually one
            for student in target_students:
                interview = Interview(
                    student_id=student.id,
                    target_audience='individual',
                    interview_type=interview_type,
                    title=title or f"{interview_type.title()} with {interviewer_name or 'Mentor'}",
                    description=description,
                    scheduled_date=scheduled_datetime,
                    interviewer_name=interviewer_name,
                    interviewer_email=interviewer_email,
                    status='scheduled',
                    meeting_link=request.form.get('meeting_link'),
                    meeting_platform=request.form.get('meeting_platform'),
                    image_url=image_url
                )
                db.session.add(interview)
            count = len(target_students)
            
        db.session.commit()
        
        if count > 1 and target_audience == 'individual':
            flash(f'Successfully scheduled interviews for {count} students!', 'success')
        elif target_audience != 'individual':
             flash(f'Successfully scheduled group interview for {target_audience.replace("_", " ").title()}!', 'success')
        else:
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
        
        student_id = request.form.get('student_id')
        all_registered = request.form.get('all_registered') == '1'
        all_enrolled = request.form.get('all_enrolled') == '1'
        
        if all_registered:
            interview.target_audience = 'all_registered'
            interview.student_id = None
        elif all_enrolled:
            interview.target_audience = 'all_enrolled'
            interview.student_id = None
        else:
            interview.target_audience = 'individual'
            interview.student_id = student_id if student_id and student_id.strip() else None
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
                
        # Update meeting link and platform
        interview.meeting_link = request.form.get('meeting_link')
        interview.meeting_platform = request.form.get('meeting_platform')
        
        # Handle Image Update
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Optional: Delete old image if exists
                if interview.image_url:
                    try:
                        old_path = os.path.join('app', interview.image_url.lstrip('/'))
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception:
                        pass # Ignore deletion errors

                filename = secure_filename(f"interview_{interview.id}_{datetime.now().timestamp()}_{file.filename}")
                upload_path = os.path.join('app', 'static', 'uploads', 'interviews', filename)
                
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                
                file.save(upload_path)
                interview.image_url = url_for('static', filename=f'uploads/interviews/{filename}')
        
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


@bp.route('/interviews/delete_all', methods=['POST'])
@admin_required
def interviews_delete_all():
    """Delete all interviews"""
    try:
        # Delete all interviews
        Interview.query.delete()
        db.session.commit()
        flash('All interviews have been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting interviews: {str(e)}', 'error')
    
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


@bp.route('/mocks/create', methods=['POST'])
@admin_required
def mocks_create():
    """Create a new mock test"""
    try:
        title = request.form.get('title')
        category = request.form.get('category', 'General')
        duration = int(request.form.get('duration', 60))
        total_marks = int(request.form.get('total_marks', 100))
        sections = request.form.getlist('sections')
        
        available_from_str = request.form.get('available_from')
        available_until_str = request.form.get('available_until')
        
        available_from = datetime.fromisoformat(available_from_str) if available_from_str else None
        available_until = datetime.fromisoformat(available_until_str) if available_until_str else None
        
        mock = MockTest(
            title=title,
            category=category,
            duration_minutes=duration,
            total_marks=total_marks,
            sections=sections,
            available_from=available_from,
            available_until=available_until,
            is_active=True
        )
        
        db.session.add(mock)
        db.session.commit()
        flash('Mock test scheduled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error scheduling test: {str(e)}', 'error')
        
    return redirect(url_for('admin.mocks'))


@bp.route('/mocks/<int:mock_id>/questions')
@admin_required
def mock_questions(mock_id):
    """View and manage questions for a specific mock test"""
    mock = MockTest.query.get_or_404(mock_id)
    questions = Question.query.filter_by(mock_test_id=mock_id).order_by(Question.question_number).all()
    return render_template('dashboard/admin/mock_questions.html', mock=mock, questions=questions)


@bp.route('/mocks/<int:mock_id>/questions/add', methods=['POST'])
@admin_required
def mock_questions_add(mock_id):
    """Add a new question to a mock test"""
    try:
        section = request.form.get('section')
        question_text = request.form.get('question_text')
        correct_answer = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        
        # Handle Question Image
        question_image_url = None
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                filename = secure_filename(f"q_{mock_id}_{datetime.now().timestamp()}_{file.filename}")
                upload_path = os.path.join('app', 'static', 'uploads', 'mocks', filename)
                file.save(upload_path)
                question_image_url = url_for('static', filename=f'uploads/mocks/{filename}')

        # Handle Options
        options = []
        for i in range(1, 5):
            opt_text = request.form.get(f'option_{i}_text')
            opt_image_url = None
            if f'option_{i}_image' in request.files:
                file = request.files[f'option_{i}_image']
                if file and file.filename:
                    filename = secure_filename(f"opt_{mock_id}_{i}_{datetime.now().timestamp()}_{file.filename}")
                    upload_path = os.path.join('app', 'static', 'uploads', 'mocks', filename)
                    file.save(upload_path)
                    opt_image_url = url_for('static', filename=f'uploads/mocks/{filename}')
            
            options.append({
                'text': opt_text,
                'image': opt_image_url
            })

        # Get next question number
        last_q = Question.query.filter_by(mock_test_id=mock_id).order_by(Question.question_number.desc()).first()
        qn = (last_q.question_number + 1) if last_q and last_q.question_number else 1

        question = Question(
            mock_test_id=mock_id,
            section=section,
            question_text=question_text,
            question_image_url=question_image_url,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            question_number=qn
        )
        
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding question: {str(e)}', 'error')
        
    return redirect(url_for('admin.mock_questions', mock_id=mock_id))


@bp.route('/mocks/<int:mock_id>/questions/<int:question_id>/edit', methods=['POST'])
@admin_required
def mock_questions_edit(mock_id, question_id):
    """Update an existing question in a mock test"""
    try:
        question = Question.query.get_or_404(question_id)
        section = request.form.get('section')
        question_text = request.form.get('question_text')
        correct_answer = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        
        # Update basic fields
        question.section = section
        question.question_text = question_text
        question.correct_answer = correct_answer
        question.explanation = explanation

        # Handle Question Image Update
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                filename = secure_filename(f"q_{mock_id}_{datetime.now().timestamp()}_{file.filename}")
                upload_path = os.path.join('app', 'static', 'uploads', 'mocks', filename)
                file.save(upload_path)
                question.question_image_url = url_for('static', filename=f'uploads/mocks/{filename}')

        # Handle Options Update
        current_options = question.options or []
        updated_options = []
        
        for i in range(1, 5):
            opt_text = request.form.get(f'option_{i}_text')
            
            # Keep existing image by default if it exists in current_options
            opt_image_url = current_options[i-1].get('image') if len(current_options) >= i else None
            
            # Check for new image upload
            if f'option_{i}_image' in request.files:
                file = request.files[f'option_{i}_image']
                if file and file.filename:
                    filename = secure_filename(f"opt_{mock_id}_{i}_{datetime.now().timestamp()}_{file.filename}")
                    upload_path = os.path.join('app', 'static', 'uploads', 'mocks', filename)
                    file.save(upload_path)
                    opt_image_url = url_for('static', filename=f'uploads/mocks/{filename}')
            
            updated_options.append({
                'text': opt_text,
                'image': opt_image_url
            })

        question.options = updated_options
        db.session.commit()
        flash('Question updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating question: {str(e)}', 'error')
        
    return redirect(url_for('admin.mock_questions', mock_id=mock_id))


@bp.route('/mocks/<int:mock_id>/questions/<int:question_id>/delete', methods=['POST'])
@admin_required
def mock_questions_delete(mock_id, question_id):
    """Delete a question from a mock test"""
    try:
        question = Question.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}', 'error')
        
    return redirect(url_for('admin.mock_questions', mock_id=mock_id))


@bp.route('/mocks/<int:mock_id>/delete', methods=['POST'])
@admin_required
def mocks_delete(mock_id):
    """Delete a mock test"""
    try:
        mock = MockTest.query.get_or_404(mock_id)
        db.session.delete(mock)
        db.session.commit()
        flash('Mock test deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting test: {str(e)}', 'error')
        
    return redirect(url_for('admin.mocks'))


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
            'full_content': announcement.content,
            'priority': announcement.priority,
            'type': type_label,
            'type_color': type_color,
            'raw_target_audience': announcement.target_audience,
            'raw_target_batch_id': announcement.target_batch_id
        })
    
    # Fetch batches for targeting
    all_batches = Batch.query.filter(Batch.status.in_(['active', 'upcoming'])).all()
    
    return render_template('dashboard/admin/announcements.html', 
                          announcements=announcements_list,
                          batches=all_batches)

@bp.route('/announcements/update/<int:announcement_id>', methods=['POST'])
@admin_required
def announcements_update(announcement_id):
    """Update an announcement"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        
        title = request.form.get('title')
        content = request.form.get('content')
        priority = request.form.get('priority')
        target_audience = request.form.get('target_audience')
        target_batch_id = request.form.get('target_batch_id')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('admin.announcements'))
            
        announcement.title = title
        announcement.content = content
        announcement.priority = priority
        announcement.target_audience = target_audience
        announcement.target_batch_id = target_batch_id if target_audience == 'specific_batch' and target_batch_id else None
        
        db.session.commit()
        flash('Announcement updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating announcement: {str(e)}', 'error')
        
    return redirect(url_for('admin.announcements'))
@bp.route('/announcements/create', methods=['POST'])
@admin_required
def announcements_create():
    """Create a new announcement"""
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        priority = request.form.get('priority', 'medium')
        target_audience = request.form.get('target_audience', 'all')
        target_batch_id = request.form.get('target_batch_id')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('admin.announcements'))
            
        announcement = Announcement(
            title=title,
            content=content,
            priority=priority,
            target_audience=target_audience,
            target_batch_id=target_batch_id if target_audience == 'specific_batch' and target_batch_id else None,
            created_by=session.get('admin_id'),
            published_at=datetime.utcnow(),
            is_published=True
        )
        
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement published successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error publishing announcement: {str(e)}', 'error')
        
    return redirect(url_for('admin.announcements'))

@bp.route('/announcements/delete/<int:announcement_id>', methods=['POST'])
@admin_required
def announcements_delete(announcement_id):
    """Delete an announcement"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting announcement: {str(e)}', 'error')
        
    return redirect(url_for('admin.announcements'))


@bp.route('/resources')
@admin_required
def resources():
    """List all resources"""
    category = request.args.get('category')
    batch_id = request.args.get('batch_id')
    
    query = Resource.query
    
    if category:
        query = query.filter_by(category=category)
    if batch_id:
        query = query.filter_by(target_batch_id=batch_id)
        
    resources_data = query.order_by(Resource.created_at.desc()).all()
    
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
            file_size = f'{size_mb:.1f} MB' if size_mb >= 0.1 else f'{resource.file_size / 1024:.1f} KB'
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
            'type': resource.file_type.upper() if resource.file_type else 'LINK',
            'file_path': resource.file_path,
            'file_url': resource.file_url
        })
    
    # Fetch batches for dropdown
    all_batches = Batch.query.filter(Batch.status.in_(['active', 'upcoming'])).all()
    
    return render_template('dashboard/admin/resources.html', resources=resources_list, batches=all_batches)


@bp.route('/resources/create', methods=['POST'])
@admin_required
def resources_create():
    """Create a new resource"""
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        resource_type = request.form.get('resource_type', 'file')
        access_level = request.form.get('access_level', 'free')
        target_batch_id = request.form.get('target_batch_id')
        
        # Validation
        if not title or not category:
            flash('Title and Category are required', 'error')
            return redirect(url_for('admin.resources'))

        file_path = None
        file_url = None
        file_size = 0
        file_type = None

        if resource_type == 'file' and 'resource_file' in request.files:
            file = request.files['resource_file']
            if file and file.filename:
                filename = secure_filename(f"res_{datetime.now().timestamp()}_{file.filename}")
                upload_path = os.path.join('app', 'static', 'uploads', 'resources', filename)
                file.save(upload_path)
                file_path = f'static/uploads/resources/{filename}'
                file_size = os.path.getsize(upload_path)
                file_type = filename.split('.')[-1].lower()
        else:
            file_url = request.form.get('file_url')
            file_type = 'LINK'

        resource = Resource(
            title=title,
            description=description,
            category=category,
            resource_type=resource_type,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            file_type=file_type,
            access_level=access_level,
            target_batch_id=target_batch_id if target_batch_id and access_level == 'batch_specific' else None,
            uploaded_by=session.get('admin_id')
        )
        
        db.session.add(resource)
        db.session.commit()
        flash('Resource uploaded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading resource: {str(e)}', 'error')
        
    return redirect(url_for('admin.resources'))


@bp.route('/resources/delete/<int:resource_id>', methods=['POST'])
@admin_required
def resources_delete(resource_id):
    """Delete a resource"""
    try:
        resource = Resource.query.get_or_404(resource_id)
        
        # Delete physical file if exists
        if resource.file_path:
            abs_path = os.path.join('app', resource.file_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)
                
        db.session.delete(resource)
        db.session.commit()
        flash('Resource deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting resource: {str(e)}', 'error')
        
    return redirect(url_for('admin.resources'))


@bp.route('/settings')
@admin_required
def settings():
    """Platform settings page"""
    settings = {
        'platform': {
            'name': SiteConfig.get_val('platform_name', 'NST Prep'),
            'email': SiteConfig.get_val('contact_email', 'admin@nstprep.com'),
            'phone': SiteConfig.get_val('contact_phone', '+91 98765 43210')
        }
    }
    
    return render_template('dashboard/admin/settings.html', settings=settings)


@bp.route('/settings/update', methods=['POST'])
@admin_required
def settings_update():
    """Update platform settings"""
    try:
        platform_name = request.form.get('platform_name')
        contact_email = request.form.get('contact_email')
        contact_phone = request.form.get('contact_phone')
        
        if platform_name:
            SiteConfig.set_val('platform_name', platform_name)
        if contact_email:
            SiteConfig.set_val('contact_email', contact_email)
        if contact_phone:
            SiteConfig.set_val('contact_phone', contact_phone)
            
        flash('Settings updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating settings: {str(e)}', 'error')
        
    return redirect(url_for('admin.settings'))


@bp.route('/settings/change-password', methods=['POST'])
@admin_required
def settings_change_password():
    """Update admin password"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('admin.settings'))
            
        admin = User.query.get(session.get('admin_id'))
        if not admin or not admin.check_password(current_password):
            flash('Incorrect current password', 'error')
            return redirect(url_for('admin.settings'))
            
        admin.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating password: {str(e)}', 'error')
        
    return redirect(url_for('admin.settings'))


@bp.route('/analytics')
@admin_required
def analytics():
    """Analytics coming soon page"""
    return render_template('dashboard/admin/analytics.html')


@bp.route('/doubts')
@admin_required
def doubts():
    """Manage student doubts"""
    from app.models.doubt import Doubt, DoubtReply
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    
    # Base query
    query = Doubt.query
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    # Get all doubts with student info
    doubts_query = query.order_by(Doubt.created_at.desc()).all()
    
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
            'category': doubt.category,
            'status': doubt.status,
            'student_name': doubt.student.full_name,
            'student_email': User.query.get(doubt.student.user_id).email if doubt.student.user_id else 'N/A',
            'timestamp': timestamp,
            'created_at': doubt.created_at.strftime('%Y-%m-%d %H:%M'),
            'replies': doubt.replies.count(),
            'views': doubt.views
        })
    
    # Get statistics
    stats = {
        'total': Doubt.query.count(),
        'pending': Doubt.query.filter_by(status='pending').count(),
        'answered': Doubt.query.filter_by(status='answered').count(),
        'closed': Doubt.query.filter_by(status='closed').count()
    }
    
    return render_template('dashboard/admin/doubts.html', 
                         doubts=doubts_list, 
                         stats=stats,
                         current_status=status_filter,
                         current_category=category_filter)
