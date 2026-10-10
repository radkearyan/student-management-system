import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestFacultyModule6(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        # Clean up test user if left over
        conn = db_adapter.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE username = 'prof_test_m6' OR email = 'prof.test.m6@college.edu'")
        row = c.fetchone()
        if row:
            uid = row['user_id']
            c.execute("DELETE FROM faculty WHERE user_id = ? OR faculty_id = 'FAC999'", (uid,))
            c.execute("DELETE FROM users WHERE user_id = ?", (uid,))
            conn.commit()
        conn.close()

        # Helper to login and establish session
        self.admin_username = "admin"
        self.admin_password = "admin123"
        
        self.teacher_username = "teacher"
        self.teacher_password = "teacher123"
        
        self.student_username = "student"
        self.student_password = "student123"


    def login(self, username, password):
        return self.client.post('/api/auth/login', json={
            "username": username,
            "password": password
        })

    def test_01_get_faculty_as_admin(self):
        """Test fetching faculty list as admin"""
        self.login(self.admin_username, self.admin_password)
        res = self.client.get('/api/faculty')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIsInstance(data.get('faculty'), list)

    def test_02_get_faculty_unauthorized_student(self):
        """Test that students cannot access full faculty admin management API if role protected"""
        # Note: faculty list endpoint is protected for ['admin', 'teacher']
        self.login(self.student_username, self.student_password)
        res = self.client.get('/api/faculty')
        self.assertEqual(res.status_code, 403)

    def test_03_add_edit_delete_faculty_flow(self):
        """Test complete CRUD flow: Add faculty, search/filter, edit, assign subject, delete"""
        self.login(self.admin_username, self.admin_password)

        # 1. Add Faculty
        new_fac = {
            "username": "prof_test_m6",
            "password": "Password123!",
            "email": "prof.test.m6@college.edu",
            "name": "Dr. Testing Faculty",
            "department": "Computer Engineering",
            "phone": "+919876500000",
            "designation": "Associate Professor",
            "qualification": "Ph.D in AI",
            "reference_id": "FAC999"
        }
        add_res = self.client.post('/api/faculty', json=new_fac)
        self.assertEqual(add_res.status_code, 200)
        add_data = add_res.get_json()
        self.assertTrue(add_data.get('success'))
        created_fac = add_data.get('faculty')
        created_id = created_fac['user_id']

        # 2. Duplicate Faculty Prevention
        dup_res = self.client.post('/api/faculty', json=new_fac)
        self.assertEqual(dup_res.status_code, 400)
        self.assertIn("already registered", dup_res.get_json().get('message').lower())

        # 3. Search and Filter Faculty
        search_res = self.client.get('/api/faculty?search=Testing')
        self.assertEqual(search_res.status_code, 200)
        s_data = search_res.get_json().get('faculty', [])
        self.assertTrue(any(f['user_id'] == created_id for f in s_data))

        dept_res = self.client.get('/api/faculty?department=Computer%20Engineering')
        self.assertEqual(dept_res.status_code, 200)
        d_data = dept_res.get_json().get('faculty', [])
        self.assertTrue(any(f['user_id'] == created_id for f in d_data))

        # 4. View Faculty Details
        detail_res = self.client.get(f'/api/faculty/{created_id}')
        self.assertEqual(detail_res.status_code, 200)
        fac_detail = detail_res.get_json().get('faculty')
        self.assertEqual(fac_detail['name'], "Dr. Testing Faculty")

        # 5. Edit Faculty
        edit_payload = {
            "name": "Dr. Testing Faculty Updated",
            "email": "prof.test.updated@college.edu",
            "phone": "+919876500001",
            "department": "Information Technology",
            "designation": "Professor & HOD",
            "qualification": "Post-Doc CS"
        }
        edit_res = self.client.put(f'/api/faculty/{created_id}', json=edit_payload)
        self.assertEqual(edit_res.status_code, 200)

        # Verify edit
        updated_detail = self.client.get(f'/api/faculty/{created_id}').get_json().get('faculty')
        self.assertEqual(updated_detail['name'], "Dr. Testing Faculty Updated")
        self.assertEqual(updated_detail['department'], "Information Technology")

        # 6. Assign Subject
        assign_res = self.client.post('/api/faculty/FAC999/assign_subject', json={"subject_id": "CS101"})
        self.assertEqual(assign_res.status_code, 200)
        self.assertTrue(assign_res.get_json().get('success'))

        # 7. Delete Faculty
        del_res = self.client.delete(f'/api/faculty/{created_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.get_json().get('success'))

        # Verify deletion
        gone_res = self.client.get(f'/api/faculty/{created_id}')
        self.assertEqual(gone_res.status_code, 404)

if __name__ == '__main__':
    unittest.main()
