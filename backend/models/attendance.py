class Attendance:
    def __init__(self, attendance_id, student_id, date, status, method='Manual'):
        self.attendance_id = attendance_id
        self.student_id = student_id
        self.date = date
        self.status = status # Present, Absent
        self.method = method
