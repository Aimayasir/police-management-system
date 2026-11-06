import pytest
from datetime import datetime, date
from app import create_app, db
from app.models import (
    User, Role, PoliceStation, Officer, FIR, Case, Detainee,
    DetentionRecord, Evidence, EvidenceCustodyLog, Vehicle,
    Weapon, InventoryItem, Complaint, CrimeType, LockupCell, Court
)

@pytest.fixture(scope='module')
def test_app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def auth_client(test_app):
    client = test_app.test_client()
    client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    return client

# ==========================================
# 1. AUTHENTICATION & SESSION TESTS
# ==========================================
def test_login_success_and_session(client):
    """Test login stores user_id and role in session, sets remember cookie."""
    with client:
        resp = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        assert resp.status_code == 200
        from flask import session
        assert session.get('user_id') is not None
        assert session.get('role') == 'Admin'

def test_login_invalid_password(test_app):
    """Test login with wrong password displays danger message."""
    anon_client = test_app.test_client()
    anon_client.get('/auth/logout')
    resp = anon_client.post('/auth/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Invalid username/email or password' in resp.data

def test_logout_clears_session(auth_client):
    """Test logout clears session and redirects to login."""
    with auth_client:
        resp = auth_client.get('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200
        assert b'logged out safely' in resp.data
        from flask import session
        assert 'user_id' not in session
        assert 'role' not in session

# ==========================================
# 2. DETAIL VIEWS & NO-ATTRIBUTE-ERROR TESTS
# ==========================================
def test_detail_pages_no_attribute_error(auth_client):
    """Ensure all detail pages (detainees, cases, firs, officers) load with 200 OK and no 500/AttributeError."""
    routes = [
        '/detainees/1',
        '/cases/1',
        '/firs/1',
        '/officers/1',
        '/evidence/1',
        '/complaints/1',
        '/detainees/cells',
        '/officers/duty-roster',
        '/officers/attendance'
    ]
    for r in routes:
        resp = auth_client.get(r)
        assert resp.status_code == 200, f'Route {r} failed with status {resp.status_code}'

# ==========================================
# 3. FIR CRUD & SOFT DELETE
# ==========================================
def test_fir_crud_lifecycle(auth_client):
    """Test complete FIR create, read, update, soft delete lifecycle."""
    # Create
    create_resp = auth_client.post('/firs/create', data={
        'station_id': 1,
        'crime_type_id': 1,
        'io_officer_id': 3,
        'complainant_name': 'Pytest Informant',
        'complainant_phone': '+92 300 1112233',
        'complainant_address': 'The Mall Lahore',
        'complainant_gender': 'Male',
        'incident_date_time': '2026-11-06T11:00',
        'incident_location': 'Mall Road Crossing',
        'incident_details': 'Purse snatching by two suspects',
        'is_cognizable': 'y'
    }, follow_redirects=False)
    assert create_resp.status_code == 302

    fir = FIR.active().order_by(FIR.id.desc()).first()
    assert fir.incident_location == 'Mall Road Crossing'

    # Read
    view_resp = auth_client.get(f'/firs/{fir.id}')
    assert view_resp.status_code == 200
    assert b'Pytest Informant' in view_resp.data

    # Update
    edit_resp = auth_client.post(f'/firs/{fir.id}/edit', data={
        'station_id': 1,
        'crime_type_id': 1,
        'io_officer_id': 3,
        'complainant_name': 'Pytest Informant Updated',
        'complainant_phone': '+92 300 1112233',
        'complainant_address': 'The Mall Lahore',
        'complainant_gender': 'Male',
        'incident_date_time': '2026-11-06T11:00',
        'incident_location': 'Mall Road Crossing Sector 2',
        'incident_details': 'Updated statement details',
        'is_cognizable': 'y'
    }, follow_redirects=False)
    assert edit_resp.status_code == 302
    db.session.refresh(fir)
    assert fir.incident_location == 'Mall Road Crossing Sector 2'

    # Soft Delete
    del_resp = auth_client.post(f'/firs/{fir.id}/delete', follow_redirects=False)
    assert del_resp.status_code == 302
    db.session.refresh(fir)
    assert fir.is_deleted is True
    assert FIR.active().filter_by(id=fir.id).first() is None

# ==========================================
# 4. CASE CRUD & CASE NOTES
# ==========================================
def test_case_crud_lifecycle(auth_client):
    """Test Case create, read, update, note logging, and soft delete."""
    c_resp = auth_client.post('/cases/create', data={
        'station_id': 1,
        'crime_type_id': 1,
        'lead_investigator_id': 3,
        'case_title': 'Pytest Investigation Dossier',
        'case_status': 'Under Investigation',
        'summary': 'Detailed investigative case narrative'
    }, follow_redirects=False)
    assert c_resp.status_code == 302

    case = Case.active().order_by(Case.id.desc()).first()
    assert case.case_title == 'Pytest Investigation Dossier'

    # Add Case Note
    note_resp = auth_client.post(f'/cases/{case.id}/notes/add', data={
        'title': 'Test Case Note',
        'content': 'Field inquiry conducted at crime scene'
    }, follow_redirects=False)
    assert note_resp.status_code == 302

    # View Case
    view_resp = auth_client.get(f'/cases/{case.id}')
    assert view_resp.status_code == 200
    assert b'Pytest Investigation Dossier' in view_resp.data

    # Soft Delete
    del_resp = auth_client.post(f'/cases/{case.id}/delete', follow_redirects=False)
    assert del_resp.status_code == 302
    db.session.refresh(case)
    assert case.is_deleted is True

# ==========================================
# 5. DETAINEE INTAKE & RELEASE
# ==========================================
def test_detainee_booking_and_release(auth_client):
    """Test detainee intake booking and release from custody."""
    book_resp = auth_client.post('/detainees/create', data={
        'full_name': 'Pytest Detainee Farooq',
        'gender': 'Male',
        'age': 30,
        'cell_id': 1,
        'arresting_officer_id': 3,
        'detention_reason': 'Held on judicial remand'
    }, follow_redirects=False)
    assert book_resp.status_code == 302

    detainee = Detainee.active().filter_by(full_name='Pytest Detainee Farooq').first()
    assert detainee is not None

    # View detainee dossier
    view_resp = auth_client.get(f'/detainees/{detainee.id}')
    assert view_resp.status_code == 200
    assert b'Pytest Detainee Farooq' in view_resp.data

    # Release detainee
    rel_resp = auth_client.post(f'/detainees/{detainee.id}/release', follow_redirects=False)
    assert rel_resp.status_code == 302

    # Soft Delete
    del_resp = auth_client.post(f'/detainees/{detainee.id}/delete', follow_redirects=False)
    assert del_resp.status_code == 302
    db.session.refresh(detainee)
    assert detainee.is_deleted is True

# ==========================================
# 6. EVIDENCE & CHAIN OF CUSTODY
# ==========================================
def test_evidence_lifecycle(auth_client):
    """Test evidence recording, chain of custody transfer, and soft delete."""
    e_resp = auth_client.post('/evidence/create', data={
        'item_name': 'Pytest Seized Firearm 9mm',
        'evidence_type_id': 2,
        'collected_by_officer_id': 3,
        'collected_from_location': 'Crime scene parking',
        'current_storage_location': 'Malkhana Vault Rack-B',
        'description': 'Handgun with empty magazine'
    }, follow_redirects=False)
    assert e_resp.status_code == 302

    evd = Evidence.active().filter_by(item_name='Pytest Seized Firearm 9mm').first()
    assert evd is not None

    # Custody Transfer
    trans_resp = auth_client.post(f'/evidence/{evd.id}/transfer', data={
        'transferred_to_user_id': 2,
        'transfer_purpose': 'Forensic Analysis',
        'source_location': 'Malkhana Vault Rack-B',
        'destination_location': 'PFSA Forensics Lab',
        'receipt_ack': 'ACK-PFSA-9901'
    }, follow_redirects=False)
    assert trans_resp.status_code == 302

    # Verify View
    v_resp = auth_client.get(f'/evidence/{evd.id}')
    assert v_resp.status_code == 200
    assert b'Pytest Seized Firearm 9mm' in v_resp.data

    # Soft Delete
    d_resp = auth_client.post(f'/evidence/{evd.id}/delete', follow_redirects=False)
    assert d_resp.status_code == 302
    db.session.refresh(evd)
    assert evd.is_deleted is True

# ==========================================
# 7. ERROR HANDLING
# ==========================================
def test_404_error_handler(auth_client):
    """Test nonexistent page returns custom 404 page."""
    resp = auth_client.get('/firs/999999')
    assert resp.status_code == 404
    assert b'404' in resp.data
    assert b'Record or Page Not Found' in resp.data
