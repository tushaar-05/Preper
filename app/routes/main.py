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
    from app.models import Mentor, TeamMember
    from app.extensions import db
    
    # Get team members ordered by display_order
    team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.display_order.asc()).all()
    
    # Fallback/Initial Seed: If no team members exist, add the founding members
    if not team_members:
        try:
            devansh = TeamMember(
                full_name="Devansh Saini",
                role="Founder & Visionary",
                description="The architect behind the vision. Devansh conceptualized Preper, validated the mission, and ensures every detail meets excellence.",
                display_order=1
            )
            tushar = TeamMember(
                full_name="Tushar",
                role="Lead Designer & Developer",
                description="The creative engine. Tushar designed and built the core of the Preper platform, turning the vision into a stunning reality.",
                display_order=2
            )
            db.session.add(devansh)
            db.session.add(tushar)
            db.session.commit()
            team_members = [devansh, tushar]
        except Exception:
            # If table doesn't exist yet or other DB error, create a mock list for display
            team_members = []
            
    mentors = Mentor.query.filter_by(is_active=True).all()
    return render_template('about.html', mentors=mentors, team=team_members)

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