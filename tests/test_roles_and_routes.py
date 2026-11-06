import unittest
from datetime import datetime, date
from app import create_app
from app.models.base import db
from app.models import FIR, Case, Detainee, Evidence, PoliceStation, CrimeType, Officer

class RolesAndRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def login_as(self, username, password):
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_role_access_inspector(self):
        """Inspector can access FIRs and Cases but cannot access User Management."""
        self.login_as('inspector', 'admin123')

        # Allowed
        fir_resp = self.client.get('/firs/')
        self.assertEqual(fir_resp.status_code, 200)

        case_resp = self.client.get('/cases/')
        self.assertEqual(case_resp.status_code, 200)

        # Restricted: Users management is Admin only
        user_resp = self.client.get('/users/', follow_redirects=True)
        self.assertIn(b'Access denied', user_resp.data)

    def test_role_access_clerk(self):
        """Clerk can access Complaints, Roster, Attendance, FIR view."""
        self.login_as('clerk', 'admin123')

        cmp_resp = self.client.get('/complaints/')
        self.assertEqual(cmp_resp.status_code, 200)

        att_resp = self.client.get('/officers/attendance')
        self.assertEqual(att_resp.status_code, 200)

    def test_fir_creation_route(self):
        """Test creating an FIR as Inspector."""
        self.login_as('inspector', 'admin123')

        station = PoliceStation.active().first()
        crime_type = CrimeType.active().first()
        officer = Officer.active().first()

        resp = self.client.post('/firs/create', data={
            'station_id': station.id,
            'crime_type_id': crime_type.id,
            'io_officer_id': officer.id,
            'complainant_name': 'Test Informant',
            'complainant_phone': '+91 91234 56789',
            'complainant_address': 'Sector 10, Test City',
            'complainant_gender': 'Male',
            'incident_date_time': '2026-10-31T14:30',
            'incident_location': 'Near City Park Main Gate',
            'incident_details': 'Test complaint details of bag snatched by motorcycle rider.',
            'is_cognizable': 'y'
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'registered successfully', resp.data)

if __name__ == '__main__':
    unittest.main()
