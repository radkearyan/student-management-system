import random
from datetime import datetime
import backend.config.db_adapter as db_adapter

class ResultService:
    @staticmethod
    def get_exams():
        return db_adapter.get_exams()

    @staticmethod
    def create_exam(name, subject, date_str, max_marks=100):
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        return db_adapter.create_exam(name, subject, date_str, max_marks)

    @staticmethod
    def delete_exam(exam_id):
        return db_adapter.delete_exam(exam_id)


    @staticmethod
    def submit_marks(student_id, exam_id, marks_obtained):
        try:
            if marks_obtained is None or str(marks_obtained).strip() == '':
                return False, "Obtained marks field is required."
                
            try:
                marks_obtained = float(marks_obtained)
            except (ValueError, TypeError):
                return False, "Invalid marks format. Must be a valid number."

            if marks_obtained < 0:
                return False, "Marks obtained cannot be negative."

            exam = db_adapter.get_exam_details(exam_id)
            if not exam:
                return False, "Exam not found."
                
            max_m = float(exam.get('max_marks', 100))
            if marks_obtained > max_m:
                return False, f"Marks obtained ({marks_obtained}) cannot exceed maximum marks ({max_m})."
                
            score_pct = (marks_obtained / max_m) * 100.0
            if score_pct >= 90: grade = 'A+'
            elif score_pct >= 80: grade = 'A'
            elif score_pct >= 70: grade = 'B'
            elif score_pct >= 60: grade = 'C'
            elif score_pct >= 40: grade = 'D'
            else: grade = 'F'
            
            success, err = db_adapter.submit_marks(student_id, exam_id, exam['subject'], marks_obtained, grade)
            if not success:
                return False, err
                
            return True, f"Marks successfully uploaded for student {student_id}."
        except Exception as e:
            return False, str(e)


    @staticmethod
    def get_makeup_applications(student_id='', role='student'):
        return db_adapter.get_makeup_applications(student_id, role)

    @staticmethod
    def apply_makeup_exam(student_id, subject, exam_name):
        try:
            applied_date = datetime.now().strftime('%Y-%m-%d')
            success, err = db_adapter.apply_makeup_exam(student_id, subject, exam_name, applied_date)
            if not success:
                return False, err
            return True, "Makeup Examination applied successfully. Please clear the pending fee."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def pay_makeup_fee(app_id, student_id, card_number):
        try:
            txn_id = "TXN_MKP_" + str(random.randint(100000, 999999))
            success, err = db_adapter.pay_makeup_fee(app_id, student_id, txn_id)
            if not success:
                return False, err
            return True, txn_id
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_hall_ticket(student_id):
        student = db_adapter.get_student_details(student_id)
        if not student:
            return None
            
        marks = db_adapter.get_marks_for_student(student_id)
        subjects = list(set([m['subject'] for m in marks if 'subject' in m]))
        
        if not subjects:
            subjects = ["Advanced Data Structures", "Linear Algebra", "Power Systems Analysis"]
            
        return {
            "student_id": student['student_id'],
            "name": student.get('name', ''),
            "department": student.get('department', ''),
            "course": student.get('course', ''),
            "semester": student.get('current_semester', 1),
            "session": "Summer Examination 2026",
            "college": "Student Management System",
            "venue": "Academic Block A, Floor 2, Main Campus",
            "subjects": subjects,
            "bar_code": f"*HT-{student['student_id']}-2026*"
        }

Class = ResultService
