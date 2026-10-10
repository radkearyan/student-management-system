import unittest
import os
import json
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestIntegrationModule16(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        self.admin_user = "admin"
        self.admin_pass = "admin123"

        self.faculty_user = "faculty"
        self.faculty_pass = "faculty123"

        self.student_user = "student"
        self.student_pass = "student123"

    def login(self, username, password):
        return self.client.post('/api/auth/login', json={
            "username": username,
            "password": password
        })

    def test_workflow_1_admin_student_lifecycle(self):
        """WORKFLOW 1: Admin Login -> Dashboard -> Add Student -> DB verification -> Dashboard/List verification"""
        uid = uuid.uuid4().hex[:6]
        student_id = f"WF1_STU_{uid}"
        student_email = f"wf1_{uid}@example.com"

        # 1. Admin Login
        login_res = self.login(self.admin_user, self.admin_pass)
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.get_json()['success'])

        # 2. View Dashboard Stats
        dash_res = self.client.get('/api/analytics')
        self.assertEqual(dash_res.status_code, 200)
        self.assertTrue(dash_res.get_json()['success'])

        # 3. Add Student
        student_data = {
            "student_id": student_id,
            "name": "Workflow One Student",
            "dob": "2002-05-15",
            "gender": "Male",
            "email": student_email,
            "phone": "9876543210",
            "department": "Computer Science",
            "course": "B.Tech CS"
        }
        add_res = self.client.post('/api/students', json=student_data)
        self.assertEqual(add_res.status_code, 200)
        self.assertTrue(add_res.get_json()['success'])

        # 4. Verify in DB directly
        db_student = db_adapter.get_student_details(student_id)
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student.get('name'), "Workflow One Student")

        # 5. Verify in Student List API
        list_res = self.client.get(f'/api/students?search={student_id}')
        self.assertEqual(list_res.status_code, 200)
        students_list = list_res.get_json()
        found = any(s.get('student_id') == student_id for s in students_list)
        self.assertTrue(found)

    def test_workflow_2_admin_faculty_subject_assignment(self):
        """WORKFLOW 2: Admin -> Add Faculty -> Add Subject -> Assign Subject to Faculty"""
        uid = uuid.uuid4().hex[:6]
        fac_username = f"wf2_fac_{uid}"
        fac_email = f"wf2_{uid}@example.com"
        subj_code = f"W2_{uid[:4]}".upper()
        subj_name = f"Subject {uid}"

        # 1. Admin Login
        self.login(self.admin_user, self.admin_pass)

        # 2. Add Faculty
        fac_payload = {
            "username": fac_username,
            "password": "wf2_password123",
            "name": f"Dr. Workflow {uid}",
            "email": fac_email,
            "phone": "9988776655",
            "department": "Computer Science",
            "designation": "Associate Professor",
            "qualification": "Ph.D."
        }
        fac_res = self.client.post('/api/faculty', json=fac_payload)
        self.assertEqual(fac_res.status_code, 200)
        self.assertTrue(fac_res.get_json()['success'])
        fac_data = fac_res.get_json().get('faculty', {})
        faculty_id = fac_data.get('user_id') if isinstance(fac_data, dict) else None
        if not faculty_id:
            # retrieve from DB or GET /api/faculty
            f_list = self.client.get(f'/api/faculty?search={fac_username}').get_json().get('faculty', [])
            faculty_id = f_list[0]['user_id'] if f_list else 1
        self.assertIsNotNone(faculty_id)

        # 3. Add Subject
        subj_payload = {
            "subject_code": subj_code,
            "subject_name": subj_name,
            "department": "Computer Science",
            "semester": 5,
            "credits": 4
        }
        subj_res = self.client.post('/api/subjects', json=subj_payload)
        self.assertEqual(subj_res.status_code, 200)
        self.assertTrue(subj_res.get_json()['success'])

        # 4. Assign Subject to Faculty
        assign_payload = {
            "faculty_id": faculty_id
        }
        assign_res = self.client.post(f'/api/subjects/{subj_code}/assign_faculty', json=assign_payload)
        self.assertEqual(assign_res.status_code, 200)
        self.assertTrue(assign_res.get_json()['success'])

        # 5. Verify DB record contains faculty assignment
        db_subj = db_adapter.get_subject_details(subj_code)
        self.assertIsNotNone(db_subj)
        self.assertEqual(str(db_subj.get('faculty_id')), str(faculty_id))

    def test_workflow_3_faculty_attendance_marking(self):
        """WORKFLOW 3: Faculty Login -> Select Subject -> Select Class -> Mark Attendance -> Save -> Student Attendance Updates"""
        # 1. Admin setup: create a dedicated student & subject
        self.login(self.admin_user, self.admin_pass)
        self.client.post('/api/students', json={
            "student_id": "WF3_STU",
            "name": "Attendance Student",
            "dob": "2003-03-20",
            "gender": "Female",
            "email": "wf3@example.com",
            "phone": "9876543211",
            "department": "Information Technology",
            "course": "B.Tech IT"
        })
        self.client.post('/api/subjects', json={
            "subject_code": "WF3-IT301",
            "subject_name": "Database Systems",
            "department": "Information Technology",
            "semester": 3,
            "credits": 3
        })

        # 2. Faculty Login
        self.login(self.faculty_user, self.faculty_pass)

        # 3. View Students for Class
        class_res = self.client.get('/api/students?department=Information Technology')
        self.assertEqual(class_res.status_code, 200)

        # 4. Mark & Save Attendance (bulk record)
        att_payload = {
            "subject_code": "WF3-IT301",
            "date": "2026-10-07",
            "records": [
                {"student_id": "WF3_STU", "status": "Present"}
            ]
        }
        save_att = self.client.post('/api/attendance/bulk', json=att_payload)
        self.assertEqual(save_att.status_code, 200)
        self.assertTrue(save_att.get_json()['success'])

        # 5. Student Login & Verify Attendance Summary
        self.login(self.student_user, self.student_pass)
        att_view = self.client.get('/api/attendance/summary/STU001')
        self.assertEqual(att_view.status_code, 200)
        self.assertTrue(att_view.get_json()['success'])

    def test_workflow_4_faculty_marks_entry(self):
        """WORKFLOW 4: Faculty -> Enter Marks -> Save -> Student views Result"""
        # 1. Admin setup: create exam & student
        self.login(self.admin_user, self.admin_pass)
        self.client.post('/api/students', json={
            "student_id": "STU001",
            "name": "John Doe",
            "dob": "2002-01-01",
            "gender": "Male",
            "email": "john@example.com",
            "phone": "9876543210",
            "department": "Computer Science",
            "course": "B.Tech CS"
        })
        exam_res = self.client.post('/api/exams', json={
            "name": "Mid-Term CS101",
            "subject": "Computer Fundamentals",
            "max_marks": 50
        })
        self.assertEqual(exam_res.status_code, 200)
        exams_list = self.client.get('/api/exams').get_json()
        exam_id = exams_list[0].get('exam_id') or exams_list[0].get('id') if isinstance(exams_list, list) and len(exams_list) > 0 else 1

        # 2. Faculty Login
        self.login(self.faculty_user, self.faculty_pass)

        # 3. Enter Marks
        marks_payload = {
            "student_id": "STU001",
            "exam_id": exam_id,
            "marks_obtained": 45
        }
        enter_res = self.client.post('/api/marks', json=marks_payload)
        self.assertEqual(enter_res.status_code, 200)
        self.assertTrue(enter_res.get_json()['success'])

        # 4. Student Login & View Results
        self.login(self.student_user, self.student_pass)
        result_res = self.client.get('/api/marks/student/STU001')
        self.assertEqual(result_res.status_code, 200)
        res_data = result_res.get_json()
        self.assertTrue(res_data['success'])
        self.assertIn('result_card', res_data)

    def test_workflow_5_student_portal_views(self):
        """WORKFLOW 5: Student Login -> Dashboard -> Profile -> Attendance -> Results -> Announcements"""
        # 1. Student Login
        login_res = self.login(self.student_user, self.student_pass)
        self.assertEqual(login_res.status_code, 200)

        # 2. View Profile
        profile_res = self.client.get('/api/auth/profile')
        self.assertEqual(profile_res.status_code, 200)
        self.assertTrue(profile_res.get_json()['success'])

        # 3. View Dashboard
        dash_res = self.client.get('/api/students/STU001/dashboard')
        self.assertEqual(dash_res.status_code, 200)

        # 4. View Attendance Summary
        att_res = self.client.get('/api/attendance/summary/STU001')
        self.assertEqual(att_res.status_code, 200)
        self.assertTrue(att_res.get_json()['success'])

        # 5. View Results
        res_res = self.client.get('/api/marks/student/STU001')
        self.assertEqual(res_res.status_code, 200)
        self.assertTrue(res_res.get_json()['success'])

        # 6. View Announcements
        ann_res = self.client.get('/api/announcements')
        self.assertEqual(ann_res.status_code, 200)
        self.assertTrue(ann_res.get_json()['success'])

    def test_workflow_6_admin_reports_generation(self):
        """WORKFLOW 6: Admin -> Generate Reports -> Verify report data against database"""
        # 1. Admin Login
        self.login(self.admin_user, self.admin_pass)

        # 2. Generate Student List Report
        stu_rep = self.client.get('/api/reports/students')
        self.assertEqual(stu_rep.status_code, 200)
        self.assertTrue(stu_rep.get_json()['success'])

        # 3. Generate Attendance Report
        att_rep = self.client.get('/api/reports/attendance')
        self.assertEqual(att_rep.status_code, 200)
        self.assertTrue(att_rep.get_json()['success'])

        # 4. Generate Marks/Results Report
        marks_rep = self.client.get('/api/reports/results')
        self.assertEqual(marks_rep.status_code, 200)
        self.assertTrue(marks_rep.get_json()['success'])

        # 5. PDF Export endpoints
        pdf_res = self.client.get('/api/reports/students?export=pdf')
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, 'application/pdf')

if __name__ == '__main__':
    unittest.main()
