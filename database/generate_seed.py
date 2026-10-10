# Helper to generate seed.sql containing static inserts and dynamic attendance dates
import os
import random
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

def generate():
    seed_file = os.path.join(os.path.dirname(globals().get('__abspath__', __file__)), 'seed.sql')
    
    admin_h = generate_password_hash('admin123')
    teacher_h = generate_password_hash('teacher123')
    student_h = generate_password_hash('student123')

    users = [
        ('admin', admin_h, 'admin@example.com', 'admin', 'NULL'),
        ('teacher', teacher_h, 'teacher@example.com', 'teacher', "'FAC001'"),
        ('student', student_h, 'student@example.com', 'student', "'STU001'"),
        ('stu001', student_h, 'alice.johnson@example.com', 'student', "'STU001'"),
        ('stu002', student_h, 'bob.smith@example.com', 'student', "'STU002'"),
        ('stu003', student_h, 'charlie.brown@example.com', 'student', "'STU003'"),
        ('stu004', student_h, 'diana.prince@example.com', 'student', "'STU004'"),
        ('stu005', student_h, 'ethan.hunt@example.com', 'student', "'STU005'")
    ]

    students = [
        ('STU001', 'Alice Johnson', '2005-04-12', 'Female', 'alice.johnson@example.com', '+919096081201', 'Computer Engineering', 'B.Tech Computer Engineering', 3, 'Active', '2025-09-01'),
        ('STU002', 'Bob Smith', '2004-08-22', 'Male', 'bob.smith@example.com', '+919096081202', 'Computer Engineering', 'B.Tech Computer Engineering', 3, 'Active', '2025-09-01'),
        ('STU003', 'Charlie Brown', '2005-11-05', 'Male', 'charlie.brown@example.com', '+919096081203', 'Information Technology', 'B.Tech Information Technology', 3, 'Active', '2025-09-01'),
        ('STU004', 'Diana Prince', '2005-01-30', 'Female', 'diana.prince@example.com', '+919096081204', 'Electrical Engineering', 'B.Tech Electrical Engineering', 3, 'Active', '2025-09-01'),
        ('STU005', 'Ethan Hunt', '2004-05-15', 'Male', 'ethan.hunt@example.com', '+919096081205', 'Computer Engineering', 'B.Tech Computer Engineering', 3, 'Active', '2025-09-01'),
        ('STU006', 'Fiona Gallagher', '2005-07-19', 'Female', 'fiona.g@example.com', '+919096081206', 'Information Technology', 'B.Tech Information Technology', 3, 'Active', '2025-09-01'),
        ('STU007', 'George Clark', '2004-12-01', 'Male', 'george.c@example.com', '+919096081207', 'Electrical Engineering', 'B.Tech Electrical Engineering', 3, 'Active', '2025-09-01'),
        ('STU008', 'Hannah Abbott', '2005-09-14', 'Female', 'hannah.a@example.com', '+919096081208', 'Computer Engineering', 'B.Tech Computer Engineering', 4, 'Active', '2024-09-01'),
        ('STU009', 'Ian Malcolm', '2004-03-25', 'Male', 'ian.m@example.com', '+919096081209', 'Information Technology', 'B.Tech Information Technology', 3, 'Active', '2025-09-01'),
        ('STU010', 'Julia Roberts', '2005-06-08', 'Female', 'julia.r@example.com', '+919096081210', 'Electrical Engineering', 'B.Tech Electrical Engineering', 3, 'Active', '2025-09-01')
    ]

    exams = [
        (1, 'Midterm Examination', 'Advanced Data Structures', '2026-03-10', 100),
        (2, 'Midterm Examination', 'Linear Algebra', '2026-03-12', 100),
        (3, 'Midterm Examination', 'Power Systems Analysis', '2026-03-14', 100),
        (4, 'Final Theory Examination', 'Advanced Data Structures', '2026-06-20', 100),
        (5, 'Final Theory Examination', 'Linear Algebra', '2026-06-22', 100),
        (6, 'Final Theory Examination', 'Power Systems Analysis', '2026-06-24', 100)
    ]

    fees = [
        ('STU001', 1500.0, "'2026-02-15'", "'Paid'", "'TXN987654'"),
        ('STU002', 1500.0, 'NULL', "'Pending'", 'NULL'),
        ('STU003', 1500.0, "'2026-02-18'", "'Paid'", "'TXN987655'"),
        ('STU004', 1500.0, "'2026-02-10'", "'Paid'", "'TXN987656'"),
        ('STU005', 1500.0, 'NULL', "'Pending'", 'NULL'),
        ('STU006', 1500.0, "'2026-02-20'", "'Paid'", "'TXN987657'"),
        ('STU007', 1500.0, "'2026-02-12'", "'Paid'", "'TXN987658'"),
        ('STU008', 1500.0, 'NULL', "'Pending'", 'NULL'),
        ('STU009', 1500.0, "'2026-02-11'", "'Paid'", "'TXN987659'"),
        ('STU010', 1500.0, 'NULL', "'Pending'", 'NULL')
    ]

    marks_distribution = {
        'STU001': {1: 85, 2: 90, 3: 88, 4: 87, 5: 92, 6: 89}, 
        'STU002': {1: 45, 2: 52, 3: 40, 4: 48, 5: 50, 6: 42}, 
        'STU003': {1: 72, 2: 75, 3: 70, 4: 76, 5: 78, 6: 74}, 
        'STU004': {1: 92, 2: 95, 3: 94, 4: 93, 5: 96, 6: 95}, 
        'STU005': {1: 35, 2: 42, 3: 38, 4: 30, 5: 45, 6: 35}, 
        'STU006': {1: 65, 2: 68, 3: 71, 4: 67, 5: 70, 6: 69}, 
        'STU007': {1: 80, 2: 82, 3: 85, 4: 83, 5: 84, 6: 86}, 
        'STU009': {1: 88, 2: 91, 3: 89, 4: 90, 5: 92, 6: 91}, 
        'STU010': {1: 48, 2: 50, 3: 46, 4: 52, 5: 49, 6: 47}  
    }

    attendance_probs = {
        'STU001': 0.95, 'STU002': 0.65, 'STU003': 0.80, 'STU004': 1.00,
        'STU005': 0.55, 'STU006': 0.85, 'STU007': 0.90, 'STU008': 0.72,
        'STU009': 0.93, 'STU010': 0.68
    }

    with open(seed_file, 'w', encoding='utf-8') as f:
        f.write("-- Seed file for Student Management System\n\n")
        
        # 1. Students
        f.write("-- Students Seed\n")
        for s in students:
            f.write(f"INSERT OR REPLACE INTO students (student_id, name, dob, gender, email, phone, department, course, current_semester, status, created_at) VALUES ('{s[0]}', '{s[1]}', '{s[2]}', '{s[3]}', '{s[4]}', '{s[5]}', '{s[6]}', '{s[7]}', {s[8]}, '{s[9]}', '{s[10]}');\n")
        f.write("\n")
        
        # 2. Users
        f.write("-- Users Seed\n")
        for u in users:
            f.write(f"INSERT OR REPLACE INTO users (username, password, email, role, reference_id) VALUES ('{u[0]}', '{u[1]}', '{u[2]}', '{u[3]}', {u[4]});\n")
        f.write("\n")
        
        # 3. Exams
        f.write("-- Exams Seed\n")
        for e in exams:
            f.write(f"INSERT OR REPLACE INTO exams (exam_id, name, subject, date, max_marks) VALUES ({e[0]}, '{e[1]}', '{e[2]}', '{e[3]}', {e[4]});\n")
        f.write("\n")
        
        # 4. Marks
        f.write("-- Marks Seed\n")
        for sid, scores in marks_distribution.items():
            for exam_id, score in scores.items():
                subject = 'Advanced Data Structures' if exam_id in [1, 4] else ('Linear Algebra' if exam_id in [2, 5] else 'Power Systems Analysis')
                if score >= 90: grade = 'A'
                elif score >= 80: grade = 'B'
                elif score >= 70: grade = 'C'
                elif score >= 60: grade = 'D'
                elif score >= 50: grade = 'E'
                else: grade = 'F'
                f.write(f"INSERT INTO marks (student_id, exam_id, subject, marks_obtained, grade) VALUES ('{sid}', {exam_id}, '{subject}', {score}, '{grade}');\n")
        f.write("\n")
        
        # 5. Fees
        f.write("-- Fees Seed\n")
        for fee in fees:
            f.write(f"INSERT INTO fees (student_id, amount, payment_date, status, txn_id) VALUES ('{fee[0]}', {fee[1]}, {fee[2]}, {fee[3]}, {fee[4]});\n")
        f.write("\n")
        
        # 6. Attendance
        f.write("-- Attendance Seed\n")
        random.seed(42)
        current_date = datetime.now()
        for i in range(30):
            date_str = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
            day_of_week = (current_date - timedelta(days=i)).weekday()
            if day_of_week >= 5: # skip weekends
                continue
            for sid, prob in attendance_probs.items():
                status = 'Present' if random.random() < prob else 'Absent'
                f.write(f"INSERT INTO attendance (student_id, date, status, method) VALUES ('{sid}', '{date_str}', '{status}', 'Manual');\n")
        f.write("\n")

if __name__ == '__main__':
    generate()
    print("seed.sql generated successfully.")
