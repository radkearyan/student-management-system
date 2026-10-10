import os
import firebase_admin
from firebase_admin import credentials, firestore

db = None

def init_firebase():
    global db
    if db is not None:
        return db
        
    cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    
    # Check if cred_path is relative and check in root and backend folders
    if cred_path:
        # Check absolute or relative to project root / backend root
        possible_paths = [
            cred_path,
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', cred_path)),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', cred_path))
        ]
        resolved_path = None
        for path in possible_paths:
            if os.path.exists(path):
                resolved_path = path
                break
                
        if resolved_path:
            try:
                cred = credentials.Certificate(resolved_path)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print(f"Firebase Admin SDK initialized successfully via credentials file: {resolved_path}")
                return db
            except Exception as e:
                print(f"Error initializing Firebase with credentials file: {e}")
                raise e

    # Fallback/local emulator mode or default credentials if available
    if os.environ.get('DATABASE_TYPE') == 'firebase':
        print("WARNING: DATABASE_TYPE is set to 'firebase' but FIREBASE_CREDENTIALS_PATH is not set or file does not exist.")
        print("Please configure FIREBASE_CREDENTIALS_PATH in backend/.env to point to your serviceAccountKey.json.")
    
    # Try default credential initialization
    try:
        firebase_admin.initialize_app()
        db = firestore.client()
        print("Firebase Admin SDK initialized successfully via default credentials.")
        return db
    except Exception:
        print("Could not initialize Firebase Admin SDK. Firestore queries will fail until credentials are provided.")
        return None

def get_firestore_client():
    global db
    if db is None:
        init_firebase()
    return db
