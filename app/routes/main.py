from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

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