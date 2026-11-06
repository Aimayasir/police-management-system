from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.common import Notification
from app.utils.notifications import sync_system_notifications

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    # Sync situational notifications for current user
    sync_system_notifications(user_id=current_user.id)

    filter_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)

    query = Notification.active().filter_by(user_id=current_user.id).order_by(Notification.created_at.desc())

    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type in ['Hearing', 'Case', 'Custody', 'Alert', 'Duty']:
        query = query.filter_by(notification_type=filter_type)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 15)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    unread_count = Notification.active().filter_by(user_id=current_user.id, is_read=False).count()

    return render_template(
        'notifications/index.html',
        pagination=pagination,
        filter_type=filter_type,
        unread_count=unread_count
    )


@notifications_bp.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    notif = Notification.active().filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        notif.is_read = True
        notif.updated_by = current_user.id
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    if notif.action_url:
        return redirect(notif.action_url)
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def read_all():
    try:
        notifications = Notification.active().filter_by(user_id=current_user.id, is_read=False).all()
        for n in notifications:
            n.is_read = True
            n.updated_by = current_user.id
        db.session.commit()
        flash('All notifications marked as read.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error marking notifications as read: {str(e)}", 'danger')

    return redirect(url_for('notifications.index'))


@notifications_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    notif = Notification.active().filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        notif.soft_delete(current_user.id)
        db.session.commit()
        flash('Notification dismissed.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting notification: {str(e)}", 'danger')

    return redirect(url_for('notifications.index'))
