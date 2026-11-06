from datetime import datetime
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.evidence import Evidence, EvidenceType, EvidenceCustodyLog
from app.models.cases import Case, FIR
from app.models.station import Officer
from app.models.users import User
from app.forms.operational_forms import EvidenceForm, CustodyTransferForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

evidence_bp = Blueprint('evidence', __name__, url_prefix='/evidence')

def generate_evidence_number():
    return f"EVD-{datetime.utcnow().strftime('%Y%m')}-{random.randint(10000, 99999)}"

@evidence_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    type_id = request.args.get('type_id', 0, type=int)
    status = request.args.get('status', '', type=str).strip()

    query = Evidence.active().order_by(Evidence.created_at.desc())

    if search:
        query = query.filter(
            (Evidence.evidence_number.ilike(f'%{search}%')) |
            (Evidence.item_name.ilike(f'%{search}%')) |
            (Evidence.barcode.ilike(f'%{search}%')) |
            (Evidence.current_storage_location.ilike(f'%{search}%'))
        )

    if type_id > 0:
        query = query.filter(Evidence.evidence_type_id == type_id)

    if status:
        query = query.filter(Evidence.chain_of_custody_status == status)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    evidence_types = EvidenceType.active().all()
    status_options = ['In Locker', 'In Forensics', 'In Court', 'Released', 'Disposed']

    return render_template(
        'evidence/index.html',
        pagination=pagination,
        search=search,
        type_id=type_id,
        current_status=status,
        evidence_types=evidence_types,
        status_options=status_options
    )


@evidence_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def create():
    form = EvidenceForm()

    types = EvidenceType.active().order_by(EvidenceType.name).all()
    form.evidence_type_id.choices = [(t.id, t.name) for t in types]

    officers = Officer.active().order_by(Officer.first_name).all()
    form.collected_by_officer_id.choices = [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    cases = Case.active().order_by(Case.case_number.desc()).all()
    form.case_id.choices = [(0, '-- Optional Link to Case --')] + [(c.id, f"{c.case_number} - {c.case_title}") for c in cases]

    firs = FIR.active().order_by(FIR.fir_number.desc()).all()
    form.fir_id.choices = [(0, '-- Optional Link to FIR --')] + [(f.id, f.fir_number) for f in firs]

    if form.validate_on_submit():
        try:
            evd_number = generate_evidence_number()
            barcode_val = form.barcode.data or f"BAR-{random.randint(10000000, 99999999)}"
            case_val = form.case_id.data if (form.case_id.data and form.case_id.data > 0) else None
            fir_val = form.fir_id.data if (form.fir_id.data and form.fir_id.data > 0) else None

            evidence = Evidence(
                evidence_number=evd_number,
                case_id=case_val,
                fir_id=fir_val,
                evidence_type_id=form.evidence_type_id.data,
                collected_by_officer_id=form.collected_by_officer_id.data,
                item_name=form.item_name.data,
                description=form.description.data,
                collected_from_location=form.collected_from_location.data,
                collected_at_datetime=datetime.utcnow(),
                current_storage_location=form.current_storage_location.data,
                condition_description=form.condition_description.data,
                chain_of_custody_status='In Locker',
                barcode=barcode_val,
                created_by=current_user.id
            )
            db.session.add(evidence)
            db.session.flush()

            # Record initial chain of custody log
            initial_log = EvidenceCustodyLog(
                evidence_id=evidence.id,
                transferred_from_user_id=current_user.id,
                transferred_to_user_id=current_user.id,
                transfer_date=datetime.utcnow(),
                transfer_purpose='Initial Seizure & Safe Deposit',
                source_location=form.collected_from_location.data,
                destination_location=form.current_storage_location.data,
                receipt_ack='SEIZED_INIT_LOG',
                created_by=current_user.id
            )
            db.session.add(initial_log)
            db.session.commit()

            log_audit('CREATE', 'evidences', evidence.id, description=f"Logged evidence {evidence.evidence_number} ({evidence.item_name})")
            flash(f"Evidence {evidence.evidence_number} recorded and catalogued successfully.", 'success')
            return redirect(url_for('evidence.view', id=evidence.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error cataloging evidence: {str(e)}", 'danger')

    return render_template('evidence/create.html', form=form)


@evidence_bp.route('/<int:id>')
@login_required
def view(id):
    evidence = Evidence.active().filter_by(id=id).first_or_404()
    transfer_form = CustodyTransferForm()
    users = User.active().order_by(User.full_name).all()
    transfer_form.transferred_to_user_id.choices = [(u.id, f"{u.full_name} ({u.role.name if u.role else 'User'})") for u in users]
    transfer_form.source_location.data = evidence.current_storage_location

    custody_logs = EvidenceCustodyLog.query.filter_by(evidence_id=evidence.id, is_deleted=False).order_by(EvidenceCustodyLog.transfer_date.desc()).all()
    return render_template(
        'evidence/view.html',
        evidence=evidence,
        transfer_form=transfer_form,
        custody_logs=custody_logs
    )


@evidence_bp.route('/<int:id>/transfer', methods=['POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def transfer(id):
    evidence = Evidence.active().filter_by(id=id).first_or_404()
    form = CustodyTransferForm()
    users = User.active().order_by(User.full_name).all()
    form.transferred_to_user_id.choices = [(u.id, u.full_name) for u in users]

    if form.validate_on_submit():
        try:
            purpose = form.transfer_purpose.data
            status_map = {
                'Forensic Analysis': 'In Forensics',
                'Court Presentation': 'In Court',
                'Vault / Locker Relocation': 'In Locker',
                'Returned to Owner': 'Released',
                'Disposed / Destroyed': 'Disposed'
            }

            custody_log = EvidenceCustodyLog(
                evidence_id=evidence.id,
                transferred_from_user_id=current_user.id,
                transferred_to_user_id=form.transferred_to_user_id.data,
                transfer_date=datetime.utcnow(),
                transfer_purpose=purpose,
                source_location=form.source_location.data,
                destination_location=form.destination_location.data,
                receipt_ack=form.receipt_ack.data,
                remarks=form.remarks.data,
                created_by=current_user.id
            )
            db.session.add(custody_log)

            # Update evidence state
            evidence.current_holder_id = form.transferred_to_user_id.data
            evidence.current_storage_location = form.destination_location.data
            evidence.chain_of_custody_status = status_map.get(purpose, 'In Locker')
            evidence.updated_by = current_user.id
            evidence.updated_at = datetime.utcnow()

            db.session.commit()
            log_audit('UPDATE', 'evidences', evidence.id, description=f"Chain of custody transferred: {purpose}")
            flash('Chain of custody transfer successfully logged.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error logging custody transfer: {str(e)}", 'danger')
    else:
        flash('Failed to record transfer. Check all required fields.', 'danger')

    return redirect(url_for('evidence.view', id=evidence.id))


@evidence_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete(id):
    evidence = Evidence.active().filter_by(id=id).first_or_404()
    try:
        evd_num = evidence.evidence_number
        evidence.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'evidences', evidence.id, description=f"Soft deleted evidence {evd_num}")
        flash(f"Evidence {evd_num} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting evidence: {str(e)}", 'danger')
    return redirect(url_for('evidence.index'))
