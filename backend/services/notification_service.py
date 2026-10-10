import backend.config.db_adapter as db_adapter
from backend.ai.prediction import predict_performance


class NotificationService:

    @staticmethod
    def get_chatbot_reply(reference_id, message, role='student', user_name=''):
        """
        Role-aware chatbot reply.
        - Admins  -> system-wide institutional stats
        - Students/Teachers -> personal academic data using reference_id
        """
        msg = message.lower().strip()

        # Greetings
        if any(w in msg for w in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            if role == 'admin':
                name_part = f" {user_name}" if user_name else ""
                return (
                    f"Hello{name_part}! I'm your AI Admin Advisor.\n"
                    "I can help you with:\n"
                    "- Total student & faculty counts\n"
                    "- Institution-wide attendance rates\n"
                    "- Fee collection & pending dues summary\n"
                    "- Grade distribution overview\n"
                    "- AI dropout risk insights\n\n"
                    "What would you like to know?"
                )
            else:
                return (
                    f"Hello{' ' + user_name if user_name else ''}! I'm your AI Academic Assistant.\n"
                    "You can ask me about:\n"
                    "- Your attendance status\n"
                    "- Your grades and exam marks\n"
                    "- Your fee payment status\n"
                    "- AI-powered academic risk assessment\n\n"
                    "How can I help you today?"
                )

        # System info / about / help
        if any(w in msg for w in ['about', 'what can you do', 'help', 'features', 'college', 'motto', 'vision', 'mission', 'contact', 'address', 'location', 'system']):
            return (
                "This is a comprehensive Student Management System designed to:\n"
                "- Manage class attendance and track trends\n"
                "- Record and analyse academic results\n"
                "- Predict student dropout risk using AI\n"
                "- Handle fee payments and receipts\n"
                "- Manage faculty and student registrations\n\n"
                "You can ask me anything about the above topics!"
            )

        # Route to admin or student handler
        if role == 'admin':
            return NotificationService._admin_reply(msg, user_name)

        if not reference_id:
            return (
                "I'm unable to fetch your personal data because your account does not have a linked profile ID. "
                "Please contact the administrator to resolve this."
            )

        return NotificationService._student_reply(reference_id, msg, user_name)

    @staticmethod
    def _admin_reply(msg, user_name):
        name_part = f" {user_name}" if user_name else ""

        # Student counts / registrations
        if any(w in msg for w in ['student', 'enrolled', 'registration', 'registered', 'how many']):
            students = db_adapter.get_students()
            active = db_adapter.get_all_active_students()
            total = len(students)
            active_count = len(active)
            inactive = total - active_count
            return (
                "Student Registry Overview:\n"
                f"- Total Registered Students: {total}\n"
                f"- Currently Active: {active_count}\n"
                f"- Inactive/Graduated: {inactive}\n\n"
                "For a detailed list, visit the Students section in the sidebar."
            )

        # Faculty
        if any(w in msg for w in ['faculty', 'teacher', 'staff', 'instructor', 'professor']):
            try:
                from backend.config.database import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
                fac_count = cursor.fetchone()[0]
                conn.close()
            except Exception:
                fac_count = "N/A"
            return (
                "Faculty Overview:\n"
                f"- Registered Faculty Members: {fac_count}\n\n"
                "Visit the Faculty section to manage faculty profiles, assignments, and timetables."
            )

        # Attendance — get_all_attendance_stats() returns {"total": N, "present": N}
        if any(w in msg for w in ['attendance', 'present', 'absent', 'attendance rate', 'attendance stats']):
            stats = db_adapter.get_all_attendance_stats()
            total_records = stats.get('total', 0) if stats else 0
            total_present = stats.get('present', 0) if stats else 0
            if total_records > 0:
                overall_rate = round(total_present / total_records * 100, 1)
                # Count at-risk students individually
                active_students = db_adapter.get_all_active_students()
                at_risk = 0
                for s in active_students:
                    sid = s.get('student_id', '')
                    s_stats = db_adapter.get_attendance_stats(sid)
                    if s_stats and s_stats.get('total', 0) > 0:
                        if s_stats['present'] / s_stats['total'] * 100 < 75:
                            at_risk += 1
                return (
                    "Institution-Wide Attendance Summary:\n"
                    f"- Overall Attendance Rate: {overall_rate}%\n"
                    f"- Students Below 75% (At Risk): {at_risk}\n"
                    f"- Total Attendance Records: {total_records}\n\n"
                    "Check the Attendance section for detailed student-wise logs."
                )
            return "No attendance records have been logged in the system yet."

        # Fees
        if any(w in msg for w in ['fee', 'fees', 'payment', 'pending', 'collected', 'revenue', 'due']):
            fee_stats = db_adapter.get_total_fees_collected_and_pending()
            collected = fee_stats.get('collected', 0.0)
            pending = fee_stats.get('pending', 0.0)
            total = collected + pending
            collection_pct = round(collected / total * 100, 1) if total > 0 else 0
            return (
                "Fee Collection Summary:\n"
                f"- Total Fees Collected: Rs.{collected:,.2f}\n"
                f"- Total Fees Pending: Rs.{pending:,.2f}\n"
                f"- Collection Rate: {collection_pct}%\n\n"
                "Visit the Fees section to view individual student records and send payment reminders."
            )

        # Grades — get_all_grade_distribution() returns {"A": 5, "B": 3, ...}
        if any(w in msg for w in ['grade', 'marks', 'score', 'result', 'exam', 'performance']):
            dist = db_adapter.get_all_grade_distribution()
            if dist:
                # Sort grades alphabetically for consistent output
                summary_lines = [f"- Grade {grade}: {count} student(s)" for grade, count in sorted(dist.items())]
                return (
                    "Institution-Wide Grade Distribution:\n"
                    + "\n".join(summary_lines)
                    + "\n\nVisit the Examinations section to manage exams and publish results."
                )
            return "No examination results have been recorded yet."

        # Departments
        if any(w in msg for w in ['department', 'dept', 'branch', 'division']):
            depts = db_adapter.get_departments()
            if depts:
                dept_lines = []
                for d in depts:
                    count = db_adapter.get_student_count_for_department(d.get('name', ''))
                    dept_lines.append(f"- {d.get('name', 'Unknown')}: {count} student(s)")
                return (
                    f"Departments in the System ({len(depts)} total):\n"
                    + "\n".join(dept_lines)
                )
            return "No departments have been configured yet. You can add them in the Departments section."

        # AI / dropout risk — check each student individually
        if any(w in msg for w in ['ai', 'predict', 'dropout', 'risk', 'at-risk', 'at risk', 'suggest']):
            active_students = db_adapter.get_all_active_students()
            at_risk_list = []
            for s in active_students:
                sid = s.get('student_id', '')
                s_stats = db_adapter.get_attendance_stats(sid)
                if s_stats and s_stats.get('total', 0) > 0:
                    if s_stats['present'] / s_stats['total'] * 100 < 75:
                        at_risk_list.append(f"{s.get('name', sid)} ({sid})")
            if at_risk_list:
                preview = ', '.join(at_risk_list[:10])
                extra = " (and more...)" if len(at_risk_list) > 10 else ""
                return (
                    "AI Dropout Risk Assessment Summary:\n"
                    f"- Students At Risk: {len(at_risk_list)}\n"
                    f"- Criteria: Attendance below 75%\n\n"
                    f"At-Risk Students: {preview}{extra}\n\n"
                    "Recommendation: Schedule counselling sessions and notify guardians immediately."
                )
            if active_students:
                return "Great news! No students are currently flagged as dropout risks based on attendance data."
            return "No active students found in the system to run the AI risk assessment."

        # Summary / dashboard
        if any(w in msg for w in ['summary', 'overview', 'report', 'dashboard', 'status', 'stats', 'statistics']):
            students = db_adapter.get_all_active_students()
            fee_stats = db_adapter.get_total_fees_collected_and_pending()
            # get_all_attendance_stats returns {"total": N, "present": N}
            att = db_adapter.get_all_attendance_stats()
            total_r = att.get('total', 0) if att else 0
            total_p = att.get('present', 0) if att else 0
            overall_rate = f"{round(total_p / total_r * 100, 1)}%" if total_r > 0 else "N/A"

            # Count at-risk students
            at_risk = 0
            for s in students:
                sid = s.get('student_id', '')
                s_stats = db_adapter.get_attendance_stats(sid)
                if s_stats and s_stats.get('total', 0) > 0:
                    if s_stats['present'] / s_stats['total'] * 100 < 75:
                        at_risk += 1

            return (
                "Quick System Dashboard Summary:\n"
                f"- Active Students: {len(students)}\n"
                f"- Overall Attendance Rate: {overall_rate}\n"
                f"- Students At Risk (< 75%): {at_risk}\n"
                f"- Fees Collected: Rs.{fee_stats.get('collected', 0):,.2f}\n"
                f"- Fees Pending: Rs.{fee_stats.get('pending', 0):,.2f}\n\n"
                "Ask me about specific topics like 'attendance', 'fees', or 'students' for more detail."
            )

        # Admin fallback
        return (
            f"Hello{name_part}! I'm your Admin AI Assistant.\n\n"
            "Here is what you can ask me:\n"
            "- 'How many students are enrolled?'\n"
            "- 'How many faculty members are registered?'\n"
            "- 'What is the institution attendance rate?'\n"
            "- 'Show the fee collection summary'\n"
            "- 'Show grade distribution'\n"
            "- 'Which students are at dropout risk?'\n"
            "- 'Give me a dashboard summary'\n"
            "- 'List all departments'\n\n"
            "Please ask about one of the above topics!"
        )


    @staticmethod
    def _student_reply(reference_id, msg, user_name):
        student = db_adapter.get_student_details(reference_id)
        display_name = (
            student['name'] if student and student.get('name')
            else (user_name if user_name else 'Student')
        )

        # Attendance
        if any(w in msg for w in ['attendance', 'present', 'absent', 'classes']):
            att = db_adapter.get_attendance_stats(reference_id)
            if att and att.get('total', 0) > 0:
                rate = att['present'] / att['total'] * 100
                reply = (
                    f"Hi {display_name}! Here is your attendance report:\n"
                    f"- Classes Attended: {att['present']} / {att['total']}\n"
                    f"- Attendance Rate: {round(rate, 1)}%\n\n"
                )
                if rate < 75:
                    reply += (
                        "Warning: Your attendance is below the mandatory 75% threshold!\n"
                        "You may be barred from examinations. Please attend all upcoming classes "
                        "and contact your faculty advisor immediately."
                    )
                else:
                    reply += "You meet the minimum attendance requirement and are eligible for examinations. Keep it up!"
            else:
                reply = (
                    f"Hi {display_name}! No attendance records have been logged for your profile yet. "
                    "Please contact the attendance coordinator if you believe this is an error."
                )
            return reply

        # Grades / marks
        if any(w in msg for w in ['grade', 'marks', 'score', 'exam', 'result', 'performance', 'subject']):
            marks = db_adapter.get_marks_for_student(reference_id)
            if marks:
                lines = [
                    f"- {m['subject']}: {m['marks_obtained']}/{m.get('max_marks', 100)} (Grade: {m.get('grade', 'N/A')})"
                    for m in marks if 'subject' in m
                ]
                return (
                    f"Hi {display_name}! Here are your latest examination results:\n"
                    + "\n".join(lines)
                    + "\n\nVisit the Examinations page for detailed analytics."
                )
            return (
                f"Hi {display_name}! No examination marks have been recorded for your profile yet. "
                "Please check back after your results are published."
            )

        # Fees
        if any(w in msg for w in ['fee', 'fees', 'payment', 'due', 'paid', 'pending', 'receipt']):
            fee = db_adapter.get_fee_record_by_student(reference_id)
            if fee:
                if fee.get('status') == 'Paid':
                    return (
                        f"Hi {display_name}! Your fee payment is confirmed.\n"
                        f"- Amount Paid: Rs.{fee['amount']:,.2f}\n"
                        f"- Transaction ID: {fee.get('txn_id', 'N/A')}\n"
                        f"- Payment Date: {fee.get('payment_date', 'N/A')}\n\n"
                        "Thank you for the timely payment! Download your receipt from the Fees section."
                    )
                else:
                    return (
                        f"Hi {display_name}! You have an outstanding fee payment.\n"
                        f"- Amount Due: Rs.{fee['amount']:,.2f}\n"
                        f"- Status: {fee.get('status', 'Pending')}\n\n"
                        "Please make the payment at the earliest from the Fees section to avoid penalties."
                    )
            return (
                f"Hi {display_name}! No fee record was found for your profile. "
                "Please contact the accounts office for assistance."
            )

        # AI prediction
        if any(w in msg for w in ['ai', 'predict', 'dropout', 'risk', 'at risk', 'suggest', 'advice', 'recommendation']):
            att_stats = db_adapter.get_attendance_stats(reference_id)
            att_rate = 100.0
            if att_stats and att_stats.get('total', 0) > 0:
                att_rate = att_stats['present'] / att_stats['total'] * 100

            marks = db_adapter.get_marks_for_student(reference_id)
            avg_mark = 70.0
            if marks:
                total_obt = sum(m.get('marks_obtained', 0) for m in marks)
                total_max = sum(m.get('max_marks', 100) for m in marks)
                avg_mark = (total_obt / total_max) * 100 if total_max > 0 else 0

            ai_res = predict_performance(att_rate, avg_mark)
            return (
                f"AI Academic Risk Report for {display_name}:\n"
                f"- Classification: {ai_res['status']}\n"
                f"- Performance Score: {ai_res['performance_score']}/100\n"
                f"- Attendance: {round(att_rate, 1)}%\n"
                f"- Average Marks: {round(avg_mark, 1)}%\n\n"
                f"Suggestion: {ai_res['suggestion']}"
            )

        # Student fallback
        return (
            f"Hello {display_name}! I'm your AI Academic Assistant.\n\n"
            "Here's what I can help you with:\n"
            "- 'What is my attendance?' - Check your attendance rate\n"
            "- 'Show my exam results' - View your grades and marks\n"
            "- 'Is my fee paid?' - Check fee payment status\n"
            "- 'Am I at dropout risk?' - Get your AI risk assessment\n"
            "- 'What is this system about?' - Learn about the platform\n\n"
            "Please try one of the above questions!"
        )

