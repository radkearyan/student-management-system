-- Triggers for Student Management System

-- Automatically initialize a Tuition Fee ledger entry of 1500.0 when a student is created
CREATE TRIGGER IF NOT EXISTS auto_init_student_fee
AFTER INSERT ON students
BEGIN
    INSERT INTO fees (student_id, amount, status)
    VALUES (NEW.student_id, 1500.0, 'Pending');
END;
