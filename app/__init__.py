import os
from flask import Flask, render_template, request, url_for, session
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from app.config import Config
from app.models.base import db
from app.models.users import User
from app.models.common import Notification

migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance and upload directories exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', os.path.join(app.instance_path, 'uploads')), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access the Police Station Management System.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.active().filter_by(id=int(user_id)).first()

    @app.before_request
    def session_management():
        # Session timeout after 30 minutes of inactivity
        session.permanent = True

    # Context processors & template globals
    @app.context_processor
    def inject_context():
        unread_count = 0
        if current_user and current_user.is_authenticated:
            try:
                unread_count = Notification.active().filter_by(user_id=current_user.id, is_read=False).count()
            except Exception:
                unread_count = 0

        return {
            'app_name': 'Police Station Management System (PSMS)',
            'current_year': 2026,
            'unread_notifications_count': unread_count
        }

    @app.template_global()
    def url_for_page(page):
        if not request.endpoint:
            return '#'
        args = request.args.to_dict()
        args['page'] = page
        return url_for(request.endpoint, **args)

    # Register Blueprints
    from app.routes import (
        auth_bp, main_bp, firs_bp, cases_bp, officers_bp,
        detainees_bp, evidence_bp, resources_bp, complaints_bp,
        users_bp, reports_bp, notifications_bp
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(firs_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(officers_bp)
    app.register_blueprint(detainees_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)

    # Health check route for Render deployment & monitoring
    @app.route('/health')
    def health_check():
        return "OK", 200

    # Custom Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
