// Dashboard Overview Analytics Charts, Metrics, Activities & Announcements

async function loadDashboardAnalytics() {
    const res = await API.get('/api/analytics');
    if (!res || !res.success) return;

    // 1. Load Metrics Cards & Count-Up Animation
    const totalStudentsEl = document.getElementById('dash-metric-students');
    const totalFacultyEl = document.getElementById('dash-metric-faculty');
    const totalCoursesEl = document.getElementById('dash-metric-courses');
    const avgAttendanceEl = document.getElementById('dash-metric-attendance');
    const feeRateEl = document.getElementById('dash-metric-fees');
    const riskEl = document.getElementById('dash-metric-risk');
    const welcomeStuCount = document.getElementById('welcome-student-count');
    
    if (totalStudentsEl) animateCountUp(totalStudentsEl, res.metrics.total_students || 0);
    if (welcomeStuCount) welcomeStuCount.textContent = res.metrics.total_students || 0;
    if (totalFacultyEl) animateCountUp(totalFacultyEl, res.metrics.total_faculty || 0);
    if (totalCoursesEl) {
        const cCount = res.metrics.total_courses || 0;
        const sCount = res.metrics.total_subjects || 0;
        totalCoursesEl.textContent = `${cCount} / ${sCount}`;
    }
    if (avgAttendanceEl) avgAttendanceEl.textContent = `${res.metrics.average_attendance || 0}%`;
    
    if (feeRateEl) {
        const collectRate = (res.metrics.fees_collected / (res.metrics.fees_collected + res.metrics.fees_pending || 1)) * 100;
        feeRateEl.textContent = `${Math.round(collectRate)}%`;
    }
    if (riskEl) riskEl.textContent = res.ai_risk_distribution ? (res.ai_risk_distribution["High Risk"] || 0) : 0;

    // 2. Render Analytics Charts
    if (document.getElementById('branchChart')) renderBranchChart(res.students_by_branch || res.department_distribution);
    if (document.getElementById('yearChart')) renderYearChart(res.students_by_year);
    if (document.getElementById('attDistChart')) renderAttendanceDistChart(res.attendance_distribution);
    if (document.getElementById('subjectPerfChart')) renderSubjectPerfChart(res.subject_performance);
    if (document.getElementById('passFailChart')) renderPassFailChart(res.pass_fail_distribution);
    if (document.getElementById('gradeChart')) renderGradeDistributionChart(res.grade_distribution);
    if (document.getElementById('riskChart')) renderRiskAnalysisChart(res.ai_risk_distribution);

    // 3. Render Recent Students Table
    if (res.recent_students) {
        renderRecentStudentsTable(res.recent_students);
    }

    // 4. Render Campus Announcements
    if (res.recent_announcements) {
        renderAnnouncementsList(res.recent_announcements);
    }

    // 5. Render Recent Activities Stream
    if (res.recent_activities) {
        renderRecentActivitiesTimeline(res.recent_activities);
    }

    // 6. Connect Modal Triggers & Form Handlers
    initAddStudentModal();
    initAnnouncementModal();
    initViewAnnouncementModal();
}

// Count Up Number Animation
function animateCountUp(el, endVal, duration = 800) {
    let startVal = 0;
    const stepTime = Math.abs(Math.floor(duration / (endVal || 1)));
    if (endVal === 0) {
        el.textContent = "0";
        return;
    }
    const timer = setInterval(() => {
        startVal += 1;
        el.textContent = startVal;
        if (startVal >= endVal) {
            el.textContent = endVal;
            clearInterval(timer);
        }
    }, Math.max(stepTime, 20));
}

function renderRecentStudentsTable(students) {
    const tbody = document.getElementById('dash-recent-students-tbody');
    if (!tbody) return;
    
    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 15px;" class="text-muted">No recent student enrollments found.</td></tr>`;
        return;
    }
    
    tbody.innerHTML = students.map(s => `
        <tr style="border-bottom: 1px solid var(--border-color); transition: background 0.2s;">
            <td style="padding: 10px; font-weight: 700; font-size: 0.85rem; color: var(--accent-gold);">${s.student_id}</td>
            <td style="padding: 10px; font-weight: 600; color: var(--text-main);">${s.name}</td>
            <td style="padding: 10px; font-size: 0.82rem;" class="text-muted">${s.department || 'General'}</td>
            <td style="padding: 10px;">
                <span class="badge ${s.status === 'Inactive' ? 'badge-warning' : 'badge-success'}" style="padding: 3px 8px; border-radius: 6px; font-size: 0.72rem;">${s.status || 'Active'}</span>
            </td>
            <td style="padding: 10px; text-align: right;">
                <a href="students.html?id=${s.student_id}" class="btn btn-sm btn-outline" style="padding: 3px 10px; font-size: 0.75rem; text-decoration: none;">Profile &rarr;</a>
            </td>
        </tr>
    `).join('');
}

let currentViewAnnouncementId = null;

function renderAnnouncementsList(announcements) {
    const container = document.getElementById('dash-announcements-list');
    if (!container) return;

    if (!announcements || announcements.length === 0) {
        container.innerHTML = `<div class="text-muted" style="text-align: center; padding: 20px; font-size: 0.85rem;">No campus announcements posted yet.</div>`;
        return;
    }

    const isStaff = STATE.user && (STATE.user.role === 'admin' || STATE.user.role === 'teacher');

    container.innerHTML = announcements.map((a, idx) => `
        <div class="bulletin-item glassmorphism" style="padding: 12px; margin-bottom: 10px; border-radius: 10px; border: 1px solid var(--border-color); transition: all 0.2s;">
            <div class="bulletin-meta" style="display: flex; justify-content: space-between; margin-bottom: 4px; align-items: center;">
                <span class="bulletin-tag info" style="font-size: 0.68rem; text-transform: uppercase; font-weight: 700; background: rgba(59,130,246,0.15); color: var(--accent-blue); padding: 2px 6px; border-radius: 4px;">${a.department || 'All Departments'}</span>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="bulletin-date" style="font-size: 0.72rem; color: var(--text-muted);">${(a.created_at || '').substring(0, 10)}</span>
                    ${isStaff ? `
                    <button class="btn-delete-ann-card" data-id="${a.announcement_id}" title="Delete Announcement" style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239,68,68,0.3); color: var(--danger); width: 22px; height: 22px; border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; font-size: 0.7rem;">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                    ` : ''}
                </div>
            </div>
            <h4 class="ann-card-clickable" data-idx="${idx}" style="margin: 4px 0; font-size: 0.9rem; color: var(--text-main); font-weight: 700; cursor: pointer;">${a.title}</h4>
            <p class="ann-card-clickable" data-idx="${idx}" style="margin: 0; font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; cursor: pointer;">${a.message}</p>
            <div style="font-size: 0.7rem; color: var(--accent-gold); margin-top: 6px; display: flex; justify-content: space-between; align-items: center;">
                <span>Posted by: ${a.posted_by || 'Admin'}</span>
                <span class="ann-card-clickable" data-idx="${idx}" style="font-weight: 600; cursor: pointer;">Read detail &rarr;</span>
            </div>
        </div>
    `).join('');

    container.querySelectorAll('.ann-card-clickable').forEach(el => {
        el.onclick = () => {
            const idx = el.getAttribute('data-idx');
            const targetAnn = announcements[idx];
            if (targetAnn) openViewAnnouncementModal(targetAnn);
        };
    });

    container.querySelectorAll('.btn-delete-ann-card').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const annId = btn.getAttribute('data-id');
            if (annId) deleteAnnouncementRecord(annId);
        };
    });
}

function renderRecentActivitiesTimeline(activities) {
    const container = document.getElementById('dash-recent-activities-list');
    if (!container) return;

    if (!activities || activities.length === 0) {
        container.innerHTML = `<div class="text-muted" style="text-align: center; padding: 15px; font-size: 0.82rem;">No recent activities logged.</div>`;
        return;
    }

    container.innerHTML = activities.map(act => `
        <div class="activity-item">
            <div class="activity-icon"><i class="fa-solid ${act.icon}"></i></div>
            <div class="activity-details">
                <div class="activity-title">${act.title}</div>
                <div class="activity-desc">${act.description}</div>
                <div class="activity-time"><i class="fa-solid fa-clock" style="font-size: 0.65rem;"></i> ${act.timestamp}</div>
            </div>
        </div>
    `).join('');
}

// 1. EMBEDDED ADD STUDENT MODAL
function initAddStudentModal() {
    const triggerBtn = document.getElementById('btn-trigger-add-student-modal');
    const modal = document.getElementById('dash-add-student-modal');
    const closeBtn = document.getElementById('btn-close-add-student-modal');
    const cancelBtn = document.getElementById('btn-cancel-add-student');
    const form = document.getElementById('form-dash-add-student');

    if (triggerBtn && modal) {
        triggerBtn.onclick = () => modal.classList.remove('hidden');
    }
    if (closeBtn && modal) {
        closeBtn.onclick = () => modal.classList.add('hidden');
    }
    if (cancelBtn && modal) {
        cancelBtn.onclick = () => modal.classList.add('hidden');
    }

    if (form && modal) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const student_id = document.getElementById('dash-stu-id').value.trim();
            const name = document.getElementById('dash-stu-name').value.trim();
            const email = document.getElementById('dash-stu-email').value.trim();
            const phone = document.getElementById('dash-stu-phone').value.trim();
            const department = document.getElementById('dash-stu-dept').value;
            const course = document.getElementById('dash-stu-course').value.trim();
            const dob = document.getElementById('dash-stu-dob').value;
            const gender = document.getElementById('dash-stu-gender').value;

            const payload = { student_id, name, email, phone, department, course, dob, gender };
            const res = await API.post('/api/students', payload);

            if (res && res.success) {
                showToast("Student Enrolled", `Student '${name}' registered successfully.`, "success");
                modal.classList.add('hidden');
                form.reset();
                loadDashboardAnalytics();
            } else {
                showToast("Enrollment Failed", res.message || "Failed to add student.", "error");
            }
        };
    }
}

// 2. POST ANNOUNCEMENT MODAL
function initAnnouncementModal() {
    const triggerBtn = document.getElementById('btn-trigger-announcement-modal');
    const cardTriggerBtn = document.getElementById('btn-card-post-announcement');
    const modal = document.getElementById('post-announcement-modal');
    const closeBtn = document.getElementById('btn-close-announcement-modal');
    const cancelBtn = document.getElementById('btn-cancel-announcement');
    const form = document.getElementById('form-post-announcement');

    const openModal = () => modal && modal.classList.remove('hidden');

    if (triggerBtn) triggerBtn.onclick = openModal;
    if (cardTriggerBtn) cardTriggerBtn.onclick = openModal;
    if (closeBtn && modal) closeBtn.onclick = () => modal.classList.add('hidden');
    if (cancelBtn && modal) cancelBtn.onclick = () => modal.classList.add('hidden');

    if (form && modal) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const title = document.getElementById('announcement-title').value.trim();
            const target_role = document.getElementById('announcement-role').value;
            const department = document.getElementById('announcement-dept').value;
            const message = document.getElementById('announcement-message').value.trim();

            const res = await API.post('/api/announcements', { title, target_role, department, message });
            if (res && res.success) {
                showToast("Announcement Published", "Campus broadcast posted successfully.", "success");
                modal.classList.add('hidden');
                form.reset();

                const refreshRes = await API.get('/api/announcements');
                if (refreshRes && refreshRes.announcements) {
                    renderAnnouncementsList(refreshRes.announcements);
                }
            } else {
                showToast("Publishing Failed", res.message || "Failed to post announcement.", "error");
            }
        };
    }

    const refreshBtn = document.getElementById('btn-refresh-announcements');
    if (refreshBtn) {
        refreshBtn.onclick = async () => {
            const refreshRes = await API.get('/api/announcements');
            if (refreshRes && refreshRes.announcements) {
                renderAnnouncementsList(refreshRes.announcements);
                showToast("Refreshed", "Campus announcements updated.", "success");
            }
        };
    }
}

// 3. VIEW ANNOUNCEMENT DETAIL MODAL
function initViewAnnouncementModal() {
    const modal = document.getElementById('view-announcement-modal');
    const closeBtn = document.getElementById('btn-close-view-ann-modal');
    const closeBtn2 = document.getElementById('btn-close-view-ann-btn');

    if (closeBtn && modal) closeBtn.onclick = () => modal.classList.add('hidden');
    if (closeBtn2 && modal) closeBtn2.onclick = () => modal.classList.add('hidden');
}

function openViewAnnouncementModal(announcement) {
    const modal = document.getElementById('view-announcement-modal');
    if (!modal) return;

    currentViewAnnouncementId = announcement.announcement_id;
    document.getElementById('view-ann-title').textContent = announcement.title;
    document.getElementById('view-ann-dept').textContent = announcement.department || 'All Departments';
    document.getElementById('view-ann-date').textContent = (announcement.created_at || '').substring(0, 10);
    document.getElementById('view-ann-body').textContent = announcement.message;
    document.getElementById('view-ann-author').textContent = announcement.posted_by || 'Admin';

    const deleteBtn = document.getElementById('btn-delete-view-ann-btn');
    if (deleteBtn) {
        const isStaff = STATE.user && (STATE.user.role === 'admin' || STATE.user.role === 'teacher');
        deleteBtn.style.display = isStaff ? 'inline-flex' : 'none';
        deleteBtn.onclick = () => {
            if (currentViewAnnouncementId) {
                deleteAnnouncementRecord(currentViewAnnouncementId);
            }
        };
    }

    modal.classList.remove('hidden');
}

async function deleteAnnouncementRecord(announcementId) {
    showConfirmModal("Confirm Announcement Deletion", "Are you sure you want to delete this campus announcement broadcast?", async () => {
        const res = await API.delete(`/api/announcements/${announcementId}`);
        if (res && res.success) {
            showToast("Announcement Deleted", res.message || "Announcement deleted successfully.", "success");
            const modal = document.getElementById('view-announcement-modal');
            if (modal) modal.classList.add('hidden');

            const refreshRes = await API.get('/api/announcements');
            if (refreshRes && refreshRes.announcements) {
                renderAnnouncementsList(refreshRes.announcements);
            } else if (typeof loadDashboardAnalytics === 'function') {
                loadDashboardAnalytics();
            }
        } else {
            showToast("Error", res.message || "Failed to delete announcement.", "error");
        }
    });
}
window.deleteAnnouncementRecord = deleteAnnouncementRecord;

// Chart.js rendering functions
function renderBranchChart(branchData) {
    const canvas = document.getElementById('branchChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (STATE.charts && STATE.charts.branch) STATE.charts.branch.destroy();
    if (!STATE.charts) STATE.charts = {};

    const labels = branchData ? Object.keys(branchData) : [];
    const data = branchData ? Object.values(branchData) : [];

    STATE.charts.branch = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.length > 0 ? labels : ['No Data'],
            datasets: [{
                data: data.length > 0 ? data : [1],
                backgroundColor: labels.length > 0 ? ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4'] : ['rgba(255,255,255,0.1)'],
                borderWidth: 1.5,
                borderColor: 'transparent'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (e, items) => {
                if (items.length > 0) {
                    const idx = items[0].index;
                    const selectedDept = labels[idx];
                    if (selectedDept) window.location.href = `students.html?department=${encodeURIComponent(selectedDept)}`;
                }
            },
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8, color: 'var(--text-muted)', font: { size: 10 } } }
            },
            cutout: '65%'
        }
    });
}

function renderYearChart(yearData) {
    const canvas = document.getElementById('yearChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (STATE.charts && STATE.charts.year) STATE.charts.year.destroy();
    if (!STATE.charts) STATE.charts = {};

    const defaultYears = ['1st Year', '2nd Year', '3rd Year', '4th Year'];
    const labels = yearData && Object.keys(yearData).length > 0 ? Object.keys(yearData) : defaultYears;
    const data = labels.map(y => (yearData && yearData[y]) || 0);

    STATE.charts.year = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Enrolled Students',
                data: data,
                backgroundColor: 'rgba(245, 158, 11, 0.85)',
                borderColor: '#f59e0b',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } }
            }
        }
    });
}

function renderAttendanceDistChart(attDistData) {
    const canvas = document.getElementById('attDistChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (STATE.charts && STATE.charts.attDist) STATE.charts.attDist.destroy();
    if (!STATE.charts) STATE.charts = {};

    const labels = ['Above 85%', '75% - 85%', 'Below 75%'];
    const data = labels.map(l => (attDistData && attDistData[l]) || 0);

    STATE.charts.attDist = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#10b981', '#3b82f6', '#ef4444'],
                borderWidth: 1.5,
                borderColor: 'transparent'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8, color: 'var(--text-muted)', font: { size: 10 } } }
            }
        }
    });
}

function renderSubjectPerfChart(subPerfData) {
    const canvas = document.getElementById('subjectPerfChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (STATE.charts && STATE.charts.subPerf) STATE.charts.subPerf.destroy();
    if (!STATE.charts) STATE.charts = {};

    const labels = subPerfData ? Object.keys(subPerfData) : [];
    const data = subPerfData ? Object.values(subPerfData) : [];

    STATE.charts.subPerf = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length > 0 ? labels : ['No Subjects'],
            datasets: [{
                label: 'Average Score (%)',
                data: data.length > 0 ? data : [0],
                backgroundColor: 'rgba(139, 92, 246, 0.85)',
                borderColor: '#8b5cf6',
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { min: 0, max: 100, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                y: { grid: { display: false } }
            }
        }
    });
}

function renderPassFailChart(passFailData) {
    const canvas = document.getElementById('passFailChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (STATE.charts && STATE.charts.passFail) STATE.charts.passFail.destroy();
    if (!STATE.charts) STATE.charts = {};

    const passCount = (passFailData && passFailData['Pass']) || 0;
    const failCount = (passFailData && passFailData['Fail']) || 0;

    STATE.charts.passFail = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['PASS', 'FAIL'],
            datasets: [{
                data: [passCount, failCount],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 1.5,
                borderColor: 'transparent'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8, color: 'var(--text-muted)', font: { size: 10 } } }
            },
            cutout: '70%'
        }
    });
}

function renderGradeDistributionChart(gradeData) {
    const canvas = document.getElementById('gradeChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (STATE.charts && STATE.charts.grade) STATE.charts.grade.destroy();
    if (!STATE.charts) STATE.charts = {};

    const labels = ['A', 'B', 'C', 'D', 'E', 'F'];
    const data = labels.map(g => (gradeData && gradeData[g]) || 0);

    STATE.charts.grade = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Student Count',
                data: data,
                backgroundColor: 'rgba(59, 130, 246, 0.85)',
                borderColor: '#3b82f6',
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } }
            }
        }
    });
}

function renderRiskAnalysisChart(riskData) {
    const canvas = document.getElementById('riskChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (STATE.charts && STATE.charts.risk) STATE.charts.risk.destroy();
    if (!STATE.charts) STATE.charts = {};

    const labels = ['Low Risk', 'Moderate Risk', 'High Risk'];
    const data = labels.map(r => (riskData && riskData[r]) || 0);

    STATE.charts.risk = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 2,
                borderColor: 'transparent'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8, color: 'var(--text-muted)', font: { size: 10 } } }
            },
            cutout: '70%'
        }
    });
}

async function loadStudentDashboard(studentId) {
    if (!studentId) return;

    try {
        const [attRes, gradesRes, feesRes] = await Promise.all([
            API.get(`/api/attendance/summary/${studentId}`),
            API.get(`/api/exams/marks/student/${studentId}`),
            API.get(`/api/fees/student/${studentId}`)
        ]);

        // 1. Attendance Metric
        const attEl = document.getElementById('student-metric-attendance');
        if (attEl && attRes && attRes.success && attRes.summary) {
            attEl.textContent = `${attRes.summary.overall_percentage}%`;
            if (attRes.summary.low_attendance_warning) {
                attEl.style.color = 'var(--danger)';
            } else {
                attEl.style.color = 'var(--success)';
            }
        }

        // 2. Grades Metric
        const gradesEl = document.getElementById('student-metric-grades');
        if (gradesEl && gradesRes && gradesRes.success && gradesRes.marks) {
            const marks = gradesRes.marks;
            if (marks.length > 0) {
                const totalPct = marks.reduce((acc, m) => acc + (m.obtained_marks / (m.max_marks || 100) * 100), 0);
                const avgPct = Math.round(totalPct / marks.length);
                gradesEl.textContent = `${avgPct}%`;
            } else {
                gradesEl.textContent = "N/A";
            }
        }

        // 3. Fees Due Metric
        const feesEl = document.getElementById('student-metric-fees-due');
        if (feesEl && feesRes && feesRes.success && feesRes.fees) {
            const pending = feesRes.fees.pending_amount || 0;
            feesEl.textContent = `₹${pending.toLocaleString('en-IN')}`;
        }

        // 4. AI Risk Status
        const riskEl = document.getElementById('student-metric-risk');
        if (riskEl && attRes && attRes.success && attRes.summary) {
            const isLow = attRes.summary.low_attendance_warning;
            if (isLow) {
                riskEl.textContent = "Moderate Risk";
                riskEl.className = "text-yellow font-bold";
            } else {
                riskEl.textContent = "Good Standing";
                riskEl.className = "text-green font-bold";
            }
        }
    } catch (err) {
        console.error("Error loading student dashboard metrics:", err);
    }
}
