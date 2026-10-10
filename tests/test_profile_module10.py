import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestProfileModule10(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        self.admin_username = "admin"
        self.admin_password = "admin123"

        self.student_username = "student"
        self.student_password = "student123"

    def login(self, username, password):
        return self.client.post('/api/auth/login', json={
            "username": username,
            "password": password
        })

    def test_01_student_profile_fetch(self):
        """Test fetching student profile data"""
        self.login(self.student_username, self.student_password)

        res = self.client.get('/api/auth/profile')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['profile']['role'], 'student')
        self.assertIn('reference_id', data['profile'])

    def test_02_student_update_authorized_fields(self):
        """Test student updating authorized personal fields (bio, phone, address)"""
        self.login(self.student_username, self.student_password)

        payload = {
            "phone": "+91-9998887770",
            "bio": "Enthusiastic CS student interested in AI and Data Science.",
            "skills": "Python, JavaScript, SQL",
            "address": "123 Academic Campus Lane"
        }
        res = self.client.put('/api/auth/profile', json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('success'))

        # Verify updated profile
        res_prof = self.client.get('/api/auth/profile')
        prof = res_prof.get_json()['profile']
        self.assertEqual(prof.get('phone'), "+91-9998887770")
        self.assertEqual(prof.get('bio'), "Enthusiastic CS student interested in AI and Data Science.")
        self.assertEqual(prof.get('skills'), "Python, JavaScript, SQL")

    def test_03_student_cannot_modify_restricted_fields(self):
        """Test that student CANNOT modify restricted fields (marks, attendance, role, student_id)"""
        self.login(self.student_username, self.student_password)

        # 1. Attempt to change role
        res_role = self.client.put('/api/auth/profile', json={"role": "admin"})
        self.assertEqual(res_role.status_code, 403)

        # 2. Attempt to change student_id
        res_id = self.client.put('/api/auth/profile', json={"student_id": "STU999_HACK"})
        self.assertEqual(res_id.status_code, 403)

        # 3. Attempt to alter marks
        res_marks = self.client.put('/api/auth/profile', json={"marks": 100})
        self.assertEqual(res_marks.status_code, 403)

        # 4. Attempt to alter attendance
        res_att = self.client.put('/api/auth/profile', json={"attendance": 100})
        self.assertEqual(res_att.status_code, 403)

        # 5. Attempt to update another student via student route
        res_other = self.client.put('/api/students/STU999_OTHER', json={"phone": "123456"})
        self.assertEqual(res_other.status_code, 403)

    def test_04_student_attendance_summary_and_results_fetch(self):
        """Test student fetching attendance summary and marks report card"""
        self.login(self.student_username, self.student_password)

        # Get session to extract student reference ID
        sess_res = self.client.get('/api/auth/session')
        user = sess_res.get_json()['user']
        student_id = user['reference_id']

        # Fetch attendance summary
        att_res = self.client.get(f'/api/attendance/summary/{student_id}')
        self.assertEqual(att_res.status_code, 200)
        self.assertTrue(att_res.get_json().get('success'))

        # Fetch marks result card
        marks_res = self.client.get(f'/api/marks/student/{student_id}')
        self.assertEqual(marks_res.status_code, 200)
        self.assertTrue(marks_res.get_json().get('success'))

if __name__ == '__main__':
    unittest.main()
