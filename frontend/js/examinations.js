// Examinations and Academic Results Management

let EXAMS_LIST = [];
let ALL_STUDENTS = [];
let ALL_SUBJECTS = [];

document.addEventListener("DOMContentLoaded", () => {
    const isStudent = STATE.user && STATE.user.role === 'student';
    if (isStudent) {
        loadStudentAcademicReportCard();
        return;
    }

    // Modal Trigger Buttons
    const btnCreateExam = document.getElementById('btn-open-create-exam-modal');
    if (btnCreateExam) btnCreateExam.addEventListener('click', openCreateExamModal);

    const btnEnterMarks = document.getElementById('btn-open-enter-marks-modal');
    if (btnEnterMarks) btnEnterMarks.addEventListener('click', openEnterMarksModal);

    // Modal Close Buttons
    const btnCloseExam = document.getElementById('btn-close-exam-modal');
    const btnCancelExam = document.getElementById('btn-cancel-exam-modal');
    if (btnCloseExam) btnCloseExam.addEventListener('click', closeCreateExamModal);
    if (btnCancelExam) btnCancelExam.addEventListener('click', closeCreateExamModal);

    const btnCloseMarks = document.getElementById('btn-close-marks-modal');
    const btnCancelMarks = document.getElementById('btn-cancel-marks-modal');
    if (btnCloseMarks) btnCloseMarks.addEventListener('click', closeEnterMarksModal);
    if (btnCancelMarks) btnCancelMarks.addEventListener('click', closeEnterMarksModal);

    const btnCloseEdit = document.getElementById('btn-close-edit-marks-modal');
    const btnCancelEdit = document.getElementById('btn-cancel-edit-marks-modal');
    if (btnCloseEdit) btnCloseEdit.addEventListener('click', closeEditMarksModal);
    if (btnCancelEdit) btnCancelEdit.addEventListener('click', closeEditMarksModal);

    const btnCloseReport = document.getElementById('btn-close-report-modal');
    if (btnCloseReport) btnCloseReport.addEventListener('click', closeReportCardModal);

    // Forms
    const createExamForm = document.getElementById('create-exam-form');
    if (createExamForm) createExamForm.addEventListener('submit', handleCreateExamSubmit);

    const enterMarksForm = document.getElementById('enter-marks-form');
    if (enterMarksForm) enterMarksForm.addEventListener('submit', handleEnterMarksSubmit);

    const editMarksForm = document.getElementById('edit-marks-form');
    if (editMarksForm) editMarksForm.addEventListener('submit', handleEditMarksSubmit);

    // Filters
    const studentFilter = document.getElementById('exam-student-filter');
    if (studentFilter) studentFilter.addEventListener('change', loadExamsAndMarksView);

    const markStudentSelect = document.getElementById('mark-student-select');
    if (markStudentSelect) markStudentSelect.addEventListener('change', renderBatchSubjectInputs);

    // Initial Load
    loadExamsAndMarksView();
});

async function loadExamsAndMarksView() {
    try {
        const [examsRes, studentsRes, subjectsRes] = await Promise.all([
            API.get('/api/exams'),
            API.get('/api/students'),
            API.get('/api/subjects')
        ]);

        EXAMS_LIST = examsRes || [];
        ALL_STUDENTS = studentsRes || [];
        ALL_SUBJECTS = (subjectsRes && subjectsRes.subjects) ? subjectsRes.subjects : (subjectsRes || []);

        populateExamDropdowns();
        renderExamsList(EXAMS_LIST);
        loadStudentMarksTable();
    } catch (err) {
        console.error("Error loading examination dashboard:", err);
    }
}

function populateExamDropdowns() {
    const studentFilter = document.getElementById('exam-student-filter');
    const markStudentSelect = document.getElementById('mark-student-select');
    const markExamSelect = document.getElementById('mark-exam-select');

    if (studentFilter) {
        studentFilter.innerHTML = '<option value="">-- All Students Results --</option>';
        ALL_STUDENTS.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.student_id;
            opt.textContent = `${s.name} (${s.student_id})`;
            studentFilter.appendChild(opt);
        });
    }

    if (markStudentSelect) {
        markStudentSelect.innerHTML = '<option value="">-- Choose Student --</option>';
        ALL_STUDENTS.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.student_id;
            opt.textContent = `${s.name} (${s.student_id}) - ${s.department || ''}`;
            markStudentSelect.appendChild(opt);
        });
    }

    if (markExamSelect) {
        markExamSelect.innerHTML = '<option value="">-- Select Examination --</option>';
        EXAMS_LIST.forEach(e => {
            const opt = document.createElement('option');
            opt.value = e.exam_id;
            opt.textContent = `${e.name} (${e.subject}) [Max: ${e.max_marks || 100}]`;
            markExamSelect.appendChild(opt);
        });
    }

    // Populate subject select for creating exam
    const examSubSelect = document.getElementById('exam-subject-select');
    if (examSubSelect) {
        let opts = '<option value="">-- Select Subject --</option>';
        ALL_SUBJECTS.forEach(s => {
            opts += `<option value="${s.subject_name || s.name}">${s.subject_code} - ${s.subject_name || s.name}</option>`;
        });
        examSubSelect.innerHTML = opts;
    }
}

function renderExamsList(exams) {
    const container = document.getElementById('exams-cards-container');
    if (!container) return;

    if (!exams || exams.length === 0) {
        container.innerHTML = `
            <div class="empty-category-notice glassmorphism" style="padding: 2rem; text-align: center; color: var(--text-muted);">
                No examination definitions created yet.
            </div>
        `;
        return;
    }

    let html = '';
    exams.forEach(e => {
        html += `
            <div class="glassmorphism" style="padding: 1.25rem; border-radius: 12px; display: flex; flex-direction: column; justify-content: space-between; gap: 0.75rem;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
                        <span class="badge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; font-weight: 700;">${e.subject}</span>
                        <span style="font-size: 0.8rem; color: var(--accent-gold); font-weight: 600;">Max: ${e.max_marks || 100} Marks</span>
                    </div>
                    <h4 style="font-size: 1.05rem; font-weight: 700; margin-top: 8px;">${e.name}</h4>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                        <span style="font-size: 0.8rem; color: var(--text-muted);"><i class="fa-solid fa-calendar-day"></i> Date: ${e.date || 'TBD'}</span>
                        <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem; color: var(--danger); border-color: var(--danger);" onclick="deleteExam('${e.exam_id}')" title="Delete Examination">
                            <i class="fa-solid fa-trash-can"></i> Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

async function deleteExam(examId) {
    showConfirmModal("Confirm Exam Deletion", "Are you sure you want to delete this examination definition? Associated student marks records will also be deleted.", async () => {
        const res = await API.delete(`/api/exams/${examId}`);
        if (res && res.success) {
            showToast("Exam Deleted", res.message || "Examination deleted successfully.", "success");
            loadExamsAndMarksView();
        } else {
            showToast("Error", res.message || "Failed to delete examination.", "error");
        }
    });
}

async function loadStudentMarksTable() {
    const body = document.getElementById('marks-table-body');
    if (!body) return;

    const studentFilter = document.getElementById('exam-student-filter');
    const selectedStudent = studentFilter ? studentFilter.value : '';

    if (selectedStudent) {
        const res = await API.get(`/api/marks/student/${selectedStudent}`);
        if (res && res.success && res.result_card) {
            renderMarksRecordsTable(res.result_card.marks_records, res.result_card);
        } else {
            body.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2rem;">No marks records found for this student.</td></tr>`;
        }
    } else {
        // Load default students sample marks
        if (ALL_STUDENTS.length > 0) {
            const defaultSid = ALL_STUDENTS[0].student_id;
            const res = await API.get(`/api/marks/student/${defaultSid}`);
            if (res && res.success && res.result_card) {
                renderMarksRecordsTable(res.result_card.marks_records, res.result_card);
            } else {
                body.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2rem;">Select a student to view academic marks.</td></tr>`;
            }
        } else {
            body.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2rem;">No student records available.</td></tr>`;
        }
    }
}

function renderMarksRecordsTable(records, card) {
    const body = document.getElementById('marks-table-body');
    const summaryCard = document.getElementById('report-card-summary-pill');
    if (!body) return;

    if (summaryCard && card) {
        const isPass = card.overall_status === 'PASS';
        summaryCard.innerHTML = `
            <div style="display: flex; gap: 1rem; align-items: center; background: rgba(0,0,0,0.2); padding: 0.75rem 1.25rem; border-radius: 10px; border: 1px solid var(--glass-border);">
                <div><strong>${card.name}</strong> (${card.student_id})</div>
                <div style="color: var(--accent-gold);">Total: <strong>${card.total_obtained} / ${card.total_max}</strong></div>
                <div>Percentage: <strong>${card.overall_percentage}%</strong></div>
                <div>Grade: <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); font-weight: 700;">${card.overall_grade}</span></div>
                <div>Status: <span class="badge" style="background: ${isPass ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}; color: ${isPass ? 'var(--success)' : 'var(--danger)'}; font-weight: 700;">${card.overall_status}</span></div>
                <button class="btn btn-outline btn-small" onclick="viewAcademicReportCard('${card.student_id}')" style="margin-left: auto;">
                    <i class="fa-solid fa-file-invoice"></i> View Report Card
                </button>
            </div>
        `;
    }

    if (!records || records.length === 0) {
        body.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2rem;">No marks recorded for this student.</td></tr>`;
        return;
    }

    let html = '';
    records.forEach(r => {
        const isPass = r.status === 'PASS';
        html += `
            <tr>
                <td><strong>${r.exam_name}</strong></td>
                <td><span class="badge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; font-weight: 600;">${r.subject}</span></td>
                <td><strong>${r.marks_obtained}</strong> / ${r.max_marks}</td>
                <td><strong>${r.percentage}%</strong></td>
                <td><span class="badge" style="background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); font-weight: 700;">${r.grade}</span></td>
                <td><span class="badge" style="background: ${isPass ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}; color: ${isPass ? 'var(--success)' : 'var(--danger)'}; font-weight: 700;">${r.status}</span></td>
                <td style="text-align: right;">
                    <div style="display: flex; justify-content: flex-end; gap: 6px;">
                        <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem;" onclick="openEditMarksModal('${r.mark_id}', '${r.marks_obtained}', '${r.max_marks}')" title="Edit Marks">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem; color: var(--danger); border-color: var(--danger);" onclick="deleteMarksRecord('${r.mark_id}')" title="Delete Marks">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    body.innerHTML = html;
}

/**
 * Modal Open / Close / Handlers
 */
function openCreateExamModal() {
    const modal = document.getElementById('create-exam-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeCreateExamModal() {
    const modal = document.getElementById('create-exam-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleCreateExamSubmit(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('exam-name-input').value.trim(),
        subject: document.getElementById('exam-subject-select').value.trim(),
        date: document.getElementById('exam-date-input').value,
        max_marks: parseInt(document.getElementById('exam-max-marks').value || 100)
    };

    if (!payload.name || !payload.subject) {
        showToast("Validation Error", "Exam Name and Subject are required.", "warning");
        return;
    }

    const res = await API.post('/api/exams', payload);
    if (res && res.success) {
        showToast("Exam Created", res.message || "Exam created successfully.", "success");
        closeCreateExamModal();
        loadExamsAndMarksView();
    } else {
        showToast("Error", res.message || "Failed to create exam.", "error");
    }
}

function openEnterMarksModal() {
    const modal = document.getElementById('enter-marks-modal');
    if (modal) {
        modal.classList.remove('hidden');
        renderBatchSubjectInputs();
    }
}

function closeEnterMarksModal() {
    const modal = document.getElementById('enter-marks-modal');
    if (modal) modal.classList.add('hidden');
}

async function renderBatchSubjectInputs() {
    const container = document.getElementById('batch-marks-subjects-container');
    if (!container) return;

    const studentSelect = document.getElementById('mark-student-select');
    const studentId = studentSelect ? studentSelect.value : '';

    if (!studentId) {
        container.innerHTML = `
            <div class="text-center text-muted" style="padding: 2rem; background: rgba(0,0,0,0.15); border-radius: 8px;">
                <i class="fa-solid fa-hand-pointer" style="font-size: 1.5rem; margin-bottom: 8px; display: block; color: var(--accent-gold);"></i>
                Select a student above to load their subject examinations list.
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="text-center text-muted" style="padding: 1.5rem;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size: 1.5rem; margin-bottom: 8px; color: var(--accent-blue);"></i>
            Loading student's subject examinations...
        </div>
    `;

    let existingMarksMap = {};
    try {
        const res = await API.get(`/api/marks/student/${studentId}`);
        if (res && res.success && res.result_card && res.result_card.marks_records) {
            res.result_card.marks_records.forEach(m => {
                existingMarksMap[m.exam_id] = m.marks_obtained;
            });
        }
    } catch (err) {
        console.error("Failed to fetch student marks:", err);
    }

    if (!EXAMS_LIST || EXAMS_LIST.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted" style="padding: 1.5rem; background: rgba(0,0,0,0.15); border-radius: 8px;">
                No examination definitions found. Please create exam definitions first.
            </div>
        `;
        return;
    }

    let html = '';
    EXAMS_LIST.forEach(e => {
        const maxM = e.max_marks || 100;
        const currentVal = existingMarksMap[e.exam_id] !== undefined ? existingMarksMap[e.exam_id] : '';
        html += `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.85rem 1rem; background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border); border-radius: 8px; gap: 1rem;">
                <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 2px;">
                        <span class="badge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; font-weight: 600; font-size: 0.75rem;">${e.subject}</span>
                        <span style="font-size: 0.75rem; color: var(--accent-gold); font-weight: 600;">Max: ${maxM} Marks</span>
                    </div>
                    <strong style="font-size: 0.95rem; color: var(--text-color); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${e.name}</strong>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <input type="number" 
                           class="batch-mark-input form-control" 
                           data-exam-id="${e.exam_id}" 
                           data-max-marks="${maxM}" 
                           data-exam-name="${e.name}" 
                           step="0.5" 
                           min="0" 
                           max="${maxM}" 
                           placeholder="0 - ${maxM}" 
                           value="${currentVal}" 
                           style="width: 110px; text-align: right; font-weight: 700;">
                    <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">/ ${maxM}</span>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

async function handleEnterMarksSubmit(e) {
    e.preventDefault();

    const studentSelect = document.getElementById('mark-student-select');
    const student_id = studentSelect ? studentSelect.value : '';

    if (!student_id) {
        showToast("Validation Error", "Please select a student first.", "warning");
        return;
    }

    const inputs = document.querySelectorAll('.batch-mark-input');
    const entries = [];
    let hasError = false;

    inputs.forEach(input => {
        const valStr = input.value.trim();
        if (valStr !== '') {
            const val = parseFloat(valStr);
            const maxMarks = parseFloat(input.dataset.maxMarks || 100);
            const examName = input.dataset.examName || 'Exam';

            if (isNaN(val) || val < 0 || val > maxMarks) {
                showToast("Invalid Marks", `Marks for "${examName}" must be between 0 and ${maxMarks}.`, "warning");
                hasError = true;
                return;
            }

            entries.push({
                exam_id: parseInt(input.dataset.examId),
                marks_obtained: val
            });
        }
    });

    if (hasError) return;

    if (entries.length === 0) {
        showToast("Validation Error", "Please enter marks for at least one examination.", "warning");
        return;
    }

    const res = await API.post('/api/marks/batch', {
        student_id: student_id,
        entries: entries
    });

    if (res && res.success) {
        showToast("Marks Saved", res.message || "Student marks saved successfully.", "success");
        closeEnterMarksModal();
        const studentFilter = document.getElementById('exam-student-filter');
        if (studentFilter) {
            studentFilter.value = student_id;
        }
        loadStudentMarksTable();
    } else {
        showToast("Error", res.message || "Failed to save marks.", "error");
    }
}

function openEditMarksModal(markId, currentObtained, maxMarks) {
    document.getElementById('edit-mark-id').value = markId;
    document.getElementById('edit-mark-obtained').value = currentObtained;
    document.getElementById('edit-mark-max').value = maxMarks;

    const modal = document.getElementById('edit-marks-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeEditMarksModal() {
    const modal = document.getElementById('edit-marks-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleEditMarksSubmit(e) {
    e.preventDefault();

    const markId = document.getElementById('edit-mark-id').value;
    const obtained_str = document.getElementById('edit-mark-obtained').value.trim();
    const max_marks = parseFloat(document.getElementById('edit-mark-max').value || 100);

    if (obtained_str === '') {
        showToast("Validation Error", "Marks obtained field is required.", "warning");
        return;
    }

    const marks_obtained = parseFloat(obtained_str);
    if (isNaN(marks_obtained) || marks_obtained < 0 || marks_obtained > max_marks) {
        showToast("Invalid Marks", `Marks must be a valid number between 0 and ${max_marks}.`, "warning");
        return;
    }

    const res = await API.put(`/api/marks/${markId}`, {
        marks_obtained: marks_obtained,
        max_marks: max_marks
    });

    if (res && res.success) {
        showToast("Marks Updated", res.message || "Marks updated successfully.", "success");
        closeEditMarksModal();
        loadStudentMarksTable();
    } else {
        showToast("Error", res.message || "Failed to update marks.", "error");
    }
}

async function deleteMarksRecord(markId) {
    showConfirmModal("Confirm Record Deletion", "Are you sure you want to delete this student marks entry?", async () => {
        const res = await API.delete(`/api/marks/${markId}`);
        if (res && res.success) {
            showToast("Record Deleted", res.message || "Marks record deleted.", "success");
            loadStudentMarksTable();
        } else {
            showToast("Error", res.message || "Failed to delete record.", "error");
        }
    });
}

async function viewAcademicReportCard(studentId) {
    const res = await API.get(`/api/marks/student/${studentId}`);
    if (!res || !res.success || !res.result_card) {
        showToast("Not Found", "Academic report card not available.", "warning");
        return;
    }

    const card = res.result_card;
    document.getElementById('rep-student-name').textContent = card.name;
    document.getElementById('rep-student-id').textContent = card.student_id;
    document.getElementById('rep-student-dept').textContent = card.department || 'Computer Engineering';
    document.getElementById('rep-student-course').textContent = card.course || 'B.Tech';
    document.getElementById('rep-student-sem').textContent = `Semester ${card.semester || 1}`;

    document.getElementById('rep-total-obtained').textContent = card.total_obtained;
    document.getElementById('rep-total-max').textContent = card.total_max;
    document.getElementById('rep-overall-pct').textContent = `${card.overall_percentage}%`;
    document.getElementById('rep-overall-grade').textContent = card.overall_grade;

    const statusBadge = document.getElementById('rep-overall-status');
    if (statusBadge) {
        statusBadge.textContent = card.overall_status;
        statusBadge.style.background = card.overall_status === 'PASS' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
        statusBadge.style.color = card.overall_status === 'PASS' ? 'var(--success)' : 'var(--danger)';
    }

    const body = document.getElementById('rep-marks-rows');
    if (body) {
        let html = '';
        (card.marks_records || []).forEach(r => {
            const isPass = r.status === 'PASS';
            html += `
                <tr>
                    <td><strong>${r.subject}</strong></td>
                    <td>${r.exam_name}</td>
                    <td><strong>${r.marks_obtained}</strong> / ${r.max_marks}</td>
                    <td><strong>${r.percentage}%</strong></td>
                    <td><span class="badge" style="background: rgba(245,158,11,0.15); color: var(--accent-gold); font-weight: 700;">${r.grade}</span></td>
                    <td><span class="badge" style="background: ${isPass ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}; color: ${isPass ? 'var(--success)' : 'var(--danger)'}; font-weight: 700;">${r.status}</span></td>
                </tr>
            `;
        });
        body.innerHTML = html || `<tr><td colspan="6" class="text-center text-muted">No marks recorded.</td></tr>`;
    }

    const modal = document.getElementById('report-card-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeReportCardModal() {
    const modal = document.getElementById('report-card-modal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Student View: Load personal academic transcript / report card
 */
async function loadStudentAcademicReportCard() {
    const studentId = STATE.user.reference_id;
    viewAcademicReportCard(studentId);
}
