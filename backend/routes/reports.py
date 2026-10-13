import csv
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_file
import backend.config.db_adapter as db_adapter
from backend.utils.authentication import require_role
from backend.utils.pdf_generator import PDFGenerator
from backend.ai.prediction import predict_performance

reports_bp = Blueprint('reports', __name__)

def make_csv_stream(records, headers, filename):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    for row in records:
        writer.writerow(row)
    
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# 1. Student Search, Filtering & Reports
@reports_bp.route('/students', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_students_report():
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    course = request.args.get('course', '').strip()
    export_fmt = request.args.get('export', 'json').strip().lower()

    user_role = session['user']['role']
    if user_role == 'teacher':
        teacher_dept = session['user'].get('department')
        if teacher_dept:
            department = teacher_dept

    students = db_adapter.get_students(search_query=search, department=department)
    if course:
        students = [s for s in students if course.lower() in str(s.get('course', '')).lower()]

    if export_fmt == 'csv':
        headers = ['student_id', 'name', 'email', 'phone', 'department', 'course', 'gender', 'dob', 'created_at']
        return make_csv_stream(students, headers, 'students_report.csv')
    elif export_fmt == 'pdf':
        user_name = session['user'].get('name', 'Staff')
        metadata = {
            'department': department or 'All Departments',
            'course': course or 'All Courses',
            'generated_by': f"{user_name} ({user_role.title()})"
        }
        pdf_buf = PDFGenerator.generate_student_list_pdf(students, metadata=metadata)
        return send_file(pdf_buf, mimetype='application/pdf', as_attachment=True, download_name='students_report.pdf')

    return jsonify({"success": True, "count": len(students), "students": students})

# 2. Attendance Search, Filtering & Reports
@reports_bp.route('/attendance', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_attendance_report():
    student_id = request.args.get('student_id', '').strip()
    department = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()
    date = request.args.get('date', '').strip()
    subject_code = request.args.get('subject_code', '').strip()
    export_fmt = request.args.get('export', 'json').strip().lower()

    user_role = session['user']['role']
    user_ref = session['user'].get('reference_id')

    if user_role == 'student':
        student_id = user_ref
    elif user_role == 'teacher':
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

    if export_fmt == 'csv':
        headers = ['log_id', 'student_id', 'name', 'department', 'subject_code', 'date', 'status', 'method']
        return make_csv_stream(logs, headers, 'attendance_report.csv')
    elif export_fmt == 'pdf':
        user_name = session['user'].get('name', 'Staff')
        metadata = {
            'department': department or 'All Departments',
            'date': date or 'All Recorded Dates',
            'generated_by': f"{user_name} ({user_role.title()})",
            'student_id': student_id
        }
        pdf_buf = PDFGenerator.generate_attendance_pdf(logs, metadata=metadata)
        return send_file(pdf_buf, mimetype='application/pdf', as_attachment=True, download_name='attendance_report.pdf')

    return jsonify({"success": True, "count": len(logs), "logs": logs})

# 3. Marks & Results Search, Filtering & Reports
@reports_bp.route('/results', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_results_report():
    student_id = request.args.get('student_id', '').strip()
    department = request.args.get('department', '').strip()
    subject = request.args.get('subject', '').strip()
    grade = request.args.get('grade', '').strip()
    status = request.args.get('status', '').strip()
    export_fmt = request.args.get('export', 'json').strip().lower()

    user_role = session['user']['role']
    user_ref = session['user'].get('reference_id')

    if user_role == 'student':
        student_id = user_ref

    marks_list = db_adapter.get_all_filtered_marks(
        student_id=student_id,
        subject=subject,
        grade=grade,
        status=status,
        department=department
    )

    if export_fmt == 'csv':
        headers = ['mark_id', 'student_id', 'name', 'department', 'exam_name', 'subject', 'marks_obtained', 'max_marks', 'percentage', 'grade', 'status']
        return make_csv_stream(marks_list, headers, 'academic_results_report.csv')
    elif export_fmt == 'pdf':
        user_name = session['user'].get('name', 'Staff')
        metadata = {
            'subject': subject or 'All Subjects',
            'status': status or 'All Statuses',
            'generated_by': f"{user_name} ({user_role.title()})"
        }
        pdf_buf = PDFGenerator.generate_marks_report_pdf(marks_list, metadata=metadata)
        return send_file(pdf_buf, mimetype='application/pdf', as_attachment=True, download_name='academic_results_report.pdf')

    return jsonify({"success": True, "count": len(marks_list), "marks": marks_list})

# 4. Faculty Search & Filtering Report
@reports_bp.route('/faculty', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_faculty_report():
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    export_fmt = request.args.get('export', 'json').strip().lower()

    faculty_list = db_adapter.get_faculty_members(department=department, search=search)

    if export_fmt == 'csv':
        headers = ['faculty_id', 'name', 'email', 'phone', 'department', 'designation']
        return make_csv_stream(faculty_list, headers, 'faculty_report.csv')

    return jsonify({"success": True, "count": len(faculty_list), "faculty": faculty_list})

# 5. Subjects Search & Filtering Report
@reports_bp.route('/subjects', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_subjects_report():
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    course = request.args.get('course', '').strip()
    export_fmt = request.args.get('export', 'json').strip().lower()

    subjects_list = db_adapter.get_subjects(department=department, search=search)

    if export_fmt == 'csv':
        headers = ['subject_id', 'subject_code', 'name', 'department', 'course', 'semester', 'credits']
        return make_csv_stream(subjects_list, headers, 'subjects_report.csv')

    return jsonify({"success": True, "count": len(subjects_list), "subjects": subjects_list})


# Student Feedback & AI Dropout Prediction
feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('', methods=['GET'])
@feedback_bp.route('/', methods=['GET'])
@reports_bp.route('/feedback', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_feedback():
    role = session['user']['role']
    ref_id = session['user'].get('reference_id', '') or session['user'].get('username', '') or ''
    rows = db_adapter.get_feedback(student_id=ref_id, role=role)
    return jsonify({"success": True, "feedback": rows})

@feedback_bp.route('/submit', methods=['POST'])
@reports_bp.route('/feedback/submit', methods=['POST'])
@require_role(['student'])
def submit_feedback():
    student_id = str(session['user'].get('reference_id') or session['user'].get('username') or 'STU001').strip()
    data = request.get_json() or {}
    subject = str(data.get('subject', '')).strip()
    faculty_name = str(data.get('faculty_name', '')).strip()
    q1 = data.get('q1')
    q2 = data.get('q2')
    q3 = data.get('q3')
    q4 = data.get('q4')
    q5 = data.get('q5')
    comments = str(data.get('comments', '')).strip()
    
    if not subject or not faculty_name or any(q is None for q in [q1, q2, q3, q4, q5]):
        return jsonify({"success": False, "message": "Missing feedback parameters"}), 400
        
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        success, err = db_adapter.submit_feedback(
            student_id, subject, faculty_name, q1, q2, q3, q4, q5, comments, created_at
        )
        if not success:
            return jsonify({"success": False, "message": err or "Failed to submit feedback"}), 400
        return jsonify({"success": True, "message": "Feedback submitted successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@reports_bp.route('/ai/predictions/dropout', methods=['GET'])
@require_role(['admin', 'teacher'])
def predict_dropout_risks():
    students = db_adapter.get_all_active_students()
    high_risk_list = []
    
    # Batch load all student attendance and marks in 2 fast queries
    att_map, marks_map = db_adapter.get_all_student_academic_metrics()
    
    for s in students:
        sid = s['student_id']
        att_rate = att_map.get(sid, 100.0)
        avg_mark = marks_map.get(sid, 70.0)
            
        ai_res = predict_performance(att_rate, avg_mark)
        
        if ai_res['status'] == 'High Risk' or att_rate < 70.0:
            high_risk_list.append({
                "student_id": sid,
                "name": s.get('name', ''),
                "department": s.get('department', ''),
                "course": s.get('course', ''),
                "attendance_rate": round(att_rate, 1),
                "avg_marks": round(avg_mark, 1),
                "performance_score": ai_res['performance_score'],
                "suggestion": ai_res['suggestion']
            })
            
    return jsonify({
        "success": True,
        "high_dropout_risk_students": high_risk_list
    })
