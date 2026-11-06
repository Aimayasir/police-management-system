from datetime import datetime, date
from app.models.base import db, BaseModel

class FirStatus(BaseModel):
    __tablename__ = 'fir_statuses'

    name = db.Column(db.String(50), unique=True, nullable=False)  # Registered, Under Investigation, Charge Sheet Filed, Closed, Quashed
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    color_badge = db.Column(db.String(30), default='secondary')

    firs = db.relationship('FIR', back_populates='status_rel', lazy='dynamic')

    def __repr__(self):
        return f"<FirStatus {self.name}>"


class CrimeCategory(BaseModel):
    __tablename__ = 'crime_categories'

    name = db.Column(db.String(100), unique=True, nullable=False)  # Violent Crime, Property Crime, Cyber Crime, Financial Fraud, Narcotics, Traffic Offense
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    crime_types = db.relationship('CrimeType', back_populates='category', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<CrimeCategory {self.name}>"


class CrimeType(BaseModel):
    __tablename__ = 'crime_types'

    category_id = db.Column(db.Integer, db.ForeignKey('crime_categories.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)  # Murder, Burglary, Online Phishing, Robbery, Assault, Smuggling
    code = db.Column(db.String(40), unique=True, nullable=False)
    relevant_sections = db.Column(db.String(255), nullable=False)  # e.g., IPC 302, 379, 420
    severity_level = db.Column(db.String(30), default='Medium', nullable=False)  # Low, Medium, High, Critical

    category = db.relationship('CrimeCategory', back_populates='crime_types')
    firs = db.relationship('FIR', back_populates='crime_type', lazy='dynamic')
    cases = db.relationship('Case', back_populates='crime_type', lazy='dynamic')

    def __repr__(self):
        return f"<CrimeType {self.name} ({self.relevant_sections})>"


class FIR(BaseModel):
    __tablename__ = 'firs'

    fir_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    crime_type_id = db.Column(db.Integer, db.ForeignKey('crime_types.id'), nullable=False, index=True)
    complainant_id = db.Column(db.Integer, db.ForeignKey('complainants.id'), nullable=True, index=True)
    current_status_id = db.Column(db.Integer, db.ForeignKey('fir_statuses.id'), nullable=False, index=True)
    registered_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    io_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=True, index=True)

    incident_date_time = db.Column(db.DateTime, nullable=False)
    incident_location = db.Column(db.String(255), nullable=False)
    distance_from_station = db.Column(db.String(50), nullable=True)
    incident_details = db.Column(db.Text, nullable=False)
    is_cognizable = db.Column(db.Boolean, default=True, nullable=False)

    station = db.relationship('PoliceStation', back_populates='firs')
    crime_type = db.relationship('CrimeType', back_populates='firs')
    complainant = db.relationship('Complainant', back_populates='firs')
    status_rel = db.relationship('FirStatus', back_populates='firs')
    registered_by = db.relationship('User', foreign_keys=[registered_by_user_id])
    io_officer = db.relationship('Officer', foreign_keys=[io_officer_id])

    case = db.relationship('Case', back_populates='fir', uselist=False)
    evidences = db.relationship('Evidence', back_populates='fir', lazy='dynamic')

    def __repr__(self):
        return f"<FIR {self.fir_number}>"


class Case(BaseModel):
    __tablename__ = 'cases'

    case_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    fir_id = db.Column(db.Integer, db.ForeignKey('firs.id'), unique=True, nullable=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    lead_investigator_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    crime_type_id = db.Column(db.Integer, db.ForeignKey('crime_types.id'), nullable=False, index=True)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=True)

    case_title = db.Column(db.String(200), nullable=False)
    case_status = db.Column(db.String(40), default='Under Investigation', nullable=False)  # Open, Under Investigation, Charge Sheeted, In Court, Closed
    date_opened = db.Column(db.Date, default=date.today, nullable=False)
    date_closed = db.Column(db.Date, nullable=True)
    summary = db.Column(db.Text, nullable=False)

    fir = db.relationship('FIR', back_populates='case')
    station = db.relationship('PoliceStation')
    lead_investigator = db.relationship('Officer', foreign_keys=[lead_investigator_id])
    crime_type = db.relationship('CrimeType', back_populates='cases')
    court = db.relationship('Court', back_populates='cases')

    status_history = db.relationship('CaseStatusHistory', back_populates='case', cascade='all, delete-orphan')
    assigned_officers = db.relationship('CaseOfficer', back_populates='case', cascade='all, delete-orphan')
    case_notes = db.relationship('CaseNote', back_populates='case', cascade='all, delete-orphan')
    case_hearings = db.relationship('CaseHearing', back_populates='case', cascade='all, delete-orphan')
    case_accused = db.relationship('CaseAccused', back_populates='case', cascade='all, delete-orphan')
    case_victims = db.relationship('CaseVictim', back_populates='case', cascade='all, delete-orphan')
    case_witnesses = db.relationship('CaseWitness', back_populates='case', cascade='all, delete-orphan')
    evidences = db.relationship('Evidence', back_populates='case', lazy='dynamic')

    def __repr__(self):
        return f"<Case {self.case_number} - {self.case_title}>"


class CaseStatusHistory(BaseModel):
    __tablename__ = 'case_status_histories'

    case_id = db.Column(db.Integer, db.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, index=True)
    previous_status = db.Column(db.String(40), nullable=False)
    new_status = db.Column(db.String(40), nullable=False)
    change_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comments = db.Column(db.Text, nullable=True)

    case = db.relationship('Case', back_populates='status_history')
    changed_by = db.relationship('User')


class CaseOfficer(BaseModel):
    """Junction table connecting Cases and Officers with specific roles."""
    __tablename__ = 'case_officers'

    case_id = db.Column(db.Integer, db.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id', ondelete='CASCADE'), nullable=False, index=True)
    role_in_case = db.Column(db.String(80), default='Investigating Officer', nullable=False)  # Lead IO, Assisting Officer, Forensics Expert
    assigned_date = db.Column(db.Date, default=date.today, nullable=False)
    relieved_date = db.Column(db.Date, nullable=True)

    case = db.relationship('Case', back_populates='assigned_officers')
    officer = db.relationship('Officer')

    def __repr__(self):
        return f"<CaseOfficer Case={self.case_id} Officer={self.officer_id}>"


class CaseNote(BaseModel):
    __tablename__ = 'case_notes'

    case_id = db.Column(db.Integer, db.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    note_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_confidential = db.Column(db.Boolean, default=False, nullable=False)

    case = db.relationship('Case', back_populates='case_notes')
    officer = db.relationship('Officer')


class Court(BaseModel):
    __tablename__ = 'courts'

    name = db.Column(db.String(150), unique=True, nullable=False)  # High Court, District Court, Sessions Court, Magistrate Court
    court_type = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    jurisdiction_area = db.Column(db.String(200), nullable=True)
    contact_number = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=False)

    judges = db.relationship('Judge', back_populates='court', cascade='all, delete-orphan')
    cases = db.relationship('Case', back_populates='court', lazy='dynamic')
    hearings = db.relationship('CaseHearing', back_populates='court', lazy='dynamic')

    def __repr__(self):
        return f"<Court {self.name}>"


class Judge(BaseModel):
    __tablename__ = 'judges'

    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    designation = db.Column(db.String(100), nullable=False)  # Chief Judicial Magistrate, Additional Sessions Judge
    room_number = db.Column(db.String(30), nullable=True)
    contact_number = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)

    court = db.relationship('Court', back_populates='judges')
    hearings = db.relationship('CaseHearing', back_populates='judge', lazy='dynamic')

    def __repr__(self):
        return f"<Judge {self.full_name}>"


class CaseHearing(BaseModel):
    __tablename__ = 'case_hearings'

    case_id = db.Column(db.Integer, db.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, index=True)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False, index=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('judges.id'), nullable=True)

    hearing_date = db.Column(db.Date, nullable=False, index=True)
    hearing_time = db.Column(db.String(20), nullable=True)
    hearing_type = db.Column(db.String(60), nullable=False)  # Bail Hearing, Charge Framing, Evidence Presentation, Cross Exam, Final Verdict
    outcome = db.Column(db.String(100), nullable=True)  # Adjourned, Bail Granted, Bail Denied, Next Date, Convicted, Acquitted
    next_hearing_date = db.Column(db.Date, nullable=True)
    judge_remarks = db.Column(db.Text, nullable=True)

    case = db.relationship('Case', back_populates='case_hearings')
    court = db.relationship('Court', back_populates='hearings')
    judge = db.relationship('Judge', back_populates='hearings')

    def __repr__(self):
        return f"<CaseHearing Case={self.case_id} Date={self.hearing_date}>"
