from datetime import datetime
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.common import Complaint
from app.models.station import PoliceStation, Officer
from app.forms.operational_forms import ComplaintForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

complaints_bp = Blueprint('complaints', __name__, url_prefix='/complaints')

def generate_complaint_number():
    return f"CMP-{datetime.utcnow().strftime('%Y%m')}-{random.randint(1000, 9999)}"

@complaints_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    status = request.args.get('status', '', type=str).strip()
    priority = request.args.get('priority', '', type=str).strip()

    query = Complaint.active().order_by(Complaint.created_at.desc())

    if search:
        query = query.filter(
            (Complaint.complaint_number.ilike(f'%{search}%')) |
            (Complaint.citizen_name.ilike(f'%{search}%')) |
            (Complaint.subject.ilike(f'%{search}%')) |
            (Complaint.citizen_phone.ilike(f'%{search}%'))
        )

    if status:
        query = query.filter(Complaint.resolution_status == status)

    if priority:
        query = query.filter(Complaint.priority == priority)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    status_options = ['Pending', 'Under Inquiry', 'Converted to FIR', 'Dismissed', 'Resolved']
    priority_options = ['Low', 'Medium', 'High', 'Urgent']

    return render_template(
        'complaints/index.html',
        pagination=pagination,
        search=search,
        current_status=status,
        current_priority=priority,
        status_options=status_options,
        priority_options=priority_options
    )


@complaints_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ComplaintForm()
    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, f"{s.station_code} - {s.name}") for s in stations]

    if form.validate_on_submit():
        try:
            cmp_num = generate_complaint_number()
            complaint = Complaint(
                complaint_number=cmp_num,
                station_id=form.station_id.data,
                citizen_name=form.citizen_name.data,
                citizen_phone=form.citizen_phone.data,
                citizen_email=form.citizen_email.data,
                citizen_address=form.citizen_address.data,
                subject=form.subject.data,
                description=form.description.data,
                priority=form.priority.data,
                resolution_status='Pending',
                complaint_date=datetime.utcnow(),
                created_by=current_user.id
            )
            db.session.add(complaint)
            db.session.commit()

            log_audit('CREATE', 'complaints', complaint.id, description=f"Lodged citizen complaint {cmp_num}")
            flash(f"Complaint {cmp_num} registered successfully.", 'success')
            return redirect(url_for('complaints.view', id=complaint.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering complaint: {str(e)}", 'danger')

    return render_template('complaints/create.html', form=form)


@complaints_bp.route('/<int:id>')
@login_required
def view(id):
    complaint = Complaint.active().filter_by(id=id).first_or_404()
    officers = Officer.active().order_by(Officer.first_name).all()
    status_options = ['Pending', 'Under Inquiry', 'Converted to FIR', 'Dismissed', 'Resolved']
    return render_template('complaints/view.html', complaint=complaint, officers=officers, status_options=status_options)


@complaints_bp.route('/<int:id>/status', methods=['POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def update_status(id):
    complaint = Complaint.active().filter_by(id=id).first_or_404()
    new_status = request.form.get('resolution_status')
    notes = request.form.get('resolution_notes')
    officer_id = request.form.get('assigned_officer_id', type=int)

    if new_status:
        try:
            complaint.resolution_status = new_status
            complaint.resolution_notes = notes
            if officer_id and officer_id > 0:
                complaint.assigned_officer_id = officer_id
            if new_status in ['Resolved', 'Dismissed', 'Converted to FIR']:
                complaint.resolved_at = datetime.utcnow()
            complaint.updated_by = current_user.id
            complaint.updated_at = datetime.utcnow()

            db.session.commit()
            log_audit('UPDATE', 'complaints', complaint.id, description=f"Updated status of complaint {complaint.complaint_number} to {new_status}")
            flash('Complaint status and inquiry notes updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating complaint: {str(e)}", 'danger')

    return redirect(url_for('complaints.view', id=complaint.id))


@complaints_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete(id):
    complaint = Complaint.active().filter_by(id=id).first_or_404()
    try:
        cmp_num = complaint.complaint_number
        complaint.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'complaints', complaint.id, description=f"Soft deleted complaint {cmp_num}")
        flash(f"Complaint {cmp_num} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting complaint: {str(e)}", 'danger')
    return redirect(url_for('complaints.index'))
