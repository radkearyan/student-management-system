import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.config import db_adapter

class TestAnnouncementDeletion(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_delete_announcement_api(self):
        # 1. Insert a temporary announcement directly into SQLite to get its integer ID
        conn = db_adapter.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO announcements (title, message, target_role, department, posted_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("Temp Announcement", "To be deleted", "all", "All", "Admin", "2026-10-08")
        )
        ann_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 2. Login as admin via session
        with self.client.session_transaction() as sess:
            sess['user'] = {'role': 'admin', 'username': 'admin'}

        # 3. Call DELETE API endpoint
        res = self.client.delete(f'/api/announcements/{ann_id}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

        # 4. Verify announcement is removed
        announcements = db_adapter.get_announcements()
        found = any(a['announcement_id'] == ann_id for a in announcements)
        self.assertFalse(found)

if __name__ == '__main__':
    unittest.main()
