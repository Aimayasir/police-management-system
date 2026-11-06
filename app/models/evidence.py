from datetime import datetime
from app.models.base import db, BaseModel

class EvidenceType(BaseModel):
    __tablename__ = 'evidence_types'

    name = db.Column(db.String(80), unique=True, nullable=False)  # Physical, Digital, Biological/DNA, Firearm/Ballistic, Document, Narcotics, Vehicle
    code = db.Column(db.String(30), unique=True, nullable=False)
    handling_protocol = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)

    evidences = db.relationship('Evidence', back_populates='evidence_type', lazy='dynamic')

    def __repr__(self):
        return f"<EvidenceType {self.name}>"


class Evidence(BaseModel):
    __tablename__ = 'evidences'

    evidence_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=True, index=True)
    fir_id = db.Column(db.Integer, db.ForeignKey('firs.id'), nullable=True, index=True)
    evidence_type_id = db.Column(db.Integer, db.ForeignKey('evidence_types.id'), nullable=False, index=True)
    collected_by_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)

    item_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    collected_from_location = db.Column(db.String(255), nullable=False)
    collected_at_datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    current_storage_location = db.Column(db.String(150), nullable=False)  # Locker 4B, Vault A, Forensic Lab, Court Repository
    condition_description = db.Column(db.String(255), nullable=True)
    chain_of_custody_status = db.Column(db.String(50), default='In Locker', nullable=False)  # In Locker, In Forensics, In Court, Released, Disposed
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    current_holder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    case = db.relationship('Case', back_populates='evidences')
    fir = db.relationship('FIR', back_populates='evidences')
    evidence_type = db.relationship('EvidenceType', back_populates='evidences')
    collected_by = db.relationship('Officer')
    current_holder = db.relationship('User', foreign_keys=[current_holder_id])
    custody_logs = db.relationship('EvidenceCustodyLog', back_populates='evidence', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Evidence {self.evidence_number} - {self.item_name}>"


class EvidenceCustodyLog(BaseModel):
    __tablename__ = 'evidence_custody_logs'

    evidence_id = db.Column(db.Integer, db.ForeignKey('evidences.id', ondelete='CASCADE'), nullable=False, index=True)
    transferred_from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    transferred_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    transfer_purpose = db.Column(db.String(150), nullable=False)  # Forensic Analysis, Court Exhibition, Locker Shift, Disposal
    source_location = db.Column(db.String(150), nullable=False)
    destination_location = db.Column(db.String(150), nullable=False)
    receipt_ack = db.Column(db.String(100), nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    evidence = db.relationship('Evidence', back_populates='custody_logs')
    transferred_from = db.relationship('User', foreign_keys=[transferred_from_user_id])
    transferred_to = db.relationship('User', foreign_keys=[transferred_to_user_id])

    def __repr__(self):
        return f"<EvidenceCustodyLog Evidence={self.evidence_id} Purpose={self.transfer_purpose}>"


class LockupCell(BaseModel):
    __tablename__ = 'lockup_cells'

    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    cell_number = db.Column(db.String(30), nullable=False)
    cell_name = db.Column(db.String(80), nullable=False)
    cell_type = db.Column(db.String(40), default='General', nullable=False)  # General, Female, Juvenile, Solitary
    capacity = db.Column(db.Integer, default=4, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0, nullable=False)
    cell_condition = db.Column(db.String(60), default='Clean & Secure', nullable=False)
    security_level = db.Column(db.String(30), default='High', nullable=False)  # Standard, High, Maximum

    station = db.relationship('PoliceStation', back_populates='lockup_cells')
    detention_records = db.relationship('DetentionRecord', back_populates='cell', lazy='dynamic')

    def __repr__(self):
        return f"<LockupCell {self.cell_number} ({self.cell_name})>"


class Detainee(BaseModel):
    __tablename__ = 'detainees'

    accused_id = db.Column(db.Integer, db.ForeignKey('accused.id', ondelete='SET NULL'), nullable=True, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    alias = db.Column(db.String(100), nullable=True)
    national_id = db.Column(db.String(50), nullable=True)
    gender = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    blood_group = db.Column(db.String(10), nullable=True)
    personal_belongings = db.Column(db.Text, nullable=True)  # Wallet, mobile, keys, belt stored in property room
    health_condition = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)

    accused = db.relationship('Accused', back_populates='detainees')
    detention_records = db.relationship('DetentionRecord', back_populates='detainee', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Detainee {self.full_name}>"


class DetentionRecord(BaseModel):
    __tablename__ = 'detention_records'

    detainee_id = db.Column(db.Integer, db.ForeignKey('detainees.id', ondelete='CASCADE'), nullable=False, index=True)
    cell_id = db.Column(db.Integer, db.ForeignKey('lockup_cells.id'), nullable=False, index=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=True)
    fir_id = db.Column(db.Integer, db.ForeignKey('firs.id'), nullable=True)
    arresting_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)

    arrest_date_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    detention_reason = db.Column(db.Text, nullable=False)
    medical_examination_done = db.Column(db.Boolean, default=True, nullable=False)
    doctor_name = db.Column(db.String(120), nullable=True)
    detention_status = db.Column(db.String(40), default='In Custody', nullable=False)  # In Custody, Released, Remanded to Judicial, Hospitalized
    release_date_time = db.Column(db.DateTime, nullable=True)
    release_authorized_by_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=True)

    detainee = db.relationship('Detainee', back_populates='detention_records')
    cell = db.relationship('LockupCell', back_populates='detention_records')
    case = db.relationship('Case')
    fir = db.relationship('FIR')
    arresting_officer = db.relationship('Officer', foreign_keys=[arresting_officer_id])
    release_authorizer = db.relationship('Officer', foreign_keys=[release_authorized_by_id])
    bail_records = db.relationship('BailRecord', back_populates='detention_record', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<DetentionRecord Detainee={self.detainee_id} Status={self.detention_status}>"


class BailRecord(BaseModel):
    __tablename__ = 'bail_records'

    detention_record_id = db.Column(db.Integer, db.ForeignKey('detention_records.id', ondelete='CASCADE'), nullable=False, index=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=True)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=True)

    surety_name = db.Column(db.String(120), nullable=False)
    surety_contact = db.Column(db.String(30), nullable=False)
    surety_national_id = db.Column(db.String(50), nullable=False)
    bail_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    bail_granted_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    bail_order_reference = db.Column(db.String(100), nullable=False)
    bail_conditions = db.Column(db.Text, nullable=True)
    lawyer_name = db.Column(db.String(120), nullable=True)

    detention_record = db.relationship('DetentionRecord', back_populates='bail_records')
    case = db.relationship('Case')
    court = db.relationship('Court')

    def __repr__(self):
        return f"<BailRecord Ref={self.bail_order_reference} Surety={self.surety_name}>"
