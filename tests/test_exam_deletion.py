import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.services.result_service import ResultService

class TestExamDeletion(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_exam_deletion(self):
        # Create temporary exam
        success, exam_id = ResultService.create_exam("Test Exam Deletion", "Computer Engineering", "2026-10-10", 100)
        self.assertTrue(success)

        # Log in as admin via session
        with self.client.session_transaction() as sess:
            sess['user'] = {'role': 'admin', 'username': 'admin'}

        # Delete the exam
        response = self.client.delete(f'/api/exams/{exam_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('success'))

        # Verify deletion
        exams = ResultService.get_exams()
        exam_ids = [e['exam_id'] for e in exams]
        self.assertNotIn(exam_id, exam_ids)

if __name__ == '__main__':
    unittest.main()
