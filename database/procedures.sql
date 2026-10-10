-- Stored Procedures and Views for Student Management System
-- Note: SQLite does not support stored procedures natively, so views are used to encapsulate complex queries.

-- View: Aggregates student name, department, average exam grades, and attendance rate
CREATE VIEW IF NOT EXISTS student_academic_summary AS
SELECT 
    s.student_id,
    s.name,
    s.department,
    s.course,
    s.current_semester,
    IFNULL(AVG(m.marks_obtained), 0) AS avg_marks,
    IFNULL((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0) / COUNT(a.attendance_id), 100.0) AS attendance_rate
FROM students s
LEFT JOIN marks m ON s.student_id = m.student_id
LEFT JOIN attendance a ON s.student_id = a.student_id
GROUP BY s.student_id;
