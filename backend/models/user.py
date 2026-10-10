class User:
    def __init__(self, user_id, username, password, email, role, reference_id=None):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.role = role # admin, teacher, student
        self.reference_id = reference_id # maps to student_id or faculty_id
        
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "reference_id": self.reference_id
        }
