import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestReportsModule11(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        self.admin_username = "admin"
        self.admin_password = "admin123"

        self.teacher_username = "teacher"
        self.teacher_password = "teacher123"

    def login(self, username, password):
        return self.client.post('/api/auth/login', json={
            "username": username,
            "password": password
        })

    def test_01_global_student_search_and_filtering(self):
        """Test global student search and department filtering"""
        self.login(self.admin_username, self.admin_password)

        # 1. Search student by query
        res_search = self.client.get('/api/reports/students?search=STU001')
        self.assertEqual(res_search.status_code, 200)
        data = res_search.get_json()
        self.assertTrue(data.get('success'))
        self.assertGreaterEqual(data['count'], 1)

        # 2. Filter by department
        res_dept = self.client.get('/api/reports/students?department=Computer Science')
        self.assertEqual(res_dept.status_code, 200)
        self.assertTrue(res_dept.get_json().get('success'))

    def test_02_faculty_and_subject_search(self):
        """Test faculty and subject search & filtering endpoints"""
        self.login(self.teacher_username, self.teacher_password)

        # Faculty search
        fac_res = self.client.get('/api/reports/faculty?search=Dr')
        self.assertEqual(fac_res.status_code, 200)
        self.assertTrue(fac_res.get_json().get('success'))

        # Subject filter
        sub_res = self.client.get('/api/reports/subjects?department=Computer Science')
        self.assertEqual(sub_res.status_code, 200)
        self.assertTrue(sub_res.get_json().get('success'))

    def test_03_attendance_and_result_filtering(self):
        """Test attendance and academic result filtering"""
        self.login(self.admin_username, self.admin_password)

        # Attendance filtering
        att_res = self.client.get('/api/reports/attendance?status=Present')
        self.assertEqual(att_res.status_code, 200)
        self.assertTrue(att_res.get_json().get('success'))

        # Marks / Result filtering
        res_marks = self.client.get('/api/reports/results?status=PASS')
        self.assertEqual(res_marks.status_code, 200)
        self.assertTrue(res_marks.get_json().get('success'))

    def test_04_csv_and_pdf_exports(self):
        """Test CSV and PDF export for student, attendance, and result reports"""
        self.login(self.admin_username, self.admin_password)

        # 1. Student List CSV export
        stu_csv = self.client.get('/api/reports/students?export=csv')
        self.assertEqual(stu_csv.status_code, 200)
        self.assertIn('text/csv', stu_csv.content_type)
        self.assertIn(b'student_id,name', stu_csv.data)

        # 2. Student List PDF export
        stu_pdf = self.client.get('/api/reports/students?export=pdf')
        self.assertEqual(stu_pdf.status_code, 200)
        self.assertIn('application/pdf', stu_pdf.content_type)
        self.assertTrue(stu_pdf.data.startswith(b'%PDF-'))

        # 3. Attendance PDF export
        att_pdf = self.client.get('/api/reports/attendance?export=pdf')
        self.assertEqual(att_pdf.status_code, 200)
        self.assertIn('application/pdf', att_pdf.content_type)
        self.assertTrue(att_pdf.data.startswith(b'%PDF-'))

        # 4. Results PDF export
        res_pdf = self.client.get('/api/reports/results?export=pdf')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertIn('application/pdf', res_pdf.content_type)
        self.assertTrue(res_pdf.data.startswith(b'%PDF-'))

if __name__ == '__main__':
    unittest.main()
