from datetime import datetime, date
from flask import Blueprint, render_template, request, current_app
from flask_login import login_required, current_user
from app.models.cases import FIR, Case
from app.models.station import Officer, DutyRoster
from app.models.evidence import Detainee, DetentionRecord, Evidence
from app.models.resources import Vehicle, Weapon, InventoryItem
from app.models.common import Complaint
from app.utils.export import (
    export_to_csv, export_to_pdf,
    generate_fir_pdf, generate_case_pdf, generate_duty_roster_pdf
)
from app.utils.audit import log_audit

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')


# ==================== INDIVIDUAL PRINTABLE PDFs ====================

@reports_bp.route('/firs/<int:id>/pdf')
@login_required
def fir_single_pdf(id):
    """Download official printable FIR document with police station header and PPC sections."""
    fir = FIR.active().filter_by(id=id).first_or_404()
    log_audit('EXPORT', 'firs', fir.id, description=f"Printed official FIR copy for {fir.fir_number}")
    return generate_fir_pdf(fir)


@reports_bp.route('/cases/<int:id>/pdf')
@login_required
def case_single_pdf(id):
    """Download official case investigation report with suspect & evidence logs."""
    case = Case.active().filter_by(id=id).first_or_404()
    log_audit('EXPORT', 'cases', case.id, description=f"Printed official Case report for {case.case_number}")
    return generate_case_pdf(case)


@reports_bp.route('/roster/pdf')
@login_required
def duty_roster_pdf():
    """Download official daily duty roster (Roznamcha deployment order) PDF."""
    date_str = request.args.get('date', '')
    duty_date = date.today()
    if date_str:
        try:
            duty_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    rosters = DutyRoster.active().filter_by(duty_date=duty_date).order_by(DutyRoster.id.asc()).all()
    log_audit('EXPORT', 'duty_rosters', description=f"Printed official Duty Roster for {duty_date}")
    return generate_duty_roster_pdf(rosters, duty_date=duty_date)


# ==================== TABULAR CSV & PDF EXPORTS ====================

@reports_bp.route('/firs/csv')
@login_required
def firs_csv():
    firs = FIR.active().order_by(FIR.id.desc()).all()
    headers = ['FIR Number', 'Station', 'Crime Type', 'Complainant', 'Incident Date', 'Location', 'Status', 'Cognizable']
    rows = []
    for f in firs:
        rows.append([
            f.fir_number,
            f.station.name if f.station else '',
            f.crime_type.name if f.crime_type else '',
            f.complainant.full_name if f.complainant else 'N/A',
            f.incident_date_time.strftime('%Y-%m-%d %H:%M') if f.incident_date_time else '',
            f.incident_location,
            f.status_rel.name if f.status_rel else '',
            'Yes' if f.is_cognizable else 'No'
        ])
    log_audit('EXPORT', 'firs', description="Exported FIRs to CSV")
    return export_to_csv(headers, rows, filename=f"firs_report_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/firs/pdf')
@login_required
def firs_pdf():
    firs = FIR.active().order_by(FIR.id.desc()).limit(100).all()
    headers = ['FIR Number', 'Crime Type', 'Complainant', 'Location', 'Status']
    rows = []
    for f in firs:
        rows.append([
            f.fir_number,
            f.crime_type.name if f.crime_type else '',
            f.complainant.full_name if f.complainant else 'N/A',
            f.incident_location[:25] + ('...' if len(f.incident_location) > 25 else ''),
            f.status_rel.name if f.status_rel else ''
        ])
    log_audit('EXPORT', 'firs', description="Exported FIRs to PDF")
    return export_to_pdf("First Information Reports (FIR)", headers, rows, filename=f"firs_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf")


@reports_bp.route('/cases/csv')
@login_required
def cases_csv():
    cases = Case.active().order_by(Case.id.desc()).all()
    headers = ['Case Number', 'Title', 'Crime Classification', 'Lead Officer', 'Status', 'Date Opened']
    rows = []
    for c in cases:
        rows.append([
            c.case_number,
            c.case_title,
            c.crime_type.name if c.crime_type else '',
            c.lead_investigator.full_name if c.lead_investigator else '',
            c.case_status,
            c.date_opened.strftime('%Y-%m-%d') if c.date_opened else ''
        ])
    log_audit('EXPORT', 'cases', description="Exported Cases to CSV")
    return export_to_csv(headers, rows, filename=f"cases_report_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/cases/pdf')
@login_required
def cases_pdf():
    cases = Case.active().order_by(Case.id.desc()).limit(100).all()
    headers = ['Case Number', 'Title', 'Classification', 'Lead Investigator', 'Status']
    rows = []
    for c in cases:
        rows.append([
            c.case_number,
            c.case_title[:30] + ('...' if len(c.case_title) > 30 else ''),
            c.crime_type.name if c.crime_type else '',
            c.lead_investigator.full_name if c.lead_investigator else '',
            c.case_status
        ])
    log_audit('EXPORT', 'cases', description="Exported Cases to PDF")
    return export_to_pdf("Active Investigation Cases", headers, rows, filename=f"cases_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf")


@reports_bp.route('/officers/csv')
@login_required
def officers_csv():
    officers = Officer.active().order_by(Officer.first_name).all()
    headers = ['Badge Number', 'Full Name', 'Rank', 'Designation', 'Station', 'Contact Phone', 'Status']
    rows = []
    for o in officers:
        rows.append([
            o.badge_number,
            o.full_name,
            o.rank.name if o.rank else '',
            o.designation.title if o.designation else '',
            o.station.name if o.station else '',
            o.contact_phone,
            o.current_status
        ])
    log_audit('EXPORT', 'officers', description="Exported Officers to CSV")
    return export_to_csv(headers, rows, filename=f"officers_roster_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/officers/pdf')
@login_required
def officers_pdf():
    officers = Officer.active().order_by(Officer.first_name).all()
    headers = ['Badge #', 'Full Name', 'Rank', 'Designation', 'Police Station', 'Phone', 'Status']
    rows = []
    for o in officers:
        rows.append([
            o.badge_number,
            o.full_name,
            o.rank.name if o.rank else '',
            o.designation.title if o.designation else '',
            o.station.name if o.station else '',
            o.contact_phone,
            o.current_status
        ])
    log_audit('EXPORT', 'officers', description="Exported Officers to PDF")
    return export_to_pdf(
        "Police Personnel & Officer Muster Roll",
        headers,
        rows,
        filename=f"officers_roster_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
        orientation='landscape'
    )


@reports_bp.route('/detainees/csv')
@login_required
def detainees_csv():
    records = DetentionRecord.active().order_by(DetentionRecord.id.desc()).all()
    headers = ['Detainee Name', 'Age/Gender', 'Cell Number', 'Status', 'Arrest DateTime', 'Arresting Officer']
    rows = []
    for r in records:
        rows.append([
            r.detainee.full_name if r.detainee else '',
            f"{r.detainee.age}/{r.detainee.gender}" if r.detainee else '',
            r.cell.cell_number if r.cell else '',
            r.detention_status,
            r.arrest_date_time.strftime('%Y-%m-%d %H:%M') if r.arrest_date_time else '',
            r.arresting_officer.full_name if r.arresting_officer else ''
        ])
    log_audit('EXPORT', 'detainees', description="Exported Detainees to CSV")
    return export_to_csv(headers, rows, filename=f"detainees_report_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/detainees/pdf')
@login_required
def detainees_pdf():
    records = DetentionRecord.active().order_by(DetentionRecord.id.desc()).all()
    headers = ['Detainee Name', 'Age / Gender', 'Cell No.', 'Status', 'Arrest Date/Time', 'Arresting Officer']
    rows = []
    for r in records:
        rows.append([
            r.detainee.full_name if r.detainee else '',
            f"{r.detainee.age}/{r.detainee.gender}" if (r.detainee and r.detainee.age) else (r.detainee.gender if r.detainee else ''),
            r.cell.cell_number if r.cell else '',
            r.detention_status,
            r.arrest_date_time.strftime('%Y-%m-%d %H:%M') if r.arrest_date_time else '',
            r.arresting_officer.full_name if r.arresting_officer else ''
        ])
    log_audit('EXPORT', 'detainees', description="Exported Detainees to PDF")
    return export_to_pdf(
        "Hawalat Custody Detainee Census",
        headers,
        rows,
        filename=f"detainees_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
        orientation='landscape'
    )


@reports_bp.route('/evidence/csv')
@login_required
def evidence_csv():
    evidences = Evidence.active().order_by(Evidence.id.desc()).all()
    headers = ['Evidence Number', 'Item Name', 'Category', 'Seized From', 'Storage Location', 'Custody Status', 'Barcode']
    rows = []
    for e in evidences:
        rows.append([
            e.evidence_number,
            e.item_name,
            e.evidence_type.name if e.evidence_type else '',
            e.collected_from_location,
            e.current_storage_location,
            e.chain_of_custody_status,
            e.barcode or ''
        ])
    log_audit('EXPORT', 'evidences', description="Exported Evidence to CSV")
    return export_to_csv(headers, rows, filename=f"evidence_register_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/vehicles/csv')
@login_required
def vehicles_csv():
    vehicles = Vehicle.active().order_by(Vehicle.id.desc()).all()
    headers = ['Registration Plate', 'Type', 'Make/Model', 'Year', 'Fuel Type', 'Odometer (KM)', 'Operational Status']
    rows = []
    for v in vehicles:
        rows.append([
            v.registration_number,
            v.vehicle_type,
            v.make_model,
            v.year,
            v.fuel_type,
            v.current_odometer_km,
            v.operational_status
        ])
    log_audit('EXPORT', 'vehicles', description="Exported Vehicles to CSV")
    return export_to_csv(headers, rows, filename=f"vehicles_fleet_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/weapons/csv')
@login_required
def weapons_csv():
    weapons = Weapon.active().order_by(Weapon.id.desc()).all()
    headers = ['Serial Number', 'Weapon Type', 'Caliber', 'Condition', 'Storage Rack', 'Magazine Capacity']
    rows = []
    for w in weapons:
        rows.append([
            w.serial_number,
            w.weapon_type,
            w.caliber,
            w.condition,
            w.storage_rack_number,
            w.ammunition_capacity
        ])
    log_audit('EXPORT', 'weapons', description="Exported Armory to CSV")
    return export_to_csv(headers, rows, filename=f"armory_weapons_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/inventory/csv')
@login_required
def inventory_csv():
    items = InventoryItem.active().order_by(InventoryItem.id.desc()).all()
    headers = ['Item Name', 'Serial Number', 'Category', 'Quantity Available', 'Reorder Level', 'Location']
    rows = []
    for i in items:
        rows.append([
            i.item_name,
            i.serial_number or '',
            i.item_category,
            i.available_quantity,
            i.reorder_level,
            i.storage_location
        ])
    log_audit('EXPORT', 'inventory', description="Exported Inventory to CSV")
    return export_to_csv(headers, rows, filename=f"inventory_items_{datetime.utcnow().strftime('%Y%m%d')}.csv")


@reports_bp.route('/complaints/csv')
@login_required
def complaints_csv():
    complaints = Complaint.active().order_by(Complaint.id.desc()).all()
    headers = ['Complaint Number', 'Citizen Name', 'Phone', 'Subject', 'Priority', 'Status', 'Lodge Date']
    rows = []
    for c in complaints:
        rows.append([
            c.complaint_number,
            c.citizen_name,
            c.citizen_phone,
            c.subject,
            c.priority,
            c.resolution_status,
            c.complaint_date.strftime('%Y-%m-%d') if c.complaint_date else ''
        ])
    log_audit('EXPORT', 'complaints', description="Exported Complaints to CSV")
    return export_to_csv(headers, rows, filename=f"citizen_complaints_{datetime.utcnow().strftime('%Y%m%d')}.csv")
