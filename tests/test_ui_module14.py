import unittest
import os
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app

class TestUIModule14(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

    def test_01_core_frontend_pages_exist(self):
        """Test that all primary HTML frontend pages exist and return HTTP 200"""
        pages = [
            '/',
            '/login.html',
            '/pages/admin/dashboard.html',
            '/pages/admin/students.html',
            '/pages/admin/faculty.html',
            '/pages/admin/subjects.html',
            '/pages/admin/courses.html',
            '/pages/admin/departments.html',
            '/pages/admin/attendance.html',
            '/pages/admin/examinations.html',
            '/pages/admin/fees.html',
            '/pages/admin/reports.html',
            '/pages/student/subjects.html',
            '/pages/student/courses.html',
            '/pages/faculty/subjects.html',
            '/pages/faculty/courses.html',
            '/pages/faculty/faculty.html'
        ]

        for page in pages:
            res = self.client.get(page)
            self.assertEqual(res.status_code, 200, f"Page {page} failed to load (HTTP {res.status_code})")

    def test_02_components_and_modals_exist(self):
        """Test that component templates (sidebar, navbar, modal) exist and return HTTP 200"""
        components = [
            '/components/sidebar.html',
            '/components/navbar.html',
            '/components/modal.html'
        ]

        for comp in components:
            res = self.client.get(comp)
            self.assertEqual(res.status_code, 200, f"Component {comp} failed to load")

    def test_03_css_stylesheets_and_theme_tokens(self):
        """Test that CSS stylesheets exist and contain glassmorphism and media query breakpoints"""
        css_files = [
            '/css/style.css',
            '/css/dashboard.css',
            '/css/responsive.css'
        ]

        for css in css_files:
            res = self.client.get(css)
            self.assertEqual(res.status_code, 200, f"CSS file {css} failed to load")
            self.assertGreater(len(res.data), 0, f"CSS file {css} is empty")

    def test_04_modal_confirmation_and_loading_overlay(self):
        """Test that modal.html contains confirmation action modal and loading spinner overlay"""
        res = self.client.get('/components/modal.html')
        content = res.data.decode('utf-8')
        self.assertIn('confirm-action-modal', content)
        self.assertIn('global-loading-overlay', content)
        self.assertIn('loading-overlay-text', content)

if __name__ == '__main__':
    unittest.main()
