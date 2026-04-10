"""
Admin dashboard routes with database integration
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from app.extensions import db
from app.utils.decorators import admin_required
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, Resource, Payment, Mentor,
    SiteConfig, TeamMember
)
from app.utils import admin_required, get_batch_status_color, get_interview_status_color
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, or_

# Define IST timezone
IST = timezone(timedelta(hours=5, minutes=30))
import os
from werkzeug.utils import secure_filename
from app.utils.storage import upload_file, delete_file

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@admin_required
def dashboard():
    admin = User.query.get(session.get('admin_id'))
    
    # Get statistics with proper error handling and default values
    try:
        total_payments = float(db.session.query(func.sum(Payment.amount))\
            .filter(Payment.status == 'completed')\
            .scalar() or 0)
        
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
            .filter(Enrollment.payment_status.in_(['completed', 'partial']))\
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
        .filter(Enrollment.payment_status.in_(['completed', 'partial']))\
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
        description = request.form.get('description')
        
        if not full_name:
            flash('Mentor name is required', 'error')
            return redirect(url_for('admin.mentors'))
            
        # Handle Image Upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                try:
                    upload_result = upload_file(file, folder='mentors')
                    image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Mentor image upload failed: {e}")
            
        new_mentor = Mentor(
            full_name=full_name,
            email=email,
            role=role,
            rating=5.0,
            image_url=image_url,
            description=description
        )
        
        db.session.add(new_mentor)
        db.session.commit()
        flash(f'Mentor {full_name} added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding mentor: {str(e)}")
        flash('Error adding mentor. Please try again.', 'error')
        
    return redirect(url_for('admin.mentors'))


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
        batch_name = batch.name if (batch and has_paid) else 'Not Enrolled'
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


@bp.route('/sync-db')
@admin_required
def sync_db():
    """Emergency route to sync database schema in production"""
    try:
        from sqlalchemy import text
        # Attempt to add the image_url and description columns to the mentors table
        # We try to add them, if they fail because they exist, that's fine.
        try:
            db.session.execute(text('ALTER TABLE mentors ADD COLUMN image_url VARCHAR(500)'))
        except: pass
        
        try:
            db.session.execute(text('ALTER TABLE mentors ADD COLUMN description TEXT'))
        except: pass
        
        # Create TeamMember table if it doesn't exist
        try:
            db.create_all()
            # If for some reason create_all doesn't work for one table in this env
            # we can use raw SQL as a backup for the specific table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS team_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name VARCHAR(100) NOT NULL,
                    role VARCHAR(100) NOT NULL,
                    description TEXT,
                    image_url VARCHAR(500),
                    display_order INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
        except: pass
        
        db.session.commit()
        flash('Database schema updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        error_msg = str(e).lower()
        if 'duplicate column' in error_msg or 'already exists' in error_msg or '1060' in error_msg:
            flash('Database is already up to date.', 'info')
        else:
            flash(f'Error updating database: {str(e)}', 'error')
            print(f"Sync DB error: {e}")
    
    return redirect(url_for('admin.mentors'))


@bp.route('/mentors')
@admin_required
def mentors():
    """List all mentors with fail-safe for schema updates"""
    admin = User.query.get(session.get('admin_id'))
    try:
        mentors_data = Mentor.query.order_by(Mentor.created_at.desc()).all()
        
        mentors_list = []
        for mentor in mentors_data:
            # Safely get image_url in case the column is somehow not loaded
            image_url = getattr(mentor, 'image_url', None)
            
            mentors_list.append({
                'id': mentor.id,
                'name': mentor.full_name,
                'email': mentor.email,
                'role': mentor.role,
                'rating': f"{mentor.rating:.1f}",
                'status': 'Active' if mentor.is_active else 'Inactive',
                'joined_date': mentor.created_at.strftime('%b %d, %Y'),
                'initial': mentor.full_name[0] if mentor.full_name else '?',
                'image_url': image_url,
                'description': getattr(mentor, 'description', None)
            })
        
        return render_template('dashboard/admin/mentors.html', mentors=mentors_list, admin=admin)
        
    except Exception as e:
        print(f"Mentors list error: {e}")
        db.session.rollback()
        # If we get a database error, show a more helpful page or flash
        flash('Notice: Database schema might need sync. Click the button below if problems persist.', 'warning')
        return render_template('dashboard/admin/mentors.html', mentors=[], db_error=True, admin=admin)

@bp.route('/mentors/edit/<int:mentor_id>', methods=['POST'])
@admin_required
def edit_mentor(mentor_id):
    """Edit an existing mentor"""
    try:
        mentor = Mentor.query.get_or_404(mentor_id)
        mentor.full_name = request.form.get('full_name')
        mentor.email = request.form.get('email')
        mentor.role = request.form.get('role')
        mentor.description = request.form.get('description')
        mentor.is_active = request.form.get('status') == 'active'
        
        # Handle Image Upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                try:
                    upload_result = upload_file(file, folder='mentors')
                    mentor.image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Mentor image update failed: {e}")
        
        db.session.commit()
        flash(f'Mentor {mentor.full_name} updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating mentor: {str(e)}', 'error')
        
    return redirect(url_for('admin.mentors'))

@bp.route('/mentors/delete/<int:mentor_id>', methods=['POST'])
@admin_required
def delete_mentor(mentor_id):
    """Delete a mentor"""
    try:
        mentor = Mentor.query.get_or_404(mentor_id)
        name = mentor.full_name
        db.session.delete(mentor)
        db.session.commit()
        flash(f'Mentor {name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting mentor: {str(e)}', 'error')
        
    return redirect(url_for('admin.mentors'))


@bp.route('/team')
@admin_required
def team():
    """List all core team members"""
    admin = User.query.get(session.get('admin_id'))
    try:
        team_data = TeamMember.query.order_by(TeamMember.display_order.asc(), TeamMember.created_at.desc()).all()
        
        team_list = []
        for member in team_data:
            team_list.append({
                'id': member.id,
                'name': member.full_name,
                'role': member.role,
                'description': member.description,
                'image_url': member.image_url,
                'status': 'Active' if member.is_active else 'Inactive',
                'initial': member.full_name[0] if member.full_name else '?',
                'display_order': member.display_order
            })
        
        return render_template('dashboard/admin/team.html', team=team_list, admin=admin)
    except Exception as e:
        print(f"Team list error: {e}")
        db.session.rollback()
        flash('Notice: Database schema might need sync.', 'warning')
        return render_template('dashboard/admin/team.html', team=[], db_error=True, admin=admin)

@bp.route('/team/add', methods=['POST'])
@admin_required
def add_team_member():
    """Add a new team member"""
    try:
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        description = request.form.get('description')
        display_order = request.form.get('display_order', 0)
        
        if not full_name or not role:
            flash('Name and Role are required', 'error')
            return redirect(url_for('admin.team'))
            
        # Handle Image Upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                try:
                    upload_result = upload_file(file, folder='team')
                    image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Team member image upload failed: {e}")
        
        new_member = TeamMember(
            full_name=full_name,
            role=role,
            description=description,
            image_url=image_url,
            display_order=display_order
        )
        
        db.session.add(new_member)
        db.session.commit()
        flash(f'Team member {full_name} added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding team member: {str(e)}', 'error')
        
    return redirect(url_for('admin.team'))

@bp.route('/team/edit/<int:member_id>', methods=['POST'])
@admin_required
def edit_team_member(member_id):
    """Edit an existing team member"""
    try:
        member = TeamMember.query.get_or_404(member_id)
        member.full_name = request.form.get('full_name')
        member.role = request.form.get('role')
        member.description = request.form.get('description')
        member.display_order = request.form.get('display_order', 0)
        member.is_active = request.form.get('status') == 'active'
        
        # Handle Image Upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                try:
                    upload_result = upload_file(file, folder='team')
                    member.image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Team member image update failed: {e}")
        
        db.session.commit()
        flash(f'Team member {member.full_name} updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating team member: {str(e)}', 'error')
        
    return redirect(url_for('admin.team'))

@bp.route('/team/delete/<int:member_id>', methods=['POST'])
@admin_required
def delete_team_member(member_id):
    """Delete a team member"""
    try:
        member = TeamMember.query.get_or_404(member_id)
        name = member.full_name
        db.session.delete(member)
        db.session.commit()
        flash(f'Team member {name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting team member: {str(e)}', 'error')
        
    return redirect(url_for('admin.team'))


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
                # Cloudinary Upload
                try:
                    upload_result = upload_file(file, folder='interviews')
                    image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Upload failed: {e}")
                    # Continue without image or handle error
                    pass

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
                        # TODO: Implement deletion if using Cloudinary public_id
                        pass 
                    except Exception:
                        pass # Ignore deletion errors

                # Cloudinary Upload
                try:
                    upload_result = upload_file(file, folder='interviews')
                    interview.image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Upload failed: {e}")
                    pass
        
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

def _update_mock_total_marks(mock_id):
    """Recalculate and update the total marks for a mock test based on its questions"""
    try:
        mock = MockTest.query.get(mock_id)
        if mock:
            # Calculate total marks from questions
            # Handle potential None result from sum if no questions exist
            total = db.session.query(func.sum(Question.marks)).filter_by(mock_test_id=mock_id).scalar() or 0
            mock.total_marks = int(total)
            db.session.commit()
    except Exception as e:
        print(f"Error updating total marks for mock {mock_id}: {e}")
        db.session.rollback()


@bp.route('/mocks')
@admin_required
def mocks():
    """List all mock tests"""
    mocks_data = MockTest.query.order_by(MockTest.created_at.desc()).all()
    batches = Batch.query.all()
    
    # Auto-update total marks for legacy data consistency check (optional but good for safety)
    # We won't do it on every load to save performance, but the system relies on it being correct.

    mocks_list = []
    for mock in mocks_data:
        # Get attempt statistics
        attempts_count = TestAttempt.query.filter_by(mock_test_id=mock.id).count()
        avg_score = db.session.query(func.avg(TestAttempt.percentage))\
            .filter_by(mock_test_id=mock.id)\
            .filter(TestAttempt.status == 'completed')\
            .scalar()
        
        # Determine status based on availability
        now = datetime.now(IST).replace(tzinfo=None)
        if mock.is_anytime:
            status = 'Live'
            status_color = 'bg-green-100 text-green-700'
        elif mock.available_from and now < mock.available_from:
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
            'category': mock.category,
            'description': mock.description,
            'duration_minutes': mock.duration_minutes,
            'total_marks': mock.total_marks,
            'passing_marks': mock.passing_marks,
            'batch_id': mock.batch_id or '',
            'batch': mock.batch.name if (mock.batch_id and mock.batch) else 'All Batches',
            'is_anytime': mock.is_anytime,
            'available_from': mock.available_from.strftime('%Y-%m-%dT%H:%M') if mock.available_from else '',
            'available_until': mock.available_until.strftime('%Y-%m-%dT%H:%M') if mock.available_until else '',
            'date': mock.available_from.strftime('%b %d, %Y') if mock.available_from else ('Anytime' if mock.is_anytime else 'N/A'),
            'attempts': attempts_count,
            'avg_score': f'{avg_score:.0f}%' if avg_score else '-',
            'status': status,
            'status_color': status_color
        })
    
    return render_template('dashboard/admin/mocks.html', mocks=mocks_list, batches_list=batches)


@bp.route('/mocks/create', methods=['POST'])
@admin_required
def mocks_create():
    """Create a new mock test"""
    try:
        title = request.form.get('title')
        category = request.form.get('category', 'General')
        duration = int(request.form.get('duration', 180))
        # Total marks starts at 0, updated as questions are added
        total_marks = 0 
        sections = request.form.getlist('sections')
        
        is_anytime = request.form.get('is_anytime') == 'on'
        available_from = None
        available_until = None
        
        if not is_anytime:
            available_from_str = request.form.get('available_from')
            available_from = datetime.fromisoformat(available_from_str) if available_from_str else None
            available_until = available_from + timedelta(minutes=duration) if available_from else None
        
        batch_id = request.form.get('batch_id')
        batch_id = int(batch_id) if batch_id else None
        
        mock = MockTest(
            title=title,
            category=category,
            batch_id=batch_id,
            duration_minutes=duration,
            total_marks=total_marks,
            sections=sections,
            available_from=available_from,
            available_until=available_until,
            is_anytime=is_anytime,
            is_active=True
        )
        
        db.session.add(mock)
        db.session.commit()
        flash('Mock test scheduled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error scheduling test: {str(e)}', 'error')
        
    return redirect(url_for('admin.mocks'))


@bp.route('/mocks/<int:mock_id>/update', methods=['POST'])
@admin_required
def mocks_update(mock_id):
    """Update an existing mock test"""
    try:
        mock = MockTest.query.get_or_404(mock_id)
        
        mock.title = request.form.get('title')
        mock.category = request.form.get('category', 'General')
        
        # Duration is manually editable, Total Marks is auto-calculated
        mock.duration_minutes = int(request.form.get('duration', 180))
        # mock.total_marks is managed automatically
        mock.passing_marks = int(request.form.get('passing_marks', 40))
        
        batch_id = request.form.get('batch_id')
        mock.batch_id = int(batch_id) if batch_id else None
        
        mock.is_anytime = request.form.get('is_anytime') == 'on'
        
        if mock.is_anytime:
            mock.available_from = None
            mock.available_until = None
        else:
            available_from_str = request.form.get('available_from')
            if available_from_str:
                mock.available_from = datetime.fromisoformat(available_from_str)
                mock.available_until = mock.available_from + timedelta(minutes=mock.duration_minutes)
            else:
                mock.available_from = None
                mock.available_until = None
        
        db.session.commit()
        flash('Mock test updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating test: {str(e)}', 'error')
        
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
        marks = int(request.form.get('marks', 1))
        
        # Handle Question Image
        question_image_url = None
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                try:
                    upload_result = upload_file(file, folder='mocks/questions')
                    question_image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Question image upload failed: {e}")
                    flash(f"Error uploading question image: {str(e)}", "error")
                    return redirect(url_for('admin.mock_questions', mock_id=mock_id))

        # Handle Options
        options = []
        i = 1
        while True:
            opt_text = request.form.get(f'option_{i}_text')
            if opt_text is None:
                break
            
            opt_image_url = None
            if f'option_{i}_image' in request.files:
                file = request.files[f'option_{i}_image']
                if file and file.filename:
                    try:
                        upload_result = upload_file(file, folder='mocks/options')
                        opt_image_url = upload_result.get('secure_url')
                    except Exception as e:
                        print(f"Option image upload failed: {e}")
                        flash(f"Error uploading option image: {str(e)}", "error")
                        return redirect(url_for('admin.mock_questions', mock_id=mock_id))
            
            options.append({
                'text': opt_text,
                'image': opt_image_url
            })
            i += 1

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
            question_number=qn,
            marks=marks
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Update mock total marks
        _update_mock_total_marks(mock_id)
        
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
        marks = int(request.form.get('marks', 1))
        
        # Update basic fields
        question.section = section
        question.question_text = question_text
        question.correct_answer = correct_answer
        question.explanation = explanation
        question.marks = marks

        # Handle Question Image Update
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                try:
                    upload_result = upload_file(file, folder='mocks/questions')
                    question.question_image_url = upload_result.get('secure_url')
                except Exception as e:
                    print(f"Question image upload failed: {e}")
                    flash(f"Error uploading question image: {str(e)}", "error")
                    return redirect(url_for('admin.mock_questions', mock_id=mock_id))

        # Handle Options Update
        current_options = question.options or []
        updated_options = []
        
        i = 1
        while True:
            opt_text = request.form.get(f'option_{i}_text')
            if opt_text is None:
                break
            
            # Keep existing image by default if it exists in current_options
            opt_image_url = current_options[i-1].get('image') if len(current_options) >= i else None
            
            # Check for new image upload
            if f'option_{i}_image' in request.files:
                file = request.files[f'option_{i}_image']
                if file and file.filename:
                    try:
                        upload_result = upload_file(file, folder='mocks/options')
                        opt_image_url = upload_result.get('secure_url')
                    except Exception as e:
                        print(f"Option image upload failed: {e}")
                        flash(f"Error uploading option image: {str(e)}", "error")
                        return redirect(url_for('admin.mock_questions', mock_id=mock_id))
            
            updated_options.append({
                'text': opt_text,
                'image': opt_image_url
            })
            i += 1
            
        question.options = updated_options
        db.session.commit()
        
        # Update mock total marks
        _update_mock_total_marks(mock_id)
        
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
        
        # Update mock total marks
        _update_mock_total_marks(mock_id)
        
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
            'category': resource.category,
            'batch': batch_name,
            'uploaded_date': resource.created_at.strftime('%b %d, %Y'),
            'file_size': file_size,
            'downloads': resource.download_count,
            'type': resource.file_type.upper() if resource.file_type else 'LINK',
            'file_path': resource.file_path,
            'file_url': resource.file_url,
            'description': resource.description,
            'access_level': resource.access_level,
            'target_batch_id': resource.target_batch_id,
            'resource_type': resource.resource_type
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
                try:
                    res_type = 'raw' if file.filename.lower().endswith('.pdf') else 'auto'
                    upload_result = upload_file(file, folder='resources', resource_type=res_type)
                    file_path = None # No local path
                    file_url = upload_result.get('secure_url')
                    file_size = upload_result.get('bytes', 0)
                    file_type = upload_result.get('format', file.filename.split('.')[-1].lower())
                except Exception as e:
                    print(f"Resource upload failed: {e}")
                    flash(f'Error uploading resource: {str(e)}', 'error')
                    return redirect(url_for('admin.resources'))
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
    return redirect(url_for('admin.resources'))


@bp.route('/resources/edit/<int:resource_id>', methods=['POST'])
@admin_required
def resources_edit(resource_id):
    """Edit an existing resource"""
    from app.models.resource import Resource
    try:
        resource = Resource.query.get_or_404(resource_id)
        
        resource.title = request.form.get('title', resource.title)
        resource.description = request.form.get('description', resource.description)
        resource.category = request.form.get('category', resource.category)
        resource.access_level = request.form.get('access_level', resource.access_level)
        
        target_batch_id = request.form.get('target_batch_id')
        if resource.access_level == 'batch_specific' and target_batch_id:
            resource.target_batch_id = target_batch_id
        else:
            resource.target_batch_id = None
            
        db.session.commit()
        flash('Resource updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating resource: {str(e)}', 'error')
        
    return redirect(url_for('admin.resources'))


@bp.route('/resources/delete/<int:resource_id>', methods=['POST'])
@admin_required
def resources_delete(resource_id):
    """Delete a resource"""
    try:
        resource = Resource.query.get_or_404(resource_id)
        
        # Delete physical file if exists
        # Cloudinary or local?
        # If it starts with http, it might be Cloudinary, but we don't have public_id stored easily
        # For now, skip deletion of remote files to be safe
        if resource.file_path and not resource.file_path.startswith('http') and 'static/uploads' in resource.file_path:
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


@bp.route('/doubts/<int:doubt_id>')
@admin_required
def doubt_detail(doubt_id):
    """View individual doubt with replies (admin)"""
    from app.models.doubt import Doubt, DoubtReply
    
    # Get the doubt
    doubt = Doubt.query.get_or_404(doubt_id)
    
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
        'student_name': doubt.student.full_name,
        'student_email': User.query.get(doubt.student.user_id).email if doubt.student.user_id else 'N/A',
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
    
    return render_template('dashboard/admin/doubt_detail.html', 
                         doubt=doubt_data, 
                         replies=replies_list)


@bp.route('/doubts/<int:doubt_id>/reply', methods=['POST'])
@admin_required
def doubt_reply(doubt_id):
    """Post a reply to a doubt (admin)"""
    from app.models.doubt import Doubt, DoubtReply
    
    # Get form data
    content = request.form.get('content')
    mark_as_answered = request.form.get('mark_as_answered') == 'on'
    
    # Validate input
    if not content:
        flash('Please provide a reply.', 'danger')
        return redirect(url_for('admin.doubt_detail', doubt_id=doubt_id))
    
    try:
        # Get the doubt
        doubt = Doubt.query.get_or_404(doubt_id)
        
        # Get admin user ID
        admin_id = session.get('admin_id')
        
        # Create new reply
        new_reply = DoubtReply(
            doubt_id=doubt_id,
            user_id=admin_id,
            content=content,
            is_staff_reply=True
        )
        
        db.session.add(new_reply)
        
        # Update doubt status if marked as answered
        if mark_as_answered:
            doubt.status = 'answered'
        
        db.session.commit()
        
        flash('Your reply has been posted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to post reply. Please try again.', 'danger')
        print(f"Error posting reply: {e}")
    
    return redirect(url_for('admin.doubt_detail', doubt_id=doubt_id))

@bp.route('/doubts/delete/<int:doubt_id>', methods=['POST'])
@admin_required
def delete_doubt(doubt_id):
    """Delete a doubt (admin)"""
    from app.models.doubt import Doubt
    try:
        doubt = Doubt.query.get_or_404(doubt_id)
        db.session.delete(doubt)
        db.session.commit()
        flash('Doubt deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete doubt. Please try again.', 'danger')
        print(f"Error deleting doubt: {e}")
    
    return redirect(url_for('admin.doubts'))
