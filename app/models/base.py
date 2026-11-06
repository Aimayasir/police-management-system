from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user

db = SQLAlchemy()

class BaseModel(db.Model):
    """
    Base model providing mandatory primary key, audit timestamps, 
    creator/updater tracking, active/deactive status, and soft-delete support.
    All 54 tables inherit from this base.
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active' / 'deactive'
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_by = db.Column(db.Integer, nullable=True)

    def soft_delete(self, user_id=None):
        """Perform soft delete by marking is_deleted=True and updating audit fields."""
        if user_id is None:
            try:
                if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                    user_id = current_user.id
            except Exception:
                user_id = None
        self.is_deleted = True
        self.deleted_by = user_id
        self.status = 'deactive'
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()

    def restore(self, user_id=None):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_by = None
        self.status = 'active'
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()

    @classmethod
    def active(cls):
        """Filter only active, non-deleted records."""
        return cls.query.filter_by(is_deleted=False)

    @classmethod
    def filter_active(cls, **kwargs):
        """Filter active records matching given kwargs."""
        return cls.query.filter_by(is_deleted=False, **kwargs)
