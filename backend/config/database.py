import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'student_system.db'))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA cache_size=-64000;") # 64MB cache
        conn.execute("PRAGMA mmap_size=268435456;") # 256MB memory map
        conn.execute("PRAGMA threads=4;") # Multi-threaded query processing
    except Exception:
        pass
    return conn

def create_indexes(cursor):
    """Ensure B-tree indexes exist on all high-traffic columns for sub-millisecond queries."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
        "CREATE INDEX IF NOT EXISTS idx_users_ref ON users(reference_id);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department);",
        "CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);",
        "CREATE INDEX IF NOT EXISTS idx_students_course ON students(course);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);",
        "CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_marks_exam ON marks(exam_id);",
        "CREATE INDEX IF NOT EXISTS idx_marks_student_exam ON marks(student_id, exam_id);",
        "CREATE INDEX IF NOT EXISTS idx_fees_student ON fees(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_fees_status ON fees(status);",
        "CREATE INDEX IF NOT EXISTS idx_exams_subject ON exams(subject);",
        "CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(date);",
        "CREATE INDEX IF NOT EXISTS idx_faculty_user ON faculty(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_faculty_dept ON faculty(department);",
        "CREATE INDEX IF NOT EXISTS idx_faculty_fac_id ON faculty(faculty_id);",
        "CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(subject_code);",
        "CREATE INDEX IF NOT EXISTS idx_subjects_dept ON subjects(department);",
        "CREATE INDEX IF NOT EXISTS idx_timetable_lookup ON timetable(department, semester, day_of_week);",
        "CREATE INDEX IF NOT EXISTS idx_feedback_student ON feedback(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_announcements_filter ON announcements(target_role, department);"
    ]
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except Exception:
            pass

def init_db():
    if os.environ.get('DATABASE_TYPE') == 'firebase':
        from backend.config.firebase_config import init_firebase
        init_firebase()
        print("Firebase database initialization check completed.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Read and execute schema
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'schema.sql'))
    with open(schema_path, 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())
        
    # Check/Migrate columns in users table
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [row['name'] for row in cursor.fetchall()]
    new_cols = ['name', 'phone', 'department', 'profile_pic', 'bio', 'skills', 'achievements', 'address', 'blood_group', 'emergency_contact']
    for col in new_cols:
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")

    # Migrate columns in courses table
    cursor.execute("PRAGMA table_info(courses)")
    cols = [r['name'] for r in cursor.fetchall()]
    if 'course_code' not in cols: cursor.execute("ALTER TABLE courses ADD COLUMN course_code TEXT")
    if 'course_name' not in cols: cursor.execute("ALTER TABLE courses ADD COLUMN course_name TEXT")
    if 'department' not in cols: cursor.execute("ALTER TABLE courses ADD COLUMN department TEXT")
    if 'duration_years' not in cols: cursor.execute("ALTER TABLE courses ADD COLUMN duration_years INTEGER DEFAULT 4")
    if 'created_at' not in cols: cursor.execute("ALTER TABLE courses ADD COLUMN created_at TEXT")
    if 'name' in cols:
        cursor.execute("UPDATE courses SET course_name = name WHERE course_name IS NULL AND name IS NOT NULL")
        cursor.execute("UPDATE courses SET course_code = 'CSE-BTECH' WHERE course_code IS NULL AND (name LIKE '%Computer%' OR course_name LIKE '%Computer%')")
        cursor.execute("UPDATE courses SET course_code = 'IT-BTECH' WHERE course_code IS NULL AND (name LIKE '%Information%' OR course_name LIKE '%Information%')")
        cursor.execute("UPDATE courses SET course_code = 'EE-BTECH' WHERE course_code IS NULL AND (name LIKE '%Electrical%' OR course_name LIKE '%Electrical%')")
        cursor.execute("UPDATE courses SET course_code = 'ME-BTECH' WHERE course_code IS NULL AND (name LIKE '%Mechanical%' OR course_name LIKE '%Mechanical%')")
    cursor.execute("UPDATE courses SET course_code = 'CRS-' || course_id WHERE course_code IS NULL")
    cursor.execute("UPDATE courses SET department = 'Computer Engineering' WHERE department IS NULL AND course_code LIKE '%CSE%'")
    cursor.execute("UPDATE courses SET department = 'Information Technology' WHERE department IS NULL AND course_code LIKE '%IT%'")
    cursor.execute("UPDATE courses SET department = 'Electrical Engineering' WHERE department IS NULL AND course_code LIKE '%EE%'")
    cursor.execute("UPDATE courses SET department = 'Mechanical Engineering' WHERE department IS NULL AND course_code LIKE '%ME%'")
    cursor.execute("UPDATE courses SET department = 'Computer Engineering' WHERE department IS NULL")

    # Migrate columns in subjects table
    cursor.execute("PRAGMA table_info(subjects)")
    cols = [r['name'] for r in cursor.fetchall()]
    if 'subject_code' not in cols: cursor.execute("ALTER TABLE subjects ADD COLUMN subject_code TEXT")
    if 'subject_name' not in cols: cursor.execute("ALTER TABLE subjects ADD COLUMN subject_name TEXT")
    if 'department' not in cols: cursor.execute("ALTER TABLE subjects ADD COLUMN department TEXT")
    if 'course_code' not in cols: cursor.execute("ALTER TABLE subjects ADD COLUMN course_code TEXT")
    if 'credits' not in cols: cursor.execute("ALTER TABLE subjects ADD COLUMN credits INTEGER DEFAULT 4")
    if 'created_at' not in cols: cursor.execute("ALTER TABLE subjects ADD COLUMN created_at TEXT")
    if 'name' in cols:
        cursor.execute("UPDATE subjects SET subject_name = name WHERE subject_name IS NULL AND name IS NOT NULL")
    cursor.execute("UPDATE subjects SET subject_code = subject_id WHERE subject_code IS NULL AND subject_id IS NOT NULL")
    cursor.execute("UPDATE subjects SET department = 'Computer Engineering' WHERE department IS NULL")

    # Migrate columns in timetable table
    cursor.execute("PRAGMA table_info(timetable)")
    cols = [r['name'] for r in cursor.fetchall()]
    if 'department' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN department TEXT")
    if 'semester' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN semester INTEGER DEFAULT 3")
    if 'day_of_week' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN day_of_week TEXT")
    if 'time_slot' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN time_slot TEXT")
    if 'subject_name' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN subject_name TEXT")
    if 'faculty_name' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN faculty_name TEXT")
    if 'room_number' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN room_number TEXT")
    if 'created_at' not in cols: cursor.execute("ALTER TABLE timetable ADD COLUMN created_at TEXT")
    cursor.execute("UPDATE timetable SET department = 'Computer Engineering' WHERE department IS NULL")
    if 'day' in cols:
        cursor.execute("UPDATE timetable SET day_of_week = day WHERE day_of_week IS NULL AND day IS NOT NULL")
    if 'start_time' in cols and 'end_time' in cols:
        cursor.execute("UPDATE timetable SET time_slot = start_time || ' - ' || end_time WHERE time_slot IS NULL AND start_time IS NOT NULL")
    if 'classroom' in cols:
        cursor.execute("UPDATE timetable SET room_number = classroom WHERE room_number IS NULL AND classroom IS NOT NULL")
    if 'subject_id' in cols:
        cursor.execute("UPDATE timetable SET subject_name = subject_id WHERE subject_name IS NULL AND subject_id IS NOT NULL")
    if 'faculty_id' in cols:
        cursor.execute("UPDATE timetable SET faculty_name = faculty_id WHERE faculty_name IS NULL AND faculty_id IS NOT NULL")

    # Migrate columns in faculty table
    cursor.execute("PRAGMA table_info(faculty)")
    f_cols = [r['name'] for r in cursor.fetchall()]
    if 'user_id' not in f_cols: cursor.execute("ALTER TABLE faculty ADD COLUMN user_id INTEGER")
    if 'designation' not in f_cols: cursor.execute("ALTER TABLE faculty ADD COLUMN designation TEXT DEFAULT 'Assistant Professor'")
    if 'qualification' not in f_cols: cursor.execute("ALTER TABLE faculty ADD COLUMN qualification TEXT DEFAULT 'M.Tech / Ph.D'")
    if 'joining_date' not in f_cols: cursor.execute("ALTER TABLE faculty ADD COLUMN joining_date TEXT")
    if 'created_at' not in f_cols: cursor.execute("ALTER TABLE faculty ADD COLUMN created_at TEXT")

    # Migrate columns in attendance table
    cursor.execute("PRAGMA table_info(attendance)")
    att_cols = [r['name'] for r in cursor.fetchall()]
    if 'subject_code' not in att_cols: cursor.execute("ALTER TABLE attendance ADD COLUMN subject_code TEXT")
    cursor.execute("UPDATE attendance SET subject_code = 'CS101' WHERE subject_code IS NULL")



        
    # Check if database has users to determine if seeding is needed
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    if user_count < 8:
        print("Seeding database...")
        # 2. Read and execute seed
        seed_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'seed.sql'))
        with open(seed_path, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
            
        # 3. Read and execute triggers
        triggers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'triggers.sql'))
        if os.path.exists(triggers_path):
            with open(triggers_path, 'r', encoding='utf-8') as f:
                cursor.executescript(f.read())
                
        # 4. Read and execute procedures (views)
        procedures_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'procedures.sql'))
        if os.path.exists(procedures_path):
            with open(procedures_path, 'r', encoding='utf-8') as f:
                cursor.executescript(f.read())
                
        print("Database initialized and seeded successfully.")
    else:
        print("Database already contains core users. Checking entity table seeds...")
        
    # Check individual tables and seed if empty
    cursor.execute("SELECT COUNT(*) FROM courses")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO courses (course_code, course_name, department, duration_years, created_at) VALUES ('CSE-BTECH', 'B.Tech Computer Engineering', 'Computer Engineering', 4, '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO courses (course_code, course_name, department, duration_years, created_at) VALUES ('IT-BTECH', 'B.Tech Information Technology', 'Information Technology', 4, '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO courses (course_code, course_name, department, duration_years, created_at) VALUES ('EE-BTECH', 'B.Tech Electrical Engineering', 'Electrical Engineering', 4, '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO courses (course_code, course_name, department, duration_years, created_at) VALUES ('ME-BTECH', 'B.Tech Mechanical Engineering', 'Mechanical Engineering', 4, '2025-01-01')")

    cursor.execute("SELECT COUNT(*) FROM faculty")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO faculty (faculty_id, user_id, name, email, phone, department, designation, qualification, joining_date, created_at) VALUES ('FAC001', 2, 'Dr. Sarah Jenkins', 'teacher@example.com', '+919876543210', 'Computer Engineering', 'Professor', 'Ph.D in Computer Science', '2020-08-15', '2025-01-10')")
        cursor.execute("INSERT OR REPLACE INTO faculty (faculty_id, user_id, name, email, phone, department, designation, qualification, joining_date, created_at) VALUES ('FAC002', NULL, 'Prof. Robert Vance', 'robert.vance@example.com', '+919876543211', 'Information Technology', 'Associate Professor', 'M.Tech in IT', '2021-06-20', '2025-01-10')")
        cursor.execute("INSERT OR REPLACE INTO faculty (faculty_id, user_id, name, email, phone, department, designation, qualification, joining_date, created_at) VALUES ('FAC003', NULL, 'Dr. Alan Turing', 'alan.turing@example.com', '+919876543212', 'Electrical Engineering', 'Professor', 'Ph.D in Electrical Engg', '2019-03-01', '2025-01-10')")

    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO subjects (subject_code, subject_name, department, course_code, semester, credits, faculty_id, created_at) VALUES ('CS101', 'Advanced Data Structures', 'Computer Engineering', 'CSE-BTECH', 3, 4, 'FAC001', '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO subjects (subject_code, subject_name, department, course_code, semester, credits, faculty_id, created_at) VALUES ('CS102', 'Database Management Systems', 'Computer Engineering', 'CSE-BTECH', 3, 4, 'FAC001', '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO subjects (subject_code, subject_name, department, course_code, semester, credits, faculty_id, created_at) VALUES ('IT201', 'Web Application Development', 'Information Technology', 'IT-BTECH', 3, 4, 'FAC002', '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO subjects (subject_code, subject_name, department, course_code, semester, credits, faculty_id, created_at) VALUES ('EE301', 'Power Systems Analysis', 'Electrical Engineering', 'EE-BTECH', 3, 4, 'FAC003', '2025-01-01')")

    cursor.execute("SELECT COUNT(*) FROM announcements")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO announcements (announcement_id, title, message, target_role, department, posted_by, created_at) VALUES (1, 'Midterm Examination Schedule Released', 'Midterm examinations for Semester 3 will begin from March 10, 2026. Please check your examination hall tickets.', 'all', 'All', 'Admin System', '2026-03-01 10:00:00')")
        cursor.execute("INSERT OR REPLACE INTO announcements (announcement_id, title, message, target_role, department, posted_by, created_at) VALUES (2, 'Campus Placement Drive 2026', 'Annual campus recruitment drive will begin next month. All registered final year students must update profile details.', 'student', 'Computer Engineering', 'Dr. Sarah Jenkins', '2026-03-05 14:30:00')")

    cursor.execute("SELECT COUNT(*) FROM timetable")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO timetable (timetable_id, department, semester, day_of_week, time_slot, subject_name, faculty_name, room_number, created_at) VALUES (1, 'Computer Engineering', 3, 'Monday', '09:00 AM - 10:00 AM', 'Advanced Data Structures', 'Dr. Sarah Jenkins', 'Room 301', '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO timetable (timetable_id, department, semester, day_of_week, time_slot, subject_name, faculty_name, room_number, created_at) VALUES (2, 'Information Technology', 3, 'Tuesday', '10:00 AM - 11:00 AM', 'Web Application Development', 'Prof. Robert Vance', 'Room 204', '2025-01-01')")
        cursor.execute("INSERT OR REPLACE INTO timetable (timetable_id, department, semester, day_of_week, time_slot, subject_name, faculty_name, room_number, created_at) VALUES (3, 'Electrical Engineering', 3, 'Wednesday', '11:15 AM - 12:15 PM', 'Power Systems Analysis', 'Dr. Alan Turing', 'Room 105', '2025-01-01')")

    cursor.execute("SELECT COUNT(*) FROM fees")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (1, 'STU001', 1500.0, '2026-02-15 10:00:00', 'Paid', 'TXN987654')")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (2, 'STU002', 1500.0, NULL, 'Pending', NULL)")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (3, 'STU003', 1500.0, '2026-02-18 11:30:00', 'Paid', 'TXN987655')")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (4, 'STU004', 1500.0, '2026-02-10 14:15:00', 'Paid', 'TXN987656')")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (5, 'STU005', 1500.0, NULL, 'Pending', NULL)")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (6, 'STU006', 1500.0, '2026-02-20 09:45:00', 'Paid', 'TXN987657')")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (7, 'STU007', 1500.0, '2026-02-12 16:20:00', 'Paid', 'TXN987658')")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (8, 'STU008', 1500.0, NULL, 'Pending', NULL)")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (9, 'STU009', 1500.0, '2026-02-11 12:00:00', 'Paid', 'TXN987659')")
        cursor.execute("INSERT OR REPLACE INTO fees (fee_id, student_id, amount, payment_date, status, txn_id) VALUES (10, 'STU010', 1500.0, NULL, 'Pending', NULL)")
        
    # Create indexes for optimal query speeds
    create_indexes(cursor)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
