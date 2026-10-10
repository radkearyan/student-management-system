// Attendance Log, Bulk Class Marking, and Student Summary Manager

let DEPARTMENTS = [];
let ALL_STUDENTS = [];
let ALL_LOGS = [];
let SUBJECT_OPTIONS = [];
let CURRENT_DEPT = '';

const DEPT_ICONS = {
    'Computer Engineering': 'fa-laptop-code',
    'Information Technology': 'fa-network-wired',
    'Electrical Engineering': 'fa-bolt-lightning',
    'Mechanical Engineering': 'fa-gears'
};

async function loadAttendanceView() {
    // Determine user role
    const isStudent = STATE.user && STATE.user.role === 'student';
    const isTeacher = STATE.user && STATE.user.role === 'teacher';
    
    if (isStudent) {
        loadStudentAttendanceDashboard();
        return;
    }

    // 1. Fetch departments, students, subjects, and attendance logs
    const [depts, students, subjects, logs] = await Promise.all([
        API.get('/api/departments'),
        API.get('/api/students'),
        API.get('/api/subjects'),
        API.get('/api/attendance')
    ]);

    DEPARTMENTS = depts || [];
    ALL_STUDENTS = students || [];
    SUBJECT_OPTIONS = (subjects && subjects.subjects) ? subjects.subjects : (subjects || []);
    ALL_LOGS = logs || [];

    // If teacher, lock to their assigned department
    if (isTeacher && STATE.user.department) {
        const facultyDept = STATE.user.department;
        CURRENT_DEPT = facultyDept;
        DEPARTMENTS = DEPARTMENTS.filter(d => d.name === facultyDept);
        if (DEPARTMENTS.length === 0) DEPARTMENTS = [{ name: facultyDept }];
        ALL_STUDENTS = ALL_STUDENTS.filter(s => s.department === facultyDept);
        ALL_LOGS = ALL_LOGS.filter(l => l.department === facultyDept);
    }

    // Set default date to today
    const dateInput = document.getElementById('att-date');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().substring(0, 10);
    }

    // Populate dropdowns
    populateAttendanceDropdowns();
    renderDepartmentAttendanceCards();
    loadClassStudentsForBulkMarking();
    renderAttendanceTable();
    setupAttendanceFilterListeners();
}

function populateAttendanceDropdowns() {
    const deptSelect = document.getElementById('att-dept-select');
    const subSelect = document.getElementById('att-subject-select');

    if (deptSelect) {
        if (STATE.user && STATE.user.role === 'teacher' && STATE.user.department) {
            deptSelect.innerHTML = `<option value="${STATE.user.department}">${STATE.user.department}</option>`;
            deptSelect.disabled = true;
        } else {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            DEPARTMENTS.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.name;
                opt.textContent = d.name;
                deptSelect.appendChild(opt);
            });
            deptSelect.onchange = () => {
                filterByAttendanceDept(deptSelect.value);
            };
        }
    }

    if (subSelect) {
        subSelect.innerHTML = '<option value="CS101">CS101 - Core Class Subject</option>';
        SUBJECT_OPTIONS.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.subject_code;
            opt.textContent = `${s.subject_code} - ${s.subject_name || s.name} (${s.department || ''})`;
            subSelect.appendChild(opt);
        });
        subSelect.onchange = loadClassStudentsForBulkMarking;
    }
}

function renderDepartmentAttendanceCards() {
    const cardsContainer = document.getElementById('attendance-dept-cards');
    if (!cardsContainer) return;

    const isTeacher = STATE.user && STATE.user.role === 'teacher' && STATE.user.department;
    const facultyDept = isTeacher ? STATE.user.department : null;

    const presentCounts = {};
    const totalStudentsCounts = {};
    DEPARTMENTS.forEach(d => {
        presentCounts[d.name] = 0;
        totalStudentsCounts[d.name] = 0;
    });

    ALL_STUDENTS.forEach(s => {
        if (totalStudentsCounts[s.department] !== undefined) {
            totalStudentsCounts[s.department]++;
        }
    });

    const presentStudentsSet = new Set();
    ALL_LOGS.forEach(l => {
        if (l.status === 'Present' && !presentStudentsSet.has(l.student_id)) {
            presentStudentsSet.add(l.student_id);
            if (l.department && presentCounts[l.department] !== undefined) {
                presentCounts[l.department]++;
            }
        }
    });

    cardsContainer.innerHTML = '';

    if (isTeacher) {
        const countPresent = presentCounts[facultyDept] || 0;
        const countTotal = totalStudentsCounts[facultyDept] || 0;
        const icon = DEPT_ICONS[facultyDept] || 'fa-building';

        cardsContainer.innerHTML = `
            <div class="dept-card glassmorphism active" data-dept-card="${facultyDept}" style="cursor: default; grid-column: 1 / -1; max-width: 480px;">
                <div class="dept-card-icon" style="background: rgba(16, 185, 129, 0.15); color: var(--success);"><i class="fa-solid ${icon}"></i></div>
                <div class="dept-card-info">
                    <h4>${facultyDept} <span style="font-size: 0.72rem; background: var(--accent-blue); color: white; padding: 2px 8px; border-radius: 12px; margin-left: 6px;"><i class="fa-solid fa-lock"></i> Branch Lock</span></h4>
                    <span class="dept-student-count" style="color: var(--success); font-weight: 700;">
                        <i class="fa-solid fa-circle-check"></i> ${countPresent} Students Check-in
                    </span>
                    <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">${countTotal} Enrolled Students</span>
                </div>
            </div>
        `;
        return;
    }

    const totalPresentAll = presentStudentsSet.size;

    cardsContainer.innerHTML = `
        <div class="dept-card glassmorphism ${CURRENT_DEPT === '' ? 'active' : ''}" data-dept-card="All" onclick="filterByAttendanceDept('')" style="cursor: pointer;">
            <div class="dept-card-icon"><i class="fa-solid fa-graduation-cap"></i></div>
            <div class="dept-card-info">
                <h4>All Departments</h4>
                <span class="dept-student-count" id="count-att-all">${totalPresentAll} Students Check-in</span>
            </div>
        </div>
    `;

    DEPARTMENTS.forEach(d => {
        const icon = DEPT_ICONS[d.name] || 'fa-building';
        const shortName = d.name.replace('Engineering', 'Engg').replace('Technology', 'Tech');
        const countPresent = presentCounts[d.name] || 0;
        const countTotal = totalStudentsCounts[d.name] || 0;
        const isActive = CURRENT_DEPT === d.name ? 'active' : '';

        cardsContainer.innerHTML += `
            <div class="dept-card glassmorphism ${isActive}" data-dept-card="${d.name}" onclick="filterByAttendanceDept('${d.name.replace(/'/g, "\\'")}')" style="cursor: pointer;">
                <div class="dept-card-icon"><i class="fa-solid ${icon}"></i></div>
                <div class="dept-card-info">
                    <h4>${shortName}</h4>
                    <span class="dept-student-count" style="color: var(--success); font-weight: 600;">
                        <i class="fa-solid fa-circle-check"></i> ${countPresent} Present
                    </span>
                    <span style="font-size: 0.7rem; color: var(--text-muted); display: block;">${countTotal} Enrolled</span>
                </div>
            </div>
        `;
    });
}

function filterByAttendanceDept(deptName) {
    if (STATE.user && STATE.user.role === 'teacher' && STATE.user.department) {
        CURRENT_DEPT = STATE.user.department;
    } else {
        CURRENT_DEPT = deptName;
    }

    document.querySelectorAll('#attendance-dept-cards .dept-card').forEach(card => {
        const cardDept = card.getAttribute('data-dept-card');
        if ((!deptName && cardDept === 'All') || cardDept === deptName) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });

    const deptSelect = document.getElementById('att-dept-select');
    if (deptSelect && deptSelect.value !== deptName) {
        deptSelect.value = deptName;
    }

    loadClassStudentsForBulkMarking();
    updateStreamHeader(deptName);
    renderAttendanceTable();
}

/**
 * Load Class Students List into Bulk Register Table
 */
function loadClassStudentsForBulkMarking() {
    const listBody = document.getElementById('bulk-students-list-body');
    if (!listBody) return;

    let targetStudents = ALL_STUDENTS;
    if (CURRENT_DEPT) {
        targetStudents = ALL_STUDENTS.filter(s => s.department === CURRENT_DEPT);
    }

    if (targetStudents.length === 0) {
        listBody.innerHTML = `
            <tr>
                <td colspan="3" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
                    No enrolled students found in this department.
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    targetStudents.forEach((s, idx) => {
        html += `
            <tr data-student-id="${s.student_id}">
                <td>
                    <div style="font-weight: 600; font-size: 0.88rem;">${s.name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${s.student_id}</div>
                </td>
                <td><span style="font-size: 0.8rem; color: var(--text-muted);">${s.department || ''}</span></td>
                <td style="text-align: right;">
                    <div class="att-status-toggle-group" style="display: inline-flex; gap: 4px; background: rgba(0,0,0,0.2); padding: 2px; border-radius: 6px;">
                        <button type="button" class="btn-att-toggle btn-present active" onclick="setStudentAttStatus(this, 'Present')" style="padding: 4px 10px; font-size: 0.75rem; border-radius: 4px; cursor: pointer; border: none; background: var(--success); color: white; font-weight: 600;">Present</button>
                        <button type="button" class="btn-att-toggle btn-absent" onclick="setStudentAttStatus(this, 'Absent')" style="padding: 4px 10px; font-size: 0.75rem; border-radius: 4px; cursor: pointer; border: none; background: transparent; color: var(--text-muted);">Absent</button>
                    </div>
                </td>
            </tr>
        `;
    });
    listBody.innerHTML = html;
}

function setStudentAttStatus(btn, status) {
    const group = btn.closest('.att-status-toggle-group');
    if (!group) return;

    group.querySelectorAll('.btn-att-toggle').forEach(b => {
        b.style.background = 'transparent';
        b.style.color = 'var(--text-muted)';
        b.classList.remove('active');
    });

    btn.classList.add('active');
    if (status === 'Present') {
        btn.style.background = 'var(--success)';
        btn.style.color = 'white';
    } else {
        btn.style.background = 'var(--danger)';
        btn.style.color = 'white';
    }
}

function setAllStudentsStatus(status) {
    const listBody = document.getElementById('bulk-students-list-body');
    if (!listBody) return;

    listBody.querySelectorAll('tr').forEach(tr => {
        const btn = tr.querySelector(status === 'Present' ? '.btn-present' : '.btn-absent');
        if (btn) setStudentAttStatus(btn, status);
    });
}

/**
 * Save Bulk Attendance
 */
async function saveBulkAttendance() {
    const dateInput = document.getElementById('att-date');
    const subSelect = document.getElementById('att-subject-select');
    const date_str = dateInput ? dateInput.value : '';
    const subject_code = subSelect ? subSelect.value : 'CS101';

    if (!date_str) {
        showToast("Date Required", "Please select a valid date for attendance.", "warning");
        return;
    }

    const listBody = document.getElementById('bulk-students-list-body');
    if (!listBody) return;

    const records = [];
    listBody.querySelectorAll('tr').forEach(tr => {
        const sid = tr.getAttribute('data-student-id');
        const activeBtn = tr.querySelector('.btn-att-toggle.active');
        const status = activeBtn ? (activeBtn.classList.contains('btn-present') ? 'Present' : 'Absent') : 'Present';
        if (sid) {
            records.push({ student_id: sid, status: status });
        }
    });

    if (records.length === 0) {
        showToast("No Students", "No student records available to save.", "warning");
        return;
    }

    const saveBtn = document.getElementById('btn-save-bulk-attendance');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving Register...';
    }

    try {
        const res = await API.post('/api/attendance/bulk', {
            date: date_str,
            subject_code: subject_code,
            records: records
        });

        if (res && res.success) {
            showToast("Attendance Saved", res.message || "Attendance saved successfully.", "success");
            const updatedLogs = await API.get('/api/attendance');
            if (updatedLogs) {
                ALL_LOGS = updatedLogs;
                renderDepartmentAttendanceCards();
                renderAttendanceTable();
            }
        } else {
            showToast("Failed to Save", res.message || "Error saving attendance.", "error");
        }
    } catch (err) {
        console.error("Save bulk attendance error:", err);
        showToast("Error", "An error occurred while saving attendance.", "error");
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Class Attendance';
        }
    }
}

function updateStreamHeader(deptName) {
    const titleEl = document.getElementById('current-dept-title');
    const subtitleEl = document.getElementById('current-dept-subtitle');
    if (!titleEl) return;

    if (!deptName) {
        titleEl.innerHTML = '<i class="fa-solid fa-building-columns" style="color: var(--accent-blue);"></i> All Departments Attendance';
        if (subtitleEl) subtitleEl.textContent = 'Showing attendance records for all institutional branches';
    } else {
        const icon = DEPT_ICONS[deptName] || 'fa-building';
        titleEl.innerHTML = `<i class="fa-solid ${icon}" style="color: var(--accent-blue);"></i> ${deptName}`;
        if (subtitleEl) subtitleEl.textContent = `Showing classroom attendance records for ${deptName}`;
    }
}

function renderAttendanceTable() {
    const body = document.getElementById('attendance-log-body');
    if (!body) return;

    const searchVal = (document.getElementById('att-search-input')?.value || '').toLowerCase().trim();
    const statusFilter = document.getElementById('att-status-filter')?.value || '';
    const dateFilter = document.getElementById('att-date-filter')?.value || '';

    let filteredLogs = ALL_LOGS;

    if (CURRENT_DEPT) {
        filteredLogs = filteredLogs.filter(l => l.department === CURRENT_DEPT);
    }
    if (statusFilter) {
        filteredLogs = filteredLogs.filter(l => l.status === statusFilter);
    }
    if (dateFilter) {
        filteredLogs = filteredLogs.filter(l => l.date === dateFilter);
    }
    if (searchVal) {
        filteredLogs = filteredLogs.filter(l => 
            (l.student_id && l.student_id.toLowerCase().includes(searchVal)) ||
            (l.name && l.name.toLowerCase().includes(searchVal)) ||
            (l.department && l.department.toLowerCase().includes(searchVal))
        );
    }

    const presentCount = filteredLogs.filter(l => l.status === 'Present').length;
    const absentCount = filteredLogs.filter(l => l.status === 'Absent').length;

    const presentPill = document.getElementById('pill-present-count');
    const absentPill = document.getElementById('pill-absent-count');
    if (presentPill) presentPill.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${presentCount} Present`;
    if (absentPill) absentPill.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${absentCount} Absent`;

    body.innerHTML = '';

    if (filteredLogs.length === 0) {
        const deptLabel = CURRENT_DEPT ? ` in ${CURRENT_DEPT}` : '';
        body.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted" style="padding: 2.5rem 1rem;">
                    <i class="fa-solid fa-folder-open" style="font-size: 1.8rem; margin-bottom: 0.5rem; opacity: 0.6;"></i>
                    <div>No attendance records found${deptLabel} matching the selected criteria.</div>
                </td>
            </tr>
        `;
        return;
    }

    filteredLogs.forEach(l => {
        const tr = document.createElement('tr');
        const isPresent = l.status === 'Present';
        const statusBadge = isPresent 
            ? '<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: var(--success); font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3);"><i class="fa-solid fa-check"></i> Present</span>' 
            : '<span class="badge" style="background: rgba(239, 68, 68, 0.15); color: var(--danger); font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.3);"><i class="fa-solid fa-xmark"></i> Absent</span>';
        
        const deptBadge = l.department 
            ? `<span style="font-size: 0.8rem; background: rgba(59, 130, 246, 0.1); color: var(--accent-blue); padding: 2px 8px; border-radius: 4px; font-weight: 500;">${l.department}</span>` 
            : '<span class="text-muted" style="font-size: 0.75rem;">General</span>';

        tr.innerHTML = `
            <td>
                <div style="font-weight: 700; color: var(--text-main);">${l.name || l.student_id}</div>
                <div style="font-size: 0.78rem; color: var(--text-muted);">${l.student_id}</div>
            </td>
            <td>${deptBadge}</td>
            <td style="font-size: 0.88rem; color: var(--text-main);">${l.date}</td>
            <td>${statusBadge}</td>
            <td><span style="font-size:0.75rem; color: var(--text-muted); background: rgba(0,0,0,0.06); padding: 2px 6px; border-radius: 4px;">${l.subject_code || 'CS101'}</span></td>
        `;
        body.appendChild(tr);
    });
}

function setupAttendanceFilterListeners() {
    const searchInput = document.getElementById('att-search-input');
    const statusFilter = document.getElementById('att-status-filter');
    const dateFilter = document.getElementById('att-date-filter');
    const resetBtn = document.getElementById('btn-reset-att-filter');

    if (searchInput) searchInput.oninput = renderAttendanceTable;
    if (statusFilter) statusFilter.onchange = renderAttendanceTable;
    if (dateFilter) dateFilter.onchange = renderAttendanceTable;
    if (resetBtn) {
        resetBtn.onclick = () => {
            if (searchInput) searchInput.value = '';
            if (statusFilter) statusFilter.value = '';
            if (dateFilter) dateFilter.value = '';
            const resetDept = (STATE.user && STATE.user.role === 'teacher' && STATE.user.department) ? STATE.user.department : '';
            filterByAttendanceDept(resetDept);
        };
    }
}

/**
 * Student Personal Attendance Dashboard View
 */
async function loadStudentAttendanceDashboard() {
    const studentId = STATE.user ? (STATE.user.reference_id || STATE.user.username) : null;
    if (!studentId) return;

    try {
        const [summaryRes, logsRes] = await Promise.all([
            API.get(`/api/attendance/summary/${studentId}`),
            API.get('/api/attendance')
        ]);

        ALL_LOGS = Array.isArray(logsRes) ? logsRes : [];

        let summaryContainer = document.getElementById('student-attendance-summary');
        if (!summaryContainer) {
            const dashView = document.querySelector('.dashboard-view');
            if (dashView) {
                summaryContainer = document.createElement('div');
                summaryContainer.id = 'student-attendance-summary';
                dashView.insertBefore(summaryContainer, dashView.firstChild);
            }
        }

        const summary = (summaryRes && summaryRes.success) ? summaryRes.summary : null;
        if (summaryContainer && summary) {
            const pct = summary.overall_percentage;
            const isLow = summary.low_attendance_warning;

            let warningBanner = '';
            if (isLow) {
                warningBanner = `
                    <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid var(--danger); padding: 1rem 1.25rem; border-radius: 12px; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem; color: #f87171;">
                        <i class="fa-solid fa-triangle-exclamation" style="font-size: 1.8rem;"></i>
                        <div>
                            <h4 style="font-weight: 700; margin-bottom: 2px;">Low Attendance Warning (< 75%)</h4>
                            <p style="font-size: 0.85rem; margin: 0;">Your overall attendance is currently ${pct}%. Please attend upcoming classes to meet the mandatory 75% requirement.</p>
                        </div>
                    </div>
                `;
            }

            let subjectsHtml = '';
            (summary.subject_wise || []).forEach(sub => {
                const subLow = sub.low_warning;
                const hasSessions = sub.total_conducted > 0;
                
                let badgeStyle = 'background: rgba(16,185,129,0.15); color: var(--success);';
                let statusMsg = '✓ Good Standing';
                let pctText = `${sub.percentage}%`;

                if (!hasSessions) {
                    badgeStyle = 'background: rgba(148,163,184,0.15); color: var(--text-muted);';
                    statusMsg = 'No Sessions Held';
                    pctText = 'N/A';
                } else if (subLow) {
                    badgeStyle = 'background: rgba(239,68,68,0.15); color: var(--danger);';
                    statusMsg = '⚠️ Below Threshold';
                }

                subjectsHtml += `
                    <div class="glassmorphism" style="padding: 1.25rem; border-radius: 12px; display: flex; flex-direction: column; gap: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <strong style="color: var(--accent-gold); font-size: 0.9rem;">${sub.subject_code}</strong>
                                <h4 style="font-size: 1.05rem; font-weight: 700; margin-top: 2px;">${sub.subject_name}</h4>
                            </div>
                            <span class="badge" style="${badgeStyle} font-weight: 700; padding: 4px 10px; border-radius: 6px;">
                                ${pctText}
                            </span>
                        </div>
                        <div style="background: rgba(0,0,0,0.2); height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="width: ${hasSessions ? sub.percentage : 0}%; height: 100%; background: ${subLow ? 'var(--danger)' : 'var(--success)'}; transition: width 0.4s;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted);">
                            <span>Attended: ${sub.total_present} / ${sub.total_conducted} Classes</span>
                            <span>${statusMsg}</span>
                        </div>
                    </div>
                `;
            });

            summaryContainer.innerHTML = `
                ${warningBanner}
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; margin-bottom: 1.5rem;">
                    <div class="glassmorphism" style="padding: 1.5rem; text-align: center; border-radius: 12px;">
                        <span style="font-size: 0.85rem; color: var(--text-muted);">Overall Attendance</span>
                        <div style="font-size: 2.5rem; font-weight: 800; color: ${isLow ? 'var(--danger)' : 'var(--accent-blue)'}; margin: 8px 0;">
                            ${pct}%
                        </div>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">${summary.overall_present} / ${summary.overall_total} Total Classes</span>
                    </div>
                    <div class="glassmorphism" style="padding: 1.5rem; text-align: center; border-radius: 12px;">
                        <span style="font-size: 0.85rem; color: var(--text-muted);">Classes Conducted</span>
                        <div style="font-size: 2.5rem; font-weight: 800; color: var(--accent-gold); margin: 8px 0;">
                            ${summary.overall_total}
                        </div>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">Recorded Sessions</span>
                    </div>
                    <div class="glassmorphism" style="padding: 1.5rem; text-align: center; border-radius: 12px;">
                        <span style="font-size: 0.85rem; color: var(--text-muted);">Status Badge</span>
                        <div style="font-size: 1.3rem; font-weight: 800; margin: 16px 0; color: ${isLow ? 'var(--danger)' : 'var(--success)'};">
                            ${isLow ? '⚠️ LOW ATTENDANCE' : '✓ ELIGIBLE FOR EXAMS'}
                        </div>
                    </div>
                </div>

                <h3 style="margin-bottom: 1rem; color: var(--accent-gold);"><i class="fa-solid fa-book-open"></i> Subject-wise Attendance Breakdown</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.25rem; margin-bottom: 1.5rem;">
                    ${subjectsHtml || '<p style="color: var(--text-muted);">No subject attendance records found.</p>'}
                </div>
            `;
        }

        renderAttendanceTable();
        setupAttendanceFilterListeners();
    } catch (err) {
        console.error("Error loading student attendance dashboard:", err);
    }
}

function loadAttendanceLogs() {
    return loadAttendanceView();
}

// PDF Download Helper
async function downloadAttendancePDF() {
    const btn = document.getElementById('btn-export-pdf');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating PDF...';
    }

    try {
        const dept = (CURRENT_DEPT || '').trim();
        const date = document.getElementById('att-date-filter')?.value || '';
        const status = document.getElementById('att-status-filter')?.value || '';

        const params = new URLSearchParams();
        if (dept) params.append('department', dept);
        if (date) params.append('date', date);
        if (status) params.append('status', status);

        const url = `/api/attendance/export/pdf?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
            showToast("Export Failed", "Could not generate PDF", "error");
            return;
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        
        const cleanDept = (dept || 'all').toLowerCase().replace(/[^a-z0-9]/g, '_');
        const cleanDate = date || new Date().toISOString().substring(0, 10);
        a.download = `attendance_${cleanDept}_${cleanDate}.pdf`;
        
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast("PDF Exported", "Class attendance PDF downloaded successfully.", "success");
    } catch (err) {
        console.error("PDF Download error:", err);
        showToast("Export Error", "Error generating attendance PDF.", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    }
}
