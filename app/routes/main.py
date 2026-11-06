from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.cases import FIR, Case, CrimeCategory, CrimeType, CaseHearing
from app.models.station import Officer, DutyRoster, PoliceStation
from app.models.evidence import Detainee, DetentionRecord, LockupCell, Evidence
from app.models.resources import Vehicle, Weapon
from app.models.common import Complaint
from app.models.people import Accused, Complainant, Victim
from app.utils.notifications import sync_system_notifications

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    # Trigger auto notification sync for current user
    sync_system_notifications(user_id=current_user.id)
    
    # 1. Stats Counters
    total_firs = FIR.active().count()
    active_cases = Case.active().filter(Case.case_status.in_(['Under Investigation', 'Charge Sheeted', 'In Court'])).count()
    officers_on_duty = Officer.active().filter_by(current_status='On Duty').count()
    detainees_in_custody = DetentionRecord.active().filter_by(detention_status='In Custody').count()
    available_vehicles = Vehicle.active().filter_by(operational_status='Available').count()
    total_weapons = Weapon.active().count()
    pending_complaints = Complaint.active().filter(Complaint.resolution_status.in_(['Pending', 'Under Inquiry'])).count()
    total_evidence = Evidence.active().count()

    # 2. Recent FIRs
    recent_firs = FIR.active().order_by(FIR.created_at.desc()).limit(5).all()

    # 3. Active Duty Roster for Today
    today_rosters = DutyRoster.active().filter_by(duty_date=today).order_by(DutyRoster.id.desc()).limit(6).all()

    # 4. Recent Detainees
    recent_detainees = DetentionRecord.active().filter_by(detention_status='In Custody').order_by(DetentionRecord.id.desc()).limit(5).all()

    # 5. Crime Category Distribution
    categories = CrimeCategory.active().all()
    category_labels = []
    category_counts = []
    for cat in categories:
        count = FIR.active().join(CrimeType).filter(CrimeType.category_id == cat.id).count()
        if count > 0 or len(category_labels) < 6:
            category_labels.append(cat.name)
            category_counts.append(count)

    # 6. Monthly FIR Registration Trends (last 6 months)
    month_labels = []
    month_counts = []
    for i in range(5, -1, -1):
        target_month_date = today - timedelta(days=i*30)
        m_label = target_month_date.strftime('%b %Y')
        month_labels.append(m_label)
        start_dt = datetime(target_month_date.year, target_month_date.month, 1)
        if target_month_date.month == 12:
            end_dt = datetime(target_month_date.year + 1, 1, 1)
        else:
            end_dt = datetime(target_month_date.year, target_month_date.month + 1, 1)
        c = FIR.active().filter(FIR.created_at >= start_dt, FIR.created_at < end_dt).count()
        month_counts.append(c)

    # 7. Case Status Breakdown
    case_status_labels = ['Under Investigation', 'Charge Sheeted', 'In Court', 'Closed - Solved', 'Closed - Unsolved']
    case_status_counts = [
        Case.active().filter_by(case_status=st).count() for st in case_status_labels
    ]

    # Role-specific contextual data
    user_role = current_user.role.name if current_user.role else 'Officer'
    officer_profile = current_user.officer_profile

    # Inspector: assigned cases
    assigned_cases = []
    if officer_profile and user_role in ['Inspector', 'SHO']:
        assigned_cases = Case.active().filter_by(lead_investigator_id=officer_profile.id).order_by(Case.id.desc()).limit(5).all()

    # Constable: assigned duty roster
    my_duties = []
    if officer_profile and user_role in ['Constable', 'Officer']:
        my_duties = DutyRoster.active().filter_by(officer_id=officer_profile.id, duty_date=today).all()

    # Clerk: recent complaints
    recent_complaints = []
    if user_role in ['Clerk', 'Admin']:
        recent_complaints = Complaint.active().order_by(Complaint.complaint_date.desc()).limit(5).all()

    return render_template(
        'dashboard/index.html',
        total_firs=total_firs,
        active_cases=active_cases,
        officers_on_duty=officers_on_duty,
        detainees_in_custody=detainees_in_custody,
        available_vehicles=available_vehicles,
        total_weapons=total_weapons,
        pending_complaints=pending_complaints,
        total_evidence=total_evidence,
        recent_firs=recent_firs,
        today_rosters=today_rosters,
        recent_detainees=recent_detainees,
        category_labels=category_labels,
        category_counts=category_counts,
        month_labels=month_labels,
        month_counts=month_counts,
        case_status_labels=case_status_labels,
        case_status_counts=case_status_counts,
        user_role=user_role,
        assigned_cases=assigned_cases,
        my_duties=my_duties,
        recent_complaints=recent_complaints
    )


@main_bp.route('/api/dashboard/charts')
@login_required
def api_dashboard_charts():
    """Real database query endpoint providing JSON data for Chart.js dashboard charts."""
    today = date.today()

    # 1. Monthly FIRs (Last 6 Months)
    month_labels = []
    month_counts = []
    for i in range(5, -1, -1):
        target_month_date = today - timedelta(days=i*30)
        m_label = target_month_date.strftime('%b %Y')
        month_labels.append(m_label)
        start_dt = datetime(target_month_date.year, target_month_date.month, 1)
        if target_month_date.month == 12:
            end_dt = datetime(target_month_date.year + 1, 1, 1)
        else:
            end_dt = datetime(target_month_date.year, target_month_date.month + 1, 1)
        c = FIR.active().filter(FIR.created_at >= start_dt, FIR.created_at < end_dt).count()
        month_counts.append(c)

    # 2. Crime Category Distribution
    categories = CrimeCategory.active().all()
    cat_labels = []
    cat_counts = []
    for cat in categories:
        count = FIR.active().join(CrimeType).filter(CrimeType.category_id == cat.id).count()
        if count > 0:
            cat_labels.append(cat.name)
            cat_counts.append(count)
    if not cat_labels:
        cat_labels = ['General Crimes', 'Narcotics', 'Theft/Robbery']
        cat_counts = [1, 1, 1]

    # 3. Case Status (Open vs Closed)
    open_cases = Case.active().filter(Case.case_status.in_(['Under Investigation', 'Charge Sheeted', 'In Court'])).count()
    closed_cases = Case.active().filter(Case.case_status.in_(['Closed - Solved', 'Closed - Unsolved', 'Untraced', 'Disposed'])).count()
    detailed_statuses = ['Under Investigation', 'Charge Sheeted', 'In Court', 'Closed - Solved', 'Closed - Unsolved']
    detailed_counts = [Case.active().filter_by(case_status=s).count() for s in detailed_statuses]

    # 4. Officers on Duty
    officers_on_duty = Officer.active().filter_by(current_status='On Duty').count()
    total_officers = Officer.active().count()

    return jsonify({
        'monthly_firs': {
            'labels': month_labels,
            'data': month_counts
        },
        'crime_categories': {
            'labels': cat_labels,
            'data': cat_counts
        },
        'case_status': {
            'labels': ['Open / Under Investigation', 'Closed / Disposed'],
            'data': [open_cases, closed_cases],
            'detailed_labels': detailed_statuses,
            'detailed_data': detailed_counts
        },
        'officers_on_duty': {
            'on_duty': officers_on_duty,
            'total': total_officers
        }
    })


@main_bp.route('/search')
@login_required
def search():
    """
    Global search across FIR number, Case number, CNIC, and names
    (accused, complainant, victim, officer, detainee).
    """
    query_str = request.args.get('q', '').strip()
    active_tab = request.args.get('tab', 'all')

    results = {
        'firs': [],
        'cases': [],
        'officers': [],
        'detainees': [],
        'accused': [],
        'complainants': [],
        'victims': []
    }
    total_matches = 0

    if query_str:
        wildcard = f"%{query_str}%"

        # Search FIRs (FIR number, incident location, details)
        results['firs'] = FIR.active().filter(
            (FIR.fir_number.ilike(wildcard)) |
            (FIR.incident_location.ilike(wildcard)) |
            (FIR.incident_details.ilike(wildcard))
        ).limit(20).all()

        # Search Cases (Case number, case title, summary)
        results['cases'] = Case.active().filter(
            (Case.case_number.ilike(wildcard)) |
            (Case.case_title.ilike(wildcard)) |
            (Case.summary.ilike(wildcard))
        ).limit(20).all()

        # Search Officers (First name, last name, badge number, phone)
        results['officers'] = Officer.active().filter(
            (Officer.first_name.ilike(wildcard)) |
            (Officer.last_name.ilike(wildcard)) |
            (Officer.badge_number.ilike(wildcard)) |
            (Officer.contact_phone.ilike(wildcard))
        ).limit(20).all()

        # Search Detainees (Full name, alias, national_id)
        results['detainees'] = Detainee.active().filter(
            (Detainee.full_name.ilike(wildcard)) |
            (Detainee.alias.ilike(wildcard)) |
            (Detainee.national_id.ilike(wildcard))
        ).limit(20).all()

        # Search Accused (Full name, CNIC, alias)
        results['accused'] = Accused.active().filter(
            (Accused.full_name.ilike(wildcard)) |
            (Accused.national_id.ilike(wildcard)) |
            (Accused.alias.ilike(wildcard))
        ).limit(20).all()

        # Search Complainants (Full name, CNIC, phone)
        results['complainants'] = Complainant.active().filter(
            (Complainant.full_name.ilike(wildcard)) |
            (Complainant.national_id.ilike(wildcard)) |
            (Complainant.phone.ilike(wildcard))
        ).limit(20).all()

        # Search Victims (Full name, CNIC, phone)
        results['victims'] = Victim.active().filter(
            (Victim.full_name.ilike(wildcard)) |
            (Victim.national_id.ilike(wildcard)) |
            (Victim.phone.ilike(wildcard))
        ).limit(20).all()

        total_matches = sum(len(items) for items in results.values())

    return render_template(
        'search/results.html',
        query=query_str,
        results=results,
        total_matches=total_matches,
        active_tab=active_tab
    )
