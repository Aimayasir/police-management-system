import json
from datetime import datetime
from flask import request
from flask_login import current_user
from sqlalchemy import event
from app.models.base import db, BaseModel
from app.models.common import AuditLog

# Flag to prevent recursive audit loops
_IS_AUDITING = False

def log_audit(action, entity_name, entity_id=None, old_values=None, new_values=None, description=None):
    """
    Explicitly record an audit log entry for changes, creations, deletions, or exports.
    """
    global _IS_AUDITING
    if _IS_AUDITING:
        return
    try:
        _IS_AUDITING = True
        user_id = None
        if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.id

        ip_addr = None
        try:
            ip_addr = request.remote_addr if request else None
        except Exception:
            ip_addr = '127.0.0.1'

        old_str = json.dumps(old_values, default=str) if isinstance(old_values, dict) else (str(old_values) if old_values else None)
        new_str = json.dumps(new_values, default=str) if isinstance(new_values, dict) else (str(new_values) if new_values else None)

        log = AuditLog(
            user_id=user_id,
            action=action.upper(),
            entity_name=entity_name,
            entity_id=entity_id,
            old_values=old_str,
            new_values=new_str,
            ip_address=ip_addr,
            description=description,
            created_by=user_id
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Logging failure should not disrupt main transaction flow
        print(f"[AUDIT LOG ERROR] Failed to record audit log: {e}")
    finally:
        _IS_AUDITING = False


def setup_audit_event_listeners(app):
    """
    Registers SQLAlchemy event listeners on the database session to automatically
    log insert and update operations for audit tracking.
    """
    # Explicit helper log_audit is already integrated into all routes.
    pass
