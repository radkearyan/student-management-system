import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestCoursesModule7(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        # Clean up test subject and course if left over
        conn = db_adapter.get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM subjects WHERE subject_code IN ('TEST101', 'TEST102')")
        c.execute("DELETE FROM courses WHERE course_code = 'TEST-BTECH'")
        conn.commit()
        conn.close()

        self.admin_username = "admin"
        self.admin_password = "admin123"
        self.student_username = "student"
        self.student_password = "student123"

    def login(self, username, password):
        return self.client.post('/api/auth/login', json={
            "username": username,
            "password": password
        })

    def test_01_get_subjects_and_courses_public(self):
        """Test fetching subjects and courses list"""
        self.login(self.admin_username, self.admin_password)
        
        # Get subjects
        s_res = self.client.get('/api/subjects')
        self.assertEqual(s_res.status_code, 200)
        s_data = s_res.get_json()
        self.assertTrue(s_data.get('success'))
        self.assertIsInstance(s_data.get('subjects'), list)

        # Get courses
        c_res = self.client.get('/api/courses')
        self.assertEqual(c_res.status_code, 200)
        c_data = c_res.get_json()
        self.assertTrue(c_data.get('success'))
        self.assertIsInstance(c_data.get('courses'), list)

    def test_02_subject_crud_and_duplicate_prevention(self):
        """Test Subject CRUD and duplicate code prevention"""
        self.login(self.admin_username, self.admin_password)

        # 1. Add Subject
        new_sub = {
            "subject_code": "TEST101",
            "subject_name": "Software Engineering Principles",
            "department": "Computer Engineering",
            "course_code": "CSE-BTECH",
            "semester": 4,
            "credits": 4
        }
        add_res = self.client.post('/api/subjects', json=new_sub)
        self.assertEqual(add_res.status_code, 200)
        self.assertTrue(add_res.get_json().get('success'))

        # 2. Duplicate Subject Code Prevention
        dup_res = self.client.post('/api/subjects', json=new_sub)
        self.assertEqual(dup_res.status_code, 400)
        self.assertIn("already exists", dup_res.get_json().get('message').lower())

        # 3. Search and Filter Subjects
        search_res = self.client.get('/api/subjects?search=Software')
        self.assertEqual(search_res.status_code, 200)
        subs = search_res.get_json().get('subjects', [])
        self.assertTrue(any(s['subject_code'] == 'TEST101' for s in subs))

        # 4. View Details
        detail_res = self.client.get('/api/subjects/TEST101')
        self.assertEqual(detail_res.status_code, 200)
        sub_detail = detail_res.get_json().get('subject')
        self.assertEqual(sub_detail['subject_name'], "Software Engineering Principles")

        # 5. Assign Faculty
        assign_res = self.client.post('/api/subjects/TEST101/assign_faculty', json={"faculty_id": "FAC001"})
        self.assertEqual(assign_res.status_code, 200)

        # 6. Edit Subject
        edit_sub = {
            "subject_code": "TEST101",
            "subject_name": "Advanced Software Engineering",
            "department": "Computer Engineering",
            "course_code": "CSE-BTECH",
            "semester": 5,
            "credits": 5,
            "faculty_id": "FAC001"
        }
        edit_res = self.client.put('/api/subjects/TEST101', json=edit_sub)
        self.assertEqual(edit_res.status_code, 200)

        # 7. Delete Subject
        del_res = self.client.delete('/api/subjects/TEST101')
        self.assertEqual(del_res.status_code, 200)

    def test_03_course_crud_flow(self):
        """Test Course Plan CRUD flow"""
        self.login(self.admin_username, self.admin_password)

        # 1. Add Course
        new_course = {
            "course_code": "TEST-BTECH",
            "course_name": "B.Tech Test Technology",
            "department": "Information Technology",
            "duration_years": 4
        }
        add_res = self.client.post('/api/courses', json=new_course)
        self.assertEqual(add_res.status_code, 200)

        # 2. Duplicate Check
        dup_res = self.client.post('/api/courses', json=new_course)
        self.assertEqual(dup_res.status_code, 400)

        # 3. View Course Detail
        detail_res = self.client.get('/api/courses/TEST-BTECH')
        self.assertEqual(detail_res.status_code, 200)
        c_detail = detail_res.get_json().get('course')
        self.assertEqual(c_detail['course_name'], "B.Tech Test Technology")
        cid = c_detail['course_id']

        # 4. Edit Course
        edit_course = {
            "course_code": "TEST-BTECH",
            "course_name": "B.Tech Test Technology Updated",
            "department": "Information Technology",
            "duration_years": 4
        }
        edit_res = self.client.put(f'/api/courses/{cid}', json=edit_course)
        self.assertEqual(edit_res.status_code, 200)

        # 5. Delete Course
        del_res = self.client.delete(f'/api/courses/{cid}')
        self.assertEqual(del_res.status_code, 200)

    def test_04_unauthorized_student_modifications(self):
        """Test that students cannot create or edit subjects or courses"""
        self.login(self.student_username, self.student_password)

        res_sub = self.client.post('/api/subjects', json={
            "subject_code": "TEST102",
            "subject_name": "Hacking",
            "department": "Computer Engineering"
        })
        self.assertEqual(res_sub.status_code, 403)

        res_crs = self.client.post('/api/courses', json={
            "course_code": "HACK-BTECH",
            "course_name": "B.Tech Hacking",
            "department": "Computer Engineering"
        })
        self.assertEqual(res_crs.status_code, 403)

if __name__ == '__main__':
    unittest.main()
