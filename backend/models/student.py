class Student:
    def __init__(self, student_id, name, dob, gender, email, phone, department, course,
                 current_semester=1, status='Active', created_at=None, profile_pic=None,
                 bio=None, skills=None, achievements=None, address=None, blood_group=None,
                 emergency_contact=None):
        self.student_id = student_id
        self.name = name
        self.dob = dob
        self.gender = gender
        self.email = email
        self.phone = phone
        self.department = department
        self.course = course
        self.current_semester = current_semester
        self.status = status
        self.created_at = created_at
        self.profile_pic = profile_pic
        self.bio = bio
        self.skills = skills
        self.achievements = achievements
        self.address = address
        self.blood_group = blood_group
        self.emergency_contact = emergency_contact
