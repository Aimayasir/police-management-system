from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.models.base import db, BaseModel

class Role(BaseModel):
    __tablename__ = 'roles'

    name = db.Column(db.String(50), unique=True, nullable=False)  # Admin, SHO, Inspector, Constable, Clerk
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    users = db.relationship('User', back_populates='role', lazy='dynamic')
    permissions = db.relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(BaseModel):
    __tablename__ = 'permissions'

    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(80), unique=True, nullable=False)
    module = db.Column(db.String(50), nullable=False)  # users, firs, cases, evidence, etc.
    description = db.Column(db.String(255), nullable=True)

    role_permissions = db.relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Permission {self.code}>"


class RolePermission(BaseModel):
    """Junction table connecting Roles and Permissions with full audit trail."""
    __tablename__ = 'role_permissions'

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False, index=True)

    role = db.relationship('Role', back_populates='permissions')
    permission = db.relationship('Permission', back_populates='role_permissions')

    def __repr__(self):
        return f"<RolePermission role_id={self.role_id} perm_id={self.permission_id}>"


class User(BaseModel, UserMixin):
    __tablename__ = 'users'

    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    badge_number = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=True, index=True)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    role = db.relationship('Role', back_populates='users')
    station = db.relationship('PoliceStation', back_populates='users', foreign_keys=[station_id])
    officer_profile = db.relationship('Officer', back_populates='user', uselist=False)
    login_logs = db.relationship('LoginLog', back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')

    @property
    def is_active(self):
        """Flask-Login required property."""
        return self.is_active_account and not self.is_deleted

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *role_names):
        return self.role is not None and self.role.name in role_names

    def has_permission(self, perm_code):
        if self.role and self.role.name == 'Admin':
            return True
        if not self.role:
            return False
        return any(rp.permission.code == perm_code for rp in self.role.permissions if not rp.is_deleted)

    def __repr__(self):
        return f"<User {self.username} ({self.role.name if self.role else 'No Role'})>"


class LoginLog(BaseModel):
    __tablename__ = 'login_logs'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    logout_time = db.Column(db.DateTime, nullable=True)
    status_message = db.Column(db.String(100), default='SUCCESS', nullable=False)

    user = db.relationship('User', back_populates='login_logs')

    def __repr__(self):
        return f"<LoginLog user_id={self.user_id} at {self.login_time}>"
