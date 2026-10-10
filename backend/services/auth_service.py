import random
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import backend.config.db_adapter as db_adapter
from backend.config.database import get_db_connection
from backend.config.firebase_config import get_firestore_client

class AuthService:
    @staticmethod
    def authenticate_user(username, password):
        user = db_adapter.get_user_by_username(username)
        if not user:
            return None
            
        if check_password_hash(user['password'], password):
            # Fetch profile pic if student
            if user.get('role') == 'student' and user.get('reference_id'):
                student = db_adapter.get_student_details(user['reference_id'])
                if student:
                    user['profile_pic'] = student.get('profile_pic', '')
                    if not user.get('department'):
                        user['department'] = student.get('department', '')
            elif user.get('role') == 'teacher':
                ref = user.get('reference_id') or user.get('user_id')
                conn = db_adapter.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT department FROM faculty WHERE faculty_id = ? OR user_id = ? OR email = ?", (ref, user.get('user_id'), user.get('email')))
                f_row = cursor.fetchone()
                conn.close()
                if f_row and f_row['department']:
                    user['department'] = f_row['department']
            return user
        return None

    @staticmethod
    def register_student(student_id, name, dob, gender, email, phone, department, course, password):
        try:
            # Check if student ID or email already exists
            s_by_id = db_adapter.get_student_details(student_id)
            if s_by_id:
                return False, "Student ID or Email already registered"
                
            # Check if username exists
            u_by_username = db_adapter.get_user_by_username(student_id)
            if u_by_username:
                return False, "Username already exists"
                
            # Check email uniqueness in students collection/table
            if db_adapter.is_firebase():
                db_fs = get_firestore_client()
                if db_fs:
                    emails = db_fs.collection('students').where('email', '==', email).get()
                    if emails:
                        return False, "Student ID or Email already registered"
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM students WHERE email = ?", (email,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    return False, "Student ID or Email already registered"
                    
            hashed_pw = generate_password_hash(password)
            created_at = datetime.now().strftime('%Y-%m-%d')
            
            # Insert Student
            success, err = db_adapter.add_student(
                student_id, name, dob, gender, email, phone, department, course, created_at
            )
            if not success:
                return False, err
                
            # Insert user record
            success_usr, usr = db_adapter.register_user(
                student_id, hashed_pw, email, 'student', student_id
            )
            if not success_usr:
                return False, usr
                
            # Initialize fee
            db_adapter.create_fee_record(student_id, 1500.0, 'Pending')
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def register_teacher(faculty_id, name, email, phone, department, password):
        try:
            if not faculty_id:
                faculty_id = f"FAC{random.randint(100, 999)}"
                
            u_by_username = db_adapter.get_user_by_username(faculty_id)
            if u_by_username:
                return False, "Username already exists"
                
            hashed_pw = generate_password_hash(password)
            success_usr, usr = db_adapter.register_user(
                faculty_id, hashed_pw, email, 'teacher', faculty_id
            )
            if not success_usr:
                return False, usr
                
            # Save extra fields in users (role teacher)
            user_id = usr.get('user_id')
            db_adapter.update_user_fields(user_id, {
                "name": name,
                "phone": phone,
                "department": department
            })
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def change_password(username, current_pw, new_pw):
        user = db_adapter.get_user_by_username(username)
        if user and check_password_hash(user['password'], current_pw):
            hashed_pw = generate_password_hash(new_pw)
            db_adapter.change_password(username, hashed_pw)
            return True, "Password changed successfully"
            
        return False, "Invalid current password"
