import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config.database import init_db

class TestAuthModule3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'testing_secret_key'

    def setUp(self):
        self.client = app.test_client()

    def test_01_correct_login_admin(self):
        res = self.client.post('/api/auth/login', json={
            "username": "admin",
            "password": "admin123"
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'admin')

    def test_02_correct_login_teacher(self):
        res = self.client.post('/api/auth/login', json={
            "username": "teacher",
            "password": "teacher123"
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'teacher')

    def test_03_correct_login_student(self):
        res = self.client.post('/api/auth/login', json={
            "username": "student",
            "password": "student123"
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'student')

    def test_04_wrong_password(self):
        res = self.client.post('/api/auth/login', json={
            "username": "admin",
            "password": "wrongpassword123"
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "Invalid username or password")

    def test_05_unknown_user(self):
        res = self.client.post('/api/auth/login', json={
            "username": "nonexistentuser_xyz",
            "password": "somepassword"
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])

    def test_06_logout(self):
        # Login first
        self.client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        
        # Logout
        res = self.client.post('/api/auth/logout')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])

        # Verify session cleared
        res_session = self.client.get('/api/auth/session')
        self.assertFalse(res_session.get_json()['success'])

    def test_07_protected_route_without_login(self):
        # Accessing protected admin route without session
        res = self.client.get('/api/analytics')
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data['success'])

    def test_08_student_accessing_admin_route(self):
        # Login as student
        self.client.post('/api/auth/login', json={"username": "student", "password": "student123"})
        
        # Attempt to access admin analytics
        res = self.client.get('/api/analytics')
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn("Access denied", data['message'])

    def test_09_faculty_accessing_unauthorized_admin_feature(self):
        # Login as teacher
        self.client.post('/api/auth/login', json={"username": "teacher", "password": "teacher123"})
        
        # Attempt to delete department (admin-only)
        res = self.client.delete('/api/departments/1')
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data['success'])

if __name__ == '__main__':
    unittest.main()
