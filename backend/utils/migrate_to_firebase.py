import os
import sys
import sqlite3

# Adjust python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
load_dotenv()

# Force database type to firebase for adapter initialization test if needed
# but we read directly from sqlite3 here and write to firestore client
from backend.config.database import get_db_connection
from backend.config.firebase_config import get_firestore_client

def migrate():
    print("Starting migration from SQLite to Firestore...")
    
    db_fs = get_firestore_client()
    if not db_fs:
        print("CRITICAL ERROR: Could not connect to Firebase. Please check your credentials file config.")
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define tables to migrate, their primary key fields (for Firestore document ID), and target collections
    tables = [
        {"name": "users", "pk": "user_id"},
        {"name": "students", "pk": "student_id"},
        {"name": "attendance", "pk": "attendance_id"},
        {"name": "exams", "pk": "exam_id"},
        {"name": "marks", "pk": "mark_id"},
        {"name": "fees", "pk": "fee_id"},
        {"name": "feedback", "pk": "feedback_id"},
        {"name": "makeup_applications", "pk": "app_id"},
        {"name": "departments", "pk": "dept_id"}
    ]
    
    for t in tables:
        t_name = t["name"]
        t_pk = t["pk"]
        
        print(f"\nMigrating table '{t_name}'...")
        
        try:
            cursor.execute(f"SELECT * FROM {t_name}")
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Table '{t_name}' does not exist or error: {e}. Skipping.")
            continue
            
        print(f"Found {len(rows)} records in SQLite table '{t_name}'.")
        
        max_id = 0
        
        for row in rows:
            data = dict(row)
            pk_val = str(data[t_pk])
            
            # If the primary key is an integer, keep track of maximum value for counter
            if isinstance(data[t_pk], int):
                max_id = max(max_id, data[t_pk])
            
            # Set document in Firestore
            doc_ref = db_fs.collection(t_name).document(pk_val)
            doc_ref.set(data)
            
        print(f"Uploaded {len(rows)} records to Firestore collection '{t_name}'.")
        
        # If we tracked integer IDs, initialize or update the sequential counter document in Firestore
        if max_id > 0:
            print(f"Setting sequence counter for '{t_name}' to: {max_id}")
            db_fs.collection('counters').document(t_name).set({"count": max_id})
            
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == '__main__':
    migrate()
