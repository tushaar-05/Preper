"""
Payment routes for handling payments and transactions
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask import session
from app.extensions import db
from app.models import Student, Batch, Enrollment, Payment
from app.utils import student_required, get_current_student, format_currency
from datetime import datetime
import secrets

bp = Blueprint('payments', __name__, url_prefix='/payment')

@bp.route('/')
@bp.route('/history')
@student_required
def payment():
    """View payment history and subscription status"""
    student = get_current_student()
    
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('user.profile'))
    
    # Get active enrollments
    active_enrollment = Enrollment.query\
        .filter_by(student_id=student.id)\
        .filter(Enrollment.payment_status.in_(['completed', 'partial']))\
        .join(Batch)\
        .first()
    
    # Subscription info
    subscription = None
    if active_enrollment:
        subscription = {
            'status': 'Active' if active_enrollment.payment_status == 'completed' else 'Partial',
            'plan': active_enrollment.batch.name,
            'amount': format_currency(active_enrollment.total_amount),
            'next_billing': 'Lifetime Access',
            'card_last4': '****'  # Placeholder
        }
    
    # Get payment transactions
    payments = Payment.query\
        .filter_by(student_id=student.id)\
        .order_by(Payment.created_at.desc())\
        .all()
    
    transactions = []
    for payment in payments:
        # Get enrollment info
        enrollment = Enrollment.query.get(payment.enrollment_id) if payment.enrollment_id else None
        batch_name = enrollment.batch.name if enrollment else 'General Payment'
        
        transactions.append({
            'id': payment.transaction_id or f'TXN_{payment.id}',
            'date': payment.created_at.strftime('%b %d, %Y'),
            'description': payment.description or f'{batch_name} Payment',
            'amount': format_currency(payment.amount),
            'status': payment.status.title(),
            'invoice_url': payment.receipt_url or '#'
        })
    
    return render_template('dashboard/user/payment.html', 
                         subscription=subscription, 
                         transactions=transactions)


@bp.route('/pending')
@student_required
def payment_pending():
    """View pending payments and available batches"""
    student = get_current_student()
    
    # Get all active batches
    active_batches = Batch.query\
        .filter(Batch.status.in_(['active', 'upcoming']))\
        .filter(Batch.current_enrollment < Batch.max_students)\
        .order_by(Batch.created_at.desc())\
        .all()
    
    # Check which batches student is already enrolled in
    enrolled_batch_ids = [e.batch_id for e in Enrollment.query.filter_by(student_id=student.id).all()]
    
    batches = []
    for batch in active_batches:
        # Skip if already enrolled
        if batch.id in enrolled_batch_ids:
            continue
        
        batches.append({
            'id': batch.id,
            'name': batch.name,
            'price': batch.discounted_price,
            'original_price': batch.original_price,
            'features': batch.features,
            'description': batch.description
        })
    
    return render_template('dashboard/user/payment-pending.html', batches=batches)


@bp.route('/initiate', methods=['POST'])
@student_required
def initiate_payment():
    """Initiate payment for a batch enrollment"""
    student = get_current_student()
    
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'}), 400
    
    batch_id = request.form.get('batch_id')
    
    if not batch_id:
        return jsonify({'success': False, 'message': 'Batch ID required'}), 400
    
    # Get batch
    batch = Batch.query.get(batch_id)
    
    if not batch:
        return jsonify({'success': False, 'message': 'Batch not found'}), 404
    
    # Check if batch is full
    if batch.is_full:
        return jsonify({'success': False, 'message': 'Batch is full'}), 400
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query\
        .filter_by(student_id=student.id, batch_id=batch.id)\
        .first()
    
    if existing_enrollment:
        return jsonify({'success': False, 'message': 'Already enrolled in this batch'}), 400
    
    try:
        # Create enrollment
        enrollment = Enrollment(
            student_id=student.id,
            batch_id=batch.id,
            payment_status='pending',
            total_amount=batch.discounted_price,
            amount_paid=0
        )
        db.session.add(enrollment)
        db.session.flush()
        
        # Create payment record
        transaction_id = f'TXN_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{secrets.token_hex(4)}'
        order_id = f'ORD_{secrets.token_hex(8)}'
        
        payment = Payment(
            student_id=student.id,
            enrollment_id=enrollment.id,
            amount=batch.discounted_price,
            currency='INR',
            transaction_id=transaction_id,
            order_id=order_id,
            status='pending',
            description=f'Enrollment in {batch.name}'
        )
        db.session.add(payment)
        db.session.commit()
        
        # In a real application, redirect to payment gateway here
        # For now, we'll simulate a successful payment
        
        return jsonify({
            'success': True,
            'message': 'Payment initiated successfully',
            'order_id': order_id,
            'redirect_url': url_for('payments.payment_callback', order_id=order_id)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Payment initiation error: {e}")
        return jsonify({'success': False, 'message': 'Error initiating payment'}), 500


@bp.route('/callback')
@student_required
def payment_callback():
    """Handle payment gateway callback (simulated)"""
    order_id = request.args.get('order_id')
    
    if not order_id:
        flash('Invalid payment callback.', 'danger')
        return redirect(url_for('payments.payment_pending'))
    
    # Find payment
    payment = Payment.query.filter_by(order_id=order_id).first()
    
    if not payment:
        flash('Payment not found.', 'danger')
        return redirect(url_for('payments.payment_pending'))
    
    # Simulate successful payment (in real app, verify with gateway)
    try:
        # Update payment status
        payment.status = 'completed'
        payment.completed_at = datetime.utcnow()
        
        # Update enrollment
        enrollment = Enrollment.query.get(payment.enrollment_id)
        if enrollment:
            enrollment.payment_status = 'completed'
            enrollment.amount_paid = payment.amount
            
            # Update batch enrollment count
            batch = Batch.query.get(enrollment.batch_id)
            if batch:
                batch.current_enrollment += 1
            
            # Update student status
            student = Student.query.get(enrollment.student_id)
            if student and student.enrollment_status == 'pending':
                student.enrollment_status = 'active'
        
        db.session.commit()
        
        flash('Payment successful! You are now enrolled in the batch.', 'success')
        return redirect(url_for('user.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Payment callback error: {e}")
        flash('Error processing payment. Please contact support.', 'danger')
        return redirect(url_for('payments.payment_pending'))


@bp.route('/verify/<order_id>')
@student_required
def verify_payment(order_id):
    """Verify payment status"""
    payment = Payment.query.filter_by(order_id=order_id).first()
    
    if not payment:
        return jsonify({'success': False, 'message': 'Payment not found'}), 404
    
    return jsonify({
        'success': True,
        'status': payment.status,
        'amount': payment.amount,
        'transaction_id': payment.transaction_id
    })
