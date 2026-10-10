import os
import sqlite3
import random
from datetime import datetime
from backend.config.database import get_db_connection
from backend.config.firebase_config import get_firestore_client
from backend.utils.helpers import dict_from_row

# Helper to determine if we are using Firebase
def is_firebase():
    return os.environ.get('DATABASE_TYPE') == 'firebase'

# Helper to get sequential integer IDs in Firestore using a counters collection
def get_next_sequence_value(collection_name):
    db_fs = get_firestore_client()
    if not db_fs:
        return random.randint(1000, 9999) # fallback
        
    counter_ref = db_fs.collection('counters').document(collection_name)
    
    try:
        from google.cloud import firestore
    except ImportError:
        return random.randint(1000, 9999)
        
    @firestore.transactional
    def update_in_transaction(transaction):
        snapshot = counter_ref.get(transaction=transaction)
        if snapshot.exists:
            new_count = snapshot.get('count') + 1
            transaction.update(counter_ref, {'count': new_count})
            return new_count
        else:
            transaction.set(counter_ref, {'count': 1})
            return 1
            
    transaction = db_fs.transaction()
    return update_in_transaction(transaction)

# ----------------- DB ADAPTER INTERFACE -----------------

# Users / Auth

def get_user_by_username(username):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
        u_lower = username.lower()
        users = db_fs.collection('users').where('username', '==', u_lower).get()
        if not users:
            users = db_fs.collection('users').where('email', '==', u_lower).get()
        if not users:
            users = db_fs.collection('users').where('reference_id', '==', username.upper()).get()
        if users:
            return users[0].to_dict()
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?) OR (reference_id IS NOT NULL AND LOWER(reference_id) = LOWER(?))", (username, username, username))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def get_user_by_id(user_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
        users = db_fs.collection('users').where('user_id', '==', int(user_id)).get()
        if users:
            return users[0].to_dict()
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def register_user(username, password_hash, email, role, reference_id=None):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        
        # Check if username exists
        users = db_fs.collection('users').where('username', '==', username.lower()).get()
        if users:
            return False, "Username already exists"
            
        user_id = get_next_sequence_value('users')
        user_data = {
            "user_id": user_id,
            "username": username.lower(),
            "password": password_hash,
            "email": email,
            "role": role,
            "reference_id": reference_id,
            "name": "",
            "phone": "",
            "department": "",
            "profile_pic": "",
            "bio": "",
            "skills": "",
            "achievements": "",
            "address": "",
            "blood_group": "",
            "emergency_contact": ""
        }
        db_fs.collection('users').document(str(user_id)).set(user_data)
        return True, user_data
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, role, reference_id) VALUES (?, ?, ?, ?, ?)",
                (username.lower(), password_hash, email, role, reference_id)
            )
            user_id = cursor.lastrowid
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = dict_from_row(cursor.fetchone())
            return True, user
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def update_user_fields(user_id, data):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False
        # Find document
        users = db_fs.collection('users').where('user_id', '==', int(user_id)).get()
        if users:
            users[0].reference.update(data)
            return True
        return False
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            fields = []
            params = []
            for k, v in data.items():
                fields.append(f"{k} = ?")
                params.append(v)
            params.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", params)
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

def change_password(username, hashed_password):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False
        users = db_fs.collection('users').where('username', '==', username.lower()).get()
        if users:
            users[0].reference.update({"password": hashed_password})
            return True
        return False
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
        conn.commit()
        conn.close()
        return True

# Students

def get_students(search_query='', department=''):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        
        students_ref = db_fs.collection('students')
        if department:
            students_ref = students_ref.where('department', '==', department)
            
        docs = students_ref.get()
        students = []
        for doc in docs:
            data = doc.to_dict()
            if search_query:
                sq = search_query.lower()
                name = data.get('name', '').lower()
                sid = data.get('student_id', '').lower()
                if sq not in name and sq not in sid:
                    continue
            students.append(data)
        return students
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM students WHERE 1=1"
        params = []
        if search_query:
            query += " AND (name LIKE ? OR student_id LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        if department:
            query += " AND department = ?"
            params.append(department)
        cursor.execute(query, params)
        students = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return students

def get_student_details(student_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
        doc = db_fs.collection('students').document(student_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def add_student(student_id, name, dob, gender, email, phone, department, course, created_at):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        
        # Check if already exists
        doc = db_fs.collection('students').document(student_id).get()
        if doc.exists:
            return False, "Student ID already exists"
            
        student_data = {
            "student_id": student_id,
            "name": name,
            "dob": dob,
            "gender": gender,
            "email": email,
            "phone": phone,
            "department": department,
            "course": course,
            "current_semester": 1,
            "status": "Active",
            "created_at": created_at,
            "profile_pic": "",
            "bio": "",
            "skills": "",
            "achievements": "",
            "address": "",
            "blood_group": "",
            "emergency_contact": ""
        }
        db_fs.collection('students').document(student_id).set(student_data)
        return True, student_data
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM students WHERE student_id = ? OR email = ?", (student_id, email))
            if cursor.fetchone():
                return False, "Student ID or Email already registered"

            cursor.execute(
                "INSERT INTO students (student_id, name, dob, gender, email, phone, department, course, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (student_id, name, dob, gender, email, phone, department, course, created_at)
            )
            conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "Student ID or Email already registered"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def update_student(student_id, data):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        doc_ref = db_fs.collection('students').document(student_id)
        if doc_ref.get().exists:
            doc_ref.update(data)
            
            # Also update user document if email/name/phone/department updated
            users = db_fs.collection('users').where('reference_id', '==', student_id).get()
            if users:
                user_update = {}
                for field in ['name', 'phone', 'department', 'email', 'profile_pic', 'bio', 'skills', 'achievements', 'address', 'blood_group', 'emergency_contact']:
                    if field in data:
                        user_update[field] = data[field]
                if user_update:
                    users[0].reference.update(user_update)
            return True, "Student updated"
        return False, "Student not found"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            fields = []
            params = []
            for k, v in data.items():
                fields.append(f"{k} = ?")
                params.append(v)
            params.append(student_id)
            cursor.execute(f"UPDATE students SET {', '.join(fields)} WHERE student_id = ?", params)
            
            # Also update the user's fields if they exist in user table
            # Since SQLite database trigger handles user sync, or we can do it manually, let's see
            # (Note: SQLite trigger might auto-sync, but let's sync fields to keep parity)
            cursor.execute("SELECT user_id FROM users WHERE reference_id = ?", (student_id,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row[0]
                user_fields = []
                user_params = []
                # list of columns in users table
                cols = ['name', 'phone', 'department', 'email', 'profile_pic', 'bio', 'skills', 'achievements', 'address', 'blood_group', 'emergency_contact']
                for k, v in data.items():
                    if k in cols:
                        user_fields.append(f"{k} = ?")
                        user_params.append(v)
                if user_fields:
                    user_params.append(user_id)
                    cursor.execute(f"UPDATE users SET {', '.join(user_fields)} WHERE user_id = ?", user_params)
            
            conn.commit()
            return True, "Student updated"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def delete_student(student_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        
        # Delete from students
        db_fs.collection('students').document(student_id).delete()
        
        # Delete from users
        users = db_fs.collection('users').where('reference_id', '==', student_id).get()
        for u in users:
            u.reference.delete()
            
        # Delete from attendance
        att = db_fs.collection('attendance').where('student_id', '==', student_id).get()
        for a in att:
            a.reference.delete()
            
        # Delete from marks
        marks = db_fs.collection('marks').where('student_id', '==', student_id).get()
        for m in marks:
            m.reference.delete()
            
        # Delete from fees
        fees = db_fs.collection('fees').where('student_id', '==', student_id).get()
        for f in fees:
            f.reference.delete()
            
        # Delete from feedback
        fdb = db_fs.collection('feedback').where('student_id', '==', student_id).get()
        for fd in fdb:
            fd.reference.delete()
            
        # Delete from makeup applications
        mka = db_fs.collection('makeup_applications').where('student_id', '==', student_id).get()
        for mk in mka:
            mk.reference.delete()
            
        return True, "Student deleted"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM marks WHERE student_id = ?", (student_id,))
            cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
            cursor.execute("DELETE FROM fees WHERE student_id = ?", (student_id,))
            cursor.execute("DELETE FROM users WHERE reference_id = ?", (student_id,))
            cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            conn.commit()
            return True, "Student deleted"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def get_all_active_students():
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        docs = db_fs.collection('students').where('status', '==', 'Active').get()
        return [d.to_dict() for d in docs]
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, name, department, course FROM students WHERE status='Active'")
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return rows

# Attendance

def get_attendance_logs(student_id='', department='', status='', date='', subject_code=''):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        
        att_ref = db_fs.collection('attendance')
        if student_id:
            docs = att_ref.where('student_id', '==', student_id).get()
            logs = [d.to_dict() for d in docs]
            logs.sort(key=lambda x: x.get('date', ''), reverse=True)
        else:
            docs = att_ref.get()
            logs = [d.to_dict() for d in docs]
            logs.sort(key=lambda x: x.get('date', ''), reverse=True)
            logs = logs[:300]
            
            # Join with student names and departments
            student_cache = {}
            for log in logs:
                sid = log['student_id']
                if sid not in student_cache:
                    s_doc = db_fs.collection('students').document(sid).get()
                    student_cache[sid] = s_doc.to_dict() if s_doc.exists else None
                s = student_cache[sid]
                if s:
                    log['name'] = s.get('name', '')
                    log['department'] = s.get('department', '')
        
        if department:
            logs = [l for l in logs if l.get('department') == department]
        if status:
            logs = [l for l in logs if l.get('status') == status]
        if date:
            logs = [l for l in logs if l.get('date') == date]
        if subject_code:
            logs = [l for l in logs if l.get('subject_code') == subject_code]
        return logs
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            SELECT a.*, s.name, s.department 
            FROM attendance a 
            JOIN students s ON a.student_id = s.student_id 
            WHERE 1=1
        '''
        params = []
        if student_id:
            query += " AND a.student_id = ?"
            params.append(student_id)
        if department:
            query += " AND s.department = ?"
            params.append(department)
        if status:
            query += " AND a.status = ?"
            params.append(status)
        if date:
            query += " AND a.date = ?"
            params.append(date)
        if subject_code:
            query += " AND (a.subject_code = ? OR a.subject_code IS NULL)"
            params.append(subject_code)
        query += " ORDER BY a.date DESC LIMIT 300"
        cursor.execute(query, tuple(params))
        logs = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return logs

def record_attendance(student_id, date_str, status='Present', method='Manual', subject_code='CS101'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        
        s_doc = db_fs.collection('students').document(student_id).get()
        if not s_doc.exists:
            return False, "Student not found"
        student = s_doc.to_dict()
        
        att_query = db_fs.collection('attendance').where('student_id', '==', student_id).where('date', '==', date_str).get()
        if att_query:
            doc_ref = att_query[0].reference
            doc_ref.update({"status": status, "method": method, "subject_code": subject_code})
            msg = f"Attendance updated for {student['name']} on {date_str} to '{status}'."
        else:
            att_id = get_next_sequence_value('attendance')
            att_data = {
                "attendance_id": att_id,
                "student_id": student_id,
                "date": date_str,
                "status": status,
                "method": method,
                "subject_code": subject_code
            }
            db_fs.collection('attendance').document(str(att_id)).set(att_data)
            msg = f"Attendance marked for {student['name']} on {date_str} as '{status}'."
            
        return True, msg
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            conn.close()
            return False, "Student not found"
            
        try:
            if subject_code:
                cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = ? AND date = ? AND (subject_code = ? OR subject_code IS NULL)", (student_id, date_str, subject_code))
            else:
                cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = ? AND date = ?", (student_id, date_str))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE attendance SET status = ?, method = ?, subject_code = ? WHERE attendance_id = ?",
                    (status, method, subject_code, existing['attendance_id'])
                )
                msg = f"Attendance updated for {student['name']} on {date_str} to '{status}'."
            else:
                cursor.execute(
                    "INSERT INTO attendance (student_id, date, status, method, subject_code) VALUES (?, ?, ?, ?, ?)",
                    (student_id, date_str, status, method, subject_code)
                )
                msg = f"Attendance marked for {student['name']} on {date_str} as '{status}'."
            conn.commit()
            return True, msg
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def bulk_record_attendance(records_list, date_str, subject_code='CS101', method='Manual'):
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    try:
        for rec in records_list:
            sid = rec.get('student_id')
            st = rec.get('status', 'Present')
            if not sid:
                continue

            cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = ? AND date = ? AND (subject_code = ? OR subject_code IS NULL)", (sid, date_str, subject_code))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE attendance SET status = ?, method = ?, subject_code = ? WHERE attendance_id = ?",
                    (st, method, subject_code, existing['attendance_id'])
                )
            else:
                cursor.execute(
                    "INSERT INTO attendance (student_id, date, status, method, subject_code) VALUES (?, ?, ?, ?, ?)",
                    (sid, date_str, st, method, subject_code)
                )
            count += 1
        conn.commit()
        return True, f"Attendance successfully saved for {count} student(s)."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_student_attendance_summary(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch student details to get student department
    cursor.execute("SELECT department FROM students WHERE student_id = ?", (student_id,))
    stu_row = cursor.fetchone()
    stu_dept = stu_row['department'] if stu_row else ''

    # 2. Fetch all subjects matching student's department or all subjects as fallback
    all_subjects = []
    if stu_dept:
        cursor.execute("SELECT subject_code, COALESCE(subject_name, subject_code) as subject_name FROM subjects WHERE department = ? OR department IS NULL OR department = 'All' OR department = ''", (stu_dept,))
        all_subjects = cursor.fetchall()
    
    if not all_subjects:
        cursor.execute("SELECT subject_code, COALESCE(subject_name, subject_code) as subject_name FROM subjects")
        all_subjects = cursor.fetchall()

    # 3. Fetch attendance per subject for this student
    cursor.execute("""
        SELECT 
            COALESCE(a.subject_code, 'CS101') as subject_code,
            COALESCE(s.subject_name, 'General Subject') as subject_name,
            COUNT(*) as total,
            SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as present
        FROM attendance a
        LEFT JOIN subjects s ON a.subject_code = s.subject_code
        WHERE a.student_id = ?
        GROUP BY COALESCE(a.subject_code, 'CS101')
    """, (student_id,))
    
    sub_rows = cursor.fetchall()
    conn.close()

    att_map = {}
    for r in sub_rows:
        scode = r['subject_code']
        att_map[scode] = {
            "subject_name": r['subject_name'],
            "total": r['total'] or 0,
            "present": r['present'] or 0
        }

    subject_wise = []
    seen_codes = set()
    total_conducted = 0
    total_present = 0

    # Add all subjects from subjects repository
    for s in all_subjects:
        scode = s['subject_code']
        sname = s['subject_name']
        seen_codes.add(scode)

        att_data = att_map.get(scode, {"subject_name": sname, "total": 0, "present": 0})
        t = att_data["total"]
        p = att_data["present"]
        total_conducted += t
        total_present += p
        pct = round((p / t * 100), 1) if t > 0 else 100.0

        subject_wise.append({
            "subject_code": scode,
            "subject_name": att_data["subject_name"] or sname,
            "total_conducted": t,
            "total_present": p,
            "percentage": pct,
            "low_warning": (pct < 75.0 and t > 0)
        })

    # Add any extra subject codes with attendance logs not in all_subjects
    for scode, att_data in att_map.items():
        if scode not in seen_codes:
            seen_codes.add(scode)
            t = att_data["total"]
            p = att_data["present"]
            total_conducted += t
            total_present += p
            pct = round((p / t * 100), 1) if t > 0 else 100.0

            subject_wise.append({
                "subject_code": scode,
                "subject_name": att_data["subject_name"] or "General Subject",
                "total_conducted": t,
                "total_present": p,
                "percentage": pct,
                "low_warning": (pct < 75.0 and t > 0)
            })

    # Overall Attendance percentage calculation (total present / total conducted across all subjects)
    overall_pct = round((total_present / total_conducted * 100), 1) if total_conducted > 0 else 100.0

    return {
        "student_id": student_id,
        "overall_total": total_conducted,
        "overall_present": total_present,
        "total_conducted": total_conducted,
        "total_present": total_present,
        "overall_percentage": overall_pct,
        "low_attendance_warning": (overall_pct < 75.0 and total_conducted > 0),
        "subject_wise": subject_wise
    }

def get_attendance_stats(student_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return {"total": 0, "present": 0}
        docs = db_fs.collection('attendance').where('student_id', '==', student_id).get()
        total = len(docs)
        present = sum([1 for d in docs if d.get('status') == 'Present'])
        return {"total": total, "present": present}
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total, SUM(case when status='Present' then 1 else 0 end) as present FROM attendance WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        conn.close()
        return {"total": row['total'] or 0, "present": row['present'] or 0}

def get_all_attendance_stats():
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return {"total": 0, "present": 0}
        docs = db_fs.collection('attendance').get()
        total = len(docs)
        present = sum([1 for d in docs if d.get('status') == 'Present'])
        return {"total": total, "present": present}
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(case when status='Present' then 1 else 0 end) FROM attendance")
        row = cursor.fetchone()
        conn.close()
        total = row[0] or 0
        present = row[1] or 0
        return {"total": total, "present": present}


# Exams

def get_exams():
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        docs = db_fs.collection('exams').get()
        exams = [d.to_dict() for d in docs]
        exams.sort(key=lambda x: x.get('date', ''), reverse=True)
        return exams
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exams ORDER BY date DESC")
        exams = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return exams

def create_exam(name, subject, date_str, max_marks):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        
        exam_id = get_next_sequence_value('exams')
        exam_data = {
            "exam_id": exam_id,
            "name": name,
            "subject": subject,
            "date": date_str,
            "max_marks": int(max_marks)
        }
        db_fs.collection('exams').document(str(exam_id)).set(exam_data)
        return True, exam_id
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO exams (name, subject, date, max_marks) VALUES (?, ?, ?, ?)",
                (name, subject, date_str, max_marks)
            )
            exam_id = cursor.lastrowid
            conn.commit()
            return True, exam_id
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def get_exam_details(exam_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
        docs = db_fs.collection('exams').where('exam_id', '==', int(exam_id)).get()
        if docs:
            return docs[0].to_dict()
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exams WHERE exam_id = ?", (exam_id,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def delete_exam(exam_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        docs = db_fs.collection('exams').where('exam_id', '==', int(exam_id)).get()
        for doc in docs:
            doc.reference.delete()
        mark_docs = db_fs.collection('marks').where('exam_id', '==', int(exam_id)).get()
        for md in mark_docs:
            md.reference.delete()
        return True, "Exam deleted successfully"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM marks WHERE exam_id = ?", (exam_id,))
            cursor.execute("DELETE FROM exams WHERE exam_id = ?", (exam_id,))
            conn.commit()
            return True, "Exam deleted successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()


# Marks

def submit_marks(student_id, exam_id, subject, marks_obtained, grade):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
            
        marks_query = db_fs.collection('marks').where('student_id', '==', student_id).where('exam_id', '==', int(exam_id)).get()
        
        if marks_query:
            marks_query[0].reference.update({
                "marks_obtained": float(marks_obtained),
                "grade": grade,
                "subject": subject
            })
        else:
            mark_id = get_next_sequence_value('marks')
            mark_data = {
                "mark_id": mark_id,
                "student_id": student_id,
                "exam_id": int(exam_id),
                "subject": subject,
                "marks_obtained": float(marks_obtained),
                "grade": grade
            }
            db_fs.collection('marks').document(str(mark_id)).set(mark_data)
        return True, "Marks submitted"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT mark_id FROM marks WHERE student_id = ? AND exam_id = ?", (student_id, exam_id))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE marks SET marks_obtained = ?, grade = ? WHERE student_id = ? AND exam_id = ?",
                    (marks_obtained, grade, student_id, exam_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO marks (student_id, exam_id, subject, marks_obtained, grade) VALUES (?, ?, ?, ?, ?)",
                    (student_id, exam_id, subject, marks_obtained, grade)
                )
            conn.commit()
            return True, "Marks submitted successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def update_marks_by_id(mark_id, marks_obtained, grade):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE marks SET marks_obtained = ?, grade = ? WHERE mark_id = ?", (marks_obtained, grade, mark_id))
        conn.commit()
        return True, "Marks record updated successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_marks(mark_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if db_fs:
            db_fs.collection('marks').document(str(mark_id)).delete()
            return True, "Marks deleted"
        return False, "Firebase client not initialized"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM marks WHERE mark_id = ?", (mark_id,))
        conn.commit()
        conn.close()
        return True, "Marks record deleted successfully"

def get_marks_for_student(student_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
            
        marks_docs = db_fs.collection('marks').where('student_id', '==', student_id).get()
        marks = [d.to_dict() for d in marks_docs]
        
        exam_cache = {}
        for m in marks:
            eid = str(m['exam_id'])
            if eid not in exam_cache:
                e_docs = db_fs.collection('exams').where('exam_id', '==', int(eid)).get()
                exam_cache[eid] = e_docs[0].to_dict() if e_docs else None
            e = exam_cache[eid]
            if e:
                m['exam_name'] = e.get('name', '')
                m['date'] = e.get('date', '')
                m['max_marks'] = e.get('max_marks', 100)
        
        marks.sort(key=lambda x: x.get('date', ''))
        return marks
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, e.name as exam_name, e.date, e.max_marks 
            FROM marks m 
            JOIN exams e ON m.exam_id = e.exam_id 
            WHERE m.student_id = ?
            ORDER BY e.date ASC
        ''', (student_id,))
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return rows

def get_student_academic_result_card(student_id):
    student = get_student_details(student_id)
    if not student:
        return None

    marks = get_marks_for_student(student_id)
    
    total_obtained = 0.0
    total_max = 0.0
    processed_marks = []
    any_failed = False

    for m in marks:
        obtained = float(m.get('marks_obtained', 0.0))
        max_m = float(m.get('max_marks', 100.0))
        pct = round((obtained / max_m * 100.0), 1) if max_m > 0 else 0.0
        
        # Pass criteria: >= 40%
        status = 'PASS' if pct >= 40.0 else 'FAIL'
        if status == 'FAIL':
            any_failed = True
            
        total_obtained += obtained
        total_max += max_m

        processed_marks.append({
            "mark_id": m.get('mark_id'),
            "exam_id": m.get('exam_id'),
            "exam_name": m.get('exam_name', 'Examination'),
            "subject": m.get('subject', 'N/A'),
            "marks_obtained": obtained,
            "max_marks": max_m,
            "percentage": pct,
            "grade": m.get('grade', 'F'),
            "status": status,
            "date": m.get('date', '')
        })

    overall_pct = round((total_obtained / total_max * 100.0), 1) if total_max > 0 else 0.0
    
    if overall_pct >= 90: overall_grade = 'A+'
    elif overall_pct >= 80: overall_grade = 'A'
    elif overall_pct >= 70: overall_grade = 'B'
    elif overall_pct >= 60: overall_grade = 'C'
    elif overall_pct >= 40: overall_grade = 'D'
    else: overall_grade = 'F'

    overall_status = 'PASS' if (overall_pct >= 40.0 and not any_failed and len(marks) > 0) else ('FAIL' if len(marks) > 0 else 'N/A')

    return {
        "student_id": student['student_id'],
        "name": student.get('name', ''),
        "email": student.get('email', ''),
        "department": student.get('department', ''),
        "course": student.get('course', ''),
        "semester": student.get('current_semester', 1),
        "total_obtained": total_obtained,
        "total_max": total_max,
        "total_marks": total_obtained,
        "total_max_marks": total_max,
        "overall_percentage": overall_pct,
        "overall_grade": overall_grade,
        "overall_status": overall_status,
        "marks_records": processed_marks
    }


def get_grade_distribution_for_student(student_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return {}
        docs = db_fs.collection('marks').where('student_id', '==', student_id).get()
        dist = {}
        for d in docs:
            g = d.get('grade')
            if g:
                dist[g] = dist.get(g, 0) + 1
        return dist
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT grade, COUNT(*) as count FROM marks WHERE student_id = ? GROUP BY grade", (student_id,))
        dist = {r['grade']: r['count'] for r in cursor.fetchall()}
        conn.close()
        return dist

def get_all_grade_distribution():
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return {}
        docs = db_fs.collection('marks').get()
        dist = {}
        for d in docs:
            g = d.get('grade')
            if g:
                dist[g] = dist.get(g, 0) + 1
        return dist
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT grade, COUNT(*) as count FROM marks GROUP BY grade")
        dist = {r['grade']: r['count'] for r in cursor.fetchall()}
        conn.close()
        return dist

# Fees

def get_fees(student_id='', search='', status=''):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
            
        fees_ref = db_fs.collection('fees')
        if student_id:
            docs = fees_ref.where('student_id', '==', student_id).get()
        else:
            docs = fees_ref.get()
            
        records = [d.to_dict() for d in docs]
        
        # Join with student to get name and department
        student_cache = {}
        for r in records:
            sid = r.get('student_id')
            if sid and sid not in student_cache:
                s_doc = db_fs.collection('students').document(sid).get()
                student_cache[sid] = s_doc.to_dict() if s_doc.exists else None
            s = student_cache.get(sid)
            if s:
                r['name'] = s.get('name', '')
                r['department'] = s.get('department', '')
                r['course'] = s.get('course', '')

        if status and status.lower() != 'all':
            records = [r for r in records if str(r.get('status', '')).lower() == status.lower()]
        if search:
            q = search.lower()
            records = [r for r in records if q in str(r.get('student_id', '')).lower() or q in str(r.get('name', '')).lower() or q in str(r.get('department', '')).lower()]
        return records
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT f.*, s.name, s.department, s.course FROM fees f JOIN students s ON f.student_id = s.student_id WHERE 1=1"
        params = []
        if student_id:
            query += " AND f.student_id = ?"
            params.append(student_id)
        if status and status.lower() != 'all':
            query += " AND LOWER(f.status) = LOWER(?)"
            params.append(status)
        if search:
            query += " AND (f.student_id LIKE ? OR s.name LIKE ? OR s.department LIKE ?)"
            q = f"%{search}%"
            params.extend([q, q, q])

        query += " ORDER BY f.fee_id ASC"
        cursor.execute(query, params)
        records = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return records

def add_fee(student_id, amount, status='Pending'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs: return False, "Firebase not initialized"
        fee_id = get_next_sequence_value('fees')
        db_fs.collection('fees').document(str(fee_id)).set({
            "fee_id": fee_id,
            "student_id": student_id,
            "amount": float(amount),
            "status": status,
            "payment_date": None,
            "txn_id": None
        })
        return True, "Fee statement assigned"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT student_id FROM students WHERE student_id = ?", (student_id,))
            if not cursor.fetchone():
                return False, f"Student '{student_id}' does not exist."
            cursor.execute(
                "INSERT INTO fees (student_id, amount, status) VALUES (?, ?, ?)",
                (student_id, float(amount), status)
            )
            conn.commit()
            return True, "Fee statement added successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def collect_fee_by_id(fee_id, pay_date, txn_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs: return False, "Firebase not initialized"
        doc = db_fs.collection('fees').document(str(fee_id))
        if doc.get().exists:
            doc.update({"status": "Paid", "payment_date": pay_date, "txn_id": txn_id})
            return True, "Fee collected successfully"
        return False, "Fee record not found"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE fees SET status = 'Paid', payment_date = ?, txn_id = ? WHERE fee_id = ?", (pay_date, txn_id, fee_id))
            conn.commit()
            return True, "Fee collected successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def pay_fees(student_id, pay_date, txn_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        fees = db_fs.collection('fees').where('student_id', '==', student_id).get()
        if not fees:
            return False, "Fee record not found for student."
        fee_rec = fees[0].to_dict()
        if fee_rec.get('status') == 'Paid':
            return False, "Fees already paid."
            
        fees[0].reference.update({
            "status": "Paid",
            "payment_date": pay_date,
            "txn_id": txn_id
        })
        return True, None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT fee_id, status FROM fees WHERE student_id = ?", (student_id,))
            fee_rec = cursor.fetchone()
            if not fee_rec:
                return False, "Fee record not found for student."
            if fee_rec['status'] == 'Paid':
                return False, "Fees already paid."
                
            cursor.execute(
                "UPDATE fees SET status = 'Paid', payment_date = ?, txn_id = ? WHERE student_id = ?",
                (pay_date, txn_id, student_id)
            )
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def get_fee_record_by_student(student_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
        fees = db_fs.collection('fees').where('student_id', '==', student_id).get()
        if fees:
            return fees[0].to_dict()
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fees WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def get_fee_receipt(fee_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
            
        # 1. Try direct document lookup by string ID
        doc = db_fs.collection('fees').document(str(fee_id)).get()
        if doc.exists:
            receipt = doc.to_dict()
        else:
            # 2. Query fee_id as string
            fees = db_fs.collection('fees').where('fee_id', '==', str(fee_id)).get()
            if not fees:
                # 3. Query fee_id as integer if numeric
                try:
                    fees = db_fs.collection('fees').where('fee_id', '==', int(fee_id)).get()
                except (ValueError, TypeError):
                    fees = []
            if not fees:
                return None
            receipt = fees[0].to_dict()
        
        # Join student details
        sid = receipt.get('student_id')
        if sid:
            s_doc = db_fs.collection('students').document(sid).get()
            if s_doc.exists:
                s = s_doc.to_dict()
                receipt['name'] = s.get('name', '')
                receipt['department'] = s.get('department', '')
                receipt['course'] = s.get('course', '')
                receipt['current_semester'] = s.get('current_semester', 1)
        return receipt
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, s.name, s.department, s.course, s.current_semester 
            FROM fees f 
            JOIN students s ON f.student_id = s.student_id 
            WHERE f.fee_id = ?
        ''', (fee_id,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def delete_fee(fee_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs: return False, "Firebase not initialized"
        db_fs.collection('fees').document(str(fee_id)).delete()
        return True, "Fee statement deleted successfully"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM fees WHERE fee_id = ?", (fee_id,))
            conn.commit()
            return True, "Fee statement deleted successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def bulk_add_fees(department, amount, status='Pending'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs: return False, "Firebase not initialized"
        students_ref = db_fs.collection('students')
        if department and department.lower() != 'all':
            students = students_ref.where('department', '==', department).get()
        else:
            students = students_ref.get()
        count = 0
        for s in students:
            sid = s.get('student_id')
            if sid:
                f_id = get_next_sequence_value('fees')
                db_fs.collection('fees').document(str(f_id)).set({
                    "fee_id": f_id,
                    "student_id": sid,
                    "amount": float(amount),
                    "status": status,
                    "payment_date": None,
                    "txn_id": None
                })
                count += 1
        return True, f"Fee statement assigned to {count} student(s) successfully"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if department and department.lower() != 'all':
                cursor.execute("SELECT student_id FROM students WHERE department = ?", (department,))
            else:
                cursor.execute("SELECT student_id FROM students")
            students = cursor.fetchall()
            count = 0
            for s in students:
                sid = s['student_id']
                cursor.execute(
                    "INSERT INTO fees (student_id, amount, status) VALUES (?, ?, ?)",
                    (sid, float(amount), status)
                )
                count += 1
            conn.commit()
            return True, f"Fee statement assigned to {count} student(s) successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def get_total_fees_collected_and_pending():
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return {"collected": 0.0, "pending": 0.0}
        docs = db_fs.collection('fees').get()
        collected = 0.0
        pending = 0.0
        for d in docs:
            status = d.get('status')
            amount = float(d.get('amount') or 0.0)
            if status == 'Paid':
                collected += amount
            elif status == 'Pending':
                pending += amount
        return {"collected": collected, "pending": pending}
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM fees WHERE status = 'Paid'")
        collected = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(amount) FROM fees WHERE status = 'Pending'")
        pending = cursor.fetchone()[0] or 0.0
        conn.close()
        return {"collected": collected, "pending": pending}

def create_fee_record(student_id, amount, status):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False
        # check if fee record already exists
        fees = db_fs.collection('fees').where('student_id', '==', student_id).get()
        if not fees:
            fee_id = get_next_sequence_value('fees')
            fee_data = {
                "fee_id": fee_id,
                "student_id": student_id,
                "amount": float(amount),
                "status": status,
                "payment_date": None,
                "txn_id": None
            }
            db_fs.collection('fees').document(str(fee_id)).set(fee_data)
        return True
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fees WHERE student_id = ?", (student_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO fees (student_id, amount, status) VALUES (?, ?, ?)",
                (student_id, amount, status)
            )
            conn.commit()
        conn.close()
        return True

# Feedback

def get_feedback(student_id='', role='student'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
            
        f_ref = db_fs.collection('feedback')
        if role == 'student' and student_id:
            docs = f_ref.where('student_id', '==', student_id).get()
        else:
            docs = f_ref.get()
            
        rows = [d.to_dict() for d in docs]
        rows.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # If admin/teacher, fetch student_name
        if role != 'student':
            student_cache = {}
            for r in rows:
                sid = r['student_id']
                if sid not in student_cache:
                    s_doc = db_fs.collection('students').document(sid).get()
                    student_cache[sid] = s_doc.to_dict() if s_doc.exists else None
                s = student_cache[sid]
                if s:
                    r['student_name'] = s.get('name', '')
        return rows
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        if role == 'student' and student_id:
            cursor.execute("SELECT * FROM feedback WHERE student_id = ? ORDER BY created_at DESC", (student_id,))
        else:
            cursor.execute("SELECT f.*, s.name as student_name FROM feedback f JOIN students s ON f.student_id = s.student_id ORDER BY f.created_at DESC")
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return rows

def submit_feedback(student_id, subject, faculty_name, q1, q2, q3, q4, q5, comments, created_at):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        f_id = get_next_sequence_value('feedback')
        f_data = {
            "feedback_id": f_id,
            "student_id": student_id,
            "subject": subject,
            "faculty_name": faculty_name,
            "q1": int(q1),
            "q2": int(q2),
            "q3": int(q3),
            "q4": int(q4),
            "q5": int(q5),
            "comments": comments,
            "created_at": created_at
        }
        db_fs.collection('feedback').document(str(f_id)).set(f_data)
        return True, None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO feedback (student_id, subject, faculty_name, q1, q2, q3, q4, q5, comments, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, subject, faculty_name, q1, q2, q3, q4, q5, comments, created_at))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

# Makeup Applications

def get_makeup_applications(student_id='', role='student'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
            
        mka_ref = db_fs.collection('makeup_applications')
        if role == 'student' and student_id:
            docs = mka_ref.where('student_id', '==', student_id).get()
        else:
            docs = mka_ref.get()
            
        rows = [d.to_dict() for d in docs]
        rows.sort(key=lambda x: x.get('applied_date', ''), reverse=True)
        
        # Resolve student names for list view
        student_cache = {}
        for r in rows:
            sid = r['student_id']
            if sid not in student_cache:
                s_doc = db_fs.collection('students').document(sid).get()
                student_cache[sid] = s_doc.to_dict() if s_doc.exists else None
            s = student_cache[sid]
            if s:
                r['student_name'] = s.get('name', '')
        return rows
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        if role == 'student' and student_id:
            cursor.execute("SELECT * FROM makeup_applications WHERE student_id = ? ORDER BY applied_date DESC", (student_id,))
        else:
            cursor.execute("SELECT m.*, s.name as student_name FROM makeup_applications m JOIN students s ON m.student_id = s.student_id ORDER BY m.applied_date DESC")
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return rows

def apply_makeup_exam(student_id, subject, exam_name, applied_date):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        app_id = get_next_sequence_value('makeup_applications')
        app_data = {
            "app_id": app_id,
            "student_id": student_id,
            "subject": subject,
            "exam_name": exam_name,
            "status": "Applied",
            "applied_date": applied_date,
            "fee_status": "Pending",
            "txn_id": None
        }
        db_fs.collection('makeup_applications').document(str(app_id)).set(app_data)
        return True, None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO makeup_applications (student_id, subject, exam_name, status, applied_date, fee_status)
                VALUES (?, ?, ?, 'Applied', ?, 'Pending')
            ''', (student_id, subject, exam_name, applied_date))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def pay_makeup_fee(app_id, student_id, txn_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        apps = db_fs.collection('makeup_applications').where('app_id', '==', int(app_id)).where('student_id', '==', student_id).get()
        if apps:
            apps[0].reference.update({
                "fee_status": "Paid",
                "txn_id": txn_id
            })
            return True, None
        return False, "Application not found"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE makeup_applications 
                SET fee_status = 'Paid', txn_id = ? 
                WHERE app_id = ? AND student_id = ?
            ''', (txn_id, app_id, student_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

# Departments

def get_departments():
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        docs = db_fs.collection('departments').get()
        rows = [d.to_dict() for d in docs]
        rows.sort(key=lambda x: x.get('name', ''))
        return rows
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM departments ORDER BY name")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

def add_department(name):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
            
        # Check if already exists
        exists = db_fs.collection('departments').where('name', '==', name).get()
        if exists:
            return False, "Department already exists"
            
        dept_id = get_next_sequence_value('departments')
        dept_data = {
            "dept_id": dept_id,
            "name": name
        }
        db_fs.collection('departments').document(str(dept_id)).set(dept_data)
        return True, None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO departments (name) VALUES (?)", (name,))
            conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "Department already exists"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def delete_department(dept_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        docs = db_fs.collection('departments').where('dept_id', '==', int(dept_id)).get()
        if docs:
            docs[0].reference.delete()
            return True
        return False
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM departments WHERE dept_id = ?", (dept_id,))
        conn.commit()
        conn.close()
        return True

def get_department_by_id(dept_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
        docs = db_fs.collection('departments').where('dept_id', '==', int(dept_id)).get()
        if docs:
            return docs[0].to_dict()
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM departments WHERE dept_id = ?", (dept_id,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def get_department_by_name(name):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return None
        docs = db_fs.collection('departments').where('name', '==', name).get()
        if docs:
            return docs[0].to_dict()
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM departments WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)

def get_student_count_for_department(dept_name):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return 0
        docs = db_fs.collection('students').where('department', '==', dept_name).get()
        return len(docs)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students WHERE department = ?", (dept_name,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

# Faculty Management

def get_faculty_members(department='', search=''):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        ref = db_fs.collection('users').where('role', '==', 'teacher')
        if department:
            ref = ref.where('department', '==', department)
        docs = ref.get()
        res = [d.to_dict() for d in docs]
        if search:
            sq = search.lower()
            res = [f for f in res if sq in f.get('name', '').lower() or sq in f.get('username', '').lower() or sq in f.get('reference_id', '').lower()]
        return res
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT user_id, username, email, role, reference_id, name, phone, department FROM users WHERE role = 'teacher'"
        params = []
        if department:
            query += " AND department = ?"
            params.append(department)
        if search:
            query += " AND (name LIKE ? OR username LIKE ? OR reference_id LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        cursor.execute(query, params)
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        
        # Merge extra details from faculty table if exists
        for r in rows:
            fac_id = r.get('reference_id')
            user_id = r.get('user_id')
            cursor.execute("SELECT designation, qualification, joining_date FROM faculty WHERE (faculty_id IS NOT NULL AND faculty_id = ?) OR (user_id IS NOT NULL AND user_id = ?)", (fac_id or '', user_id))
            f_row = cursor.fetchone()
            if f_row:
                r['designation'] = f_row['designation']
                r['qualification'] = f_row['qualification']
                r['joining_date'] = f_row['joining_date']
        conn.close()
        return rows

def get_faculty_details(user_id_or_ref):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, email, role, reference_id, name, phone, department FROM users WHERE (user_id = ? OR reference_id = ?) AND role = 'teacher'", (user_id_or_ref, str(user_id_or_ref)))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return None
    
    faculty_dict = dict_from_row(user_row)
    fac_id = faculty_dict.get('reference_id')
    user_id = faculty_dict.get('user_id')
    
    cursor.execute("SELECT designation, qualification, joining_date FROM faculty WHERE (faculty_id IS NOT NULL AND faculty_id = ?) OR (user_id IS NOT NULL AND user_id = ?)", (fac_id or '', user_id))
    f_extra = cursor.fetchone()
    if f_extra:
        faculty_dict['designation'] = f_extra['designation']
        faculty_dict['qualification'] = f_extra['qualification']
        faculty_dict['joining_date'] = f_extra['joining_date']
    else:
        faculty_dict['designation'] = 'Assistant Professor'
        faculty_dict['qualification'] = 'M.Tech / Ph.D'
        faculty_dict['joining_date'] = '2024-01-01'

    # Get assigned subjects
    cursor.execute("SELECT * FROM subjects WHERE (faculty_id IS NOT NULL AND faculty_id = ?) OR (faculty_id IS NOT NULL AND faculty_id = ?)", (fac_id or '', str(user_id)))
    faculty_dict['assigned_subjects'] = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return faculty_dict


def add_faculty_member(username, password_hash, email, name, department, phone='', reference_id=None, designation='Assistant Professor', qualification='M.Tech / Ph.D'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        users = db_fs.collection('users').where('username', '==', username.lower()).get()
        if users:
            return False, "Username already exists"
        user_id = get_next_sequence_value('users')
        fac_id = reference_id or f"FAC{user_id:03d}"
        user_data = {
            "user_id": user_id,
            "username": username.lower(),
            "password": password_hash,
            "email": email,
            "role": "teacher",
            "reference_id": fac_id,
            "name": name,
            "phone": phone,
            "department": department
        }
        db_fs.collection('users').document(str(user_id)).set(user_data)
        return True, user_data
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check duplicate username or email
            cursor.execute("SELECT 1 FROM users WHERE username = ? OR email = ?", (username.lower(), email))
            if cursor.fetchone():
                return False, "Username or Email already registered"

            fac_id = reference_id or f"FAC{random.randint(100, 999)}"
            cursor.execute(
                "INSERT INTO users (username, password, email, role, reference_id, name, phone, department) VALUES (?, ?, ?, 'teacher', ?, ?, ?, ?)",
                (username.lower(), password_hash, email, fac_id, name, phone, department)
            )
            user_id = cursor.lastrowid

            created_at = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                "INSERT OR REPLACE INTO faculty (faculty_id, user_id, name, email, phone, department, designation, qualification, joining_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (fac_id, user_id, name, email, phone, department, designation, qualification, created_at, created_at)
            )

            conn.commit()
            cursor.execute("SELECT user_id, username, email, role, reference_id, name, phone, department FROM users WHERE user_id = ?", (user_id,))
            user = dict_from_row(cursor.fetchone())
            return True, user
        except sqlite3.IntegrityError:
            return False, "Username or Email already registered"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def update_faculty_department(user_id, department, name=None, email=None, phone=None, designation=None, qualification=None):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        users = db_fs.collection('users').where('user_id', '==', int(user_id)).get()
        if users:
            update_data = {"department": department}
            if name: update_data["name"] = name
            if email: update_data["email"] = email
            if phone: update_data["phone"] = phone
            users[0].reference.update(update_data)
            return True, "Faculty department updated"
        return False, "Faculty member not found"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            fields = ["department = ?"]
            params = [department]
            if name:
                fields.append("name = ?")
                params.append(name)
            if email:
                fields.append("email = ?")
                params.append(email)
            if phone:
                fields.append("phone = ?")
                params.append(phone)
            params.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ? AND role = 'teacher'", params)

            # Also update faculty table
            cursor.execute("SELECT reference_id FROM users WHERE user_id = ?", (user_id,))
            u_row = cursor.fetchone()
            if u_row and u_row['reference_id']:
                fac_id = u_row['reference_id']
                f_fields = ["department = ?"]
                f_params = [department]
                if name: f_fields.append("name = ?"); f_params.append(name)
                if email: f_fields.append("email = ?"); f_params.append(email)
                if phone: f_fields.append("phone = ?"); f_params.append(phone)
                if designation: f_fields.append("designation = ?"); f_params.append(designation)
                if qualification: f_fields.append("qualification = ?"); f_params.append(qualification)
                f_params.append(fac_id)
                cursor.execute(f"UPDATE faculty SET {', '.join(f_fields)} WHERE faculty_id = ?", f_params)

            conn.commit()
            return True, "Faculty updated successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def delete_faculty_member(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT reference_id FROM users WHERE user_id = ? AND role = 'teacher'", (user_id,))
        u_row = cursor.fetchone()
        if not u_row:
            conn.close()
            return False, "Faculty member not found"

        ref_id = u_row['reference_id']
        cursor.execute("DELETE FROM faculty WHERE faculty_id = ? OR user_id = ?", (ref_id, user_id))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE subjects SET faculty_id = NULL WHERE faculty_id = ?", (ref_id,))
        conn.commit()
        return True, "Faculty member deleted successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def assign_subject_to_faculty(faculty_id, subject_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE subjects SET faculty_id = ? WHERE subject_id = ? OR subject_code = ?", (faculty_id, subject_id, str(subject_id)))
        conn.commit()
        return True, "Subject assigned to faculty successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ----------------- COURSES CRUD -----------------

def get_courses(department='', search=''):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        ref = db_fs.collection('courses')
        if department:
            ref = ref.where('department', '==', department)
        docs = ref.get()
        res = [d.to_dict() for d in docs]
        if search:
            sq = search.lower()
            res = [c for c in res if sq in c.get('course_name', '').lower() or sq in c.get('course_code', '').lower()]
        return res
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM courses WHERE 1=1"
        params = []
        if department:
            query += " AND department = ?"
            params.append(department)
        if search:
            query += " AND (course_name LIKE ? OR course_code LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        cursor.execute(query, params)
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return rows

def get_course_details(course_id_or_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE course_id = ? OR course_code = ? OR course_name = ?", (course_id_or_code, str(course_id_or_code), str(course_id_or_code)))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    c_dict = dict_from_row(row)
    cursor.execute("SELECT * FROM subjects WHERE course_code = ?", (c_dict.get('course_code'),))
    c_dict['subjects'] = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return c_dict

def add_course(course_code, course_name, department, duration_years=4):
    created_at = datetime.now().strftime('%Y-%m-%d')
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        course_id = get_next_sequence_value('courses')
        data = {
            "course_id": course_id,
            "course_code": course_code.upper(),
            "course_name": course_name,
            "department": department,
            "duration_years": int(duration_years),
            "created_at": created_at
        }
        db_fs.collection('courses').document(str(course_id)).set(data)
        return True, data
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM courses WHERE course_code = ? OR course_name = ?", (course_code.upper(), course_name))
            if cursor.fetchone():
                return False, "Course code or course name already exists"
                
            cursor.execute(
                "INSERT INTO courses (course_code, course_name, department, duration_years, created_at) VALUES (?, ?, ?, ?, ?)",
                (course_code.upper(), course_name, department, duration_years, created_at)
            )
            conn.commit()
            return True, "Course added successfully"
        except sqlite3.IntegrityError:
            return False, "Course code or course name already exists"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def update_course(course_id, course_code, course_name, department, duration_years=4):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase not initialized"
        docs = db_fs.collection('courses').where('course_id', '==', int(course_id)).get()
        if docs:
            docs[0].reference.update({
                "course_code": course_code.upper(),
                "course_name": course_name,
                "department": department,
                "duration_years": int(duration_years)
            })
            return True, "Course updated successfully"
        return False, "Course not found"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM courses WHERE (course_code = ? OR course_name = ?) AND course_id != ?",
                (course_code.upper(), course_name, course_id)
            )
            if cursor.fetchone():
                return False, "Course code or course name already exists"
                
            cursor.execute(
                "UPDATE courses SET course_code = ?, course_name = ?, department = ?, duration_years = ? WHERE course_id = ?",
                (course_code.upper(), course_name, department, duration_years, course_id)
            )
            conn.commit()
            return True, "Course updated successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def delete_course(course_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if db_fs:
            db_fs.collection('courses').document(str(course_id)).delete()
            return True, "Course deleted"
        return False, "Firebase client not initialized"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM courses WHERE course_id = ? OR course_code = ? OR course_name = ?", (course_id, str(course_id), str(course_id)))
        conn.commit()
        conn.close()
        return True, "Course deleted successfully"

# ----------------- SUBJECTS CRUD -----------------

def get_subjects(department='', course_code='', search='', semester=None):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        ref = db_fs.collection('subjects')
        if department:
            ref = ref.where('department', '==', department)
        docs = ref.get()
        res = [d.to_dict() for d in docs]
        if search:
            sq = search.lower()
            res = [s for s in res if sq in s.get('subject_name', '').lower() or sq in s.get('subject_code', '').lower()]
        return res
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT s.*, f.name as faculty_name 
            FROM subjects s 
            LEFT JOIN faculty f ON (s.faculty_id = f.faculty_id OR s.faculty_id = CAST(f.user_id AS TEXT))
            WHERE 1=1
        """
        params = []
        if department:
            query += " AND s.department = ?"
            params.append(department)
        if course_code:
            query += " AND s.course_code = ?"
            params.append(course_code)
        if semester:
            query += " AND s.semester = ?"
            params.append(int(semester))
        if search:
            query += " AND (s.subject_name LIKE ? OR s.subject_code LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        cursor.execute(query, params)
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return rows

def get_subject_details(subject_id_or_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, f.name as faculty_name, f.email as faculty_email, f.department as faculty_department
        FROM subjects s 
        LEFT JOIN faculty f ON (s.faculty_id = f.faculty_id OR s.faculty_id = CAST(f.user_id AS TEXT))
        WHERE s.subject_id = ? OR s.subject_code = ? OR s.subject_name = ?
    """, (subject_id_or_code, str(subject_id_or_code), str(subject_id_or_code)))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row) if row else None

def add_subject(subject_code, subject_name, department, course_code='', semester=1, credits=4, faculty_id=None):
    created_at = datetime.now().strftime('%Y-%m-%d')
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        sub_id = get_next_sequence_value('subjects')
        data = {
            "subject_id": sub_id,
            "subject_code": subject_code.upper(),
            "subject_name": subject_name,
            "department": department,
            "course_code": course_code,
            "semester": int(semester),
            "credits": int(credits),
            "faculty_id": faculty_id,
            "created_at": created_at
        }
        db_fs.collection('subjects').document(str(sub_id)).set(data)
        return True, data
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check duplicate subject code
            cursor.execute("SELECT 1 FROM subjects WHERE subject_code = ? OR subject_name = ?", (subject_code.upper(), subject_name))
            if cursor.fetchone():
                return False, f"Subject code '{subject_code.upper()}' or name already exists"

            cursor.execute(
                "INSERT INTO subjects (subject_code, subject_name, department, course_code, semester, credits, faculty_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (subject_code.upper(), subject_name, department, course_code, int(semester), int(credits), faculty_id, created_at)
            )
            conn.commit()
            return True, "Subject added successfully"
        except sqlite3.IntegrityError:
            return False, f"Subject code '{subject_code.upper()}' already exists"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def update_subject(subject_id, subject_code, subject_name, department, course_code='', semester=1, credits=4, faculty_id=None):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        docs = db_fs.collection('subjects').where('subject_id', '==', int(subject_id)).get()
        if docs:
            docs[0].reference.update({
                "subject_code": subject_code.upper(),
                "subject_name": subject_name,
                "department": department,
                "course_code": course_code,
                "semester": int(semester),
                "credits": int(credits),
                "faculty_id": faculty_id
            })
            return True, "Subject updated successfully"
        return False, "Subject not found"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM subjects WHERE (subject_code = ? OR subject_name = ?) AND subject_id != ? AND subject_code != ?",
                (subject_code.upper(), subject_name, subject_id, str(subject_id))
            )
            if cursor.fetchone():
                return False, f"Subject code '{subject_code.upper()}' or name already exists"

            cursor.execute(
                """UPDATE subjects 
                   SET subject_code = ?, subject_name = ?, department = ?, course_code = ?, semester = ?, credits = ?, faculty_id = ? 
                   WHERE subject_id = ? OR subject_code = ?""",
                (subject_code.upper(), subject_name, department, course_code, semester, credits, faculty_id, subject_id, str(subject_id))
            )
            conn.commit()
            return True, "Subject updated successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def delete_subject(subject_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if db_fs:
            db_fs.collection('subjects').document(str(subject_id)).delete()
            return True, "Subject deleted"
        return False, "Firebase client not initialized"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subjects WHERE subject_id = ? OR subject_code = ?", (subject_id, str(subject_id)))
        conn.commit()
        conn.close()
        return True, "Subject deleted successfully"


# ----------------- ANNOUNCEMENTS CRUD -----------------

def get_announcements(target_role='all', department='All'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        docs = db_fs.collection('announcements').get()
        return [d.to_dict() for d in docs]
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM announcements ORDER BY created_at DESC"
        cursor.execute(query)
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        
        filtered = []
        for r in rows:
            role_match = r.get('target_role') in ['all', target_role]
            dept_match = r.get('department') in ['All', department, '']
            if role_match and dept_match:
                filtered.append(r)
        return filtered

def add_announcement(title, message, target_role='all', department='All', posted_by='Admin'):
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        ann_id = get_next_sequence_value('announcements')
        data = {
            "announcement_id": ann_id,
            "title": title,
            "message": message,
            "target_role": target_role,
            "department": department,
            "posted_by": posted_by,
            "created_at": created_at
        }
        db_fs.collection('announcements').document(str(ann_id)).set(data)
        return True, data
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO announcements (title, message, target_role, department, posted_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (title, message, target_role, department, posted_by, created_at)
            )
            conn.commit()
            return True, "Announcement posted successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def delete_announcement(announcement_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if db_fs:
            db_fs.collection('announcements').document(str(announcement_id)).delete()
            return True, "Announcement deleted"
        return False, "Firebase client not initialized"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM announcements WHERE announcement_id = ?", (announcement_id,))
        conn.commit()
        conn.close()
        return True, "Announcement deleted successfully"

def update_announcement(announcement_id, title, message, target_role='all', department='All'):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        db_fs.collection('announcements').document(str(announcement_id)).update({
            "title": title,
            "message": message,
            "target_role": target_role,
            "department": department
        })
        return True, "Announcement updated successfully"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE announcements SET title = ?, message = ?, target_role = ?, department = ? WHERE announcement_id = ?",
                (title, message, target_role, department, announcement_id)
            )
            conn.commit()
            return True, "Announcement updated successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()


# ----------------- TIMETABLE CRUD -----------------

def get_timetable(department='', semester=None):
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return []
        ref = db_fs.collection('timetable')
        if department:
            ref = ref.where('department', '==', department)
        docs = ref.get()
        return [d.to_dict() for d in docs]
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM timetable WHERE 1=1"
        params = []
        if department:
            query += " AND department = ?"
            params.append(department)
        if semester:
            query += " AND semester = ?"
            params.append(semester)
        cursor.execute(query, params)
        rows = [dict_from_row(r) for r in cursor.fetchall()]
        conn.close()
        return rows

def add_timetable_entry(department, semester, day_of_week, time_slot, subject_name, faculty_name, room_number):
    created_at = datetime.now().strftime('%Y-%m-%d')
    if is_firebase():
        db_fs = get_firestore_client()
        if not db_fs:
            return False, "Firebase client not initialized"
        tt_id = get_next_sequence_value('timetable')
        data = {
            "timetable_id": tt_id,
            "department": department,
            "semester": int(semester),
            "day_of_week": day_of_week,
            "time_slot": time_slot,
            "subject_name": subject_name,
            "faculty_name": faculty_name,
            "room_number": room_number,
            "created_at": created_at
        }
        db_fs.collection('timetable').document(str(tt_id)).set(data)
        return True, data
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            class_sec = f"{(department or 'CE')[:3].upper()}-A"
            st_time = time_slot.split(' - ')[0] if ' - ' in time_slot else time_slot
            end_time = time_slot.split(' - ')[1] if ' - ' in time_slot else time_slot
            cursor.execute(
                "INSERT INTO timetable (department, semester, day_of_week, time_slot, subject_name, faculty_name, room_number, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (department, int(semester), day_of_week, time_slot, subject_name, faculty_name, room_number, created_at)
            )
            conn.commit()
            return True, "Timetable entry created"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

def delete_timetable_entry(timetable_id):
    if is_firebase():
        db_fs = get_firestore_client()
        if db_fs:
            db_fs.collection('timetable').document(str(timetable_id)).delete()
            return True, "Timetable entry deleted"
        return False, "Firebase client not initialized"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM timetable WHERE timetable_id = ?", (timetable_id,))
        conn.commit()
        conn.close()
        return True, "Timetable entry deleted successfully"

def get_all_filtered_marks(student_id='', subject='', grade='', status='', department=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            m.mark_id,
            m.student_id,
            COALESCE(st.name, m.student_id) as name,
            COALESCE(st.department, 'General') as department,
            COALESCE(e.name, 'Semester Exam') as exam_name,
            COALESCE(e.subject, 'General Subject') as subject,
            m.marks_obtained,
            COALESCE(e.max_marks, 100) as max_marks,
            m.grade
        FROM marks m
        LEFT JOIN exams e ON m.exam_id = e.exam_id
        LEFT JOIN students st ON m.student_id = st.student_id
        WHERE 1=1
    """
    params = []
    if student_id:
        query += " AND (m.student_id LIKE ? OR st.name LIKE ?)"
        params.extend([f"%{student_id}%", f"%{student_id}%"])
    if subject:
        query += " AND (e.subject LIKE ? OR e.name LIKE ?)"
        params.extend([f"%{subject}%", f"%{subject}%"])
    if grade:
        query += " AND m.grade = ?"
        params.append(grade)
    if department:
        query += " AND st.department LIKE ?"
        params.append(f"%{department}%")

    query += " ORDER BY m.mark_id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        obt = float(r['marks_obtained'] or 0)
        mx = float(r['max_marks'] or 100)
        pct = round((obt / mx * 100), 1) if mx > 0 else 0.0
        st_val = 'PASS' if pct >= 40.0 else 'FAIL'
        
        if status and st_val.upper() != status.upper():
            continue

        calc_grade = r['grade']
        if not calc_grade or calc_grade == 'N/A':
            if pct >= 90: calc_grade = 'A+'
            elif pct >= 80: calc_grade = 'A'
            elif pct >= 70: calc_grade = 'B'
            elif pct >= 60: calc_grade = 'C'
            elif pct >= 40: calc_grade = 'D'
            else: calc_grade = 'F'

        results.append({
            "mark_id": r['mark_id'],
            "student_id": r['student_id'],
            "name": r['name'],
            "department": r['department'],
            "exam_name": r['exam_name'],
            "subject": r['subject'],
            "marks_obtained": obt,
            "max_marks": mx,
            "percentage": pct,
            "grade": calc_grade,
            "status": st_val
        })
    return results

def get_dashboard_analytics_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Students by branch / department
    cursor.execute("SELECT COALESCE(department, 'General') as branch, COUNT(*) as count FROM students GROUP BY COALESCE(department, 'General')")
    branch_rows = cursor.fetchall()
    students_by_branch = {r['branch']: r['count'] for r in branch_rows}

    # 2. Students by year (1st Year, 2nd Year, 3rd Year, 4th Year based on current_semester)
    cursor.execute("""
        SELECT 
            CASE 
                WHEN current_semester IN (1, 2) THEN '1st Year'
                WHEN current_semester IN (3, 4) THEN '2nd Year'
                WHEN current_semester IN (5, 6) THEN '3rd Year'
                WHEN current_semester IN (7, 8) THEN '4th Year'
                ELSE '1st Year'
            END as year_group,
            COUNT(*) as count
        FROM students
        GROUP BY year_group
    """)
    year_rows = cursor.fetchall()
    students_by_year = {r['year_group']: r['count'] for r in year_rows}

    # 3. Attendance distribution (Brackets: >=85%, 75-84%, <75%)
    cursor.execute("""
        SELECT student_id,
               COUNT(*) as total,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present
        FROM attendance
        GROUP BY student_id
    """)
    att_rows = cursor.fetchall()
    att_dist = {"Above 85%": 0, "75% - 85%": 0, "Below 75%": 0}
    for r in att_rows:
        t = r['total'] or 0
        p = r['present'] or 0
        pct = (p / t * 100) if t > 0 else 100.0
        if pct >= 85.0:
            att_dist["Above 85%"] += 1
        elif pct >= 75.0:
            att_dist["75% - 85%"] += 1
        else:
            att_dist["Below 75%"] += 1

    # 4. Subject performance (Average percentage per subject)
    cursor.execute("""
        SELECT 
            COALESCE(e.subject, 'Core Subject') as subject,
            AVG((m.marks_obtained * 100.0) / COALESCE(e.max_marks, 100)) as avg_score
        FROM marks m
        LEFT JOIN exams e ON m.exam_id = e.exam_id
        GROUP BY COALESCE(e.subject, 'Core Subject')
    """)
    sub_rows = cursor.fetchall()
    subject_performance = {r['subject']: round(r['avg_score'] or 0, 1) for r in sub_rows}

    # 5. Pass/Fail distribution
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN (m.marks_obtained * 100.0 / COALESCE(e.max_marks, 100)) >= 40.0 THEN 1 ELSE 0 END) as pass_count,
            SUM(CASE WHEN (m.marks_obtained * 100.0 / COALESCE(e.max_marks, 100)) < 40.0 THEN 1 ELSE 0 END) as fail_count
        FROM marks m
        LEFT JOIN exams e ON m.exam_id = e.exam_id
    """)
    pf_row = cursor.fetchone()
    pass_count = pf_row['pass_count'] or 0 if pf_row else 0
    fail_count = pf_row['fail_count'] or 0 if pf_row else 0
    pass_fail_distribution = {"Pass": pass_count, "Fail": fail_count}

    conn.close()

    return {
        "students_by_branch": students_by_branch,
        "students_by_year": students_by_year,
        "attendance_distribution": att_dist,
        "subject_performance": subject_performance,
        "pass_fail_distribution": pass_fail_distribution
    }

def get_recent_activities(limit=10):
    activities = []
    if is_firebase():
        return activities
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Recent Student Enrollments
        cursor.execute("SELECT student_id, name, department, created_at FROM students ORDER BY created_at DESC LIMIT 3")
        for r in cursor.fetchall():
            activities.append({
                "type": "student",
                "icon": "fa-user-plus",
                "title": f"New Student Enrolled: {r['name']}",
                "description": f"ID: {r['student_id']} - Dept: {r['department'] or 'General'}",
                "timestamp": r['created_at'] or "Recently",
                "user": "Registrar"
            })
            
        # 2. Recent Announcements
        cursor.execute("SELECT title, posted_by, created_at FROM announcements ORDER BY created_at DESC LIMIT 3")
        for r in cursor.fetchall():
            activities.append({
                "type": "announcement",
                "icon": "fa-bullhorn",
                "title": f"Announcement Published: {r['title']}",
                "description": f"Posted by {r['posted_by'] or 'Admin'}",
                "timestamp": (r['created_at'] or '')[:16],
                "user": r['posted_by'] or 'Admin'
            })
            
        # 3. Recent Attendance Logs
        cursor.execute("SELECT student_id, status, date, subject_code FROM attendance ORDER BY date DESC, attendance_id DESC LIMIT 3")
        for r in cursor.fetchall():
            activities.append({
                "type": "attendance",
                "icon": "fa-calendar-check",
                "title": f"Attendance Recorded for {r['student_id']}",
                "description": f"Subject: {r['subject_code']} - Status: {r['status']}",
                "timestamp": r['date'] or "Today",
                "user": "Faculty"
            })
    except Exception as e:
        print(f"Error fetching recent activities: {e}")
    finally:
        conn.close()

    return activities[:limit]

def search_all(query):
    query_str = f"%{query}%"
    results = {
        "students": [],
        "faculty": [],
        "subjects": [],
        "announcements": []
    }
    if not query or len(query.strip()) < 1:
        return results

    if is_firebase():
        return results

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Students
        cursor.execute("""
            SELECT student_id, name, department, course, email 
            FROM students 
            WHERE student_id LIKE ? OR name LIKE ? OR department LIKE ?
            LIMIT 5
        """, (query_str, query_str, query_str))
        results["students"] = [dict_from_row(r) for r in cursor.fetchall()]

        # 2. Faculty
        cursor.execute("""
            SELECT user_id, name, department, email, reference_id 
            FROM users 
            WHERE role='teacher' AND (name LIKE ? OR department LIKE ? OR email LIKE ?)
            LIMIT 5
        """, (query_str, query_str, query_str))
        results["faculty"] = [dict_from_row(r) for r in cursor.fetchall()]

        # 3. Subjects
        cursor.execute("""
            SELECT subject_code, subject_name, department 
            FROM subjects 
            WHERE subject_code LIKE ? OR subject_name LIKE ? OR department LIKE ?
            LIMIT 5
        """, (query_str, query_str, query_str))
        results["subjects"] = [dict_from_row(r) for r in cursor.fetchall()]

        # 4. Announcements
        cursor.execute("""
            SELECT announcement_id, title, message, created_at 
            FROM announcements 
            WHERE title LIKE ? OR message LIKE ?
            LIMIT 5
        """, (query_str, query_str))
        results["announcements"] = [dict_from_row(r) for r in cursor.fetchall()]

    except Exception as e:
        print(f"Error in search_all: {e}")
    finally:
        conn.close()

    return results






