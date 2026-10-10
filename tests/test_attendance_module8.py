import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestAttendanceModule8(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

        # Clean up test attendance records if left over
        conn = db_adapter.get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM attendance WHERE student_id = 'STU001' AND date = '2026-10-10'")
        c.execute("DELETE FROM attendance WHERE student_id IN ('STU001', 'STU002') AND date = '2026-10-11'")
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

    def test_01_single_and_duplicate_attendance_recording(self):
        """Test single student attendance marking & duplicate prevention update"""
        self.login(self.admin_username, self.admin_password)

        payload = {
            "student_id": "STU001",
            "date": "2026-10-10",
            "status": "Present",
            "subject_code": "CS101"
        }

        # 1. First Insertion
        res1 = self.client.post('/api/attendance', json=payload)
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.get_json().get('success'))

        # 2. Duplicate Marking (Should update existing without creating duplicate entry or crashing)
        payload["status"] = "Absent"
        res2 = self.client.post('/api/attendance', json=payload)
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.get_json().get('success'))
        self.assertIn("updated", res2.get_json().get('message').lower())

        # Verify only one log exists for this date & student
        logs = db_adapter.get_attendance_logs(student_id="STU001", date="2026-10-10", subject_code="CS101")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['status'], "Absent")

    def test_02_bulk_attendance_marking(self):
        """Test bulk class register attendance submission"""
        self.login(self.teacher_username, self.teacher_password)

        bulk_payload = {
            "date": "2026-10-11",
            "subject_code": "CS101",
            "records": [
                {"student_id": "STU001", "status": "Present"},
                {"student_id": "STU002", "status": "Absent"}
            ]
        }

        res = self.client.post('/api/attendance/bulk', json=bulk_payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('success'))

        # Verify both logs were recorded
        logs_11 = db_adapter.get_attendance_logs(date="2026-10-11", subject_code="CS101")
        self.assertTrue(any(l['student_id'] == 'STU001' and l['status'] == 'Present' for l in logs_11))
        self.assertTrue(any(l['student_id'] == 'STU002' and l['status'] == 'Absent' for l in logs_11))

    def test_03_student_attendance_summary_and_low_warning(self):
        """Test student percentage calculation and low-attendance warning banner flag"""
        self.login(self.admin_username, self.admin_password)

        # Fetch attendance summary for STU001
        res = self.client.get('/api/attendance/summary/STU001')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        
        summary = data.get('summary')
        self.assertIn('overall_percentage', summary)
        self.assertIn('low_attendance_warning', summary)
        self.assertIsInstance(summary.get('subject_wise'), list)

        # Verify percentage math: (overall_present / overall_total) * 100
        if summary['overall_total'] > 0:
            expected_pct = round((summary['overall_present'] / summary['overall_total']) * 100, 1)
            self.assertEqual(summary['overall_percentage'], expected_pct)

    def test_04_invalid_and_unauthorized_attendance_submissions(self):
        """Test error handling for missing student ID & unauthorized student posting"""
        self.login(self.admin_username, self.admin_password)

        # Missing student_id
        res_err = self.client.post('/api/attendance', json={"date": "2026-10-10", "status": "Present"})
        self.assertEqual(res_err.status_code, 400)

        # Student user attempting to record attendance
        self.login(self.student_username, self.student_password)
        res_unauth = self.client.post('/api/attendance', json={"student_id": "STU001", "date": "2026-10-10", "status": "Present"})
        self.assertEqual(res_unauth.status_code, 403)

if __name__ == '__main__':
    unittest.main()
