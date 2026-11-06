from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.evidence import Detainee, DetentionRecord, LockupCell, BailRecord
from app.models.station import Officer, PoliceStation
from app.models.cases import Case, FIR
from app.forms.operational_forms import DetaineeForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

detainees_bp = Blueprint('detainees', __name__, url_prefix='/detainees')

@detainees_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    status = request.args.get('status', 'In Custody', type=str).strip()

    query = DetentionRecord.active().order_by(DetentionRecord.created_at.desc())

    if search:
        query = query.join(Detainee).filter(
            (Detainee.full_name.ilike(f'%{search}%')) |
            (Detainee.national_id.ilike(f'%{search}%')) |
            (Detainee.alias.ilike(f'%{search}%'))
        )

    if status and status != 'ALL':
        query = query.filter(DetentionRecord.detention_status == status)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('detainees/index.html', pagination=pagination, search=search, current_status=status)


@detainees_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def create():
    form = DetaineeForm()

    cells = LockupCell.active().order_by(LockupCell.cell_number).all()
    form.cell_id.choices = [(c.id, f"{c.cell_number} - {c.cell_name} ({c.current_occupancy}/{c.capacity} occupied)") for c in cells]

    officers = Officer.active().order_by(Officer.first_name).all()
    form.arresting_officer_id.choices = [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    cases = Case.active().order_by(Case.case_number.desc()).all()
    form.case_id.choices = [(0, '-- None --')] + [(cs.id, f"{cs.case_number} - {cs.case_title}") for cs in cases]

    firs = FIR.active().order_by(FIR.fir_number.desc()).all()
    form.fir_id.choices = [(0, '-- None --')] + [(f.id, f.fir_number) for f in firs]

    if form.validate_on_submit():
        try:
            cell = db.session.get(LockupCell, form.cell_id.data)
            if cell and cell.current_occupancy >= cell.capacity:
                flash(f"Warning: Cell {cell.cell_number} is already at full capacity ({cell.capacity}). Please select another cell.", 'warning')
                return render_template('detainees/create.html', form=form)

            detainee = Detainee(
                full_name=form.full_name.data,
                alias=form.alias.data,
                national_id=form.national_id.data,
                gender=form.gender.data,
                age=form.age.data,
                blood_group=form.blood_group.data if form.blood_group.data else None,
                personal_belongings=form.personal_belongings.data,
                health_condition=form.health_condition.data,
                created_by=current_user.id
            )
            db.session.add(detainee)
            db.session.flush()

            case_val = form.case_id.data if (form.case_id.data and form.case_id.data > 0) else None
            fir_val = form.fir_id.data if (form.fir_id.data and form.fir_id.data > 0) else None

            record = DetentionRecord(
                detainee_id=detainee.id,
                cell_id=cell.id,
                case_id=case_val,
                fir_id=fir_val,
                arresting_officer_id=form.arresting_officer_id.data,
                arrest_date_time=datetime.utcnow(),
                detention_reason=form.detention_reason.data,
                detention_status='In Custody',
                medical_examination_done=True,
                created_by=current_user.id
            )
            db.session.add(record)

            # Update cell occupancy
            cell.current_occupancy += 1
            cell.updated_by = current_user.id

            db.session.commit()
            log_audit('CREATE', 'detainees', detainee.id, description=f"Booked detainee {detainee.full_name} into Cell {cell.cell_number}")
            flash(f"Detainee {detainee.full_name} booked and locked into Cell {cell.cell_number} successfully.", 'success')
            return redirect(url_for('detainees.view', id=detainee.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error booking detainee: {str(e)}", 'danger')

    return render_template('detainees/create.html', form=form)


@detainees_bp.route('/<int:id>')
@login_required
def view(id):
    detainee = Detainee.active().filter_by(id=id).first_or_404()
    records = DetentionRecord.query.filter_by(detainee_id=detainee.id, is_deleted=False).order_by(DetentionRecord.created_at.desc()).all()
    active_rec = DetentionRecord.query.filter_by(detainee_id=detainee.id, detention_status='In Custody', is_deleted=False).order_by(DetentionRecord.created_at.desc()).first()
    return render_template('detainees/view.html', detainee=detainee, records=records, active_rec=active_rec)


@detainees_bp.route('/<int:id>/release', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def release(id):
    detainee = Detainee.active().filter_by(id=id).first_or_404()
    record = DetentionRecord.active().filter_by(detainee_id=detainee.id, detention_status='In Custody').first()
    
    if not record:
        flash('No active in-custody record found for this detainee.', 'warning')
        return redirect(url_for('detainees.view', id=detainee.id))

    try:
        officer = Officer.active().filter_by(user_id=current_user.id).first()
        officer_id = officer.id if officer else None

        record.detention_status = 'Released'
        record.release_date_time = datetime.utcnow()
        record.release_authorized_by_id = officer_id
        record.updated_by = current_user.id

        if record.cell and record.cell.current_occupancy > 0:
            record.cell.current_occupancy -= 1

        db.session.commit()
        log_audit('UPDATE', 'detention_records', record.id, description=f"Released detainee {detainee.full_name}")
        flash(f"Detainee {detainee.full_name} released from custody successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error processing release: {str(e)}", 'danger')

    return redirect(url_for('detainees.view', id=detainee.id))


@detainees_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete(id):
    detainee = Detainee.active().filter_by(id=id).first_or_404()
    try:
        name = detainee.full_name
        detainee.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'detainees', detainee.id, description=f"Soft deleted detainee {name}")
        flash(f"Detainee {name} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting detainee: {str(e)}", 'danger')
    return redirect(url_for('detainees.index'))


@detainees_bp.route('/cells')
@login_required
def cells():
    cells = LockupCell.active().order_by(LockupCell.cell_number).all()
    return render_template('detainees/cells.html', cells=cells)
