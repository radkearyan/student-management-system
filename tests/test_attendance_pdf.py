import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app

class TestAttendancePDFExport(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()

    def test_pdf_export_unauthorized(self):
        """Unauthenticated request to export attendance PDF should return 401."""
        response = self.client.get('/api/attendance/export/pdf')
        self.assertEqual(response.status_code, 401)

    def test_pdf_export_admin(self):
        """Admin should be able to export attendance as a valid PDF stream."""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'role': 'admin',
                'name': 'System Administrator'
            }

        response = self.client.get('/api/attendance/export/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF-'))
        self.assertIn('attendance_report_', response.headers.get('Content-Disposition', ''))

    def test_pdf_export_with_filters(self):
        """Admin should be able to export filtered attendance."""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'role': 'admin',
                'name': 'System Administrator'
            }

        response = self.client.get('/api/attendance/export/pdf?department=Computer+Engineering&status=Present')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF-'))

    def test_pdf_export_teacher_dept_restricted(self):
        """Teacher can export PDF for their assigned department."""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 2,
                'username': 'faculty_ce',
                'role': 'teacher',
                'name': 'Prof. Smith',
                'department': 'Computer Engineering'
            }

        response = self.client.get('/api/attendance/export/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF-'))

if __name__ == '__main__':
    unittest.main()
