from flask import Blueprint, jsonify, request
import backend.config.db_adapter as db_adapter
from backend.utils.authentication import require_role

courses_bp = Blueprint('courses', __name__)

# ---------------- SUBJECTS ROUTES ----------------

@courses_bp.route('/subjects', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_subjects_route():
    dept = request.args.get('department', '').strip()
    course_code = request.args.get('course_code', '').strip()
    search = request.args.get('search', '').strip()
    semester = request.args.get('semester')
    
    subjects = db_adapter.get_subjects(
        department=dept,
        course_code=course_code,
        search=search,
        semester=semester
    )
    return jsonify({"success": True, "subjects": subjects})

@courses_bp.route('/subjects/<sub_id_or_code>', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_subject_detail_route(sub_id_or_code):
    subject = db_adapter.get_subject_details(sub_id_or_code)
    if not subject:
        return jsonify({"success": False, "message": "Subject not found"}), 404
    return jsonify({"success": True, "subject": subject})

@courses_bp.route('/subjects', methods=['POST'])
@require_role(['admin'])
def add_subject_route():
    data = request.get_json() or {}
    subject_code = data.get('subject_code', '').strip()
    subject_name = data.get('subject_name', '').strip()
    department = data.get('department', '').strip()
    course_code = data.get('course_code', '').strip()
    semester = data.get('semester', 1)
    credits = data.get('credits', 4)
    faculty_id = data.get('faculty_id')
    
    if not subject_code or not subject_name or not department:
        return jsonify({"success": False, "message": "Subject Code, Subject Name, and Department are required."}), 400
        
    success, result = db_adapter.add_subject(
        subject_code=subject_code,
        subject_name=subject_name,
        department=department,
        course_code=course_code,
        semester=semester,
        credits=credits,
        faculty_id=faculty_id
    )
    if not success:
        return jsonify({"success": False, "message": result}), 400
    return jsonify({"success": True, "message": "Subject created successfully", "subject": result})

@courses_bp.route('/subjects/<sub_id_or_code>', methods=['PUT'])
@require_role(['admin'])
def update_subject_route(sub_id_or_code):
    data = request.get_json() or {}
    subject_code = data.get('subject_code', '').strip()
    subject_name = data.get('subject_name', '').strip()
    department = data.get('department', '').strip()
    course_code = data.get('course_code', '').strip()
    semester = data.get('semester', 1)
    credits = data.get('credits', 4)
    faculty_id = data.get('faculty_id')
    
    if not subject_code or not subject_name or not department:
        return jsonify({"success": False, "message": "Subject Code, Subject Name, and Department are required."}), 400
        
    success, msg = db_adapter.update_subject(
        subject_id=sub_id_or_code,
        subject_code=subject_code,
        subject_name=subject_name,
        department=department,
        course_code=course_code,
        semester=semester,
        credits=credits,
        faculty_id=faculty_id
    )
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@courses_bp.route('/subjects/<sub_id_or_code>', methods=['DELETE'])
@require_role(['admin'])
def delete_subject_route(sub_id_or_code):
    success, msg = db_adapter.delete_subject(sub_id_or_code)
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@courses_bp.route('/subjects/<sub_id_or_code>/assign_faculty', methods=['POST'])
@require_role(['admin'])
def assign_faculty_route(sub_id_or_code):
    data = request.get_json() or {}
    faculty_id = data.get('faculty_id')
    if not faculty_id:
        return jsonify({"success": False, "message": "Faculty ID is required."}), 400
        
    success, msg = db_adapter.assign_subject_to_faculty(faculty_id, sub_id_or_code)
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

# ---------------- COURSES ROUTES ----------------

@courses_bp.route('/courses', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_courses_route():
    dept = request.args.get('department', '').strip()
    search = request.args.get('search', '').strip()
    courses = db_adapter.get_courses(department=dept, search=search)
    return jsonify({"success": True, "courses": courses})

@courses_bp.route('/courses/<course_id_or_code>', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_course_detail_route(course_id_or_code):
    course = db_adapter.get_course_details(course_id_or_code)
    if not course:
        return jsonify({"success": False, "message": "Course not found"}), 404
    return jsonify({"success": True, "course": course})

@courses_bp.route('/courses', methods=['POST'])
@require_role(['admin'])
def add_course_route():
    data = request.get_json() or {}
    course_code = data.get('course_code', '').strip()
    course_name = data.get('course_name', '').strip()
    department = data.get('department', '').strip()
    duration_years = data.get('duration_years', 4)
    
    if not course_code or not course_name or not department:
        return jsonify({"success": False, "message": "Course Code, Course Name, and Department are required."}), 400
        
    success, res = db_adapter.add_course(
        course_code=course_code,
        course_name=course_name,
        department=department,
        duration_years=duration_years
    )
    if not success:
        return jsonify({"success": False, "message": res}), 400
    return jsonify({"success": True, "message": "Course created successfully", "course": res})

@courses_bp.route('/courses/<int:course_id>', methods=['PUT'])
@require_role(['admin'])
def update_course_route(course_id):
    data = request.get_json() or {}
    course_code = data.get('course_code', '').strip()
    course_name = data.get('course_name', '').strip()
    department = data.get('department', '').strip()
    duration_years = data.get('duration_years', 4)
    
    if not course_code or not course_name or not department:
        return jsonify({"success": False, "message": "Course Code, Course Name, and Department are required."}), 400
        
    success, msg = db_adapter.update_course(
        course_id=course_id,
        course_code=course_code,
        course_name=course_name,
        department=department,
        duration_years=duration_years
    )
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@courses_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@require_role(['admin'])
def delete_course_route(course_id):
    success, msg = db_adapter.delete_course(course_id)
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})
