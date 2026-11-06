from datetime import datetime
from app.models.base import db, BaseModel

class Complaint(BaseModel):
    __tablename__ = 'complaints'

    complaint_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    citizen_name = db.Column(db.String(120), nullable=False)
    citizen_phone = db.Column(db.String(30), nullable=False)
    citizen_email = db.Column(db.String(120), nullable=True)
    citizen_address = db.Column(db.Text, nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)

    complaint_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(30), default='Medium', nullable=False)  # Low, Medium, High, Urgent
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=True)
    resolution_status = db.Column(db.String(40), default='Pending', nullable=False)  # Pending, Under Inquiry, Converted to FIR, Dismissed, Resolved
    resolution_notes = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    station = db.relationship('PoliceStation', back_populates='complaints')
    assigned_officer = db.relationship('Officer')

    def __repr__(self):
        return f"<Complaint {self.complaint_number} - {self.subject}>"


class Notification(BaseModel):
    __tablename__ = 'notifications'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(40), default='Alert', nullable=False)  # Alert, Duty, FIR, Case, Custody, System
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    action_url = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification User={self.user_id} Title={self.title}>"


class AuditLog(BaseModel):
    __tablename__ = 'audit_logs'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, SOFT_DELETE, LOGIN, EXPORT
    entity_name = db.Column(db.String(60), nullable=False)  # firs, cases, officers, detainees, etc.
    entity_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(db.Text, nullable=True)
    new_values = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    description = db.Column(db.Text, nullable=True)

    user = db.relationship('User')

    def __repr__(self):
        return f"<AuditLog Action={self.action} Entity={self.entity_name} ID={self.entity_id}>"


class Document(BaseModel):
    __tablename__ = 'documents'

    entity_name = db.Column(db.String(60), nullable=False, index=True)  # FIR, Case, Evidence, Officer, Detainee, Complaint
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    original_file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, jpg, png, docx
    file_size_kb = db.Column(db.Integer, default=0, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)

    uploaded_by = db.relationship('User')

    def __repr__(self):
        return f"<Document {self.original_file_name} for {self.entity_name}#{self.entity_id}>"
