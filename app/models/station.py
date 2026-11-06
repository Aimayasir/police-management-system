from datetime import datetime, date
from app.models.base import db, BaseModel

class PoliceStation(BaseModel):
    __tablename__ = 'police_stations'

    station_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=True)
    contact_number = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    sho_officer_id = db.Column(db.Integer, nullable=True)
    capacity = db.Column(db.Integer, default=50, nullable=False)

    users = db.relationship('User', back_populates='station', foreign_keys='User.station_id')
    departments = db.relationship('Department', back_populates='station', lazy='dynamic')
    officers = db.relationship('Officer', back_populates='station', foreign_keys='Officer.station_id', lazy='dynamic')
    lockup_cells = db.relationship('LockupCell', back_populates='station', lazy='dynamic')
    vehicles = db.relationship('Vehicle', back_populates='station', lazy='dynamic')
    weapons = db.relationship('Weapon', back_populates='station', lazy='dynamic')
    firs = db.relationship('FIR', back_populates='station', lazy='dynamic')
    complaints = db.relationship('Complaint', back_populates='station', lazy='dynamic')

    def __repr__(self):
        return f"<PoliceStation {self.station_code} - {self.name}>"


class Department(BaseModel):
    __tablename__ = 'departments'

    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # Investigation, Traffic, Patrol, Forensics, Cyber
    code = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=True)

    station = db.relationship('PoliceStation', back_populates='departments')
    officers = db.relationship('Officer', back_populates='department', lazy='dynamic')

    def __repr__(self):
        return f"<Department {self.code} - {self.name}>"


class Rank(BaseModel):
    __tablename__ = 'ranks'

    name = db.Column(db.String(100), unique=True, nullable=False)  # Director General, SP, Inspector, Sub-Inspector, Constable
    rank_level = db.Column(db.Integer, nullable=False)  # 1 = Highest, 10 = Entry
    insignia_code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    officers = db.relationship('Officer', back_populates='rank', lazy='dynamic')

    def __repr__(self):
        return f"<Rank {self.name} (Level {self.rank_level})>"


class Designation(BaseModel):
    __tablename__ = 'designations'

    title = db.Column(db.String(100), unique=True, nullable=False)  # SHO, Investigating Officer, Desk In-Charge, Armory In-Charge
    code = db.Column(db.String(30), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    officers = db.relationship('Officer', back_populates='designation', lazy='dynamic')

    def __repr__(self):
        return f"<Designation {self.title}>"


class Officer(BaseModel):
    __tablename__ = 'officers'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, unique=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True, index=True)
    rank_id = db.Column(db.Integer, db.ForeignKey('ranks.id'), nullable=False, index=True)
    designation_id = db.Column(db.Integer, db.ForeignKey('designations.id'), nullable=False, index=True)

    badge_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(10), nullable=True)
    contact_phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    joining_date = db.Column(db.Date, nullable=False, default=date.today)
    salary = db.Column(db.Numeric(10, 2), default=0.00)
    current_status = db.Column(db.String(30), default='On Duty', nullable=False)  # On Duty, On Leave, Suspended, Transferred

    user = db.relationship('User', back_populates='officer_profile')
    station = db.relationship('PoliceStation', back_populates='officers', foreign_keys=[station_id])
    department = db.relationship('Department', back_populates='officers')
    rank = db.relationship('Rank', back_populates='officers')
    designation = db.relationship('Designation', back_populates='officers')

    postings = db.relationship('OfficerPosting', back_populates='officer', cascade='all, delete-orphan')
    duty_rosters = db.relationship('DutyRoster', back_populates='officer', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', back_populates='officer', cascade='all, delete-orphan')
    leaves = db.relationship('Leave', back_populates='officer', foreign_keys='Leave.officer_id', cascade='all, delete-orphan')
    trainings = db.relationship('TrainingRecord', back_populates='officer', cascade='all, delete-orphan')
    transfers = db.relationship('Transfer', back_populates='officer', foreign_keys='Transfer.officer_id')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Officer {self.badge_number} - {self.full_name}>"


class OfficerPosting(BaseModel):
    __tablename__ = 'officer_postings'

    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id', ondelete='CASCADE'), nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    role_title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    transfer_order_number = db.Column(db.String(80), nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    officer = db.relationship('Officer', back_populates='postings')
    station = db.relationship('PoliceStation')
    department = db.relationship('Department')


class Shift(BaseModel):
    __tablename__ = 'shifts'

    name = db.Column(db.String(50), unique=True, nullable=False)  # Morning (06:00-14:00), Evening (14:00-22:00), Night (22:00-06:00)
    start_time = db.Column(db.String(10), nullable=False)  # "06:00"
    end_time = db.Column(db.String(10), nullable=False)    # "14:00"
    duration_hours = db.Column(db.Integer, default=8, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    rosters = db.relationship('DutyRoster', back_populates='shift')

    def __repr__(self):
        return f"<Shift {self.name} ({self.start_time}-{self.end_time})>"


class DutyRoster(BaseModel):
    __tablename__ = 'duty_rosters'

    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False, index=True)
    duty_date = db.Column(db.Date, nullable=False, index=True)
    assigned_area = db.Column(db.String(150), nullable=False)
    duty_type = db.Column(db.String(50), default='Patrol', nullable=False)  # Patrol, Station Guard, Investigation, Desk, VIP Escort
    remarks = db.Column(db.Text, nullable=True)

    station = db.relationship('PoliceStation')
    officer = db.relationship('Officer', back_populates='duty_rosters')
    shift = db.relationship('Shift', back_populates='rosters')

    def __repr__(self):
        return f"<DutyRoster Officer={self.officer_id} Date={self.duty_date}>"


class Attendance(BaseModel):
    __tablename__ = 'attendances'

    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    attendance_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    attendance_status = db.Column(db.String(30), default='Present', nullable=False)  # Present, Absent, On Duty, Leave, Late
    remarks = db.Column(db.String(255), nullable=True)

    officer = db.relationship('Officer', back_populates='attendances')
    station = db.relationship('PoliceStation')

    def __repr__(self):
        return f"<Attendance Officer={self.officer_id} Status={self.attendance_status}>"


class Leave(BaseModel):
    __tablename__ = 'leaves'

    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    leave_type = db.Column(db.String(50), nullable=False)  # Casual, Medical, Earned, Emergency
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, default=1, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    approval_status = db.Column(db.String(30), default='Pending', nullable=False)  # Pending, Approved, Rejected
    approved_by_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=True)
    approval_date = db.Column(db.Date, nullable=True)

    officer = db.relationship('Officer', foreign_keys=[officer_id], back_populates='leaves')
    approver = db.relationship('Officer', foreign_keys=[approved_by_officer_id])

    def __repr__(self):
        return f"<Leave Officer={self.officer_id} Status={self.approval_status}>"


class TrainingRecord(BaseModel):
    __tablename__ = 'training_records'

    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    course_name = db.Column(db.String(150), nullable=False)
    training_institution = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    certification_name = db.Column(db.String(150), nullable=True)
    grade = db.Column(db.String(30), nullable=True)
    result = db.Column(db.String(30), default='Pass', nullable=False)  # Pass, Fail, Distinction

    officer = db.relationship('Officer', back_populates='trainings')

    def __repr__(self):
        return f"<TrainingRecord Officer={self.officer_id} Course={self.course_name}>"


class Transfer(BaseModel):
    __tablename__ = 'transfers'

    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    from_station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False)
    to_station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False)
    transfer_order_date = db.Column(db.Date, nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    order_reference_number = db.Column(db.String(100), nullable=False)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    officer = db.relationship('Officer', foreign_keys=[officer_id], back_populates='transfers')
    from_station = db.relationship('PoliceStation', foreign_keys=[from_station_id])
    to_station = db.relationship('PoliceStation', foreign_keys=[to_station_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_user_id])

    def __repr__(self):
        return f"<Transfer Officer={self.officer_id} Ref={self.order_reference_number}>"
