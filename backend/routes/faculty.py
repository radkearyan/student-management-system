from flask import Blueprint, jsonify, request
import backend.config.db_adapter as db_adapter
from backend.utils.authentication import require_role
from werkzeug.security import generate_password_hash

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('', methods=['GET'])
@require_role(['admin', 'teacher'])
def get_faculty():
    dept = request.args.get('department', '').strip()
    search = request.args.get('search', '').strip()
    faculty_list = db_adapter.get_faculty_members(department=dept, search=search)
    return jsonify({"success": True, "faculty": faculty_list})

@faculty_bp.route('/<user_id_or_ref>', methods=['GET'])
@require_role(['admin', 'teacher'])
def get_faculty_detail(user_id_or_ref):
    fac = db_adapter.get_faculty_details(user_id_or_ref)
    if not fac:
        return jsonify({"success": False, "message": "Faculty member not found."}), 404
    return jsonify({"success": True, "faculty": fac})

@faculty_bp.route('', methods=['POST'])
@require_role(['admin'])
def add_faculty():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    phone = data.get('phone', '').strip()
    reference_id = data.get('reference_id', '').strip() or None
    designation = data.get('designation', 'Assistant Professor').strip()
    qualification = data.get('qualification', 'M.Tech / Ph.D').strip()
    
    if not all([username, password, email, name, department]):
        return jsonify({"success": False, "message": "Username, password, email, name, and department are required."}), 400
        
    pwd_hash = generate_password_hash(password)
    success, res = db_adapter.add_faculty_member(
        username, pwd_hash, email, name, department, phone=phone,
        reference_id=reference_id, designation=designation, qualification=qualification
    )
    if not success:
        return jsonify({"success": False, "message": res or "Failed to add faculty member."}), 400
    return jsonify({"success": True, "message": f"Faculty '{name}' added successfully.", "faculty": res})

@faculty_bp.route('/<int:user_id>', methods=['PUT'])
@require_role(['admin'])
def update_faculty(user_id):
    data = request.get_json() or {}
    department = data.get('department', '').strip()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    designation = data.get('designation', '').strip()
    qualification = data.get('qualification', '').strip()
    
    if not department:
        return jsonify({"success": False, "message": "Department is required."}), 400
        
    success, msg = db_adapter.update_faculty_department(
        user_id, department, name=name, email=email, phone=phone,
        designation=designation, qualification=qualification
    )
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@faculty_bp.route('/<int:user_id>/department', methods=['PUT'])
@require_role(['admin'])
def update_faculty_dept(user_id):
    return update_faculty(user_id)

@faculty_bp.route('/<int:user_id>', methods=['DELETE'])
@require_role(['admin'])
def delete_faculty(user_id):
    success, msg = db_adapter.delete_faculty_member(user_id)
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@faculty_bp.route('/<faculty_id>/assign_subject', methods=['POST'])
@require_role(['admin'])
def assign_subject(faculty_id):
    data = request.get_json() or {}
    subject_id = data.get('subject_id') or data.get('subject_code')
    if not subject_id:
        return jsonify({"success": False, "message": "Subject ID or Code is required."}), 400
        
    success, msg = db_adapter.assign_subject_to_faculty(faculty_id, subject_id)
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})


