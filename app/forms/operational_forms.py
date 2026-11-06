from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, BooleanField,
    IntegerField, DecimalField, DateField, DateTimeLocalField, SubmitField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email

class FIRForm(FlaskForm):
    station_id = SelectField('Police Station', coerce=int, validators=[DataRequired()])
    crime_type_id = SelectField('Crime Classification', coerce=int, validators=[DataRequired()])
    io_officer_id = SelectField('Assigned Investigating Officer', coerce=int, validators=[Optional()])
    
    # Complainant Info
    complainant_name = StringField('Complainant Full Name', validators=[DataRequired(), Length(max=120)])
    complainant_phone = StringField('Complainant Phone', validators=[DataRequired(), Length(max=30)])
    complainant_address = TextAreaField('Complainant Address', validators=[DataRequired()])
    complainant_national_id = StringField('CNIC / National ID (e.g. 35201-1234567-1)', validators=[Optional(), Length(max=50)])
    complainant_gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Male')
    
    # Incident Info
    incident_date_time = DateTimeLocalField('Incident Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    incident_location = StringField('Incident Location / Address', validators=[DataRequired(), Length(max=255)])
    distance_from_station = StringField('Distance / Direction from Station', validators=[Optional(), Length(max=50)])
    incident_details = TextAreaField('Incident Statement & Facts', validators=[DataRequired()])
    is_cognizable = BooleanField('Cognizable Offense (Police can arrest without warrant)', default=True)
    
    submit = SubmitField('Register FIR')


class CaseForm(FlaskForm):
    fir_id = SelectField('Linked FIR (Optional)', coerce=int, validators=[Optional()])
    station_id = SelectField('Police Station', coerce=int, validators=[DataRequired()])
    crime_type_id = SelectField('Crime Classification', coerce=int, validators=[DataRequired()])
    lead_investigator_id = SelectField('Lead Investigating Officer', coerce=int, validators=[DataRequired()])
    court_id = SelectField('Jurisdiction Court', coerce=int, validators=[Optional()])
    
    case_title = StringField('Case Title', validators=[DataRequired(), Length(max=200)])
    case_status = SelectField('Case Status', choices=[
        ('Under Investigation', 'Under Investigation'),
        ('Charge Sheeted', 'Charge Sheeted'),
        ('In Court', 'In Court'),
        ('Closed - Solved', 'Closed - Solved'),
        ('Closed - Unsolved', 'Closed - Unsolved')
    ], default='Under Investigation')
    summary = TextAreaField('Investigation Summary / Theory', validators=[DataRequired()])
    
    submit = SubmitField('Save Case')


class CaseNoteForm(FlaskForm):
    title = StringField('Note Subject / Heading', validators=[DataRequired(), Length(max=150)])
    content = TextAreaField('Investigative Note Details', validators=[DataRequired()])
    is_confidential = BooleanField('Mark as Confidential (Lead Officers Only)')
    submit = SubmitField('Add Case Note')


class CaseHearingForm(FlaskForm):
    court_id = SelectField('Court', coerce=int, validators=[DataRequired()])
    judge_id = SelectField('Presiding Judge', coerce=int, validators=[Optional()])
    hearing_date = DateField('Hearing Date', validators=[DataRequired()])
    hearing_time = StringField('Time (e.g. 10:30 AM)', validators=[Optional(), Length(max=20)])
    hearing_type = SelectField('Hearing Type', choices=[
        ('Bail Hearing', 'Bail Hearing'),
        ('Framing of Charges', 'Framing of Charges'),
        ('Witness Examination', 'Witness Examination'),
        ('Cross Examination', 'Cross Examination'),
        ('Evidence Presentation', 'Evidence Presentation'),
        ('Final Arguments', 'Final Arguments'),
        ('Verdict / Sentencing', 'Verdict / Sentencing')
    ], default='Bail Hearing')
    outcome = StringField('Outcome / Ruling', validators=[Optional(), Length(max=100)])
    next_hearing_date = DateField('Next Hearing Date', validators=[Optional()])
    judge_remarks = TextAreaField('Judge Remarks / Court Directions', validators=[Optional()])
    submit = SubmitField('Schedule / Log Hearing')


class OfficerForm(FlaskForm):
    badge_number = StringField('Badge Number', validators=[DataRequired(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=60)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=60)])
    station_id = SelectField('Assigned Station', coerce=int, validators=[DataRequired()])
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    rank_id = SelectField('Rank', coerce=int, validators=[DataRequired()])
    designation_id = SelectField('Designation', coerce=int, validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[Optional()])
    contact_phone = StringField('Contact Phone', validators=[DataRequired(), Length(max=30)])
    email = StringField('Official Email', validators=[Optional(), Email(), Length(max=120)])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=100)])
    joining_date = DateField('Joining Date', validators=[DataRequired()])
    salary = DecimalField('Monthly Salary', places=2, validators=[Optional()])
    current_status = SelectField('Duty Status', choices=[
        ('On Duty', 'On Duty'),
        ('On Leave', 'On Leave'),
        ('On Patrol', 'On Patrol'),
        ('Suspended', 'Suspended')
    ], default='On Duty')
    submit = SubmitField('Save Officer')


class DutyRosterForm(FlaskForm):
    station_id = SelectField('Station', coerce=int, validators=[DataRequired()])
    officer_id = SelectField('Officer', coerce=int, validators=[DataRequired()])
    shift_id = SelectField('Shift', coerce=int, validators=[DataRequired()])
    duty_date = DateField('Duty Date', validators=[DataRequired()])
    assigned_area = StringField('Assigned Beat / Sector / Area', validators=[DataRequired(), Length(max=150)])
    duty_type = SelectField('Duty Type', choices=[
        ('Beat Patrol', 'Beat Patrol'),
        ('Station Guard', 'Station Guard'),
        ('Desk Duty', 'Desk Duty'),
        ('Investigation Fieldwork', 'Investigation Fieldwork'),
        ('Court Order Duty', 'Court Order Duty'),
        ('Traffic Management', 'Traffic Management'),
        ('VIP Escort', 'VIP Escort')
    ], default='Beat Patrol')
    remarks = TextAreaField('Special Instructions', validators=[Optional()])
    submit = SubmitField('Assign Roster Duty')


class AttendanceForm(FlaskForm):
    officer_id = SelectField('Officer', coerce=int, validators=[DataRequired()])
    station_id = SelectField('Station', coerce=int, validators=[DataRequired()])
    attendance_date = DateField('Date', validators=[DataRequired()])
    attendance_status = SelectField('Status', choices=[
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('On Duty', 'On Duty (Field)'),
        ('Leave', 'On Leave'),
        ('Late', 'Late Arrival')
    ], default='Present')
    remarks = StringField('Remarks', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Mark Attendance')


class DetaineeForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    alias = StringField('Known Alias', validators=[Optional(), Length(max=100)])
    national_id = StringField('CNIC / National ID (e.g. 35201-1234567-1)', validators=[Optional(), Length(max=50)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=10, max=110)])
    blood_group = SelectField('Blood Group', choices=[
        ('', 'Select...'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[Optional()])
    personal_belongings = TextAreaField('Belongings Confiscated (Wallet, phone, belt, etc.)', validators=[Optional()])
    health_condition = TextAreaField('Medical State / Wounds / Conditions', validators=[Optional()])
    
    # Booking / Detention
    cell_id = SelectField('Lockup Cell', coerce=int, validators=[DataRequired()])
    arresting_officer_id = SelectField('Arresting Officer', coerce=int, validators=[DataRequired()])
    case_id = SelectField('Related Case (Optional)', coerce=int, validators=[Optional()])
    fir_id = SelectField('Related FIR (Optional)', coerce=int, validators=[Optional()])
    detention_reason = TextAreaField('Arrest & Detention Ground', validators=[DataRequired()])
    
    submit = SubmitField('Book Detainee')


class EvidenceForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired(), Length(max=150)])
    evidence_type_id = SelectField('Evidence Type', coerce=int, validators=[DataRequired()])
    case_id = SelectField('Linked Case', coerce=int, validators=[Optional()])
    fir_id = SelectField('Linked FIR', coerce=int, validators=[Optional()])
    collected_by_officer_id = SelectField('Seized By Officer', coerce=int, validators=[DataRequired()])
    collected_from_location = StringField('Seizure Location', validators=[DataRequired(), Length(max=255)])
    current_storage_location = StringField('Storage Location (e.g. Locker #3)', validators=[DataRequired(), Length(max=150)])
    condition_description = StringField('Physical Condition at Seizure', validators=[Optional(), Length(max=255)])
    description = TextAreaField('Detailed Item Description & Markings', validators=[DataRequired()])
    barcode = StringField('Barcode / Serial Tag', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Log Evidence')


class CustodyTransferForm(FlaskForm):
    transferred_to_user_id = SelectField('Transferred To Officer/User', coerce=int, validators=[DataRequired()])
    transfer_purpose = SelectField('Transfer Reason', choices=[
        ('Forensic Analysis', 'Forensic Analysis'),
        ('Court Presentation', 'Court Presentation'),
        ('Vault / Locker Relocation', 'Vault / Locker Relocation'),
        ('Returned to Owner', 'Returned to Owner'),
        ('Disposed / Destroyed', 'Disposed / Destroyed')
    ], default='Forensic Analysis')
    source_location = StringField('Source Location', validators=[DataRequired(), Length(max=150)])
    destination_location = StringField('Destination Location / Court / Lab', validators=[DataRequired(), Length(max=150)])
    receipt_ack = StringField('Receipt / Acknowledgment Ref', validators=[Optional(), Length(max=100)])
    remarks = TextAreaField('Transfer Remarks / Custody Notes', validators=[Optional()])
    submit = SubmitField('Record Chain of Custody Transfer')


class VehicleForm(FlaskForm):
    station_id = SelectField('Station', coerce=int, validators=[DataRequired()])
    registration_number = StringField('License Plate Number', validators=[DataRequired(), Length(max=40)])
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('Patrol Car', 'Patrol Car'),
        ('Motorcycle', 'Motorcycle'),
        ('SWAT Van', 'SWAT Van'),
        ('Prisoner Van', 'Prisoner Transport Van'),
        ('SUV', 'SUV / Pursuit')
    ], default='Patrol Car')
    make_model = StringField('Make & Model (e.g. Toyota Hilux)', validators=[DataRequired(), Length(max=100)])
    year = IntegerField('Year of Manufacture', validators=[DataRequired(), NumberRange(min=1990, max=2030)])
    fuel_type = SelectField('Fuel Type', choices=[('Petrol', 'Petrol'), ('Diesel', 'Diesel'), ('Electric', 'Electric')])
    operational_status = SelectField('Operational Status', choices=[
        ('Available', 'Available'),
        ('On Patrol', 'On Patrol'),
        ('In Maintenance', 'In Maintenance'),
        ('Out of Order', 'Out of Order')
    ], default='Available')
    current_odometer_km = IntegerField('Odometer (KM)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Vehicle')


class WeaponForm(FlaskForm):
    station_id = SelectField('Station', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Armory Serial Number', validators=[DataRequired(), Length(max=60)])
    weapon_type = SelectField('Weapon Model', choices=[
        ('Glock 19 9mm Pistol', 'Glock 19 9mm Pistol'),
        ('Beretta 92FS 9mm', 'Beretta 92FS 9mm'),
        ('AK-47 Assault Rifle', 'AK-47 Assault Rifle'),
        ('12 Gauge Remington Shotgun', '12 Gauge Remington Shotgun'),
        ('MP5 Submachine Gun', 'MP5 Submachine Gun'),
        ('.38 Special Revolver', '.38 Special Revolver')
    ], default='Glock 19 9mm Pistol')
    caliber = StringField('Caliber', validators=[DataRequired(), Length(max=30)])
    condition = SelectField('Condition', choices=[
        ('Good', 'Good / Serviceable'),
        ('Fair', 'Fair'),
        ('Needs Maintenance', 'Needs Maintenance'),
        ('Decommissioned', 'Decommissioned')
    ], default='Good')
    storage_rack_number = StringField('Storage Rack / Safe Number', validators=[DataRequired(), Length(max=30)])
    ammunition_capacity = IntegerField('Magazine Capacity', validators=[DataRequired(), NumberRange(min=1, max=100)])
    submit = SubmitField('Save Weapon')


class ComplaintForm(FlaskForm):
    station_id = SelectField('Police Station', coerce=int, validators=[DataRequired()])
    citizen_name = StringField('Citizen Name', validators=[DataRequired(), Length(max=120)])
    citizen_phone = StringField('Citizen Phone', validators=[DataRequired(), Length(max=30)])
    citizen_email = StringField('Citizen Email', validators=[Optional(), Email(), Length(max=120)])
    citizen_address = TextAreaField('Citizen Address', validators=[DataRequired()])
    subject = StringField('Subject of Grievance', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Grievance Description', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent')
    ], default='Medium')
    submit = SubmitField('Lodge Public Complaint')
