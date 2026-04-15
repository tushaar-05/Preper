"""
Payment routes for handling payments and transactions
"""

import razorpay
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
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
        
    # If no active enrollment, redirect to pending payments page
    if not active_enrollment:
        return redirect(url_for('payments.payment_pending'))
    
    # Subscription info
    subscription = None
    if active_enrollment:
        subscription = {
            'status': 'Active' if active_enrollment.payment_status == 'completed' else 'Partial',
            'plan': active_enrollment.batch.name,
            'amount': format_currency(active_enrollment.batch.discounted_price),
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
                         transactions=transactions,
                         student=student)


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
    
    # Check which batches student is already enrolled in (completed or partial)
    enrolled_batch_ids = [
        e.batch_id for e in Enrollment.query
        .filter_by(student_id=student.id)
        .filter(Enrollment.payment_status.in_(['completed', 'partial']))
        .all()
    ]
    
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
    
    return render_template('dashboard/user/payment-pending.html', batches=batches, student=student)


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
        
    if existing_enrollment and existing_enrollment.payment_status == 'completed':
        return jsonify({'success': False, 'message': 'Already enrolled in this batch'}), 400
    
    try:
        # Create enrollment if not exists
        enrollment = existing_enrollment
        if not enrollment:
            enrollment = Enrollment(
                student_id=student.id,
                batch_id=batch.id,
                payment_status='pending',
                total_amount=batch.discounted_price,
                amount_paid=0
            )
            db.session.add(enrollment)
            db.session.flush()
        
        # Initialize Razorpay Client
        razorpay_client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'], 
            current_app.config['RAZORPAY_KEY_SECRET']
        ))

        # Create Razorpay Order
        amount_in_paise = int(batch.discounted_price * 100)
        currency = 'INR'
        
        razorpay_order = razorpay_client.order.create(dict(
            amount=amount_in_paise,
            currency=currency,
            payment_capture='1',
            notes={
                'enrollment_id': enrollment.id,
                'student_id': student.id,
                'batch_id': batch.id
            }
        ))
        
        razorpay_order_id = razorpay_order['id']
        
        # Create payment record
        transaction_id = f'TXN_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{secrets.token_hex(4)}'
        
        payment = Payment(
            student_id=student.id,
            enrollment_id=enrollment.id,
            amount=batch.discounted_price,
            currency=currency,
            transaction_id=transaction_id,
            order_id=razorpay_order_id,
            gateway='razorpay',
            status='pending',
            description=f'Enrollment in {batch.name}'
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment initiated successfully',
            'order_id': razorpay_order_id,
            'amount': amount_in_paise,
            'currency': currency,
            'key': current_app.config['RAZORPAY_KEY_ID'],
            'prefill': {
                'name': student.full_name,
                'email': student.user.email,
                'contact': student.phone
            },
            'description': f'Payment for {batch.name}'
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        print(f"Payment initiation error: {e}")
        print(f"Key ID configured: {bool(current_app.config.get('RAZORPAY_KEY_ID'))}")
        return jsonify({'success': False, 'message': f'Error initiating payment: {str(e)}'}), 500


@bp.route('/verify', methods=['POST'])
@student_required
def verify_payment():
    """Verify payment signature from Razorpay"""
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')
    
    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        if request.is_json:
            return jsonify({'success': False, 'message': 'Missing payment details'}), 400
        else:
            flash('Missing payment details. Please try again.', 'danger')
            return redirect(url_for('payments.payment_pending'))
        
    try:
        # Initialize Razorpay Client
        razorpay_client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'], 
            current_app.config['RAZORPAY_KEY_SECRET']
        ))

        # Verify Signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update Payment Record
        payment = Payment.query.filter_by(order_id=razorpay_order_id).first()
        
        if not payment:
            return jsonify({'success': False, 'message': 'Payment record not found'}), 404
            
        payment.status = 'completed'
        payment.gateway_response = str(data)
        payment.completed_at = datetime.utcnow()
        payment.payment_method = 'razorpay'
        
        # Update Enrollment
        enrollment = Enrollment.query.get(payment.enrollment_id)
        if enrollment:
            # Check if this is first time completion BEFORE updating
            is_first_completion = enrollment.payment_status != 'completed'
            
            enrollment.payment_status = 'completed'
            enrollment.amount_paid = payment.amount
            
            # Update Batch Count (only if first time completion)
            if is_first_completion:
                 batch = Batch.query.get(enrollment.batch_id)
                 if batch:
                     batch.current_enrollment += 1
            
            # Update Student Status
            student = Student.query.get(enrollment.student_id)
            if student:
                student.enrollment_status = 'active'
                
        db.session.commit()
        
        flash('Payment successful! You are now enrolled.', 'success')
        
        if request.is_json:
            return jsonify({'success': True, 'redirect_url': url_for('payments.payment')})
        else:
            return redirect(url_for('payments.payment'))
        
    except razorpay.errors.SignatureVerificationError:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Payment signature verification failed'}), 400
        else:
            flash('Payment verification failed. Please contact support.', 'danger')
            return redirect(url_for('payments.payment_pending'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Payment verification error: {e}")
        if request.is_json:
            return jsonify({'success': False, 'message': 'Error verifying payment'}), 500
        else:
            flash('An error occurred during verification.', 'danger')
            return redirect(url_for('payments.payment_pending'))



