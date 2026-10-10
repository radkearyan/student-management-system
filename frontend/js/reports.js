// Academic Reports & Global Filtering Module

document.addEventListener("DOMContentLoaded", async () => {
    const authOk = await checkAuth(['admin', 'teacher', 'student']);
    if (authOk) {
        const titleEl = document.getElementById('header-view-title');
        const subTitleEl = document.getElementById('header-view-subtitle');
        if (titleEl) titleEl.textContent = "Academic Reports & Analytics";
        if (subTitleEl) subTitleEl.textContent = "Generate, search, filter, and export student, attendance, and exam reports";

        setupTabNavigation();
        await loadDepartmentDropdowns();

        // Initial loading for all report tabs
        await loadStudentsReport();
        await loadAttendanceReport();
        await loadResultsReport();
        await loadFeedbackReport();

        setupReportEvents();
    }
});

function setupTabNavigation() {
    const tabBtns = document.querySelectorAll('.report-tab-btn');
    const tabContents = document.querySelectorAll('.report-tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));

            btn.classList.add('active');
            const targetTabId = btn.getAttribute('data-tab');
            const targetContent = document.getElementById(targetTabId);
            if (targetContent) {
                targetContent.classList.remove('hidden');
            }
        });
    });
}

async function loadDepartmentDropdowns() {
    try {
        const depts = await API.get('/api/departments');
        const selects = [
            document.getElementById('stu-dept-select'),
            document.getElementById('att-dept-select'),
            document.getElementById('res-dept-select')
        ];

        selects.forEach(sel => {
            if (sel && depts) {
                sel.innerHTML = '<option value="">All Departments</option>';
                depts.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.name;
                    opt.textContent = d.name;
                    sel.appendChild(opt);
                });
            }
        });
    } catch (err) {
        console.error("Could not load departments", err);
    }
}

function setupReportEvents() {
    // 1. Student List Report
    const filterStuBtn = document.getElementById('btn-filter-students');
    if (filterStuBtn) filterStuBtn.onclick = () => loadStudentsReport();

    const exportStuCsv = document.getElementById('btn-export-students-csv');
    if (exportStuCsv) {
        exportStuCsv.onclick = () => {
            const search = document.getElementById('stu-search-input').value.trim();
            const dept = document.getElementById('stu-dept-select').value;
            window.open(`/api/reports/students?search=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&export=csv`, '_blank');
        };
    }

    const exportStuPdf = document.getElementById('btn-export-students-pdf');
    if (exportStuPdf) {
        exportStuPdf.onclick = () => {
            const search = document.getElementById('stu-search-input').value.trim();
            const dept = document.getElementById('stu-dept-select').value;
            window.open(`/api/reports/students?search=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&export=pdf`, '_blank');
        };
    }

    // 2. Attendance Report
    const filterAttBtn = document.getElementById('btn-filter-attendance');
    if (filterAttBtn) filterAttBtn.onclick = () => loadAttendanceReport();

    const exportAttCsv = document.getElementById('btn-export-attendance-csv');
    if (exportAttCsv) {
        exportAttCsv.onclick = () => {
            const search = document.getElementById('att-search-input').value.trim();
            const dept = document.getElementById('att-dept-select').value;
            const status = document.getElementById('att-status-select').value;
            const date = document.getElementById('att-date-input').value;
            window.open(`/api/reports/attendance?student_id=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}&date=${encodeURIComponent(date)}&export=csv`, '_blank');
        };
    }

    const exportAttPdf = document.getElementById('btn-export-attendance-pdf');
    if (exportAttPdf) {
        exportAttPdf.onclick = () => {
            const search = document.getElementById('att-search-input').value.trim();
            const dept = document.getElementById('att-dept-select').value;
            const status = document.getElementById('att-status-select').value;
            const date = document.getElementById('att-date-input').value;
            window.open(`/api/reports/attendance?student_id=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}&date=${encodeURIComponent(date)}&export=pdf`, '_blank');
        };
    }

    // 3. Marks / Results Report
    const filterResBtn = document.getElementById('btn-filter-results');
    if (filterResBtn) filterResBtn.onclick = () => loadResultsReport();

    const exportResCsv = document.getElementById('btn-export-results-csv');
    if (exportResCsv) {
        exportResCsv.onclick = () => {
            const search = document.getElementById('res-search-input').value.trim();
            const dept = document.getElementById('res-dept-select').value;
            const status = document.getElementById('res-status-select').value;
            const grade = document.getElementById('res-grade-select').value;
            window.open(`/api/reports/results?student_id=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}&grade=${encodeURIComponent(grade)}&export=csv`, '_blank');
        };
    }

    const exportResPdf = document.getElementById('btn-export-results-pdf');
    if (exportResPdf) {
        exportResPdf.onclick = () => {
            const search = document.getElementById('res-search-input').value.trim();
            const dept = document.getElementById('res-dept-select').value;
            const status = document.getElementById('res-status-select').value;
            const grade = document.getElementById('res-grade-select').value;
            window.open(`/api/reports/results?student_id=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}&grade=${encodeURIComponent(grade)}&export=pdf`, '_blank');
        };
    }
}

async function loadStudentsReport() {
    const search = document.getElementById('stu-search-input')?.value.trim() || '';
    const dept = document.getElementById('stu-dept-select')?.value || '';

    const res = await API.get(`/api/reports/students?search=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}`);
    const tbody = document.getElementById('tbl-students-report-body');
    const badge = document.getElementById('stu-count-badge');

    if (res && res.success && res.students) {
        if (badge) badge.textContent = `${res.count} Students`;
        if (res.students.length > 0) {
            tbody.innerHTML = res.students.map(s => `
                <tr>
                    <td><strong>${s.student_id}</strong></td>
                    <td>${s.name}</td>
                    <td>${s.department}</td>
                    <td>${s.course || 'N/A'}</td>
                    <td>${s.email}</td>
                    <td>${s.gender || 'N/A'}</td>
                    <td>${s.dob || 'N/A'}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No student records match search criteria.</td></tr>`;
        }
    }
}

async function loadAttendanceReport() {
    const search = document.getElementById('att-search-input')?.value.trim() || '';
    const dept = document.getElementById('att-dept-select')?.value || '';
    const status = document.getElementById('att-status-select')?.value || '';
    const date = document.getElementById('att-date-input')?.value || '';

    const url = `/api/reports/attendance?student_id=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}&date=${encodeURIComponent(date)}`;
    const res = await API.get(url);
    const tbody = document.getElementById('tbl-attendance-report-body');
    const badge = document.getElementById('att-count-badge');

    if (res && res.success && res.logs) {
        if (badge) badge.textContent = `${res.count} Records`;
        if (res.logs.length > 0) {
            tbody.innerHTML = res.logs.map(l => {
                const stClass = l.status === 'Present' ? 'badge-success' : 'badge-danger';
                return `
                    <tr>
                        <td>#${l.log_id || '-'}</td>
                        <td><strong>${l.student_id}</strong></td>
                        <td>${l.name || '-'}</td>
                        <td>${l.department || '-'}</td>
                        <td>${l.subject_code || 'CS101'}</td>
                        <td>${l.date}</td>
                        <td><span class="badge ${stClass}">${l.status}</span></td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No attendance logs found matching filters.</td></tr>`;
        }
    }
}

async function loadResultsReport() {
    const search = document.getElementById('res-search-input')?.value.trim() || '';
    const dept = document.getElementById('res-dept-select')?.value || '';
    const status = document.getElementById('res-status-select')?.value || '';
    const grade = document.getElementById('res-grade-select')?.value || '';

    const url = `/api/reports/results?student_id=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}&grade=${encodeURIComponent(grade)}`;
    const res = await API.get(url);
    const tbody = document.getElementById('tbl-results-report-body');
    const badge = document.getElementById('res-count-badge');

    if (res && res.success && res.marks) {
        if (badge) badge.textContent = `${res.count} Entries`;
        if (res.marks.length > 0) {
            tbody.innerHTML = res.marks.map(m => {
                const stClass = m.status === 'PASS' ? 'badge-success' : 'badge-danger';
                return `
                    <tr>
                        <td><strong>${m.student_id}</strong></td>
                        <td>${m.name}</td>
                        <td>${m.department}</td>
                        <td>${m.exam_name} (${m.subject})</td>
                        <td><strong>${m.marks_obtained}</strong> / ${m.max_marks}</td>
                        <td style="font-weight: 700;">${m.percentage.toFixed(1)}%</td>
                        <td><span class="badge badge-primary">${m.grade}</span></td>
                        <td><span class="badge ${stClass}">${m.status}</span></td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No examination results found.</td></tr>`;
        }
    }
}

async function loadFeedbackReport() {
    const res = await API.get('/api/reports/feedback');
    const body = document.getElementById('feedback-report-body');
    if (!body) return;
    
    if (res && res.success && res.feedback && res.feedback.length > 0) {
        body.innerHTML = res.feedback.map(f => `
            <tr>
                <td><strong>${f.student_id}</strong></td>
                <td>${f.student_name || 'N/A'}</td>
                <td>${f.faculty_name}</td>
                <td>${f.subject}</td>
                <td class="text-center">${f.q1}</td>
                <td class="text-center">${f.q2}</td>
                <td class="text-center">${f.q3}</td>
                <td class="text-center">${f.q4}</td>
                <td class="text-center">${f.q5}</td>
                <td style="max-width:150px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${f.comments || ''}">${f.comments || '-'}</td>
                <td>${f.created_at}</td>
            </tr>
        `).join('');
    } else {
        body.innerHTML = `<tr><td colspan="11" class="text-center text-muted">No feedback records found.</td></tr>`;
    }
}
