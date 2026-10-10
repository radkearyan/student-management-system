import os
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from backend.services.student_service import StudentService
from backend.utils.authentication import require_role

student_bp = Blueprint('student', __name__)


@student_bp.route('', methods=['GET'])
@require_role(['admin', 'teacher'])
def get_students():
    search = request.args.get('search', '')
    dept = request.args.get('department', '')
    
    # Teachers can ONLY view students of their registered department
    if session['user']['role'] == 'teacher':
        teacher_dept = session['user'].get('department')
        if teacher_dept:
            dept = teacher_dept
            
    students = StudentService.get_students(search, dept)
    return jsonify(students)

@student_bp.route('', methods=['POST'])
@require_role(['admin', 'teacher'])
def add_student():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    name = data.get('name')
    dob = data.get('dob')
    gender = data.get('gender')
    email = data.get('email')
    phone = data.get('phone')
    department = data.get('department')
    course = data.get('course')
    
    # Teachers can only add students to their own department
    if session['user']['role'] == 'teacher':
        teacher_dept = session['user'].get('department')
        if teacher_dept and department != teacher_dept:
            return jsonify({
                "success": False, 
                "message": f"Unauthorized: As faculty of {teacher_dept}, you can only enroll students in {teacher_dept}."
            }), 403
    
    if not all([student_id, name, dob, gender, email, phone, department, course]):
        return jsonify({"success": False, "message": "All fields are required"}), 400
        
    success, msg = StudentService.add_student(
        student_id, name, dob, gender, email, phone, department, course
    )
    
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@student_bp.route('/<student_id>', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_student_details(student_id):
    # Check permissions (student can only check their own profile)
    if session['user']['role'] == 'student' and session['user']['reference_id'] != student_id:
        return jsonify({"success": False, "message": "Access denied"}), 403
        
    student = StudentService.get_student_details(student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
        
    # Teacher can only view student details of their own department
    if session['user']['role'] == 'teacher':
        teacher_dept = session['user'].get('department')
        if teacher_dept and student.get('department') != teacher_dept:
            return jsonify({"success": False, "message": f"Access denied: Student does not belong to {teacher_dept}"}), 403
        
    return jsonify(student)

@student_bp.route('/<student_id>', methods=['PUT'])
@require_role(['admin', 'teacher', 'student'])
def update_student(student_id):
    user_role = session['user']['role']
    user_ref = session['user'].get('reference_id')
    
    # Check permissions
    if user_role == 'student':
        if user_ref != student_id:
            return jsonify({"success": False, "message": "Access denied"}), 403
            
        data = request.get_json() or {}
        forbidden_fields = ['student_id', 'role', 'marks', 'attendance', 'department', 'course', 'status', 'current_semester']
        for key in forbidden_fields:
            if key in data:
                return jsonify({"success": False, "message": f"Unauthorized: Students are not permitted to modify restricted field '{key}'"}), 403
        
    data = request.get_json() or {}
    success, msg = StudentService.update_student(student_id, data)
    
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@student_bp.route('/<student_id>/upload-profile-pic', methods=['POST'])
@require_role(['admin', 'teacher', 'student'])
def upload_profile_pic(student_id):
    if session['user']['role'] == 'student' and session['user']['reference_id'] != student_id:
        return jsonify({"success": False, "message": "Access denied"}), 403
        
    if 'profile_pic' not in request.files:
        return jsonify({"success": False, "message": "No file part in request"}), 400
        
    file = request.files['profile_pic']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
        return jsonify({"success": False, "message": "Invalid file type. Only JPG, JPEG, PNG, and GIF allowed"}), 400
        
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
    os.makedirs(upload_folder, exist_ok=True)
    
    safe_id = secure_filename(str(student_id))
    filename = f"{safe_id}{ext}"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    
    relative_path = f"/uploads/profiles/{filename}"
    success = StudentService.update_profile_pic(student_id, relative_path)
    
    if success:
        # Update current session if student
        if session['user']['role'] == 'student' and session['user']['reference_id'] == student_id:
            session['user']['profile_pic'] = relative_path
            session.modified = True
        return jsonify({"success": True, "message": "Profile picture uploaded successfully", "profile_pic": relative_path})
        
    return jsonify({"success": False, "message": "Database update failed"}), 500

@student_bp.route('/<student_id>', methods=['DELETE'])
@require_role(['admin'])
def delete_student(student_id):
    success, msg = StudentService.delete_student(student_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@student_bp.route('/<student_id>/performance', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_student_performance(student_id):
    if session['user']['role'] == 'student' and session['user']['reference_id'] != student_id:
        return jsonify({"success": False, "message": "Access denied"}), 403
        
    stats = StudentService.get_student_performance_stats(student_id)
    if not stats:
        return jsonify({"success": False, "message": "Student not found"}), 404
        
    return jsonify({
        "success": True,
        **stats
    })

@student_bp.route('/<student_id>/dashboard', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_student_dashboard_analytics(student_id):
    if session['user']['role'] == 'student' and session['user']['reference_id'] != student_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    dashboard_data = StudentService.get_student_dashboard_analytics(student_id)
    if not dashboard_data:
        return jsonify({"success": False, "message": "Student not found"}), 404
        
    return jsonify({
        "success": True,
        **dashboard_data
    })
