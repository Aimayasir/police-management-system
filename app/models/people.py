from datetime import datetime, date
from app.models.base import db, BaseModel

class Complainant(BaseModel):
    __tablename__ = 'complainants'

    full_name = db.Column(db.String(120), nullable=False)
    father_or_spouse_name = db.Column(db.String(120), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=False)
    national_id = db.Column(db.String(50), nullable=True, index=True)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=False)
    occupation = db.Column(db.String(100), nullable=True)

    firs = db.relationship('FIR', back_populates='complainant', lazy='dynamic')

    def __repr__(self):
        return f"<Complainant {self.full_name}>"


class Accused(BaseModel):
    __tablename__ = 'accused'

    full_name = db.Column(db.String(120), nullable=False)
    alias = db.Column(db.String(100), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=False)
    national_id = db.Column(db.String(50), nullable=True, index=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    physical_features = db.Column(db.Text, nullable=True)  # Height, scars, tattoos, build
    nationality = db.Column(db.String(60), default='National', nullable=False)
    occupation = db.Column(db.String(100), nullable=True)
    is_in_custody = db.Column(db.Boolean, default=False, nullable=False)

    cases = db.relationship('CaseAccused', back_populates='accused', cascade='all, delete-orphan')
    criminal_records = db.relationship('CriminalRecord', back_populates='accused', cascade='all, delete-orphan')
    detainees = db.relationship('Detainee', back_populates='accused', lazy='dynamic')

    def __repr__(self):
        return f"<Accused {self.full_name} ({self.alias or 'No Alias'})>"


class Victim(BaseModel):
    __tablename__ = 'victims'

    full_name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=False)
    national_id = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    medical_report_summary = db.Column(db.Text, nullable=True)
    injury_status = db.Column(db.String(60), nullable=True)  # Uninjured, Minor, Severe, Critical, Deceased
    contact_person = db.Column(db.String(120), nullable=True)

    cases = db.relationship('CaseVictim', back_populates='victim', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Victim {self.full_name}>"


class Witness(BaseModel):
    __tablename__ = 'witnesses'

    full_name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=False)
    national_id = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(30), nullable=False)
    address = db.Column(db.Text, nullable=True)
    witness_type = db.Column(db.String(50), default='Eye Witness', nullable=False)  # Eye Witness, Expert, Character, Police Witness
    protection_required = db.Column(db.Boolean, default=False, nullable=False)

    cases = db.relationship('CaseWitness', back_populates='witness', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Witness {self.full_name} ({self.witness_type})>"


class CaseAccused(BaseModel):
    """Junction table connecting Cases and Accused with charge information."""
    __tablename__ = 'case_accused'

    case_id = db.Column(db.Integer, db.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, index=True)
    accused_id = db.Column(db.Integer, db.ForeignKey('accused.id', ondelete='CASCADE'), nullable=False, index=True)
    charges_framed = db.Column(db.Text, nullable=True)
    arrest_status = db.Column(db.String(50), default='Wanted', nullable=False)  # Wanted, Arrested, Bailed, Detained, Acquitted
    arrest_date = db.Column(db.Date, nullable=True)

    case = db.relationship('Case', back_populates='case_accused')
    accused = db.relationship('Accused', back_populates='cases')

    def __repr__(self):
        return f"<CaseAccused Case={self.case_id} Accused={self.accused_id}>"


class CaseVictim(BaseModel):
    """Junction table connecting Cases and Victims with deposition details."""
    __tablename__ = 'case_victims'

    case_id = db.Column(db.Integer, db.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, index=True)
    victim_id = db.Column(db.Integer, db.ForeignKey('victims.id', ondelete='CASCADE'), nullable=False, index=True)
    statement_taken = db.Column(db.Boolean, default=False, nullable=False)
    victim_statement = db.Column(db.Text, nullable=True)
    statement_date = db.Column(db.Date, nullable=True)

    case = db.relationship('Case', back_populates='case_victims')
    victim = db.relationship('Victim', back_populates='cases')

    def __repr__(self):
        return f"<CaseVictim Case={self.case_id} Victim={self.victim_id}>"


class CaseWitness(BaseModel):
    """Junction table connecting Cases and Witnesses with testimony summaries."""
    __tablename__ = 'case_witnesses'

    case_id = db.Column(db.Integer, db.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, index=True)
    witness_id = db.Column(db.Integer, db.ForeignKey('witnesses.id', ondelete='CASCADE'), nullable=False, index=True)
    statement_summary = db.Column(db.Text, nullable=True)
    statement_date = db.Column(db.Date, nullable=True)
    is_hostile = db.Column(db.Boolean, default=False, nullable=False)

    case = db.relationship('Case', back_populates='case_witnesses')
    witness = db.relationship('Witness', back_populates='cases')

    def __repr__(self):
        return f"<CaseWitness Case={self.case_id} Witness={self.witness_id}>"


class CriminalRecord(BaseModel):
    __tablename__ = 'criminal_records'

    accused_id = db.Column(db.Integer, db.ForeignKey('accused.id', ondelete='SET NULL'), nullable=True, index=True)
    person_name = db.Column(db.String(120), nullable=False)
    alias = db.Column(db.String(100), nullable=True)
    criminal_id_code = db.Column(db.String(60), unique=True, nullable=False, index=True)
    finger_print_ref = db.Column(db.String(100), nullable=True)
    criminal_history_summary = db.Column(db.Text, nullable=False)
    known_gang_affiliation = db.Column(db.String(150), nullable=True)
    previous_convictions_count = db.Column(db.Integer, default=0, nullable=False)
    risk_level = db.Column(db.String(30), default='Medium', nullable=False)  # Low, Medium, High, Extreme

    accused = db.relationship('Accused', back_populates='criminal_records')

    def __repr__(self):
        return f"<CriminalRecord Code={self.criminal_id_code} Risk={self.risk_level}>"


class MissingPerson(BaseModel):
    __tablename__ = 'missing_persons'

    report_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    reporting_person_name = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)
    missing_person_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    date_last_seen = db.Column(db.Date, nullable=False)
    place_last_seen = db.Column(db.String(255), nullable=False)
    physical_description = db.Column(db.Text, nullable=False)
    clothing_description = db.Column(db.Text, nullable=True)
    status_resolution = db.Column(db.String(40), default='Missing', nullable=False)  # Missing, Traced, Deceased, Closed
    traced_date = db.Column(db.Date, nullable=True)
    io_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=True)

    station = db.relationship('PoliceStation')
    io_officer = db.relationship('Officer')

    def __repr__(self):
        return f"<MissingPerson {self.missing_person_name} ({self.status_resolution})>"
