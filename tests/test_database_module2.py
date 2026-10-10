import os
import sys
import unittest

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.config.database import init_db, get_db_connection
import backend.config.db_adapter as db_adapter

class TestDatabaseModule2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_users_and_students(self):
        # Read student
        student = db_adapter.get_student_details('STU001')
        self.assertIsNotNone(student, "STU001 should exist in database")
        self.assertEqual(student['name'], 'Alice Johnson')

        # Check user
        user = db_adapter.get_user_by_username('admin')
        self.assertIsNotNone(user, "Admin user should exist")
        self.assertEqual(user['role'], 'admin')

    def test_02_courses_crud(self):
        # Pre-cleanup
        db_adapter.delete_course('TEST-101')
        
        # Insert
        success, msg = db_adapter.add_course('TEST-101', 'Unique Test Engineering Course', 'Computer Engineering', 4)
        self.assertTrue(success, f"Add course failed: {msg}")

        # Duplicate constraint test
        dup_success, dup_msg = db_adapter.add_course('TEST-101', 'Unique Test Engineering Course', 'Computer Engineering', 4)
        self.assertFalse(dup_success, "Duplicate course_code should be rejected")

        # Read
        courses = db_adapter.get_courses('Computer Engineering')
        found = any(c.get('course_code') == 'TEST-101' or c.get('course_name') == 'Unique Test Engineering Course' for c in courses)
        self.assertTrue(found, "Added course should be retrieved")

        # Delete
        del_success, del_msg = db_adapter.delete_course('TEST-101')
        self.assertTrue(del_success, f"Delete course failed: {del_msg}")

    def test_03_subjects_crud(self):
        # Pre-cleanup
        db_adapter.delete_subject('SUB-999')

        # Insert
        success, msg = db_adapter.add_subject('SUB-999', 'Test Subject Algorithms', 'Computer Engineering', 'CSE-BTECH', 3, 4, 'FAC001')
        self.assertTrue(success, f"Add subject failed: {msg}")

        # Read
        subjects = db_adapter.get_subjects('Computer Engineering')
        found = any(s.get('subject_code') == 'SUB-999' or s.get('subject_id') == 'SUB-999' for s in subjects)
        self.assertTrue(found, "Added subject should be retrieved")

        # Delete
        del_success, del_msg = db_adapter.delete_subject('SUB-999')
        self.assertTrue(del_success, f"Delete subject failed: {del_msg}")

    def test_04_announcements_crud(self):
        # Insert
        success, msg = db_adapter.add_announcement('Test Announcement', 'This is a test notification.', 'all', 'All', 'Tester')
        self.assertTrue(success, f"Add announcement failed: {msg}")

        # Read
        announcements = db_adapter.get_announcements('student', 'All')
        found = any(a['title'] == 'Test Announcement' for a in announcements)
        self.assertTrue(found, "Added announcement should be retrieved")

        # Clean up
        if announcements:
            for a in announcements:
                if a['title'] == 'Test Announcement':
                    db_adapter.delete_announcement(a['announcement_id'])

    def test_05_timetable_crud(self):
        # Insert
        success, msg = db_adapter.add_timetable_entry('Computer Engineering', 3, 'Friday', '02:00 PM - 03:00 PM', 'Software Engineering', 'Dr. Sarah Jenkins', 'Room 401')
        self.assertTrue(success, f"Add timetable failed: {msg}")

        # Read
        entries = db_adapter.get_timetable('Computer Engineering', 3)
        found = any(e.get('day_of_week') == 'Friday' and e.get('subject_name') == 'Software Engineering' for e in entries)
        self.assertTrue(found, "Added timetable entry should be retrieved")

        # Clean up
        if entries:
            for e in entries:
                if e.get('subject_name') == 'Software Engineering':
                    db_adapter.delete_timetable_entry(e['timetable_id'])

if __name__ == '__main__':
    unittest.main()
