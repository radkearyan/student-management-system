import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config.database import init_db

class TestStudentManagementModule5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()
        # Login as Admin
        self.client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})

    def test_01_add_student_success(self):
        # Pre-cleanup
        self.client.delete('/api/students/STU999')

        res = self.client.post('/api/students', json={
            "student_id": "STU999",
            "name": "Test Student Module5",
            "dob": "2005-05-15",
            "gender": "Male",
            "email": "test.stu999@example.com",
            "phone": "+919999988888",
            "department": "Computer Engineering",
            "course": "B.Tech Computer Engineering"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

    def test_02_duplicate_student_id_prevention(self):
        res = self.client.post('/api/students', json={
            "student_id": "STU999",
            "name": "Duplicate Student ID",
            "dob": "2005-05-15",
            "gender": "Male",
            "email": "another.email@example.com",
            "phone": "+919999988889",
            "department": "Computer Engineering",
            "course": "B.Tech Computer Engineering"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])

    def test_03_duplicate_email_prevention(self):
        res = self.client.post('/api/students', json={
            "student_id": "STU998",
            "name": "Duplicate Email Student",
            "dob": "2005-05-15",
            "gender": "Male",
            "email": "test.stu999@example.com",
            "phone": "+919999988889",
            "department": "Computer Engineering",
            "course": "B.Tech Computer Engineering"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])

    def test_04_search_and_filter_students(self):
        # Search by name
        res = self.client.get('/api/students?search=Module5')
        self.assertEqual(res.status_code, 200)
        students = res.get_json()
        found = any(s['student_id'] == 'STU999' for s in students)
        self.assertTrue(found, "Added student should be found in search")

    def test_05_get_student_details(self):
        res = self.client.get('/api/students/STU999')
        self.assertEqual(res.status_code, 200)
        student = res.get_json()
        self.assertEqual(student['student_id'], 'STU999')
        self.assertEqual(student['name'], 'Test Student Module5')

    def test_06_edit_student(self):
        res = self.client.put('/api/students/STU999', json={
            "name": "Test Student Module5 Updated",
            "phone": "+919999977777",
            "bio": "Updated bio information"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        # Verify update
        detail_res = self.client.get('/api/students/STU999')
        student = detail_res.get_json()
        self.assertEqual(student['name'], 'Test Student Module5 Updated')

    def test_07_faculty_department_restriction(self):
        # Login as teacher (Computer Engineering)
        self.client.post('/api/auth/login', json={"username": "teacher", "password": "teacher123"})

        # Attempt to add student to Electrical Engineering
        res = self.client.post('/api/students', json={
            "student_id": "STU777",
            "name": "Unauthorized Add",
            "dob": "2005-05-15",
            "gender": "Male",
            "email": "unauthorized.add@example.com",
            "phone": "+919999966666",
            "department": "Electrical Engineering",
            "course": "B.Tech Electrical Engineering"
        })
        self.assertEqual(res.status_code, 403)

    def test_08_delete_student(self):
        # Login as Admin
        self.client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})

        res = self.client.delete('/api/students/STU999')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        # Verify deletion
        detail_res = self.client.get('/api/students/STU999')
        self.assertEqual(detail_res.status_code, 404)

if __name__ == '__main__':
    unittest.main()
