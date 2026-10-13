-- SQL Schema for Student Management System

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL, -- admin, teacher, student
    reference_id TEXT   -- maps to student_id or faculty_id
);

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    gender TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    department TEXT NOT NULL,
    course TEXT NOT NULL,
    current_semester INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'Active', -- Active, Alumni
    created_at TEXT NOT NULL,
    profile_pic TEXT,
    bio TEXT,
    skills TEXT,
    achievements TEXT,
    address TEXT,
    blood_group TEXT,
    emergency_contact TEXT
);

-- 3. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL, -- Present, Absent
    method TEXT NOT NULL, -- Manual
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 4. Exams Table
CREATE TABLE IF NOT EXISTS exams (
    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    date TEXT NOT NULL,
    max_marks INTEGER NOT NULL
);

-- 5. Marks Table
CREATE TABLE IF NOT EXISTS marks (
    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    exam_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    marks_obtained REAL NOT NULL,
    grade TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
);

-- 6. Fees Table
CREATE TABLE IF NOT EXISTS fees (
    fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_date TEXT,
    status TEXT NOT NULL, -- Paid, Pending
    txn_id TEXT,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 7. Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    faculty_name TEXT NOT NULL,
    q1 INTEGER NOT NULL,
    q2 INTEGER NOT NULL,
    q3 INTEGER NOT NULL,
    q4 INTEGER NOT NULL,
    q5 INTEGER NOT NULL,
    comments TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 8. Makeup Applications Table
CREATE TABLE IF NOT EXISTS makeup_applications (
    app_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    exam_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Applied', -- Applied, Approved, Rejected
    applied_date TEXT NOT NULL,
    fee_status TEXT NOT NULL DEFAULT 'Pending', -- Pending, Paid
    txn_id TEXT,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 9. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT OR IGNORE INTO departments (name) VALUES ('Computer Engineering');
INSERT OR IGNORE INTO departments (name) VALUES ('Information Technology');
INSERT OR IGNORE INTO departments (name) VALUES ('Electrical Engineering');
INSERT OR IGNORE INTO departments (name) VALUES ('Mechanical Engineering');

-- 10. Faculty Table
CREATE TABLE IF NOT EXISTS faculty (
    faculty_id TEXT PRIMARY KEY,
    user_id INTEGER,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    department TEXT NOT NULL,
    designation TEXT DEFAULT 'Assistant Professor',
    qualification TEXT DEFAULT 'M.Tech / Ph.D',
    joining_date TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 11. Courses Table
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    department TEXT NOT NULL,
    duration_years INTEGER DEFAULT 4,
    created_at TEXT NOT NULL
);

-- 12. Subjects Table
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT UNIQUE NOT NULL,
    subject_name TEXT NOT NULL,
    department TEXT NOT NULL,
    course_code TEXT,
    semester INTEGER DEFAULT 1,
    credits INTEGER DEFAULT 4,
    faculty_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

-- 13. Announcements Table
CREATE TABLE IF NOT EXISTS announcements (
    announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    target_role TEXT DEFAULT 'all',
    department TEXT DEFAULT 'All',
    posted_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 14. Timetable Table
CREATE TABLE IF NOT EXISTS timetable (
    timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    faculty_name TEXT NOT NULL,
    room_number TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- ====================================================================
-- PERFORMANCE INDEXES (Optimizing Query & Filter Time Complexity)
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_ref ON users(reference_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
CREATE INDEX IF NOT EXISTS idx_students_course ON students(course);

CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);

CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id);
CREATE INDEX IF NOT EXISTS idx_marks_exam ON marks(exam_id);
CREATE INDEX IF NOT EXISTS idx_marks_student_exam ON marks(student_id, exam_id);

CREATE INDEX IF NOT EXISTS idx_fees_student ON fees(student_id);
CREATE INDEX IF NOT EXISTS idx_fees_status ON fees(status);

CREATE INDEX IF NOT EXISTS idx_exams_subject ON exams(subject);
CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(date);

CREATE INDEX IF NOT EXISTS idx_faculty_user ON faculty(user_id);
CREATE INDEX IF NOT EXISTS idx_faculty_dept ON faculty(department);
CREATE INDEX IF NOT EXISTS idx_faculty_fac_id ON faculty(faculty_id);

CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(subject_code);
CREATE INDEX IF NOT EXISTS idx_subjects_dept ON subjects(department);

CREATE INDEX IF NOT EXISTS idx_timetable_lookup ON timetable(department, semester, day_of_week);

CREATE INDEX IF NOT EXISTS idx_feedback_student ON feedback(student_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);

CREATE INDEX IF NOT EXISTS idx_announcements_filter ON announcements(target_role, department);


