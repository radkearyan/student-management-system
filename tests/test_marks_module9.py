import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestMarksModule9(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        # Ensure an exam exists for testing
        conn = db_adapter.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT exam_id FROM exams WHERE name = 'Module9 Test Exam'")
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO exams (name, subject, date, max_marks) VALUES ('Module9 Test Exam', 'Computer Networks', '2026-10-15', 100)")
            self.test_exam_id = c.lastrowid
            conn.commit()
        else:
            self.test_exam_id = row['user_id'] if 'user_id' in row.keys() else row[0]

        # Clean up test marks for STU001 & STU002 for this test exam
        c.execute("DELETE FROM marks WHERE exam_id = ?", (self.test_exam_id,))
        conn.commit()
        conn.close()

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

    def test_01_valid_marks_and_grade_calculation(self):
        """Test submitting valid marks and verify percentage, grade (A+), status (PASS)"""
        self.login(self.admin_username, self.admin_password)

        payload = {
            "student_id": "STU001",
            "exam_id": self.test_exam_id,
            "marks_obtained": 95
        }
        res = self.client.post('/api/marks', json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('success'))

        # Check student report card details
        card_res = self.client.get('/api/marks/student/STU001')
        self.assertEqual(card_res.status_code, 200)
        card = card_res.get_json().get('result_card')
        self.assertEqual(card['student_id'], "STU001")
        
        # Verify recorded mark entry
        target = next((m for m in card['marks_records'] if m['exam_id'] == self.test_exam_id), None)
        self.assertIsNotNone(target)
        self.assertEqual(target['marks_obtained'], 95.0)
        self.assertEqual(target['percentage'], 95.0)
        self.assertEqual(target['grade'], 'A+')
        self.assertEqual(target['status'], 'PASS')

    def test_02_boundary_cases(self):
        """Test boundary cases: 0 marks, max marks, negative marks, > max marks, non-numeric"""
        self.login(self.teacher_username, self.teacher_password)

        # 1. Zero Marks (Valid -> Grade F, FAIL status)
        res_zero = self.client.post('/api/marks', json={
            "student_id": "STU002",
            "exam_id": self.test_exam_id,
            "marks_obtained": 0
        })
        self.assertEqual(res_zero.status_code, 200)

        card_zero = self.client.get('/api/marks/student/STU002').get_json().get('result_card')
        target_zero = next((m for m in card_zero['marks_records'] if m['exam_id'] == self.test_exam_id), None)
        self.assertEqual(target_zero['marks_obtained'], 0.0)
        self.assertEqual(target_zero['percentage'], 0.0)
        self.assertEqual(target_zero['grade'], 'F')
        self.assertEqual(target_zero['status'], 'FAIL')

        # 2. Maximum Marks (Valid 100/100 -> Grade A+, PASS status)
        res_max = self.client.post('/api/marks', json={
            "student_id": "STU002",
            "exam_id": self.test_exam_id,
            "marks_obtained": 100
        })
        self.assertEqual(res_max.status_code, 200)

        card_max = self.client.get('/api/marks/student/STU002').get_json().get('result_card')
        target_max = next((m for m in card_max['marks_records'] if m['exam_id'] == self.test_exam_id), None)
        self.assertEqual(target_max['marks_obtained'], 100.0)
        self.assertEqual(target_max['percentage'], 100.0)
        self.assertEqual(target_max['grade'], 'A+')
        self.assertEqual(target_max['status'], 'PASS')

        # 3. Invalid Negative Marks (Should fail with status 400)
        res_neg = self.client.post('/api/marks', json={
            "student_id": "STU001",
            "exam_id": self.test_exam_id,
            "marks_obtained": -15
        })
        self.assertEqual(res_neg.status_code, 400)

        # 4. Invalid Exceeding Max Marks (110 > 100 -> Should fail with status 400)
        res_exc = self.client.post('/api/marks', json={
            "student_id": "STU001",
            "exam_id": self.test_exam_id,
            "marks_obtained": 115
        })
        self.assertEqual(res_exc.status_code, 400)

        # 5. Non-numeric / Missing marks
        res_nan = self.client.post('/api/marks', json={
            "student_id": "STU001",
            "exam_id": self.test_exam_id,
            "marks_obtained": "invalid_text"
        })
        self.assertEqual(res_nan.status_code, 400)

    def test_03_edit_and_delete_marks(self):
        """Test edit and delete marks flow"""
        self.login(self.admin_username, self.admin_password)

        # Add mark
        self.client.post('/api/marks', json={
            "student_id": "STU001",
            "exam_id": self.test_exam_id,
            "marks_obtained": 75
        })

        card = self.client.get('/api/marks/student/STU001').get_json().get('result_card')
        target = next((m for m in card['marks_records'] if m['exam_id'] == self.test_exam_id), None)
        mark_id = target['mark_id']

        # Edit mark
        edit_res = self.client.put(f'/api/marks/{mark_id}', json={
            "marks_obtained": 82,
            "max_marks": 100
        })
        self.assertEqual(edit_res.status_code, 200)

        # Delete mark
        del_res = self.client.delete(f'/api/marks/{mark_id}')
        self.assertEqual(del_res.status_code, 200)

    def test_04_unauthorized_student_submission(self):
        """Test that student role cannot enter marks for anyone"""
        self.login(self.student_username, self.student_password)

        res = self.client.post('/api/marks', json={
            "student_id": "STU001",
            "exam_id": self.test_exam_id,
            "marks_obtained": 100
        })
        self.assertEqual(res.status_code, 403)

    def test_05_batch_marks_submission(self):
        """Test batch marks submission for multiple exams at once"""
        self.login(self.admin_username, self.admin_password)

        payload = {
            "student_id": "STU002",
            "entries": [
                {"exam_id": self.test_exam_id, "marks_obtained": 88}
            ]
        }
        res = self.client.post('/api/marks/batch', json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('success'))

        # Verify STU002 marks recorded correctly
        card_res = self.client.get('/api/marks/student/STU002')
        self.assertEqual(card_res.status_code, 200)
        card = card_res.get_json().get('result_card')
        target = next((m for m in card['marks_records'] if m['exam_id'] == self.test_exam_id), None)
        self.assertIsNotNone(target)
        self.assertEqual(target['marks_obtained'], 88.0)

if __name__ == '__main__':
    unittest.main()
