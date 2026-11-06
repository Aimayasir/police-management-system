from datetime import datetime, date
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.cases import (
    Case, CaseStatusHistory, CaseOfficer, CaseNote,
    Court, Judge, CaseHearing, FIR, CrimeType
)
from app.models.station import PoliceStation, Officer
from app.models.people import CaseAccused
from app.models.evidence import Evidence
from app.forms.operational_forms import CaseForm, CaseNoteForm, CaseHearingForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

cases_bp = Blueprint('cases', __name__, url_prefix='/cases')

@cases_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    status = request.args.get('status', '', type=str).strip()

    query = Case.active().order_by(Case.created_at.desc())

    if search:
        query = query.outerjoin(Officer, Case.lead_investigator_id == Officer.id).filter(
            (Case.case_number.ilike(f'%{search}%')) |
            (Case.case_title.ilike(f'%{search}%')) |
            (Officer.first_name.ilike(f'%{search}%')) |
            (Officer.last_name.ilike(f'%{search}%'))
        )

    if status:
        query = query.filter(Case.case_status == status)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    status_options = ['Under Investigation', 'Charge Sheeted', 'In Court', 'Closed - Solved', 'Closed - Unsolved']
    return render_template('cases/index.html', pagination=pagination, search=search, current_status=status, status_options=status_options)


@cases_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def create():
    form = CaseForm()

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, f"{s.station_code} - {s.name}") for s in stations]

    crime_types = CrimeType.active().order_by(CrimeType.name).all()
    form.crime_type_id.choices = [(c.id, f"{c.name} ({c.relevant_sections})") for c in crime_types]

    officers = Officer.active().order_by(Officer.first_name).all()
    form.lead_investigator_id.choices = [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    firs = FIR.active().order_by(FIR.fir_number.desc()).all()
    form.fir_id.choices = [(0, '-- Standalone Case (No FIR) --')] + [(f.id, f"{f.fir_number} - {f.crime_type.name if f.crime_type else ''}") for f in firs]

    courts = Court.active().order_by(Court.name).all()
    form.court_id.choices = [(0, '-- Court Not Assigned Yet --')] + [(c.id, f"{c.name} ({c.court_type})") for c in courts]

    if form.validate_on_submit():
        try:
            case_num = f"CASE-{datetime.utcnow().strftime('%Y')}-{random.randint(10000, 99999)}"
            fir_val = form.fir_id.data if (form.fir_id.data and form.fir_id.data > 0) else None
            court_val = form.court_id.data if (form.court_id.data and form.court_id.data > 0) else None

            case = Case(
                case_number=case_num,
                fir_id=fir_val,
                station_id=form.station_id.data,
                lead_investigator_id=form.lead_investigator_id.data,
                crime_type_id=form.crime_type_id.data,
                court_id=court_val,
                case_title=form.case_title.data,
                case_status=form.case_status.data,
                date_opened=date.today(),
                summary=form.summary.data,
                created_by=current_user.id
            )
            db.session.add(case)
            db.session.flush()

            # Add Lead Officer to junction table
            case_officer = CaseOfficer(
                case_id=case.id,
                officer_id=case.lead_investigator_id,
                role_in_case='Lead Investigating Officer',
                assigned_date=date.today(),
                created_by=current_user.id
            )
            db.session.add(case_officer)

            # Record initial status in history
            history = CaseStatusHistory(
                case_id=case.id,
                previous_status='Created',
                new_status=case.case_status,
                changed_by_user_id=current_user.id,
                comments='Case registered initially',
                created_by=current_user.id
            )
            db.session.add(history)
            db.session.commit()

            log_audit('CREATE', 'cases', case.id, description=f"Created case {case.case_number}")
            flash(f"Case {case.case_number} registered successfully!", 'success')
            return redirect(url_for('cases.view', id=case.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating case: {str(e)}", 'danger')

    return render_template('cases/create.html', form=form)


@cases_bp.route('/<int:id>')
@login_required
def view(id):
    case = Case.active().filter_by(id=id).first_or_404()
    note_form = CaseNoteForm()
    hearing_form = CaseHearingForm()

    courts = Court.active().order_by(Court.name).all()
    hearing_form.court_id.choices = [(c.id, c.name) for c in courts]
    
    judges = Judge.active().order_by(Judge.full_name).all()
    hearing_form.judge_id.choices = [(0, '-- Select Presiding Judge --')] + [(j.id, f"{j.full_name} ({j.designation})") for j in judges]

    officers = Officer.active().order_by(Officer.first_name).all()
    
    case_notes = CaseNote.query.filter_by(case_id=case.id, is_deleted=False).order_by(CaseNote.created_at.desc()).all()
    case_hearings = CaseHearing.query.filter_by(case_id=case.id, is_deleted=False).order_by(CaseHearing.hearing_date.asc()).all()
    assigned_officers = CaseOfficer.query.filter_by(case_id=case.id, is_deleted=False).order_by(CaseOfficer.id.desc()).all()
    case_accused = CaseAccused.query.filter_by(case_id=case.id, is_deleted=False).order_by(CaseAccused.id.desc()).all()
    evidences = Evidence.query.filter_by(case_id=case.id, is_deleted=False).order_by(Evidence.created_at.desc()).all()
    status_history = CaseStatusHistory.query.filter_by(case_id=case.id, is_deleted=False).order_by(CaseStatusHistory.created_at.desc()).all()

    return render_template(
        'cases/view.html',
        case=case,
        note_form=note_form,
        hearing_form=hearing_form,
        officers=officers,
        case_notes=case_notes,
        case_hearings=case_hearings,
        assigned_officers=assigned_officers,
        case_accused=case_accused,
        evidences=evidences,
        status_history=status_history
    )


@cases_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def edit(id):
    case = Case.active().filter_by(id=id).first_or_404()
    form = CaseForm(obj=case)

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, f"{s.station_code} - {s.name}") for s in stations]

    crime_types = CrimeType.active().order_by(CrimeType.name).all()
    form.crime_type_id.choices = [(c.id, f"{c.name} ({c.relevant_sections})") for c in crime_types]

    officers = Officer.active().order_by(Officer.first_name).all()
    form.lead_investigator_id.choices = [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    firs = FIR.active().order_by(FIR.fir_number.desc()).all()
    form.fir_id.choices = [(0, '-- None --')] + [(f.id, f.fir_number) for f in firs]

    courts = Court.active().order_by(Court.name).all()
    form.court_id.choices = [(0, '-- None --')] + [(c.id, c.name) for c in courts]

    if request.method == 'GET':
        form.fir_id.data = case.fir_id or 0
        form.court_id.data = case.court_id or 0

    if form.validate_on_submit():
        try:
            prev_status = case.case_status
            new_status = form.case_status.data

            case.station_id = form.station_id.data
            case.crime_type_id = form.crime_type_id.data
            case.lead_investigator_id = form.lead_investigator_id.data
            case.court_id = form.court_id.data if (form.court_id.data and form.court_id.data > 0) else None
            case.fir_id = form.fir_id.data if (form.fir_id.data and form.fir_id.data > 0) else None
            case.case_title = form.case_title.data
            case.case_status = new_status
            case.summary = form.summary.data
            case.updated_by = current_user.id
            case.updated_at = datetime.utcnow()

            if prev_status != new_status:
                history = CaseStatusHistory(
                    case_id=case.id,
                    previous_status=prev_status,
                    new_status=new_status,
                    changed_by_user_id=current_user.id,
                    comments="Status changed via case edit",
                    created_by=current_user.id
                )
                db.session.add(history)

            db.session.commit()
            log_audit('UPDATE', 'cases', case.id, description=f"Updated case {case.case_number}")
            flash("Case details updated successfully.", "success")
            return redirect(url_for('cases.view', id=case.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating case: {str(e)}", "danger")

    return render_template('cases/edit.html', form=form, case=case)


@cases_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete(id):
    case = Case.active().filter_by(id=id).first_or_404()
    try:
        case_num = case.case_number
        case.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'cases', case.id, description=f"Soft deleted case {case_num}")
        flash(f"Case {case_num} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting case: {str(e)}", 'danger')
    return redirect(url_for('cases.index'))


@cases_bp.route('/<int:id>/notes/add', methods=['POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def add_note(id):
    case = Case.active().filter_by(id=id).first_or_404()
    form = CaseNoteForm()
    if form.validate_on_submit():
        try:
            officer = Officer.active().filter_by(user_id=current_user.id).first()
            officer_id = officer.id if officer else case.lead_investigator_id

            note = CaseNote(
                case_id=case.id,
                officer_id=officer_id,
                note_date=datetime.utcnow(),
                title=form.title.data,
                content=form.content.data,
                is_confidential=form.is_confidential.data,
                created_by=current_user.id
            )
            db.session.add(note)
            db.session.commit()
            log_audit('CREATE', 'case_notes', note.id, description=f"Added note to case {case.case_number}")
            flash('Case note added to case diary.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding note: {str(e)}", 'danger')
    else:
        flash('Failed to add note. Please verify input fields.', 'danger')
    return redirect(url_for('cases.view', id=case.id))


@cases_bp.route('/<int:id>/hearings/add', methods=['POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector', 'Clerk')
def add_hearing(id):
    case = Case.active().filter_by(id=id).first_or_404()
    form = CaseHearingForm()
    courts = Court.active().order_by(Court.name).all()
    form.court_id.choices = [(c.id, c.name) for c in courts]
    judges = Judge.active().order_by(Judge.full_name).all()
    form.judge_id.choices = [(0, '-- None --')] + [(j.id, j.full_name) for j in judges]

    if form.validate_on_submit():
        try:
            judge_val = form.judge_id.data if (form.judge_id.data and form.judge_id.data > 0) else None
            hearing = CaseHearing(
                case_id=case.id,
                court_id=form.court_id.data,
                judge_id=judge_val,
                hearing_date=form.hearing_date.data,
                hearing_time=form.hearing_time.data,
                hearing_type=form.hearing_type.data,
                outcome=form.outcome.data,
                next_hearing_date=form.next_hearing_date.data,
                judge_remarks=form.judge_remarks.data,
                created_by=current_user.id
            )
            db.session.add(hearing)
            
            # If case wasn't marked In Court, mark it
            if case.case_status not in ['In Court', 'Closed - Solved', 'Closed - Unsolved']:
                case.case_status = 'In Court'

            db.session.commit()
            log_audit('CREATE', 'case_hearings', hearing.id, description=f"Scheduled hearing for case {case.case_number}")
            flash('Court hearing scheduled and recorded successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error logging hearing: {str(e)}", 'danger')
    else:
        flash('Failed to record hearing. Please check the form.', 'danger')
    return redirect(url_for('cases.view', id=case.id))


@cases_bp.route('/<int:id>/assign-officer', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def assign_officer(id):
    case = Case.active().filter_by(id=id).first_or_404()
    officer_id = request.form.get('officer_id', type=int)
    role_in_case = request.form.get('role_in_case', 'Assisting Officer')
    
    if officer_id:
        try:
            # Check if already assigned
            existing = CaseOfficer.active().filter_by(case_id=case.id, officer_id=officer_id).first()
            if existing:
                flash('Officer is already assigned to this case.', 'warning')
            else:
                co = CaseOfficer(
                    case_id=case.id,
                    officer_id=officer_id,
                    role_in_case=role_in_case,
                    assigned_date=date.today(),
                    created_by=current_user.id
                )
                db.session.add(co)
                db.session.commit()
                log_audit('CREATE', 'case_officers', co.id, description=f"Assigned officer {officer_id} to case {case.case_number}")
                flash('Officer assigned to case team successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error assigning officer: {str(e)}", 'danger')
    return redirect(url_for('cases.view', id=case.id))
