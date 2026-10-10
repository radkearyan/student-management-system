import os
from datetime import datetime
from werkzeug.security import generate_password_hash
import backend.config.db_adapter as db_adapter
from backend.ai.prediction import predict_performance

class StudentService:
    @staticmethod
    def get_students(search_query='', department=''):
        return db_adapter.get_students(search_query, department)

    @staticmethod
    def add_student(student_id, name, dob, gender, email, phone, department, course):
        try:
            created_at = datetime.now().strftime('%Y-%m-%d')
            success, err = db_adapter.add_student(
                student_id, name, dob, gender, email, phone, department, course, created_at
            )
            if not success:
                return False, err
                
            temp_pw = generate_password_hash(student_id + "123")
            success_usr, usr_err = db_adapter.register_user(
                student_id, temp_pw, email, 'student', student_id
            )
            if not success_usr:
                return False, usr_err
                
            # Initialize student fee
            db_adapter.create_fee_record(student_id, 1500.0, 'Pending')
            return True, f"Student {name} successfully added."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_student_details(student_id):
        return db_adapter.get_student_details(student_id)

    @staticmethod
    def update_student(student_id, data):
        try:
            update_fields = {}
            possible_fields = [
                'name', 'dob', 'gender', 'email', 'phone', 'department', 'course',
                'current_semester', 'status', 'profile_pic', 'bio', 'skills',
                'achievements', 'address', 'blood_group', 'emergency_contact'
            ]
            
            for field in possible_fields:
                if field in data:
                    update_fields[field] = data[field]
                    
            if not update_fields:
                return False, "No fields to update"
                
            success, msg = db_adapter.update_student(student_id, update_fields)
            return success, msg
        except Exception as e:
            return False, str(e)

    @staticmethod
    def update_profile_pic(student_id, relative_path):
        try:
            success, _ = db_adapter.update_student(student_id, {"profile_pic": relative_path})
            return success
        except Exception:
            return False

    @staticmethod
    def delete_student(student_id):
        try:
            success, msg = db_adapter.delete_student(student_id)
            return success, msg
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_student_performance_stats(student_id):
        student = db_adapter.get_student_details(student_id)
        if not student:
            return None
            
        att_stats = db_adapter.get_attendance_stats(student_id)
        att_rate = 100.0
        if att_stats and att_stats['total'] > 0:
            att_rate = float(att_stats['present']) / att_stats['total'] * 100
            
        marks = db_adapter.get_marks_for_student(student_id)
        avg_mark = 0.0
        if marks:
            total_obt = sum([m['marks_obtained'] for m in marks])
            total_max = sum([m['max_marks'] for m in marks])
            avg_mark = (total_obt / total_max) * 100 if total_max > 0 else 0
        else:
            avg_mark = 70.0
            
        ai_result = predict_performance(att_rate, avg_mark)
        
        marks_history = []
        for m in marks:
            marks_history.append({
                "subject": m.get('subject'),
                "marks_obtained": m.get('marks_obtained'),
                "grade": m.get('grade'),
                "exam_name": m.get('exam_name'),
                "date": m.get('date')
            })
            
        return {
            "student_id": student_id,
            "name": student.get('name', ''),
            "department": student.get('department', ''),
            "course": student.get('course', ''),
            "attendance_pct": round(att_rate, 1),
            "average_marks": round(avg_mark, 1),
            "ai_prediction": ai_result,
            "marks_history": marks_history
        }

    @staticmethod
    def get_student_dashboard_analytics(student_id):
        student = db_adapter.get_student_details(student_id)
        if not student:
            return None
            
        att_stats = db_adapter.get_attendance_stats(student_id)
        att_rate = 100.0
        if att_stats and att_stats['total'] > 0:
            att_rate = float(att_stats['present']) / att_stats['total'] * 100
            
        marks = db_adapter.get_marks_for_student(student_id)
        avg_mark = 0.0
        if marks:
            total_obt = sum([m['marks_obtained'] for m in marks])
            total_max = sum([m['max_marks'] for m in marks])
            avg_mark = (total_obt / total_max) * 100 if total_max > 0 else 0
        else:
            avg_mark = 70.0
            
        ai_res = predict_performance(att_rate, avg_mark)
        
        fees = db_adapter.get_fees(student_id)
        fees_pending = sum([f.get('amount', 0.0) for f in fees if f.get('status') == 'Pending'])
        fees_collected = sum([f.get('amount', 0.0) for f in fees if f.get('status') == 'Paid'])
        
        grade_dist = db_adapter.get_grade_distribution_for_student(student_id)
        
        marks_history = []
        for m in marks:
            marks_history.append({
                "subject": m.get('subject'),
                "marks_obtained": m.get('marks_obtained'),
                "exam_name": m.get('exam_name'),
                "date": m.get('date')
            })
            
        return {
            "metrics": {
                "name": student.get('name', ''),
                "attendance": round(att_rate, 1),
                "grades_rate": round(avg_mark, 1),
                "fees_pending": fees_pending,
                "fees_collected": fees_collected,
                "ai_risk": ai_res['status']
            },
            "ai_prediction": ai_res,
            "grade_distribution": grade_dist,
            "marks_history": marks_history
        }
