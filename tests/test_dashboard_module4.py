import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config.database import init_db

class TestAdminDashboardModule4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['DATABASE_TYPE'] = 'sqlite'
        init_db()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()
        # Login as Admin
        self.client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})

    def test_01_get_dashboard_analytics_structure(self):
        res = self.client.get('/api/analytics')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        
        # Verify metrics keys
        metrics = data['metrics']
        self.assertIn('total_students', metrics)
        self.assertIn('total_faculty', metrics)
        self.assertIn('total_courses', metrics)
        self.assertIn('total_subjects', metrics)
        self.assertIn('average_attendance', metrics)
        self.assertIn('fees_collected', metrics)
        
        # Verify recent students and announcements
        self.assertIn('recent_students', data)
        self.assertIn('recent_announcements', data)
        self.assertIn('grade_distribution', data)
        self.assertIn('ai_risk_distribution', data)

    def test_02_post_and_get_announcement(self):
        # Post new announcement
        post_res = self.client.post('/api/announcements', json={
            "title": "Module 4 Dashboard Test Announcement",
            "message": "Testing real-time announcement publishing on admin dashboard.",
            "target_role": "all",
            "department": "All"
        })
        self.assertEqual(post_res.status_code, 200)
        post_data = post_res.get_json()
        self.assertTrue(post_data['success'])

        # Fetch announcements
        get_res = self.client.get('/api/announcements')
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.get_json()
        self.assertTrue(get_data['success'])
        
        announcements = get_data['announcements']
        found = any(a['title'] == "Module 4 Dashboard Test Announcement" for a in announcements)
        self.assertTrue(found, "Newly posted announcement should be returned from database")

if __name__ == '__main__':
    unittest.main()
