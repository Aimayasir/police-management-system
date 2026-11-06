from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.base import db
from app.models.users import User, LoginLog
from app.forms.auth_forms import LoginForm, ChangePasswordForm
from app.utils.audit import log_audit

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        raw_input = form.username.data.strip().lower()
        alias_map = {
            'sho_singh': 'sho',
            'insp_kumar': 'inspector',
            'const_sharma': 'constable',
            'clerk_verma': 'clerk'
        }
        target_username = alias_map.get(raw_input, raw_input)

        user = User.active().filter(
            (db.func.lower(User.username) == raw_input) |
            (db.func.lower(User.username) == target_username) |
            (db.func.lower(User.email) == raw_input)
        ).first()

        now = datetime.utcnow()

        if user:
            # 1. Check if account is currently locked out
            if user.locked_until and user.locked_until > now:
                remaining_mins = max(1, int((user.locked_until - now).total_seconds() / 60) + 1)
                flash(f"Account temporarily locked due to 5 consecutive failed logins. Please retry in {remaining_mins} minute(s).", 'danger')
                return render_template('auth/login.html', form=form)

            # Auto-unlock if lockout window has elapsed
            if user.locked_until and user.locked_until <= now:
                user.locked_until = None
                user.failed_login_attempts = 0
                db.session.commit()

            # 2. Check Password
            if user.check_password(form.password.data):
                if not user.is_active_account:
                    flash('Your account has been deactivated. Please contact the Station House Officer (SHO) or Administrator.', 'danger')
                    return render_template('auth/login.html', form=form)

                try:
                    # Reset failure tracking upon success
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    user.last_login = now

                    login_log = LoginLog(
                        user_id=user.id,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', '')[:255],
                        login_time=now,
                        status_message='SUCCESS',
                        created_by=user.id
                    )
                    db.session.add(login_log)
                    db.session.commit()

                    login_user(user, remember=form.remember_me.data)
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['role'] = user.role.name if user.role else 'Officer'
                    log_audit('LOGIN', 'users', user.id, description=f"User {user.username} logged in successfully")
                    
                    flash(f'Welcome back, {user.full_name} ({session["role"]}).', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
                except Exception as e:
                    db.session.rollback()
                    flash('An unexpected error occurred during login. Please try again.', 'danger')
            else:
                # Password incorrect: increment failure count
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = now + timedelta(minutes=15)
                    db.session.commit()
                    log_audit('LOCKOUT', 'users', user.id, description=f"Account {user.username} locked out for 15 minutes after 5 failed login attempts")
                    flash('Account locked for 15 minutes due to 5 consecutive failed login attempts.', 'danger')
                else:
                    db.session.commit()
                    attempts_left = 5 - user.failed_login_attempts
                    flash(f'Invalid username/email or password. ({attempts_left} attempt(s) remaining before account lockout)', 'danger')
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    try:
        user_id = current_user.id
        username = current_user.username
        last_log = LoginLog.active().filter_by(user_id=user_id).order_by(LoginLog.id.desc()).first()
        if last_log and not last_log.logout_time:
            last_log.logout_time = datetime.utcnow()
            db.session.commit()
        
        log_audit('LOGOUT', 'users', user_id, description=f"User {username} logged out")
    except Exception:
        db.session.rollback()

    logout_user()
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    user = current_user

    if form.validate_on_submit():
        if not user.check_password(form.current_password.data):
            flash('Incorrect current password. Please re-enter your existing password.', 'danger')
        else:
            try:
                user.set_password(form.new_password.data)
                user.updated_at = datetime.utcnow()
                user.updated_by = user.id
                db.session.commit()
                log_audit('UPDATE', 'users', user.id, description=f"User {user.username} changed account password")
                flash('Your password has been changed successfully.', 'success')
                return redirect(url_for('auth.profile'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error changing password: {str(e)}", 'danger')

    # Fetch recent login logs for this user
    recent_logins = LoginLog.active().filter_by(user_id=user.id).order_by(LoginLog.login_time.desc()).limit(5).all()

    return render_template(
        'auth/profile.html',
        user=user,
        form=form,
        recent_logins=recent_logins
    )
