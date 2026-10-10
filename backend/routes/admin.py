from flask import Blueprint, jsonify, request, session
import backend.config.db_adapter as db_adapter
from backend.utils.authentication import require_role
from backend.ai.prediction import predict_performance

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/analytics', methods=['GET'])
@require_role(['admin', 'teacher'])
def get_dashboard_analytics():
    students = db_adapter.get_students()
    total_students = len(students)
    recent_students = students[:5]
    
    depts = db_adapter.get_departments()
    total_depts = len(depts)
    
    faculty_list = db_adapter.get_faculty_members()
    total_faculty = len(faculty_list)
    
    courses_list = db_adapter.get_courses()
    total_courses = len(courses_list)
    
    subjects_list = db_adapter.get_subjects()
    total_subjects = len(subjects_list)
    
    announcements_list = db_adapter.get_announcements()
    recent_announcements = announcements_list[:5]
    
    fees_stats = db_adapter.get_total_fees_collected_and_pending()
    fees_collected = fees_stats['collected']
    fees_pending = fees_stats['pending']
    
    att_stats = db_adapter.get_all_attendance_stats()
    avg_attendance = 100.0
    if att_stats and att_stats['total'] > 0:
        avg_attendance = (att_stats['present'] / att_stats['total']) * 100
        
    dept_enrollments = {}
    for s in students:
        dept = s.get('department')
        if dept:
            dept_enrollments[dept] = dept_enrollments.get(dept, 0) + 1
            
    grade_distribution = db_adapter.get_all_grade_distribution()
    analytics_extra = db_adapter.get_dashboard_analytics_data()
    
    high_risk_count = 0
    mod_risk_count = 0
    low_risk_count = 0
    
    for s in students:
        sid = s['student_id']
        att_stats = db_adapter.get_attendance_stats(sid)
        att_rate = 100.0
        if att_stats and att_stats['total'] > 0:
            att_rate = float(att_stats['present']) / att_stats['total'] * 100
            
        marks = db_adapter.get_marks_for_student(sid)
        avg_mark = 70.0
        if marks:
            total_obt = sum([m['marks_obtained'] for m in marks])
            total_max = sum([m['max_marks'] for m in marks])
            avg_mark = (total_obt / total_max) * 100 if total_max > 0 else 0
            
        ai_res = predict_performance(att_rate, avg_mark)
        if ai_res['status'] == 'High Risk':
            high_risk_count += 1
        elif ai_res['status'] == 'Moderate Risk':
            mod_risk_count += 1
        else:
            low_risk_count += 1
            
    return jsonify({
        "success": True,
        "metrics": {
            "total_students": total_students,
            "total_departments": total_depts,
            "total_faculty": total_faculty,
            "total_courses": total_courses,
            "total_subjects": total_subjects,
            "average_attendance": round(avg_attendance, 1),
            "fees_collected": fees_collected,
            "fees_pending": fees_pending
        },
        "recent_students": recent_students,
        "recent_announcements": recent_announcements,
        "recent_activities": db_adapter.get_recent_activities(),
        "department_distribution": dept_enrollments,
        "students_by_branch": analytics_extra.get('students_by_branch', {}),
        "students_by_year": analytics_extra.get('students_by_year', {}),
        "attendance_distribution": analytics_extra.get('attendance_distribution', {}),
        "subject_performance": analytics_extra.get('subject_performance', {}),
        "pass_fail_distribution": analytics_extra.get('pass_fail_distribution', {}),
        "grade_distribution": grade_distribution,
        "ai_risk_distribution": {
            "High Risk": high_risk_count,
            "Moderate Risk": mod_risk_count,
            "Low Risk": low_risk_count
        }
    })

@admin_bp.route('/search', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def global_search():
    q = request.args.get('q', '').strip()
    results = db_adapter.search_all(q)
    return jsonify({"success": True, "query": q, "results": results})

@admin_bp.route('/announcements', methods=['GET'])
def get_announcements_route():
    role = session.get('user', {}).get('role', 'student')
    dept = session.get('user', {}).get('department', 'All')
    announcements = db_adapter.get_announcements(target_role=role, department=dept)
    return jsonify({"success": True, "announcements": announcements})

@admin_bp.route('/announcements', methods=['POST'])
@require_role(['admin', 'teacher'])
def post_announcement_route():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    message = data.get('message', '').strip()
    target_role = data.get('target_role', 'all')
    department = data.get('department', 'All')
    posted_by = session.get('user', {}).get('name') or session.get('user', {}).get('username', 'Admin')
    
    if not title or not message:
        return jsonify({"success": False, "message": "Title and message are required"}), 400
        
    success, res = db_adapter.add_announcement(title, message, target_role, department, posted_by)
    if success:
        return jsonify({"success": True, "message": "Announcement posted successfully"})
    return jsonify({"success": False, "message": str(res)}), 400

@admin_bp.route('/announcements/<int:announcement_id>', methods=['PUT'])
@require_role(['admin', 'teacher'])
def update_announcement_route(announcement_id):
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    message = data.get('message', '').strip()
    target_role = data.get('target_role', 'all')
    department = data.get('department', 'All')

    if not title or not message:
        return jsonify({"success": False, "message": "Title and message are required"}), 400

    success, msg = db_adapter.update_announcement(announcement_id, title, message, target_role, department)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@admin_bp.route('/announcements/<int:announcement_id>', methods=['DELETE'])
@require_role(['admin', 'teacher'])
def delete_announcement_route(announcement_id):
    success, msg = db_adapter.delete_announcement(announcement_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@admin_bp.route('/departments', methods=['GET'])
def get_departments():
    depts = db_adapter.get_departments()
    return jsonify(depts)

@admin_bp.route('/departments', methods=['POST'])
@require_role(['admin'])
def add_department():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"success": False, "message": "Department name is required"}), 400
    
    success, err = db_adapter.add_department(name)
    if success:
        return jsonify({"success": True, "message": "Department added successfully"})
    return jsonify({"success": False, "message": err or "Failed to add department"}), 400

@admin_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@require_role(['admin'])
def delete_department(dept_id):
    dept = db_adapter.get_department_by_id(dept_id)
    if not dept:
        return jsonify({"success": False, "message": "Department not found"}), 404
    
    # Check if any student is assigned to this department
    student_count = db_adapter.get_student_count_for_department(dept['name'])
    if student_count > 0:
        return jsonify({"success": False, "message": f"Cannot delete department. {student_count} student(s) currently enrolled."}), 400
        
    db_adapter.delete_department(dept_id)
    return jsonify({"success": True, "message": "Department deleted successfully"})
