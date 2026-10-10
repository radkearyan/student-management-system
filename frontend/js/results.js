// Examinations, Marks, Hall Tickets, and Marksheets Manager

async function loadExamsView() {
    if (STATE.user && STATE.user.role === 'student') {
        const teacherView = document.getElementById('teacher-exams-view');
        const studentView = document.getElementById('student-exams-view');
        if (teacherView) teacherView.classList.add('hidden');
        if (studentView) studentView.classList.remove('hidden');
        loadStudentServicesHub();
        return;
    } else {
        const teacherView = document.getElementById('teacher-exams-view');
        const studentView = document.getElementById('student-exams-view');
        if (teacherView) teacherView.classList.remove('hidden');
        if (studentView) studentView.classList.add('hidden');
    }

    const exams = await API.get('/api/exams');
    const listContainer = document.getElementById('exams-registry-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';

    if (!exams || exams.length === 0) {
        listContainer.innerHTML = '<p class="text-center text-muted">No assessment cards registered.</p>';
    } else {
        exams.forEach(e => {
            const card = document.createElement('div');
            card.className = 'exam-registry-card glassmorphism mb-3';
            card.innerHTML = `
                <div class="card-title-row" style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="font-weight:700; color:var(--text-main);">${e.name}</h4>
                    <span class="exam-date-badge" style="font-size:0.75rem; background:rgba(255,255,255,0.05); padding:3px 8px; border-radius:4px;">${e.date}</span>
                </div>
                <div class="card-details-row mt-2" style="font-size:0.85rem; opacity:0.8; display:flex; gap:1.5rem;">
                    <span>Subject: <strong>${e.subject}</strong></span>
                    <span>Max Marks: <strong>${e.max_marks}</strong></span>
                </div>
            `;
            listContainer.appendChild(card);
        });
    }

    // Populate selects for Upload Marks
    const examSelect = document.getElementById('marks-exam-select');
    const studSelect = document.getElementById('marks-student-select');
    
    if (examSelect) {
        examSelect.innerHTML = '';
        if (exams) {
            exams.forEach(e => {
                const opt = document.createElement('option');
                opt.value = e.exam_id;
                opt.textContent = `${e.name} (${e.subject})`;
                examSelect.appendChild(opt);
            });
        }
    }

    if (studSelect) {
        const students = await API.get('/api/students');
        studSelect.innerHTML = '';
        if (students) {
            students.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.student_id;
                opt.textContent = `${s.name} (${s.student_id})`;
                studSelect.appendChild(opt);
            });
        }
    }
}

// Binds Exams and Upload Forms
const createExamForm = document.getElementById('create-exam-form');
if (createExamForm) {
    createExamForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('exam-name').value,
            subject: document.getElementById('exam-subject').value,
            date: document.getElementById('exam-date').value,
            max_marks: document.getElementById('exam-max-marks').value
        };

        const res = await API.post('/api/exams', payload);
        if (res && res.success) {
            showToast("Success", res.message, "success");
            createExamForm.reset();
            loadExamsView();
        } else {
            showToast("Error", res.message || "Assessment creation failed.", "error");
        }
    });
}

const uploadMarksForm = document.getElementById('upload-marks-form');
if (uploadMarksForm) {
    uploadMarksForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            exam_id: document.getElementById('marks-exam-select').value,
            student_id: document.getElementById('marks-student-select').value,
            marks_obtained: document.getElementById('marks-value').value
        };

        const res = await API.post('/api/marks', payload);
        if (res && res.success) {
            showToast("Success", res.message, "success");
            uploadMarksForm.reset();
        } else {
            showToast("Error", res.message || "Failed to submit marks.", "error");
        }
    });
}

// Student Specific Services (Admit Cards, Transcripts, Makeups)
async function loadStudentServicesHub() {
    // 1. Load Makeup registrations
    loadMakeupLogs();
    
    // 2. Bind Admit Card print preview button
    const hallticketBtn = document.getElementById('btn-view-my-hallticket');
    if (hallticketBtn) {
        hallticketBtn.onclick = () => openHallTicketModal(STATE.user.reference_id);
    }
    
    // 3. Bind Grade Card print preview button
    const marksheetBtn = document.getElementById('btn-view-my-marksheet');
    if (marksheetBtn) {
        marksheetBtn.onclick = () => openMarksheetModal(STATE.user.reference_id);
    }
}

async function loadMakeupLogs() {
    const res = await API.get('/api/exams/makeup');
    const body = document.getElementById('student-makeup-list-body');
    if (!body) return;
    body.innerHTML = '';

    if (!res || !res.success || res.applications.length === 0) {
        body.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No makeup exams registered.</td></tr>';
        return;
    }

    res.applications.forEach(app => {
        const tr = document.createElement('tr');
        
        let action = '';
        if (app.fee_status === 'Pending') {
            action = `<button class="btn btn-primary btn-small btn-pay-makeup" data-app-id="${app.app_id}" style="padding:4px 8px; font-size:0.75rem;"><i class="fa-solid fa-credit-card"></i> Pay ₹500</button>`;
        } else {
            action = `<span class="text-green" style="font-size:0.75rem; font-weight:600;"><i class="fa-solid fa-circle-check"></i> Cleared</span>`;
        }

        tr.innerHTML = `
            <td><strong>${app.subject}</strong></td>
            <td>${app.applied_date}</td>
            <td><span class="${app.fee_status === 'Paid' ? 'text-green' : 'text-red'} font-bold">${app.fee_status}</span></td>
            <td>${action}</td>
        `;
        body.appendChild(tr);
    });

    // Wire Makeup fee buttons
    body.querySelectorAll('.btn-pay-makeup').forEach(btn => {
        btn.onclick = () => {
            const appId = btn.getAttribute('data-app-id');
            processMakeupFee(appId);
        };
    });
}

// Apply Makeup Form Submits
const makeupForm = document.getElementById('apply-makeup-form');
if (makeupForm) {
    makeupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const subject = document.getElementById('makeup-subject').value;
        const exam_name = document.getElementById('makeup-exam-name').value;
        
        if (!subject) return;

        const res = await API.post('/api/exams/makeup/apply', { subject, exam_name });
        if (res && res.success) {
            showToast("Application Saved", res.message, "success");
            makeupForm.reset();
            loadMakeupLogs();
        } else {
            showToast("Failed", res.message || "Registration failed.", "error");
        }
    });
}

// Payment simulation for Makeup fees
async function processMakeupFee(appId) {
    const cardNum = prompt("Enter 16-digit credit card number to clear ₹500 fee:");
    if (!cardNum || cardNum.length < 16) {
        showToast("Transaction Cancelled", "Valid credit card details are required.", "error");
        return;
    }

    const res = await API.post('/api/exams/makeup/pay', { app_id: appId, card_number: cardNum });
    if (res && res.success) {
        showToast("Payment Successful", `Txn ID: ${res.txn_id}`, "success");
        loadMakeupLogs();
    } else {
        showToast("Payment Failed", res.message || "Failed to process card.", "error");
    }
}

// Print Modal triggers: Hall Ticket
async function openHallTicketModal(studentId) {
    const res = await API.get(`/api/exams/hallticket/${studentId}`);
    if (!res || !res.success) {
        showToast("Error", "Could not fetch hall ticket details.", "error");
        return;
    }

    const modal = document.getElementById('hallticket-modal');
    if (!modal) return;

    const t = res.hall_ticket;
    document.getElementById('ticket-student-name').textContent = t.name;
    document.getElementById('ticket-student-id').textContent = t.student_id;
    document.getElementById('ticket-course').textContent = t.course;
    document.getElementById('ticket-department').textContent = t.department;
    document.getElementById('ticket-semester').textContent = `Semester ${t.semester}`;
    document.getElementById('ticket-venue').textContent = t.venue;
    
    // Set fallback photo or photo image
    const photoImg = document.getElementById('ticket-student-photo');
    const photoFallback = document.getElementById('ticket-photo-fallback');
    
    // Check if profile pic is loaded in STATE
    if (STATE.user && STATE.user.profile_pic) {
        photoImg.src = STATE.user.profile_pic;
        photoImg.classList.remove('hidden');
        photoFallback.classList.add('hidden');
    } else {
        photoImg.classList.add('hidden');
        photoFallback.classList.remove('hidden');
    }

    // Populate examination subjects registry
    const tbody = document.getElementById('ticket-subjects-body');
    tbody.innerHTML = '';
    t.subjects.forEach((subj, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="border:1px solid #ddd; padding:8px;">${idx + 1}</td>
            <td style="border:1px solid #ddd; padding:8px;"><strong>${subj}</strong></td>
            <td style="border:1px solid #ddd; padding:8px;">TBD (Aug 2026)</td>
            <td style="border:1px solid #ddd; padding:8px;">09:30 AM - 12:30 PM</td>
            <td style="border:1px solid #ddd; padding:8px; width:120px;"></td>
            <td style="border:1px solid #ddd; padding:8px; width:140px;"></td>
        `;
        tbody.appendChild(tr);
    });

    modal.classList.remove('hidden');
    
    const closeBtn1 = document.getElementById('btn-close-hallticket-modal');
    const closeBtn2 = document.getElementById('btn-close-hallticket-modal-footer');
    if (closeBtn1) closeBtn1.onclick = () => modal.classList.add('hidden');
    if (closeBtn2) closeBtn2.onclick = () => modal.classList.add('hidden');
}

// Print Modal triggers: Marksheet
async function openMarksheetModal(studentId) {
    const perf = await API.get(`/api/students/${studentId}/performance`);
    if (!perf || !perf.success) {
        showToast("Error", "Could not fetch academic records.", "error");
        return;
    }

    const modal = document.getElementById('marksheet-modal');
    if (!modal) return;

    document.getElementById('sheet-student-name').textContent = perf.name;
    document.getElementById('sheet-student-id').textContent = perf.student_id;
    document.getElementById('sheet-dept').textContent = perf.department;
    document.getElementById('sheet-course').textContent = perf.course;

    const tbody = document.getElementById('sheet-grades-body');
    tbody.innerHTML = '';

    if (perf.marks_history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No assessments completed.</td></tr>';
        document.getElementById('sheet-aggregate-avg').textContent = '0.0%';
        document.getElementById('sheet-sgpa').textContent = '0.00';
        document.getElementById('sheet-result-status').textContent = 'N/A';
    } else {
        perf.marks_history.forEach((g, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="border:1px solid #ddd; padding:8px;">${idx + 1}</td>
                <td style="border:1px solid #ddd; padding:8px;"><strong>${g.subject} (${g.exam_name})</strong></td>
                <td style="border:1px solid #ddd; padding:8px;">100</td>
                <td style="border:1px solid #ddd; padding:8px;">${g.marks_obtained}</td>
                <td style="border:1px solid #ddd; padding:8px;"><strong>${g.grade}</strong></td>
                <td style="border:1px solid #ddd; padding:8px; font-weight:600;" class="${g.grade === 'F' ? 'text-red' : 'text-green'}">${g.grade === 'F' ? 'FAIL' : 'PASS'}</td>
            `;
            tbody.appendChild(tr);
        });

        // Compute averages and SGPA
        const scores = perf.marks_history.map(m => m.marks_obtained);
        const avg = scores.reduce((a,b)=>a+b, 0) / scores.length;
        document.getElementById('sheet-aggregate-avg').textContent = `${avg.toFixed(1)}%`;
        
        // SGPA mapping
        let totalSgPoints = 0;
        perf.marks_history.forEach(m => {
            if (m.grade === 'A') totalSgPoints += 10.0;
            else if (m.grade === 'B') totalSgPoints += 9.0;
            else if (m.grade === 'C') totalSgPoints += 8.0;
            else if (m.grade === 'D') totalSgPoints += 7.0;
            else if (m.grade === 'E') totalSgPoints += 6.0;
            else totalSgPoints += 0.0;
        });
        const sgpa = totalSgPoints / perf.marks_history.length;
        document.getElementById('sheet-sgpa').textContent = sgpa.toFixed(2);
        
        const isFail = perf.marks_history.some(m => m.grade === 'F');
        const statusEl = document.getElementById('sheet-result-status');
        if (isFail) {
            statusEl.textContent = 'FAIL / BACKLOGS';
            statusEl.style.color = 'var(--danger)';
        } else {
            statusEl.textContent = 'PASS';
            statusEl.style.color = 'darkgreen';
        }
    }

    modal.classList.remove('hidden');
    
    const closeBtn1 = document.getElementById('btn-close-marksheet-modal');
    const closeBtn2 = document.getElementById('btn-close-marksheet-modal-footer');
    if (closeBtn1) closeBtn1.onclick = () => modal.classList.add('hidden');
    if (closeBtn2) closeBtn2.onclick = () => modal.classList.add('hidden');
}
