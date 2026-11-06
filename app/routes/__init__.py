from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.firs import firs_bp
from app.routes.cases import cases_bp
from app.routes.officers import officers_bp
from app.routes.detainees import detainees_bp
from app.routes.evidence import evidence_bp
from app.routes.resources import resources_bp
from app.routes.complaints import complaints_bp
from app.routes.users import users_bp
from app.routes.reports import reports_bp
from app.routes.notifications import notifications_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'firs_bp',
    'cases_bp',
    'officers_bp',
    'detainees_bp',
    'evidence_bp',
    'resources_bp',
    'complaints_bp',
    'users_bp',
    'reports_bp',
    'notifications_bp'
]
