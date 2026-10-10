from flask import Blueprint, request, jsonify, session
from backend.services.result_service import ResultService
from backend.utils.authentication import require_role
import backend.config.db_adapter as db_adapter


exams_bp = Blueprint('examination', __name__)

@exams_bp.route('/exams', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_exams():
    exams = ResultService.get_exams()
    return jsonify(exams)

@exams_bp.route('/exams', methods=['POST'])
@require_role(['admin', 'teacher'])
def create_exam():
    data = request.get_json() or {}
    name = data.get('name')
    subject = data.get('subject')
    date = data.get('date')
    max_marks = data.get('max_marks', 100)
    
    if not name or not subject:
        return jsonify({"success": False, "message": "Exam Name and Subject are required."}), 400
        
    success, msg = ResultService.create_exam(name, subject, date, max_marks)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@exams_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
@require_role(['admin', 'teacher'])
def delete_exam(exam_id):
    success, msg = ResultService.delete_exam(exam_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@exams_bp.route('/marks', methods=['POST'])
@require_role(['admin', 'teacher'])
def upload_marks():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    exam_id = data.get('exam_id')
    marks_obtained = data.get('marks_obtained')
    
    if not student_id or not exam_id or marks_obtained is None or str(marks_obtained).strip() == '':
        return jsonify({"success": False, "message": "Student ID, Exam ID, and Obtained Marks are required."}), 400
        
    success, msg = ResultService.submit_marks(student_id, exam_id, marks_obtained)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@exams_bp.route('/marks/batch', methods=['POST'])
@require_role(['admin', 'teacher'])
def upload_batch_marks():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    entries = data.get('entries', [])
    
    if not student_id or not entries:
        return jsonify({"success": False, "message": "Student ID and marks entries are required."}), 400
        
    saved_count = 0
    errors = []
    
    for entry in entries:
        exam_id = entry.get('exam_id')
        marks_obtained = entry.get('marks_obtained')
        if exam_id and marks_obtained is not None and str(marks_obtained).strip() != '':
            try:
                mo = float(marks_obtained)
                if mo >= 0:
                    success, msg = ResultService.submit_marks(student_id, exam_id, mo)
                    if success:
                        saved_count += 1
                    else:
                        errors.append(msg)
            except (ValueError, TypeError):
                pass
                
    if saved_count > 0:
        return jsonify({"success": True, "message": f"Successfully updated marks for {saved_count} examination(s)."})
    return jsonify({"success": False, "message": errors[0] if errors else "No valid marks were submitted."}), 400

@exams_bp.route('/marks/student/<student_id>', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_student_report_card(student_id):
    user_role = session['user']['role']
    user_ref = session['user'].get('reference_id')
    
    if user_role == 'student' and user_ref != student_id:
        return jsonify({"success": False, "message": "Unauthorized access to report card"}), 403

    card = db_adapter.get_student_academic_result_card(student_id)
    if not card:
        return jsonify({"success": False, "message": "Student record not found"}), 404
    return jsonify({"success": True, "result_card": card})

@exams_bp.route('/marks/<int:mark_id>', methods=['PUT'])
@require_role(['admin', 'teacher'])
def update_marks(mark_id):
    data = request.get_json() or {}
    marks_obtained = data.get('marks_obtained')
    max_marks = data.get('max_marks', 100)
    
    if marks_obtained is None or str(marks_obtained).strip() == '':
        return jsonify({"success": False, "message": "Marks obtained is required."}), 400
        
    try:
        marks_obtained = float(marks_obtained)
        max_marks = float(max_marks)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid marks format."}), 400
        
    if marks_obtained < 0 or marks_obtained > max_marks:
        return jsonify({"success": False, "message": f"Marks must be between 0 and {max_marks}."}), 400

    score_pct = (marks_obtained / max_marks) * 100.0
    if score_pct >= 90: grade = 'A+'
    elif score_pct >= 80: grade = 'A'
    elif score_pct >= 70: grade = 'B'
    elif score_pct >= 60: grade = 'C'
    elif score_pct >= 40: grade = 'D'
    else: grade = 'F'

    success, msg = db_adapter.update_marks_by_id(mark_id, marks_obtained, grade)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@exams_bp.route('/marks/<int:mark_id>', methods=['DELETE'])
@require_role(['admin', 'teacher'])
def delete_marks(mark_id):
    success, msg = db_adapter.delete_marks(mark_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@exams_bp.route('/exams/makeup', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_makeup_applications():
    role = session['user']['role']
    ref_id = session['user']['reference_id']
    
    apps = ResultService.get_makeup_applications(ref_id, role)
    return jsonify({"success": True, "applications": apps})

@exams_bp.route('/exams/makeup/apply', methods=['POST'])
@require_role(['student'])
def apply_makeup_exam():
    student_id = session['user']['reference_id']
    data = request.get_json() or {}
    subject = data.get('subject')
    exam_name = data.get('exam_name')
    
    if not subject or not exam_name:
        return jsonify({"success": False, "message": "Subject and exam title are required"}), 400
        
    success, msg = ResultService.apply_makeup_exam(student_id, subject, exam_name)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@exams_bp.route('/exams/makeup/pay', methods=['POST'])
@require_role(['student'])
def pay_makeup_fee():
    data = request.get_json() or {}
    app_id = data.get('app_id')
    card_num = data.get('card_number')
    
    if not app_id or not card_num:
        return jsonify({"success": False, "message": "Invalid transaction data"}), 400
        
    student_id = session['user']['reference_id']
    success, result = ResultService.pay_makeup_fee(app_id, student_id, card_num)
    
    if success:
        return jsonify({"success": True, "message": "Fee paid successfully", "txn_id": result})
    return jsonify({"success": False, "message": result}), 400

@exams_bp.route('/exams/hallticket/<student_id>', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_hall_ticket(student_id):
    if session['user']['role'] == 'student' and session['user']['reference_id'] != student_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    ticket = ResultService.get_hall_ticket(student_id)
    if not ticket:
        return jsonify({"success": False, "message": "Student not found"}), 404
        
    return jsonify({"success": True, "hall_ticket": ticket})
