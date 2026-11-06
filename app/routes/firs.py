from datetime import datetime, date
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.cases import FIR, FirStatus, CrimeType, Case, CaseStatusHistory
from app.models.station import PoliceStation, Officer
from app.models.people import Complainant
from app.models.evidence import Evidence
from app.forms.operational_forms import FIRForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

firs_bp = Blueprint('firs', __name__, url_prefix='/firs')

def generate_fir_number(station_code):
    date_str = datetime.utcnow().strftime('%Y%m%d')
    rand_suffix = random.randint(1000, 9999)
    return f"FIR-{station_code}-{date_str}-{rand_suffix}"

@firs_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    status_id = request.args.get('status_id', 0, type=int)
    
    query = FIR.active().order_by(FIR.created_at.desc())
    
    if search:
        query = query.outerjoin(Complainant).filter(
            (FIR.fir_number.ilike(f'%{search}%')) |
            (FIR.incident_location.ilike(f'%{search}%')) |
            (Complainant.full_name.ilike(f'%{search}%'))
        )
    
    if status_id > 0:
        query = query.filter(FIR.current_status_id == status_id)
        
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    statuses = FirStatus.active().all()
    return render_template(
        'firs/index.html',
        pagination=pagination,
        search=search,
        status_id=status_id,
        statuses=statuses
    )


@firs_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector', 'Clerk')
def create():
    form = FIRForm()
    
    # Populate dropdown choices
    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, f"{s.station_code} - {s.name}") for s in stations]
    
    crime_types = CrimeType.active().order_by(CrimeType.name).all()
    form.crime_type_id.choices = [(c.id, f"{c.name} ({c.relevant_sections})") for c in crime_types]
    
    officers = Officer.active().order_by(Officer.first_name).all()
    form.io_officer_id.choices = [(0, '-- Assign IO Later --')] + [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    if form.validate_on_submit():
        try:
            # 1. Create or link complainant
            complainant = Complainant(
                full_name=form.complainant_name.data,
                phone=form.complainant_phone.data,
                address=form.complainant_address.data,
                national_id=form.complainant_national_id.data,
                gender=form.complainant_gender.data,
                created_by=current_user.id
            )
            db.session.add(complainant)
            db.session.flush()

            # 2. Get initial status
            default_status = FirStatus.active().filter_by(code='REG').first()
            if not default_status:
                default_status = FirStatus.active().first()

            station = db.session.get(PoliceStation, form.station_id.data)
            fir_num = generate_fir_number(station.station_code if station else 'PS01')

            io_id = form.io_officer_id.data if (form.io_officer_id.data and form.io_officer_id.data > 0) else None

            # 3. Create FIR
            fir = FIR(
                fir_number=fir_num,
                station_id=form.station_id.data,
                crime_type_id=form.crime_type_id.data,
                complainant_id=complainant.id,
                current_status_id=default_status.id,
                registered_by_user_id=current_user.id,
                io_officer_id=io_id,
                incident_date_time=form.incident_date_time.data,
                incident_location=form.incident_location.data,
                distance_from_station=form.distance_from_station.data,
                incident_details=form.incident_details.data,
                is_cognizable=form.is_cognizable.data,
                created_by=current_user.id
            )
            db.session.add(fir)
            db.session.commit()

            log_audit('CREATE', 'firs', fir.id, description=f"Registered FIR {fir.fir_number}")
            flash(f"First Information Report {fir.fir_number} registered successfully!", 'success')
            return redirect(url_for('firs.view', id=fir.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"FIR registration error: {e}")
            flash(f"Error registering FIR: {str(e)}", 'danger')

    return render_template('firs/create.html', form=form)


@firs_bp.route('/<int:id>')
@login_required
def view(id):
    fir = FIR.active().filter_by(id=id).first_or_404()
    evidences = Evidence.query.filter_by(fir_id=fir.id, is_deleted=False).order_by(Evidence.created_at.desc()).all()
    return render_template('firs/view.html', fir=fir, evidences=evidences)


@firs_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def edit(id):
    fir = FIR.active().filter_by(id=id).first_or_404()
    form = FIRForm(obj=fir)
    
    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, f"{s.station_code} - {s.name}") for s in stations]
    
    crime_types = CrimeType.active().order_by(CrimeType.name).all()
    form.crime_type_id.choices = [(c.id, f"{c.name} ({c.relevant_sections})") for c in crime_types]
    
    officers = Officer.active().order_by(Officer.first_name).all()
    form.io_officer_id.choices = [(0, '-- None --')] + [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    if request.method == 'GET':
        if fir.complainant:
            form.complainant_name.data = fir.complainant.full_name
            form.complainant_phone.data = fir.complainant.phone
            form.complainant_address.data = fir.complainant.address
            form.complainant_national_id.data = fir.complainant.national_id
            form.complainant_gender.data = fir.complainant.gender
        form.io_officer_id.data = fir.io_officer_id or 0

    if form.validate_on_submit():
        try:
            old_data = {"location": fir.incident_location, "details": fir.incident_details}
            fir.station_id = form.station_id.data
            fir.crime_type_id = form.crime_type_id.data
            fir.io_officer_id = form.io_officer_id.data if (form.io_officer_id.data and form.io_officer_id.data > 0) else None
            fir.incident_date_time = form.incident_date_time.data
            fir.incident_location = form.incident_location.data
            fir.distance_from_station = form.distance_from_station.data
            fir.incident_details = form.incident_details.data
            fir.is_cognizable = form.is_cognizable.data
            fir.updated_by = current_user.id
            fir.updated_at = datetime.utcnow()

            if fir.complainant:
                fir.complainant.full_name = form.complainant_name.data
                fir.complainant.phone = form.complainant_phone.data
                fir.complainant.address = form.complainant_address.data
                fir.complainant.national_id = form.complainant_national_id.data
                fir.complainant.gender = form.complainant_gender.data
                fir.complainant.updated_by = current_user.id

            db.session.commit()
            log_audit('UPDATE', 'firs', fir.id, old_values=old_data, description=f"Updated FIR {fir.fir_number}")
            flash('FIR details updated successfully.', 'success')
            return redirect(url_for('firs.view', id=fir.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating FIR: {str(e)}", 'danger')

    return render_template('firs/edit.html', form=form, fir=fir)


@firs_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete(id):
    fir = FIR.active().filter_by(id=id).first_or_404()
    try:
        fir_num = fir.fir_number
        fir.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'firs', fir.id, description=f"Soft deleted FIR {fir_num}")
        flash(f"FIR {fir_num} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting FIR: {str(e)}", 'danger')
    return redirect(url_for('firs.index'))


@firs_bp.route('/<int:id>/escalate', methods=['POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def escalate_to_case(id):
    fir = FIR.active().filter_by(id=id).first_or_404()
    if fir.case and not fir.case.is_deleted:
        flash(f"FIR already has an active case: {fir.case.case_number}", 'info')
        return redirect(url_for('cases.view', id=fir.case.id))

    try:
        # Create Case Number
        case_num = f"CASE-{datetime.utcnow().strftime('%Y')}-{random.randint(10000, 99999)}"
        lead_officer_id = fir.io_officer_id
        if not lead_officer_id:
            first_officer = Officer.active().filter_by(station_id=fir.station_id).first()
            lead_officer_id = first_officer.id if first_officer else 1

        case = Case(
            case_number=case_num,
            fir_id=fir.id,
            station_id=fir.station_id,
            lead_investigator_id=lead_officer_id,
            crime_type_id=fir.crime_type_id,
            case_title=f"Investigation into {fir.crime_type.name} ({fir.fir_number})",
            case_status='Under Investigation',
            date_opened=date.today(),
            summary=fir.incident_details,
            created_by=current_user.id
        )
        db.session.add(case)
        db.session.flush()

        # Update FIR status to under investigation
        investigation_status = FirStatus.active().filter_by(code='INV').first()
        if investigation_status:
            fir.current_status_id = investigation_status.id

        # Log case status history
        history = CaseStatusHistory(
            case_id=case.id,
            previous_status='Registered',
            new_status='Under Investigation',
            changed_by_user_id=current_user.id,
            comments=f"Escalated from FIR {fir.fir_number}",
            created_by=current_user.id
        )
        db.session.add(history)
        db.session.commit()

        log_audit('CREATE', 'cases', case.id, description=f"Created case {case.case_number} from FIR {fir.fir_number}")
        flash(f"FIR {fir.fir_number} escalated to formal case {case.case_number} successfully!", 'success')
        return redirect(url_for('cases.view', id=case.id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error escalating to case: {str(e)}", 'danger')
        return redirect(url_for('firs.view', id=fir.id))
