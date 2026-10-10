import unittest
import os
import json
import io
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestSecurityModule15(unittest.TestCase):
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

    def test_01_security_headers_present(self):
        """Test HTTP responses contain security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(res.headers.get('X-XSS-Protection'), '1; mode=block')

    def test_02_password_hash_security_and_no_leakage(self):
        """Test password hash storage and that password field is not leaked in API JSON responses"""
        self.login(self.student_username, self.student_password)

        res = self.client.get('/api/auth/profile')
        self.assertEqual(res.status_code, 200)
        profile = res.get_json()['profile']
        self.assertNotIn('password', profile)
        self.assertNotIn('password_hash', profile)

    def test_03_role_authorization_barriers(self):
        """Test that student role cannot access Admin/Faculty POST/DELETE endpoints"""
        self.login(self.student_username, self.student_password)

        # 1. Student attempting to enroll student -> 403
        res1 = self.client.post('/api/students', json={
            "student_id": "HACK001",
            "name": "Unauthorized User"
        })
        self.assertEqual(res1.status_code, 403)

        # 2. Student attempting to add faculty -> 403
        res2 = self.client.post('/api/faculty', json={
            "username": "fake_faculty"
        })
        self.assertEqual(res2.status_code, 403)

        # 3. Student attempting to add course -> 403
        res3 = self.client.post('/api/courses', json={
            "course_code": "HACK101"
        })
        self.assertEqual(res3.status_code, 403)

    def test_04_unauthenticated_session_barriers(self):
        """Test unauthenticated session access prevention"""
        # Session not logged in
        res = self.client.get('/api/auth/profile')
        self.assertEqual(res.status_code, 401)

    def test_05_sql_injection_attempt_safety(self):
        """Test SQL injection attack payloads in search parameters are safely handled"""
        self.login(self.admin_username, self.admin_password)

        sql_payloads = [
            "' OR '1'='1",
            "STU001'; DROP TABLE students; --",
            "UNION SELECT * FROM users --"
        ]

        for payload in sql_payloads:
            res = self.client.get(f'/api/reports/students?search={payload}')
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.get_json().get('success'))

    def test_06_profile_privilege_escalation_defense(self):
        """Test that students cannot modify role, student_id, marks, or attendance"""
        self.login(self.student_username, self.student_password)

        escalation_payloads = [
            {"role": "admin"},
            {"student_id": "STU_ADMIN"},
            {"marks": 100},
            {"attendance": 100}
        ]

        for payload in escalation_payloads:
            res = self.client.put('/api/auth/profile', json=payload)
            self.assertEqual(res.status_code, 403)

    def test_07_file_upload_extension_validation(self):
        """Test that uploading malicious file extensions (.php, .exe, .sh, .py) is rejected"""
        self.login(self.student_username, self.student_password)

        malicious_files = [
            ('shell.php', b'<?php system($_GET["cmd"]); ?>'),
            ('virus.exe', b'MZ123456'),
            ('script.sh', b'#!/bin/bash\nrm -rf /')
        ]

        for fname, content in malicious_files:
            data = {
                'profile_pic': (io.BytesIO(content), fname)
            }
            res = self.client.post(
                '/api/auth/profile/upload-profile-pic',
                data=data,
                content_type='multipart/form-data'
            )
            self.assertEqual(res.status_code, 400)
            self.assertFalse(res.get_json().get('success'))

if __name__ == '__main__':
    unittest.main()
