import unittest
import os
import json
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter
from backend.config.database import init_db

class TestAnnouncementsModule13(unittest.TestCase):
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

        self.student_username = "student"
        self.student_password = "student123"

    def login(self, username, password):
        return self.client.post('/api/auth/login', json={
            "username": username,
            "password": password
        })

    def test_01_create_and_publish_announcement(self):
        """Test Admin and Faculty creating and publishing an announcement"""
        self.login(self.teacher_username, self.teacher_password)

        payload = {
            "title": "Module 13 Workshop Notice",
            "message": "All students are requested to attend the upcoming AI Seminar on Friday.",
            "target_role": "student",
            "department": "Computer Science"
        }
        res = self.client.post('/api/announcements', json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('success'))

    def test_02_student_visibility_and_permissions(self):
        """Test student visibility of announcements and prevention of unauthorized posting/deleting"""
        # 1. Login as student and view announcements
        self.login(self.student_username, self.student_password)

        get_res = self.client.get('/api/announcements')
        self.assertEqual(get_res.status_code, 200)
        announcements = get_res.get_json().get('announcements', [])
        self.assertIsInstance(announcements, list)

        # 2. Student attempts to post announcement -> Should be forbidden (403)
        post_res = self.client.post('/api/announcements', json={
            "title": "Hacked Notice",
            "message": "Unapproved content"
        })
        self.assertEqual(post_res.status_code, 403)

        # 3. Student attempts to delete announcement -> Should be forbidden (403)
        del_res = self.client.delete('/api/announcements/1')
        self.assertEqual(del_res.status_code, 403)

    def test_03_edit_and_delete_announcement(self):
        """Test editing and deleting an announcement by Admin"""
        self.login(self.admin_username, self.admin_password)

        # Create
        create_res = self.client.post('/api/announcements', json={
            "title": "Temporary Exam Alert",
            "message": "Schedule change for Room 102",
            "target_role": "all",
            "department": "All"
        })
        self.assertEqual(create_res.status_code, 200)

        # Get announcements to find ID
        get_res = self.client.get('/api/announcements')
        announcements = get_res.get_json()['announcements']
        target = next((a for a in announcements if a['title'] == "Temporary Exam Alert"), None)
        self.assertIsNotNone(target)
        ann_id = target['announcement_id']

        # Edit
        edit_res = self.client.put(f'/api/announcements/{ann_id}', json={
            "title": "Updated Exam Alert",
            "message": "Schedule change confirmed for Room 204",
            "target_role": "student",
            "department": "All"
        })
        self.assertEqual(edit_res.status_code, 200)
        self.assertTrue(edit_res.get_json().get('success'))

        # Delete
        del_res = self.client.delete(f'/api/announcements/{ann_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.get_json().get('success'))

if __name__ == '__main__':
    unittest.main()
