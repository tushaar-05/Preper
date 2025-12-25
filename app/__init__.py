from flask import Flask
from config import Config
from app.extensions import db, migrate

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

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

    # Register error handlers
    from flask import render_template
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    return app
