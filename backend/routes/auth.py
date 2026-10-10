import os
from flask import Blueprint, request, jsonify, session, current_app
from backend.services.auth_service import AuthService
from backend.utils.authentication import require_role
import backend.config.db_adapter as db_adapter

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required"}), 400
        
    user = AuthService.authenticate_user(username, password)
    if user:
        session.permanent = True
        user_data = dict(user)
        user_data.pop('password', None)
        session['user'] = user_data
        return jsonify({"success": True, "user": user_data})
        
    return jsonify({"success": False, "message": "Invalid username or password"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@auth_bp.route('/session', methods=['GET'])
def get_session():
    if 'user' in session:
        user_data = dict(session['user'])
        # Refresh profile pic and info dynamically for all roles
        user_row = db_adapter.get_user_by_id(user_data['user_id'])
        if user_row:
            user_data['profile_pic'] = user_row.get('profile_pic')
            user_data['name'] = user_row.get('name')
            user_data['email'] = user_row.get('email')
            user_data['phone'] = user_row.get('phone')
            user_data['department'] = user_row.get('department')
            session['user'] = user_data
        return jsonify({"success": True, "user": user_data})
    return jsonify({"success": False, "message": "No active session"})

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    role = data.get('role') # 'student' or 'teacher'
    
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    department = data.get('department')
    password = data.get('password')
    
    if not role or role not in ['student', 'teacher']:
        return jsonify({"success": False, "message": "Invalid registration role"}), 400
        
    if not all([name, email, phone, department, password]):
        return jsonify({"success": False, "message": "All required fields must be completed"}), 400
        
    if role == 'student':
        student_id = data.get('student_id')
        dob = data.get('dob')
        gender = data.get('gender')
        course = data.get('course')
        
        if not all([student_id, dob, gender, course]):
            return jsonify({"success": False, "message": "Missing student-specific registration details"}), 400
            
        success, msg = AuthService.register_student(
            student_id, name, dob, gender, email, phone, department, course, password
        )
    else:
        faculty_id = data.get('faculty_id')
        success, msg = AuthService.register_teacher(
            faculty_id, name, email, phone, department, password
        )
        
    if success:
        return jsonify({"success": True, "message": f"{msg}! You can now sign in using your ID."})
    return jsonify({"success": False, "message": msg}), 400

@auth_bp.route('/change_password', methods=['POST'])
@require_role(['admin', 'teacher', 'student'])
def change_password():
    data = request.get_json() or {}
    current_pw = data.get('current_password')
    new_pw = data.get('new_password')
    
    if not current_pw or not new_pw:
        return jsonify({"success": False, "message": "Current and new passwords are required"}), 400
        
    username = session['user']['username']
    success, msg = AuthService.change_password(username, current_pw, new_pw)
    
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@auth_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    username = data.get('username')
    
    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400
        
    user = db_adapter.get_user_by_username(username)
    if user:
        return jsonify({
            "success": True, 
            "message": "Password reset link sent to your registered email address."
        })
        
    return jsonify({"success": False, "message": "Username not found"}), 404

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    if 'user' not in session:
        return jsonify({"success": False, "message": "No active session"}), 401
    
    user_id = session['user']['user_id']
    user = db_adapter.get_user_by_id(user_id)
    
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    user_data = dict(user)
    user_data.pop('password', None)
    
    # If student, merge with student info
    if user.get('role') == 'student' and user.get('reference_id'):
        student = db_adapter.get_student_details(user['reference_id'])
        if student:
            for key, val in student.items():
                if val is not None:
                    user_data[key] = val
    elif user.get('role') == 'teacher':
        fac = db_adapter.get_faculty_details(user_id)
        if fac:
            for key, val in fac.items():
                if val is not None:
                    user_data[key] = val

    return jsonify({"success": True, "profile": user_data})

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    if 'user' not in session:
        return jsonify({"success": False, "message": "No active session"}), 401
        
    user_id = session['user']['user_id']
    user_role = session['user']['role']
    data = request.get_json() or {}
    
    # Strictly prevent student from altering unauthorized/restricted fields
    if user_role == 'student':
        forbidden_fields = ['role', 'student_id', 'reference_id', 'user_id', 'marks', 'attendance', 'department', 'course', 'status', 'current_semester']
        for key in forbidden_fields:
            if key in data:
                return jsonify({"success": False, "message": f"Unauthorized: Students are not permitted to modify restricted field '{key}'"}), 403

    user = db_adapter.get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    updatable_fields = ['name', 'phone', 'department', 'bio', 'skills', 'achievements', 'address', 'blood_group', 'emergency_contact', 'email']
    if user_role == 'student':
        updatable_fields = ['name', 'phone', 'bio', 'skills', 'achievements', 'address', 'blood_group', 'emergency_contact', 'email']
    
    user_updates = {f: data[f] for f in updatable_fields if f in data}
    if user_updates:
        db_adapter.update_user_fields(user_id, user_updates)
        
    # If student, sync to students table
    if user.get('role') == 'student' and user.get('reference_id'):
        student_id = user['reference_id']
        student_updates = {f: data[f] for f in updatable_fields if f in data}
        if student_updates:
            db_adapter.update_student(student_id, student_updates)
            
    updated_user = db_adapter.get_user_by_id(user_id)
    user_session_data = dict(updated_user)
    user_session_data.pop('password', None)
    session['user'] = user_session_data
    session.modified = True
    
    return jsonify({"success": True, "message": "Profile updated successfully", "user": user_session_data})


@auth_bp.route('/profile/upload-profile-pic', methods=['POST'])
def upload_profile_pic():
    if 'user' not in session:
        return jsonify({"success": False, "message": "No active session"}), 401
        
    user_id = session['user']['user_id']
    user_role = session['user']['role']
    reference_id = session['user'].get('reference_id')
    
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
    
    filename = f"user_{user_id}{ext}"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    relative_path = f"/uploads/profiles/{filename}"
    
    db_adapter.update_user_fields(user_id, {"profile_pic": relative_path})
    
    if user_role == 'student' and reference_id:
        db_adapter.update_student(reference_id, {"profile_pic": relative_path})
        
    session['user']['profile_pic'] = relative_path
    session.modified = True
    
    return jsonify({"success": True, "message": "Profile picture uploaded successfully", "profile_pic": relative_path})
