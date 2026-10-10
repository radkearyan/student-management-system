from datetime import datetime
import backend.config.db_adapter as db_adapter

class AttendanceService:
    @staticmethod
    def get_attendance_logs(student_id='', department='', status='', date=''):
        return db_adapter.get_attendance_logs(student_id=student_id, department=department, status=status, date=date)

    @staticmethod
    def record_attendance(student_id, status='Present', method='Manual', date_str=None):
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        success, msg = db_adapter.record_attendance(student_id, date_str, status, method)
        return success, msg
