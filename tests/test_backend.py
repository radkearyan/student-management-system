import unittest
import os
import sys

# Append project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config.database import get_db_connection

class TestBackendEndpoints(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_database_connection(self):
        """Test database connection is alive."""
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_root_redirection(self):
        """Test that root URL serves frontend template index."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_session_unauthorized(self):
        """Test session query returns success=false when unauthorized."""
        response = self.client.get('/api/auth/session')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])

    def test_get_departments(self):
        """Test retrieving departments list."""
        response = self.client.get('/api/departments')
        self.assertEqual(response.status_code, 200)
        depts = response.get_json()
        self.assertIsInstance(depts, list)
        self.assertTrue(len(depts) >= 4)
        dept_names = [d['name'] for d in depts]
        self.assertIn('Computer Engineering', dept_names)

    def test_post_department_unauthorized(self):
        """Test adding department without session returns 403 or 401/error."""
        response = self.client.post('/api/departments', json={"name": "Bio-Tech"})
        # Should be forbidden or require authorization
        self.assertIn(response.status_code, [401, 403])

    def test_get_profile_unauthorized(self):
        """Test accessing profile details without session returns 401."""
        response = self.client.get('/api/auth/profile')
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
