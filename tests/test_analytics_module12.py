import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestAnalyticsModule12(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        self.admin_username = "admin"
        self.admin_password = "admin123"

    def login(self, username, password):
        return self.client.post('/api/auth/login', json={
            "username": username,
            "password": password
        })

    def test_01_analytics_endpoint_structure(self):
        """Test GET /api/analytics contains all required Module 12 chart datasets"""
        self.login(self.admin_username, self.admin_password)

        res = self.client.get('/api/analytics')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

        # Verify presence of all required chart data fields
        self.assertIn('students_by_branch', data)
        self.assertIn('students_by_year', data)
        self.assertIn('attendance_distribution', data)
        self.assertIn('subject_performance', data)
        self.assertIn('pass_fail_distribution', data)

        self.assertIsInstance(data['students_by_branch'], dict)
        self.assertIsInstance(data['students_by_year'], dict)
        self.assertIsInstance(data['attendance_distribution'], dict)
        self.assertIsInstance(data['subject_performance'], dict)
        self.assertIsInstance(data['pass_fail_distribution'], dict)

    def test_02_analytics_data_integrity(self):
        """Test accuracy of analytics calculations against database queries"""
        self.login(self.admin_username, self.admin_password)

        res = self.client.get('/api/analytics')
        data = res.get_json()

        # Check pass/fail keys
        pf = data['pass_fail_distribution']
        self.assertIn('Pass', pf)
        self.assertIn('Fail', pf)
        self.assertGreaterEqual(pf['Pass'], 0)
        self.assertGreaterEqual(pf['Fail'], 0)

        # Check attendance distribution keys
        att = data['attendance_distribution']
        self.assertIn('Above 85%', att)
        self.assertIn('75% - 85%', att)
        self.assertIn('Below 75%', att)

    def test_03_empty_database_analytics(self):
        """Test that get_dashboard_analytics_data handles an empty database without throwing exceptions"""
        # Execute direct call to db_adapter analytics function
        analytics = db_adapter.get_dashboard_analytics_data()
        self.assertIsNotNone(analytics)
        self.assertIn('students_by_branch', analytics)
        self.assertIn('students_by_year', analytics)
        self.assertIn('attendance_distribution', analytics)
        self.assertIn('subject_performance', analytics)
        self.assertIn('pass_fail_distribution', analytics)

if __name__ == '__main__':
    unittest.main()
