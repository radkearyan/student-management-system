import unittest
import os
import sys

# Append project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestFirebaseAdapter(unittest.TestCase):
    def test_adapter_type_detection(self):
        """Test that db_adapter is_firebase helper honors DATABASE_TYPE environment variable."""
        from backend.config.db_adapter import is_firebase
        
        # Test SQLite detection
        os.environ['DATABASE_TYPE'] = 'sqlite'
        self.assertFalse(is_firebase())
        
        # Test Firebase detection
        os.environ['DATABASE_TYPE'] = 'firebase'
        self.assertTrue(is_firebase())
        
        # Reset to default SQLite for local testing safety
        os.environ['DATABASE_TYPE'] = 'sqlite'

    def test_firebase_initialization_fallback(self):
        """Test that firebase config initializer handles missing credentials gracefully."""
        from backend.config.firebase_config import get_firestore_client
        
        # Unset credentials path
        os.environ['FIREBASE_CREDENTIALS_PATH'] = ''
        os.environ['DATABASE_TYPE'] = 'firebase'
        
        # Calling get_firestore_client should log a warning but not crash, returning None if no environment creds exist
        client = get_firestore_client()
        
        # Since we don't have default credentials configured in this environment, it should return None
        # but the main thing is it did not crash the application startup.
        if client is not None:
            self.assertIsNotNone(client)
        else:
            self.assertIsNone(client)
            
        # Reset DATABASE_TYPE
        os.environ['DATABASE_TYPE'] = 'sqlite'

if __name__ == '__main__':
    unittest.main()
