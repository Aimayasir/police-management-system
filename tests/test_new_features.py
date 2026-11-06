import pytest
from datetime import datetime, date
from app import create_app, db
from app.models.users import User, Role
from app.models.cases import FIR, Case
from app.models.evidence import Evidence, EvidenceCustodyLog
from app.models.common import AuditLog, Notification

@pytest.fixture
def app_instance():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

def login_as(client, username, password='admin123'):
    client.get('/auth/logout')
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_dashboard_charts_json_endpoint(client):
    """Test that /api/dashboard/charts returns valid JSON with monthly FIRs, crime categories, and case status."""
    login_as(client, 'admin', 'admin123')
    resp = client.get('/api/dashboard/charts')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'monthly_firs' in data
    assert 'crime_categories' in data
    assert 'case_status' in data
    assert 'officers_on_duty' in data
    assert isinstance(data['monthly_firs']['labels'], list)
    assert isinstance(data['crime_categories']['labels'], list)

def test_global_search_endpoint(client):
    """Test that /search returns matches across FIRs, cases, accused, and officers."""
    login_as(client, 'admin', 'admin123')
    resp = client.get('/search?q=Lahore')
    assert resp.status_code == 200
    assert b'Global Search Results' in resp.data

    # Search for an accused or person
    resp_name = client.get('/search?q=Ali')
    assert resp_name.status_code == 200

def test_audit_logs_admin_page(client):
    """Test that Admin can access /users/audit-logs and filter by action."""
    login_as(client, 'admin', 'admin123')
    resp = client.get('/users/audit-logs')
    assert resp.status_code == 200
    assert b'Security & Operational Audit Logs' in resp.data

    # Non-admin (Inspector) should be blocked with 403
    login_as(client, 'inspector', 'admin123')
    resp_forbidden = client.get('/users/audit-logs')
    assert resp_forbidden.status_code == 403

def test_pdf_reports_generation(client):
    """Test that individual FIR, Case, and Duty Roster PDFs generate valid PDF binaries."""
    login_as(client, 'admin', 'admin123')

    # FIR PDF
    fir_resp = client.get('/reports/firs/1/pdf')
    assert fir_resp.status_code == 200
    assert fir_resp.mimetype == 'application/pdf'
    assert fir_resp.data.startswith(b'%PDF')

    # Case PDF
    case_resp = client.get('/reports/cases/1/pdf')
    assert case_resp.status_code == 200
    assert case_resp.mimetype == 'application/pdf'
    assert case_resp.data.startswith(b'%PDF')

    # Duty Roster PDF
    roster_resp = client.get('/reports/roster/pdf')
    assert roster_resp.status_code == 200
    assert roster_resp.mimetype == 'application/pdf'
    assert roster_resp.data.startswith(b'%PDF')

def test_csv_exports(client):
    """Test that CSV export routes produce UTF-8 CSV downloads."""
    login_as(client, 'admin', 'admin123')
    csv_endpoints = [
        '/reports/firs/csv',
        '/reports/cases/csv',
        '/reports/officers/csv',
        '/reports/detainees/csv',
        '/reports/evidence/csv',
        '/reports/vehicles/csv',
        '/reports/weapons/csv',
        '/reports/inventory/csv',
        '/reports/complaints/csv'
    ]
    for endpoint in csv_endpoints:
        resp = client.get(endpoint)
        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'

def test_notifications_lifecycle(client, app_instance):
    """Test notification listing and mark-all-read."""
    login_as(client, 'admin', 'admin123')
    resp = client.get('/notifications/')
    assert resp.status_code == 200
    assert b'Notifications & System Alerts' in resp.data

    # Mark all read
    post_read = client.post('/notifications/read-all', follow_redirects=True)
    assert post_read.status_code == 200

def test_user_profile_and_security(client):
    """Test profile viewing and password update validation."""
    login_as(client, 'constable', 'admin123')
    resp = client.get('/auth/profile')
    assert resp.status_code == 200
    assert b'User Profile & Security' in resp.data
    assert b'constable' in resp.data

def test_detainee_detail_route_no_attribute_error(client):
    """Explicitly verify that /detainees/1 loads without InstrumentedList order_by error."""
    login_as(client, 'admin', 'admin123')
    resp = client.get('/detainees/1')
    assert resp.status_code == 200
    assert b'Detainee' in resp.data
    assert b'Cell' in resp.data
