import unittest
from datetime import datetime, date
from app import create_app
from app.models.base import db
from app.models import (
    Role, User, PoliceStation, Officer, FIR, FirStatus,
    Case, Detainee, DetentionRecord, LockupCell, Evidence,
    Vehicle, Weapon, Complaint, CrimeType
)

class PSMSTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_database_table_count(self):
        """Verify the database schema contains at least 40 normalized tables."""
        metadata = db.metadata
        table_count = len(metadata.tables)
        print(f"\n[TEST] Total registered database tables: {table_count}")
        self.assertGreaterEqual(table_count, 40, "Database must have at least 40 tables")

    def test_mandatory_base_model_columns(self):
        """Verify that every model has the mandatory audit and soft delete columns."""
        metadata = db.metadata
        mandatory_columns = {'id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'status', 'is_deleted', 'deleted_by'}
        
        for table_name, table in metadata.tables.items():
            cols = {c.name for c in table.columns}
            missing = mandatory_columns - cols
            self.assertEqual(missing, set(), f"Table '{table_name}' is missing mandatory columns: {missing}")

    def test_soft_delete_functionality(self):
        """Verify soft deletion sets is_deleted=True and active() filters it out."""
        # Find or create a test complaint
        station = PoliceStation.active().first()
        self.assertIsNotNone(station)

        cmp_num = f"CMP-TEST-{int(datetime.utcnow().timestamp()*1000)}"
        cmp = Complaint(
            complaint_number=cmp_num,
            citizen_name='Test Citizen',
            citizen_phone='+92 300 9999000',
            citizen_address='Test Address',
            station_id=station.id,
            subject='Test Subject',
            description='Test Description',
            priority='Low',
            resolution_status='Pending',
            status='active'
        )
        db.session.add(cmp)
        db.session.commit()

        # Check it is returned by active()
        found = Complaint.active().filter_by(complaint_number=cmp_num).first()
        self.assertIsNotNone(found)
        self.assertFalse(found.is_deleted)

        # Soft delete
        found.soft_delete(user_id=1)
        db.session.commit()

        # Verify it is no longer returned by active()
        active_check = Complaint.active().filter_by(complaint_number=cmp_num).first()
        self.assertIsNone(active_check)

        # Verify record still exists in database with is_deleted=True
        raw_check = Complaint.query.filter_by(complaint_number=cmp_num).first()
        self.assertIsNotNone(raw_check)
        self.assertTrue(raw_check.is_deleted)
        self.assertEqual(raw_check.status, 'deactive')

    def test_auth_login_and_dashboard(self):
        """Test login with Admin credentials and dashboard access."""
        # Attempt login
        response = self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
        self.assertIn(b'Total FIRs', response.data)

    def test_reports_export_csv_and_pdf(self):
        """Test that CSV and PDF reports return 200 OK with correct MIME types."""
        # Log in first
        self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        # Test FIR CSV Export
        csv_resp = self.client.get('/reports/firs/csv')
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp.mimetype, 'text/csv')

        # Test FIR PDF Export
        pdf_resp = self.client.get('/reports/firs/pdf')
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp.mimetype, 'application/pdf')

if __name__ == '__main__':
    unittest.main()
