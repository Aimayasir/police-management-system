from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.station import (
    Officer, PoliceStation, Department, Rank, Designation,
    DutyRoster, Attendance, Shift, OfficerPosting, Leave, TrainingRecord
)
from app.forms.operational_forms import OfficerForm, DutyRosterForm, AttendanceForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

officers_bp = Blueprint('officers', __name__, url_prefix='/officers')

@officers_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    station_id = request.args.get('station_id', 0, type=int)
    rank_id = request.args.get('rank_id', 0, type=int)

    query = Officer.active().order_by(Officer.first_name)

    if search:
        query = query.filter(
            (Officer.badge_number.ilike(f'%{search}%')) |
            (Officer.first_name.ilike(f'%{search}%')) |
            (Officer.last_name.ilike(f'%{search}%')) |
            (Officer.contact_phone.ilike(f'%{search}%'))
        )

    if station_id > 0:
        query = query.filter(Officer.station_id == station_id)

    if rank_id > 0:
        query = query.filter(Officer.rank_id == rank_id)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    ranks = Rank.active().order_by(Rank.rank_level).all()

    return render_template(
        'officers/index.html',
        pagination=pagination,
        search=search,
        station_id=station_id,
        rank_id=rank_id,
        stations=stations,
        ranks=ranks
    )


@officers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO')
def create():
    form = OfficerForm()

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, f"{s.station_code} - {s.name}") for s in stations]

    departments = Department.active().order_by(Department.name).all()
    form.department_id.choices = [(0, '-- None --')] + [(d.id, d.name) for d in departments]

    ranks = Rank.active().order_by(Rank.rank_level).all()
    form.rank_id.choices = [(r.id, f"{r.name} (Lvl {r.rank_level})") for r in ranks]

    designations = Designation.active().order_by(Designation.title).all()
    form.designation_id.choices = [(ds.id, ds.title) for ds in designations]

    if form.validate_on_submit():
        try:
            # Check unique badge number
            existing = Officer.active().filter_by(badge_number=form.badge_number.data).first()
            if existing:
                flash(f"Officer with Badge Number {form.badge_number.data} already exists.", 'danger')
                return render_template('officers/create.html', form=form)

            dept_val = form.department_id.data if (form.department_id.data and form.department_id.data > 0) else None

            officer = Officer(
                badge_number=form.badge_number.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                station_id=form.station_id.data,
                department_id=dept_val,
                rank_id=form.rank_id.data,
                designation_id=form.designation_id.data,
                date_of_birth=form.date_of_birth.data,
                gender=form.gender.data,
                blood_group=form.blood_group.data,
                contact_phone=form.contact_phone.data,
                email=form.email.data,
                emergency_contact=form.emergency_contact.data,
                joining_date=form.joining_date.data,
                salary=form.salary.data or 0.00,
                current_status=form.current_status.data,
                created_by=current_user.id
            )
            db.session.add(officer)
            db.session.flush()

            # Record initial posting
            posting = OfficerPosting(
                officer_id=officer.id,
                station_id=officer.station_id,
                department_id=officer.department_id,
                role_title=officer.designation.title,
                start_date=officer.joining_date,
                transfer_order_number=f"INIT-{officer.badge_number}",
                created_by=current_user.id
            )
            db.session.add(posting)
            db.session.commit()

            log_audit('CREATE', 'officers', officer.id, description=f"Enrolled officer {officer.badge_number} ({officer.full_name})")
            flash(f"Officer {officer.full_name} enrolled successfully!", 'success')
            return redirect(url_for('officers.view', id=officer.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error enrolling officer: {str(e)}", 'danger')

    return render_template('officers/create.html', form=form)


@officers_bp.route('/<int:id>')
@login_required
def view(id):
    officer = Officer.active().filter_by(id=id).first_or_404()
    recent_rosters = DutyRoster.active().filter_by(officer_id=officer.id).order_by(DutyRoster.duty_date.desc()).limit(10).all()
    recent_attendance = Attendance.active().filter_by(officer_id=officer.id).order_by(Attendance.attendance_date.desc()).limit(10).all()
    postings = OfficerPosting.active().filter_by(officer_id=officer.id).order_by(OfficerPosting.start_date.desc()).all()
    trainings = TrainingRecord.query.filter_by(officer_id=officer.id, is_deleted=False).order_by(TrainingRecord.start_date.desc()).all()
    return render_template(
        'officers/view.html',
        officer=officer,
        recent_rosters=recent_rosters,
        recent_attendance=recent_attendance,
        postings=postings,
        trainings=trainings
    )


@officers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'SHO')
def edit(id):
    officer = Officer.active().filter_by(id=id).first_or_404()
    form = OfficerForm(obj=officer)

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, f"{s.station_code} - {s.name}") for s in stations]

    departments = Department.active().order_by(Department.name).all()
    form.department_id.choices = [(0, '-- None --')] + [(d.id, d.name) for d in departments]

    ranks = Rank.active().order_by(Rank.rank_level).all()
    form.rank_id.choices = [(r.id, f"{r.name} (Lvl {r.rank_level})") for r in ranks]

    designations = Designation.active().order_by(Designation.title).all()
    form.designation_id.choices = [(ds.id, ds.title) for ds in designations]

    if request.method == 'GET':
        form.department_id.data = officer.department_id or 0

    if form.validate_on_submit():
        try:
            dept_val = form.department_id.data if (form.department_id.data and form.department_id.data > 0) else None
            officer.first_name = form.first_name.data
            officer.last_name = form.last_name.data
            officer.station_id = form.station_id.data
            officer.department_id = dept_val
            officer.rank_id = form.rank_id.data
            officer.designation_id = form.designation_id.data
            officer.date_of_birth = form.date_of_birth.data
            officer.gender = form.gender.data
            officer.blood_group = form.blood_group.data
            officer.contact_phone = form.contact_phone.data
            officer.email = form.email.data
            officer.emergency_contact = form.emergency_contact.data
            officer.salary = form.salary.data
            officer.current_status = form.current_status.data
            officer.updated_by = current_user.id
            officer.updated_at = datetime.utcnow()

            db.session.commit()
            log_audit('UPDATE', 'officers', officer.id, description=f"Updated officer {officer.badge_number}")
            flash('Officer profile updated successfully.', 'success')
            return redirect(url_for('officers.view', id=officer.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating officer: {str(e)}", 'danger')

    return render_template('officers/edit.html', form=form, officer=officer)


@officers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete(id):
    officer = Officer.active().filter_by(id=id).first_or_404()
    try:
        badge = officer.badge_number
        officer.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'officers', officer.id, description=f"Soft deleted officer {badge}")
        flash(f"Officer {badge} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting officer: {str(e)}", 'danger')
    return redirect(url_for('officers.index'))


@officers_bp.route('/duty-roster', methods=['GET', 'POST'])
@login_required
def duty_roster():
    form = DutyRosterForm()
    
    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, s.name) for s in stations]

    officers = Officer.active().order_by(Officer.first_name).all()
    form.officer_id.choices = [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    shifts = Shift.active().all()
    form.shift_id.choices = [(sh.id, f"{sh.name} ({sh.start_time}-{sh.end_time})") for sh in shifts]

    if form.validate_on_submit() and current_user.has_role('Admin', 'SHO', 'Inspector'):
        try:
            roster = DutyRoster(
                station_id=form.station_id.data,
                officer_id=form.officer_id.data,
                shift_id=form.shift_id.data,
                duty_date=form.duty_date.data,
                assigned_area=form.assigned_area.data,
                duty_type=form.duty_type.data,
                remarks=form.remarks.data,
                created_by=current_user.id
            )
            db.session.add(roster)
            db.session.commit()
            log_audit('CREATE', 'duty_rosters', roster.id, description=f"Scheduled roster duty for officer {roster.officer_id}")
            flash('Duty assigned in roster successfully!', 'success')
            return redirect(url_for('officers.duty_roster', date=form.duty_date.data.strftime('%Y-%m-%d')))
        except Exception as e:
            db.session.rollback()
            flash(f"Error assigning duty: {str(e)}", 'danger')

    selected_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except Exception:
        selected_date = date.today()

    form.duty_date.data = selected_date

    rosters = DutyRoster.active().filter_by(duty_date=selected_date).order_by(DutyRoster.id.desc()).all()
    return render_template('officers/duty_roster.html', form=form, rosters=rosters, selected_date=selected_date)


@officers_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    form = AttendanceForm()

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, s.name) for s in stations]

    officers = Officer.active().order_by(Officer.first_name).all()
    form.officer_id.choices = [(o.id, f"{o.badge_number} - {o.full_name}") for o in officers]

    if form.validate_on_submit() and current_user.has_role('Admin', 'SHO', 'Inspector', 'Clerk'):
        try:
            # Check if attendance already marked for this officer on this date
            existing = Attendance.active().filter_by(
                officer_id=form.officer_id.data,
                attendance_date=form.attendance_date.data
            ).first()

            if existing:
                existing.attendance_status = form.attendance_status.data
                existing.remarks = form.remarks.data
                existing.updated_by = current_user.id
                existing.updated_at = datetime.utcnow()
                flash('Attendance record updated for officer.', 'info')
            else:
                att = Attendance(
                    officer_id=form.officer_id.data,
                    station_id=form.station_id.data,
                    attendance_date=form.attendance_date.data,
                    check_in_time=datetime.utcnow() if form.attendance_status.data == 'Present' else None,
                    attendance_status=form.attendance_status.data,
                    remarks=form.remarks.data,
                    created_by=current_user.id
                )
                db.session.add(att)
                flash('Attendance marked successfully!', 'success')

            db.session.commit()
            return redirect(url_for('officers.attendance', date=form.attendance_date.data.strftime('%Y-%m-%d')))
        except Exception as e:
            db.session.rollback()
            flash(f"Error marking attendance: {str(e)}", 'danger')

    selected_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except Exception:
        selected_date = date.today()

    form.attendance_date.data = selected_date
    attendances = Attendance.active().filter_by(attendance_date=selected_date).order_by(Attendance.id.desc()).all()
    return render_template('officers/attendance.html', form=form, attendances=attendances, selected_date=selected_date)
