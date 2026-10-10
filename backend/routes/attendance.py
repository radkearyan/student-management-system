from flask import Blueprint, request, jsonify, session, send_file
from backend.services.attendance_service import AttendanceService
from backend.utils.authentication import require_role
from backend.utils.pdf_generator import PDFGenerator
import backend.config.db_adapter as db_adapter

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_attendance_logs():
    student_id = request.args.get('student_id', '').strip()
    department = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()
    date = request.args.get('date', '').strip()
    subject_code = request.args.get('subject_code', '').strip()
    
    # Students can only check their own attendance
    if session['user']['role'] == 'student':
        student_id = session['user']['reference_id']
        
    # Faculty / Teachers can ONLY check their own department's attendance
    if session['user']['role'] == 'teacher':
        teacher_dept = session['user'].get('department')
        if teacher_dept:
            department = teacher_dept
        
    logs = db_adapter.get_attendance_logs(
        student_id=student_id,
        department=department,
        status=status,
        date=date,
        subject_code=subject_code
    )
    return jsonify(logs)

@attendance_bp.route('/summary/<student_id>', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_student_attendance_summary_route(student_id):
    user_role = session['user']['role']
    user_ref = session['user'].get('reference_id')
    
    # Students can only view their own summary
    if user_role == 'student' and user_ref != student_id:
        return jsonify({"success": False, "message": "Unauthorized access to student attendance summary"}), 403

    summary = db_adapter.get_student_attendance_summary(student_id)
    return jsonify({"success": True, "summary": summary})

@attendance_bp.route('', methods=['POST'])
@require_role(['admin', 'teacher'])
def record_attendance():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    status = data.get('status', 'Present')
    date = data.get('date')
    subject_code = data.get('subject_code', 'CS101')
    
    if not student_id:
        return jsonify({"success": False, "message": "Student ID is required."}), 400
        
    # Faculty can only record attendance for students in their registered department
    if session['user']['role'] == 'teacher':
        teacher_dept = session['user'].get('department')
        if teacher_dept:
            student = db_adapter.get_student_details(student_id)
            if student and student.get('department') != teacher_dept:
                return jsonify({
                    "success": False, 
                    "message": f"Unauthorized: As faculty of {teacher_dept}, you can only record attendance for {teacher_dept} students."
                }), 403
        
    success, msg = db_adapter.record_attendance(student_id, date, status, 'Manual', subject_code)
    
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@attendance_bp.route('/bulk', methods=['POST'])
@require_role(['admin', 'teacher'])
def bulk_record_attendance_route():
    data = request.get_json() or {}
    date_str = data.get('date')
    subject_code = data.get('subject_code', 'CS101')
    records = data.get('records', [])
    
    if not date_str or not records:
        return jsonify({"success": False, "message": "Date and student records list are required."}), 400
        
    success, msg = db_adapter.bulk_record_attendance(records, date_str, subject_code=subject_code)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@attendance_bp.route('/export/pdf', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def export_attendance_pdf():
    student_id = request.args.get('student_id', '').strip()
    department = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()
    date = request.args.get('date', '').strip()
    subject_code = request.args.get('subject_code', '').strip()

    user = session.get('user', {})
    user_role = user.get('role', '')

    if user_role == 'student':
        student_id = user.get('reference_id', '')
    elif user_role == 'teacher':
        teacher_dept = user.get('department')
        if teacher_dept:
            department = teacher_dept

    logs = db_adapter.get_attendance_logs(
        student_id=student_id,
        department=department,
        status=status,
        date=date,
        subject_code=subject_code
    )

    metadata = {
        'generated_by': f"{user.get('name', user.get('username', 'Staff'))} ({user_role.title()})",
        'department': department or 'All Departments',
        'date': date or 'All Recorded Dates',
        'status': status or 'All Statuses',
        'student_id': student_id
    }

    pdf_buffer = PDFGenerator.generate_attendance_pdf(logs, metadata=metadata)
    
    clean_dept = (department or 'all').replace(' ', '_').lower()
    clean_date = (date or 'recent').replace(' ', '_')
    filename = f"attendance_report_{clean_dept}_{clean_date}.pdf"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
