from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Landing page"""
    from app.models import Batch
    # Get Neumann batch or first active batch
    batch = Batch.query.filter(Batch.name.ilike('%neumann%')).first()
    if not batch:
        batch = Batch.query.filter_by(status='active').first()
    
    return render_template('index.html', batch=batch)

@bp.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')

@bp.route('/terms')
def terms():
    """Terms and Conditions"""
    return render_template('policy/terms.html')

@bp.route('/refund-policy')
def refund_policy():
    """Cancellation and Refund Policy"""
    return render_template('policy/refund.html')

@bp.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy"""
    return render_template('policy/privacy.html')