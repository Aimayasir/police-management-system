from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.users import User, Role
from app.models.station import PoliceStation
from app.forms.auth_forms import UserForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@login_required
@role_required('Admin')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    role_id = request.args.get('role_id', 0, type=int)

    query = User.active().order_by(User.id.desc())

    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%')) |
            (User.badge_number.ilike(f'%{search}%'))
        )

    if role_id > 0:
        query = query.filter(User.role_id == role_id)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    roles = Role.active().all()
    return render_template('users/index.html', pagination=pagination, search=search, role_id=role_id, roles=roles)


@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create():
    form = UserForm()
    roles = Role.active().order_by(Role.name).all()
    form.role_id.choices = [(r.id, r.name) for r in roles]

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(0, '-- Headquarter / No Station --')] + [(s.id, s.name) for s in stations]

    if form.validate_on_submit():
        try:
            # Check username/email uniqueness
            existing_user = User.active().filter_by(username=form.username.data).first()
            if existing_user:
                flash(f"Username '{form.username.data}' is already taken.", 'danger')
                return render_template('users/create.html', form=form)

            existing_email = User.active().filter_by(email=form.email.data).first()
            if existing_email:
                flash(f"Email '{form.email.data}' is already registered.", 'danger')
                return render_template('users/create.html', form=form)

            station_val = form.station_id.data if (form.station_id.data and form.station_id.data > 0) else None

            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                badge_number=form.badge_number.data,
                phone=form.phone.data,
                role_id=form.role_id.data,
                station_id=station_val,
                is_active_account=True,
                created_by=current_user.id
            )
            raw_password = form.password.data or 'Password@123'
            user.set_password(raw_password)

            db.session.add(user)
            db.session.commit()

            log_audit('CREATE', 'users', user.id, description=f"Created system user {user.username} with role {user.role.name}")
            flash(f"User {user.username} created successfully with default password.", 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating user: {str(e)}", 'danger')

    return render_template('users/create.html', form=form)


@users_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit(id):
    user = User.active().filter_by(id=id).first_or_404()
    form = UserForm(obj=user)

    roles = Role.active().order_by(Role.name).all()
    form.role_id.choices = [(r.id, r.name) for r in roles]

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(0, '-- None --')] + [(s.id, s.name) for s in stations]

    if request.method == 'GET':
        form.station_id.data = user.station_id or 0

    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.full_name = form.full_name.data
            user.badge_number = form.badge_number.data
            user.phone = form.phone.data
            user.role_id = form.role_id.data
            user.station_id = form.station_id.data if (form.station_id.data and form.station_id.data > 0) else None
            user.updated_by = current_user.id
            user.updated_at = datetime.utcnow()

            if form.password.data:
                user.set_password(form.password.data)

            db.session.commit()
            log_audit('UPDATE', 'users', user.id, description=f"Updated user account {user.username}")
            flash('User profile updated successfully.', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating user: {str(e)}", 'danger')

    return render_template('users/create.html', form=form, user=user)


@users_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_status(id):
    user = User.active().filter_by(id=id).first_or_404()
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('users.index'))

    try:
        user.is_active_account = not user.is_active_account
        user.updated_by = current_user.id
        status_label = 'Activated' if user.is_active_account else 'Deactivated'
        db.session.commit()
        log_audit('UPDATE', 'users', user.id, description=f"{status_label} user account {user.username}")
        flash(f"User {user.username} {status_label}.", 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error changing user status: {str(e)}", 'danger')

    return redirect(url_for('users.index'))


@users_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete(id):
    user = User.active().filter_by(id=id).first_or_404()
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users.index'))

    try:
        username = user.username
        user.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'users', user.id, description=f"Soft deleted user {username}")
        flash(f"User {username} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", 'danger')

    return redirect(url_for('users.index'))


@users_bp.route('/audit-logs')
@login_required
@role_required('Admin')
def audit_logs():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    action = request.args.get('action', '', type=str).strip()
    user_id = request.args.get('user_id', 0, type=int)
    date_from = request.args.get('date_from', '', type=str).strip()
    date_to = request.args.get('date_to', '', type=str).strip()

    from app.models.common import AuditLog
    query = AuditLog.active().order_by(AuditLog.created_at.desc())

    if search:
        query = query.filter(
            (AuditLog.description.ilike(f'%{search}%')) |
            (AuditLog.entity_name.ilike(f'%{search}%')) |
            (AuditLog.ip_address.ilike(f'%{search}%'))
        )

    if action:
        query = query.filter(AuditLog.action == action.upper())

    if user_id > 0:
        query = query.filter(AuditLog.user_id == user_id)

    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.created_at <= dt_to)
        except ValueError:
            pass

    per_page = current_app.config.get('ITEMS_PER_PAGE', 15)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    users_list = User.active().order_by(User.full_name).all()
    actions_list = ['CREATE', 'UPDATE', 'SOFT_DELETE', 'LOGIN', 'LOGOUT', 'EXPORT']

    return render_template(
        'users/audit_logs.html',
        pagination=pagination,
        search=search,
        action=action,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        users_list=users_list,
        actions_list=actions_list
    )

