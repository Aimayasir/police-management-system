from datetime import datetime, date
from app.models.base import db, BaseModel

class Vehicle(BaseModel):
    __tablename__ = 'vehicles'

    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    registration_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(50), nullable=False)  # Patrol Car, Motorcycle, SWAT Van, Prisoner Van, SUV
    make_model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    fuel_type = db.Column(db.String(30), default='Petrol', nullable=False)
    operational_status = db.Column(db.String(40), default='Available', nullable=False)  # Available, On Patrol, In Maintenance, Out of Order
    current_odometer_km = db.Column(db.Integer, default=0, nullable=False)
    chassis_number = db.Column(db.String(60), nullable=True)

    station = db.relationship('PoliceStation', back_populates='vehicles')
    assignments = db.relationship('VehicleAssignment', back_populates='vehicle', cascade='all, delete-orphan')
    patrol_logs = db.relationship('PatrolLog', back_populates='vehicle', lazy='dynamic')

    def __repr__(self):
        return f"<Vehicle {self.registration_number} ({self.vehicle_type})>"


class VehicleAssignment(BaseModel):
    __tablename__ = 'vehicle_assignments'

    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    assignment_date = db.Column(db.Date, default=date.today, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    purpose = db.Column(db.String(150), nullable=False)  # Daily Area Patrol, Emergency Response, Prisoner Escort, IO Investigation
    start_km = db.Column(db.Integer, nullable=False)
    end_km = db.Column(db.Integer, nullable=True)
    fuel_issued_liters = db.Column(db.Numeric(6, 2), default=0.00)
    status_remarks = db.Column(db.Text, nullable=True)

    vehicle = db.relationship('Vehicle', back_populates='assignments')
    officer = db.relationship('Officer')

    def __repr__(self):
        return f"<VehicleAssignment Vehicle={self.vehicle_id} Officer={self.officer_id}>"


class Weapon(BaseModel):
    __tablename__ = 'weapons'

    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    serial_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    weapon_type = db.Column(db.String(60), nullable=False)  # Glock 19 9mm, AK-47 Rifle, 12 Gauge Shotgun, MP5 Submachine Gun, .38 Revolver
    caliber = db.Column(db.String(30), nullable=False)
    condition = db.Column(db.String(40), default='Good', nullable=False)  # Good, Fair, Needs Maintenance, Decommissioned
    storage_rack_number = db.Column(db.String(30), nullable=False)
    ammunition_capacity = db.Column(db.Integer, default=15, nullable=False)

    station = db.relationship('PoliceStation', back_populates='weapons')
    issuances = db.relationship('WeaponIssuance', back_populates='weapon', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Weapon {self.serial_number} ({self.weapon_type})>"


class WeaponIssuance(BaseModel):
    __tablename__ = 'weapon_issuances'

    weapon_id = db.Column(db.Integer, db.ForeignKey('weapons.id', ondelete='CASCADE'), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)
    duty_roster_id = db.Column(db.Integer, db.ForeignKey('duty_rosters.id'), nullable=True)
    issued_by_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)

    issue_datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    return_datetime = db.Column(db.DateTime, nullable=True)
    rounds_issued = db.Column(db.Integer, default=30, nullable=False)
    rounds_returned = db.Column(db.Integer, nullable=True)
    rounds_discharged = db.Column(db.Integer, default=0, nullable=False)
    discharge_justification = db.Column(db.Text, nullable=True)

    weapon = db.relationship('Weapon', back_populates='issuances')
    officer = db.relationship('Officer', foreign_keys=[officer_id])
    issued_by = db.relationship('Officer', foreign_keys=[issued_by_officer_id])
    duty_roster = db.relationship('DutyRoster')

    def __repr__(self):
        return f"<WeaponIssuance Weapon={self.weapon_id} Officer={self.officer_id}>"


class InventoryItem(BaseModel):
    __tablename__ = 'inventory_items'

    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    item_category = db.Column(db.String(60), nullable=False)  # Tactical Gear, Radios, Body Armor, First Aid, Forensics Kits, Office Supplies
    item_name = db.Column(db.String(120), nullable=False)
    serial_number = db.Column(db.String(80), nullable=True)
    total_quantity = db.Column(db.Integer, default=1, nullable=False)
    available_quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_of_measure = db.Column(db.String(30), default='units', nullable=False)
    storage_location = db.Column(db.String(100), nullable=False)  # Armory, Storage Room B, Forensics Cabinet
    reorder_level = db.Column(db.Integer, default=5, nullable=False)

    station = db.relationship('PoliceStation')

    def __repr__(self):
        return f"<InventoryItem {self.item_name} ({self.available_quantity}/{self.total_quantity})>"


class PatrolLog(BaseModel):
    __tablename__ = 'patrol_logs'

    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)
    lead_officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False, index=True)

    route_name = db.Column(db.String(120), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    areas_covered = db.Column(db.Text, nullable=False)
    incidents_reported_count = db.Column(db.Integer, default=0, nullable=False)
    suspicious_activities_noted = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    station = db.relationship('PoliceStation')
    vehicle = db.relationship('Vehicle', back_populates='patrol_logs')
    lead_officer = db.relationship('Officer')

    def __repr__(self):
        return f"<PatrolLog Route={self.route_name} Officer={self.lead_officer_id}>"
