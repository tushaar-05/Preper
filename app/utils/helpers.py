from flask import session
from flask import current_app
from babel.numbers import format_currency as babel_format_currency
from datetime import datetime
from app.models import Student, Enrollment, Batch, MockTest, TestAttempt
from app.extensions import cache

def get_current_student():
    user_id = session.get('student_id')
    if not user_id:
        return None
    return Student.query.filter_by(user_id=user_id).first()

@cache.memoize(timeout=300)
def get_user_batch_ids(student_id):
    return [e.batch_id for e in Enrollment.query.filter_by(student_id=student_id).all()]

def get_user_batches(student_id):
    batch_ids = get_user_batch_ids(student_id)
    return Batch.query.filter(Batch.id.in_(batch_ids)).all()

def format_currency(amount, currency='INR', locale='en_IN'):
    """
    Format a number as a currency string.
    
    Args:
        amount (float): The amount to format
        currency (str): ISO 4217 currency code (default: 'INR' for Indian Rupees)
        locale (str): Locale to use for formatting (default: 'en_IN' for Indian English)
    
    Returns:
        str: Formatted currency string
    """
    try:
        return babel_format_currency(amount, currency, locale=locale)
    except Exception as e:
        current_app.logger.error(f"Error formatting currency: {str(e)}")
        # Fallback to simple formatting if Babel fails
        return f"{currency} {amount:,.2f}"

def get_enrollment_status_color(status):
    """
    Get the appropriate color class for an enrollment status.
    
    Args:
        status (str): The enrollment status (e.g., 'active', 'completed', 'pending')
        
    Returns:
        str: A CSS class name for the status color
    """
    status_colors = {
        'active': 'success',      # Green
        'completed': 'primary',   # Blue
        'pending': 'warning',     # Yellow
        'dropped': 'danger',      # Red
        'cancelled': 'secondary', # Gray
        'on_hold': 'info',        # Light blue
    }
    return status_colors.get(status.lower(), 'secondary')  # Default to gray if status not found

def get_payment_status_color(status):
    """
    Get the appropriate color class for a payment status.
    
    Args:
        status (str): The payment status (e.g., 'paid', 'pending', 'failed')
        
    Returns:
        str: A CSS class name for the status color
    """
    status_colors = {
        'paid': 'success',         # Green
        'completed': 'success',    # Green (synonym for paid)
        'pending': 'warning',      # Yellow
        'processing': 'info',      # Light blue
        'failed': 'danger',        # Red
        'refunded': 'secondary',   # Gray
        'cancelled': 'secondary',  # Gray
        'partially_paid': 'info',  # Light blue
        'overdue': 'danger',       # Red
    }
    return status_colors.get(status.lower(), 'secondary')  # Default to gray if status not found

def get_interview_status_color(status):
    """
    Get the appropriate color class for an interview status.
    
    Args:
        status (str): The interview status (e.g., 'scheduled', 'completed', 'cancelled')
        
    Returns:
        str: A CSS class name for the status color
    """
    status_colors = {
        'scheduled': 'info',        # Light blue
        'completed': 'success',     # Green
        'cancelled': 'danger',      # Red
        'rescheduled': 'warning',   # Yellow
        'no_show': 'secondary',     # Gray
        'in_progress': 'primary',   # Blue
        'pending': 'warning',       # Yellow
        'rejected': 'danger',       # Red
        'accepted': 'success',      # Green
    }
    return status_colors.get(status.lower(), 'secondary')  # Default to gray if status not found

def get_batch_status_color(status):
    """
    Get the appropriate color class for a batch status.
    
    Args:
        status (str): The batch status (e.g., 'upcoming', 'ongoing', 'completed')
        
    Returns:
        str: A CSS class name for the status color
    """
    status_colors = {
        'upcoming': 'info',        # Light blue
        'ongoing': 'success',      # Green
        'completed': 'secondary',  # Gray
        'cancelled': 'danger',     # Red
        'full': 'warning',         # Yellow
        'registration_open': 'success',  # Green
        'registration_closed': 'secondary',  # Gray
        'in_session': 'primary',   # Blue
        'on_hold': 'warning',     # Yellow
        'archived': 'secondary',  # Gray
    }
    return status_colors.get(status.lower(), 'secondary')  # Default to gray if status not found


def calculate_enrollment_progress(student_id, batch_id):
    """
    Calculate the progress of a student in a specific batch.
    
    Args:
        student_id (int): The ID of the student
        batch_id (int): The ID of the batch
        
    Returns:
        dict: A dictionary containing progress information including:
            - completed_tests: Number of completed tests
            - total_tests: Total number of tests in the batch
            - progress_percentage: Percentage of tests completed
            - last_attempt: Timestamp of the last test attempt
    """
    try:
        # Get all tests for the batch
        tests = MockTest.query.filter_by(batch_id=batch_id, is_active=True).all()
        total_tests = len(tests)
        
        if total_tests == 0:
            return {
                'completed_tests': 0,
                'total_tests': 0,
                'progress_percentage': 0,
                'last_attempt': None
            }
        
        # Get all test attempts by the student for this batch
        test_attempts = TestAttempt.query.join(
            MockTest,
            TestAttempt.mock_test_id == MockTest.id
        ).filter(
            TestAttempt.student_id == student_id,
            MockTest.batch_id == batch_id
        ).all()
        
        # Count completed tests (status is 'completed' or 'passed' or 'failed')
        completed_attempts = [
            ta for ta in test_attempts 
            if ta.status in ['completed', 'passed', 'failed']
        ]
        
        # Get the latest attempt timestamp
        last_attempt = max(
            [ta.submitted_at for ta in test_attempts if ta.submitted_at],
            default=None
        )
        
        # Calculate progress percentage
        progress_percentage = min(
            round((len(completed_attempts) / total_tests) * 100, 2),
            100.0  # Cap at 100%
        )
        
        return {
            'completed_tests': len(completed_attempts),
            'total_tests': total_tests,
            'progress_percentage': progress_percentage,
            'last_attempt': last_attempt
        }
        
    except Exception as e:
        current_app.logger.error(f"Error calculating enrollment progress: {str(e)}")
        return {
            'completed_tests': 0,
            'total_tests': 0,
            'progress_percentage': 0,
            'last_attempt': None,
            'error': str(e)
        }
def handle_image_upload(file, folder):
    """Refactored helper for Cloudinary uploads to keep routes clean."""
    from app.utils.storage import upload_file
    if file and file.filename:
        try:
            result = upload_file(file, folder=folder)
            return result.get('secure_url')
        except Exception as e:
            current_app.logger.error(f"Upload to {folder} failed: {e}")
    return None
