from datetime import datetime, date, timedelta
from app.models.base import db
from app.models.common import Notification
from app.models.cases import Case, CaseHearing
from app.models.evidence import Evidence, EvidenceCustodyLog
from app.models.users import User

def sync_system_notifications(user_id=None):
    """
    Auto-generates situational alerts and notifications:
    1. Upcoming court hearings within the next 3 days
    2. Pending cases older than 30 days requiring review
    3. Overdue evidence custody items out of the malkhana locker
    """
    try:
        today = date.today()
        three_days_later = today + timedelta(days=3)
        thirty_days_ago = today - timedelta(days=30)
        
        target_users = []
        if user_id:
            u = User.active().filter_by(id=user_id).first()
            if u:
                target_users = [u]
        else:
            target_users = User.active().all()

        if not target_users:
            return

        # 1. Upcoming Court Hearings (next 3 days)
        hearings = CaseHearing.active().filter(
            CaseHearing.hearing_date >= today,
            CaseHearing.hearing_date <= three_days_later
        ).all()

        for h in hearings:
            if not h.case:
                continue
            case = h.case
            judge_name = h.judge.name if h.judge else "Special Magistrate"
            title = f"Court Hearing: {case.case_number}"
            msg = f"Hearing for Case {case.case_number} scheduled on {h.hearing_date.strftime('%d-%b-%Y')} at {h.hearing_time or '09:00 AM'} before {judge_name} ({h.hearing_type})."
            action_url = f"/cases/{case.id}"

            # Notify lead investigator and SHO/Admin
            assigned_user_ids = set()
            if case.lead_investigator and case.lead_investigator.user_id:
                assigned_user_ids.add(case.lead_investigator.user_id)
            for u in target_users:
                if u.role and u.role.name in ['Admin', 'SHO'] or u.id in assigned_user_ids:
                    # Avoid duplicate unread notification
                    existing = Notification.active().filter_by(
                        user_id=u.id,
                        title=title,
                        is_read=False
                    ).first()
                    if not existing:
                        n = Notification(
                            user_id=u.id,
                            title=title,
                            message=msg,
                            notification_type='Hearing',
                            is_read=False,
                            action_url=action_url,
                            created_by=u.id
                        )
                        db.session.add(n)

        # 2. Pending Cases older than 30 days
        pending_cases = Case.active().filter(
            Case.date_opened <= thirty_days_ago,
            Case.case_status.in_(['Under Investigation', 'Charge Sheeted'])
        ).all()

        for c in pending_cases:
            title = f"30-Day Review Due: {c.case_number}"
            msg = f"Case {c.case_number} ({c.case_title}) opened on {c.date_opened.strftime('%d-%b-%Y')} is pending over 30 days without final resolution."
            action_url = f"/cases/{c.id}"

            assigned_user_ids = set()
            if c.lead_investigator and c.lead_investigator.user_id:
                assigned_user_ids.add(c.lead_investigator.user_id)
            for u in target_users:
                if u.role and u.role.name in ['Admin', 'SHO'] or u.id in assigned_user_ids:
                    existing = Notification.active().filter_by(
                        user_id=u.id,
                        title=title,
                        is_read=False
                    ).first()
                    if not existing:
                        n = Notification(
                            user_id=u.id,
                            title=title,
                            message=msg,
                            notification_type='Case',
                            is_read=False,
                            action_url=action_url,
                            created_by=u.id
                        )
                        db.session.add(n)

        # 3. Overdue Evidence Custody (items out of locker > 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        overdue_evidences = Evidence.active().filter(
            Evidence.chain_of_custody_status.in_(['In Forensics', 'In Court']),
            Evidence.updated_at <= seven_days_ago
        ).all()

        for ev in overdue_evidences:
            title = f"Evidence Custody Alert: {ev.evidence_number}"
            msg = f"Evidence {ev.evidence_number} ({ev.item_name}) has been at '{ev.current_storage_location}' for over 7 days. Return to Malkhana locker is overdue."
            action_url = f"/evidence/{ev.id}"

            for u in target_users:
                if u.role and u.role.name in ['Admin', 'SHO', 'Inspector']:
                    existing = Notification.active().filter_by(
                        user_id=u.id,
                        title=title,
                        is_read=False
                    ).first()
                    if not existing:
                        n = Notification(
                            user_id=u.id,
                            title=title,
                            message=msg,
                            notification_type='Custody',
                            is_read=False,
                            action_url=action_url,
                            created_by=u.id
                        )
                        db.session.add(n)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[NOTIFICATION SYNC ERROR]: {e}")
