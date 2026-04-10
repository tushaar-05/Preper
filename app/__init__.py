from flask import Flask
from config import Config
from app.extensions import db, migrate, cache, compress
from app.utils.email_service import init_mail

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    compress.init_app(app)
    init_mail(app)  # Initialize Flask-Mail

    # Initialize Cloudinary
    from app.utils.storage import init_cloudinary
    init_cloudinary(app)

    # Register blueprints - import here to avoid circular imports
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.user import bp as user_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.payments import bp as payments_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payments_bp)

    # Initialize OAuth
    from app.routes.auth import init_oauth
    init_oauth(app)

    # Register error handlers
    from flask import render_template
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    return app
