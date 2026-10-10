import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app

class TestFeeReceiptPDFExport(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()

    def test_fee_receipt_pdf_unauthorized(self):
        """Unauthenticated request to export fee receipt PDF should return 401."""
        response = self.client.get('/api/fees/receipt/1/pdf')
        self.assertEqual(response.status_code, 401)

    def test_fee_receipt_pdf_admin(self):
        """Admin should be able to export any valid fee receipt as PDF."""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'role': 'admin',
                'name': 'Administrator'
            }

        response = self.client.get('/api/fees/receipt/1/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF-'))
        self.assertIn('fee_receipt_', response.headers.get('Content-Disposition', ''))

    def test_fee_receipt_pdf_student_owner(self):
        """Student should be able to export their own fee receipt as PDF."""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 10,
                'username': 'student1',
                'role': 'student',
                'reference_id': 'STU001',
                'name': 'Student One'
            }

        response = self.client.get('/api/fees/receipt/1/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF-'))

    def test_fee_receipt_pdf_student_forbidden(self):
        """Student cannot access another student's fee receipt."""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 11,
                'username': 'student2',
                'role': 'student',
                'reference_id': 'STU002',
                'name': 'Student Two'
            }

        # Receipt 1 belongs to STU001
        response = self.client.get('/api/fees/receipt/1/pdf')
        self.assertEqual(response.status_code, 403)

    def test_fee_receipt_pdf_not_found(self):
        """Request for non-existent fee receipt should return 404."""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'role': 'admin',
                'name': 'Administrator'
            }

        response = self.client.get('/api/fees/receipt/999999/pdf')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
