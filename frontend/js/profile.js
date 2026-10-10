// Student Profile & Academic Management Module

document.addEventListener("DOMContentLoaded", async () => {
    const authOk = await checkAuth(['admin', 'teacher', 'student']);
    if (authOk) {
        const titleEl = document.getElementById('header-view-title');
        const subTitleEl = document.getElementById('header-view-subtitle');
        if (titleEl) titleEl.textContent = "My Profile";
        if (subTitleEl) subTitleEl.textContent = "View personal records, attendance, results, and announcements";
        
        setupTabNavigation();
        await loadProfile();
        
        // Add avatar photo upload hover handler
        const container = document.querySelector('.profile-avatar-container');
        const overlay = document.querySelector('.profile-avatar-overlay');
        if (container && overlay) {
            container.onmouseenter = () => overlay.style.opacity = '1';
            container.onmouseleave = () => overlay.style.opacity = '0';
        }
    }
});

function setupTabNavigation() {
    const tabBtns = document.querySelectorAll('.profile-tab-btn');
    const tabContents = document.querySelectorAll('.profile-tab-content');

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

async function loadProfile() {
    const res = await API.get('/api/auth/profile');
    if (!res || !res.success) {
        showToast("Error", "Could not fetch profile details", "error");
        return;
    }
    
    const profile = res.profile;
    const studentId = profile.reference_id || profile.username || 'STU001';
    
    // Set Header & Banner Details
    const displayName = profile.name || profile.username;
    document.getElementById('det-avatar-name').textContent = displayName;
    
    if (document.getElementById('header-student-id')) {
        document.getElementById('header-student-id').textContent = studentId;
    }
    if (document.getElementById('header-dept')) {
        document.getElementById('header-dept').textContent = profile.department || 'General Department';
    }
    
    let roleText = "Student";
    if (profile.role === 'student' && profile.course) {
        roleText = `${profile.course}`;
    } else if (profile.role === 'teacher') {
        roleText = `Faculty - ${profile.department || 'No Dept'}`;
    }
    document.getElementById('det-avatar-role').textContent = roleText;
    
    // Avatar picture setup
    const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase();
    const fallback = document.getElementById('det-avatar-fallback');
    const avatarImg = document.getElementById('det-avatar-img');
    
    if (profile.profile_pic) {
        avatarImg.src = profile.profile_pic;
        avatarImg.classList.remove('hidden');
        fallback.classList.add('hidden');
    } else {
        avatarImg.classList.add('hidden');
        fallback.textContent = initials;
        fallback.classList.remove('hidden');
    }
    
    // Official Academic Information (Read-only)
    if (document.getElementById('det-id')) document.getElementById('det-id').textContent = studentId;
    if (document.getElementById('det-dept')) document.getElementById('det-dept').textContent = profile.department || 'N/A';
    if (document.getElementById('det-course')) document.getElementById('det-course').textContent = profile.course || 'N/A';
    if (document.getElementById('det-dob')) document.getElementById('det-dob').textContent = profile.dob || 'N/A';
    if (document.getElementById('det-gender')) document.getElementById('det-gender').textContent = profile.gender || 'N/A';
    if (document.getElementById('det-status')) document.getElementById('det-status').textContent = profile.status || 'Active Enrolled';
    
    // Personal Details (Editable fields)
    if (document.getElementById('det-email')) document.getElementById('det-email').textContent = profile.email || 'N/A';
    if (document.getElementById('det-phone')) document.getElementById('det-phone').textContent = profile.phone || 'N/A';
    if (document.getElementById('det-bio')) document.getElementById('det-bio').textContent = profile.bio || "No biography added yet.";
    if (document.getElementById('det-skills')) document.getElementById('det-skills').textContent = profile.skills || "Not specified";
    if (document.getElementById('det-achievements')) document.getElementById('det-achievements').textContent = profile.achievements || "None listed";
    if (document.getElementById('det-blood-group')) document.getElementById('det-blood-group').textContent = profile.blood_group || "Not specified";
    if (document.getElementById('det-emergency-contact')) document.getElementById('det-emergency-contact').textContent = profile.emergency_contact || "Not specified";
    if (document.getElementById('det-address')) document.getElementById('det-address').textContent = profile.address || "No address provided";
    
    // Wire Picture Change Trigger
    setupAvatarUpload();
    
    // Wire Personal Info Edit Form
    setupEditProfileForm(profile);

    // Load Academic Sections (Attendance, Marks, Announcements)
    await loadAttendanceData(studentId);
    await loadMarksData(studentId);
    await loadAnnouncementsData();
}

function setupAvatarUpload() {
    const changeAvatarTrigger = document.getElementById('btn-change-avatar');
    const fileInput = document.getElementById('profile-pic-input');
    
    if (changeAvatarTrigger && fileInput) {
        changeAvatarTrigger.onclick = () => fileInput.click();
        
        fileInput.onchange = async () => {
            if (fileInput.files.length === 0) return;
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('profile_pic', file);
            
            try {
                const resUpload = await fetch('/api/auth/profile/upload-profile-pic', {
                    method: 'POST',
                    body: formData
                });
                const data = await resUpload.json();
                if (data.success) {
                    showToast("Success", "Profile photo updated successfully.", "success");
                    loadProfile();
                    if (typeof updateSidebarHeaderUI === 'function') updateSidebarHeaderUI();
                } else {
                    showToast("Upload Failed", data.message || "Failed to save photo.", "error");
                }
            } catch (err) {
                console.error(err);
                showToast("Connection Error", "Could not send picture file to server.", "error");
            }
        };
    }
}

function setupEditProfileForm(profile) {
    const editBtn = document.getElementById('btn-edit-extra-info');
    const cancelBtn = document.getElementById('btn-cancel-extra-info');
    const displayPanel = document.getElementById('extra-info-display');
    const formPanel = document.getElementById('extra-info-form');
    
    if (editBtn && cancelBtn && displayPanel && formPanel) {
        editBtn.onclick = () => {
            document.getElementById('edit-name').value = profile.name || '';
            document.getElementById('edit-email').value = profile.email || '';
            document.getElementById('edit-phone').value = profile.phone || '';
            document.getElementById('edit-bio').value = profile.bio || '';
            document.getElementById('edit-skills').value = profile.skills || '';
            document.getElementById('edit-achievements').value = profile.achievements || '';
            document.getElementById('edit-blood-group').value = profile.blood_group || '';
            document.getElementById('edit-emergency-contact').value = profile.emergency_contact || '';
            document.getElementById('edit-address').value = profile.address || '';
            
            displayPanel.classList.add('hidden');
            formPanel.classList.remove('hidden');
        };
        
        cancelBtn.onclick = () => {
            formPanel.classList.add('hidden');
            displayPanel.classList.remove('hidden');
        };
        
        formPanel.onsubmit = async (e) => {
            e.preventDefault();
            // Authorized personal fields payload only
            const payload = {
                name: document.getElementById('edit-name').value.trim(),
                email: document.getElementById('edit-email').value.trim(),
                phone: document.getElementById('edit-phone').value.trim(),
                bio: document.getElementById('edit-bio').value.trim(),
                skills: document.getElementById('edit-skills').value.trim(),
                achievements: document.getElementById('edit-achievements').value.trim(),
                blood_group: document.getElementById('edit-blood-group').value.trim(),
                emergency_contact: document.getElementById('edit-emergency-contact').value.trim(),
                address: document.getElementById('edit-address').value.trim()
            };
            
            const resUpdate = await API.put('/api/auth/profile', payload);
            if (resUpdate && resUpdate.success) {
                showToast("Profile Updated", "Personal information saved successfully.", "success");
                loadProfile();
                if (typeof updateSidebarHeaderUI === 'function') updateSidebarHeaderUI();
                cancelBtn.click();
            } else {
                showToast("Error", resUpdate ? resUpdate.message : "Failed to update profile details.", "error");
            }
        };
    }
}

async function loadAttendanceData(studentId) {
    try {
        const res = await API.get(`/api/attendance/summary/${studentId}`);
        if (res && res.success && res.summary) {
            const sum = res.summary;
            const overallPct = sum.overall_percentage !== undefined ? sum.overall_percentage : 100.0;
            const totalCond = sum.overall_total !== undefined ? sum.overall_total : (sum.total_conducted || 0);
            const totalPres = sum.overall_present !== undefined ? sum.overall_present : (sum.total_present || 0);
            const totalAbs = Math.max(0, totalCond - totalPres);
            
            // Populate Stat Cards
            document.getElementById('quick-att-pct').textContent = `${overallPct.toFixed(1)}%`;
            if (overallPct < 75.0) {
                document.getElementById('quick-att-pct').style.color = '#ef4444';
            } else {
                document.getElementById('quick-att-pct').style.color = '#10b981';
            }
            
            document.getElementById('att-summary-total').textContent = totalCond;
            document.getElementById('att-summary-present').textContent = totalPres;
            document.getElementById('att-summary-absent').textContent = totalAbs;
            document.getElementById('att-summary-pct').textContent = `${overallPct.toFixed(1)}%`;

            // Low attendance warning
            const warningBanner = document.getElementById('att-warning-banner');
            if (overallPct < 75.0 && totalCond > 0) {
                warningBanner.innerHTML = `<span class="badge badge-danger" style="font-size: 0.85rem; padding: 6px 12px;"><i class="fa-solid fa-triangle-exclamation"></i> Low Attendance Warning (&lt;75%)</span>`;
            } else {
                warningBanner.innerHTML = `<span class="badge badge-success" style="font-size: 0.85rem; padding: 6px 12px;"><i class="fa-solid fa-circle-check"></i> Satisfactory Attendance</span>`;
            }

            // Subject-wise Breakdown Table
            const tbody = document.getElementById('tbl-subject-attendance-body');
            if (sum.subject_wise && sum.subject_wise.length > 0) {
                tbody.innerHTML = sum.subject_wise.map(sub => {
                    const hasSessions = sub.total_conducted > 0;
                    const pct = sub.percentage !== undefined ? sub.percentage : 100.0;
                    
                    let statusClass = 'badge-success';
                    let statusText = 'Eligible';
                    let pctDisplay = `${pct.toFixed(1)}%`;

                    if (!hasSessions) {
                        statusClass = 'badge-secondary';
                        statusText = 'No Classes Held';
                        pctDisplay = 'N/A';
                    } else if (pct < 75.0) {
                        statusClass = 'badge-danger';
                        statusText = 'Deported / Warning';
                    }

                    return `
                        <tr>
                            <td><strong>${sub.subject_code}</strong></td>
                            <td>${sub.subject_name}</td>
                            <td style="color: #10b981; font-weight: 600;">${sub.total_present}</td>
                            <td>${sub.total_conducted}</td>
                            <td style="font-weight: 700;">${pctDisplay}</td>
                            <td><span class="badge ${statusClass}">${statusText}</span></td>
                        </tr>
                    `;
                }).join('');
            } else {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No attendance records found for current subjects.</td></tr>`;
            }
        }
    } catch (err) {
        console.error("Failed to load student attendance data", err);
    }
}

async function loadMarksData(studentId) {
    try {
        const res = await API.get(`/api/marks/student/${studentId}`);
        if (res && res.success && res.result_card) {
            const card = res.result_card;
            
            const totalObt = card.total_obtained !== undefined ? card.total_obtained : (card.total_marks || 0);
            const totalMax = card.total_max !== undefined ? card.total_max : (card.total_max_marks || 0);
            const overallPct = card.overall_percentage !== undefined ? card.overall_percentage : (totalMax > 0 ? (totalObt / totalMax * 100) : 0);

            document.getElementById('quick-gpa').textContent = `${overallPct.toFixed(1)}%`;
            document.getElementById('res-total-obt').textContent = Math.round(totalObt);
            document.getElementById('res-total-max').textContent = Math.round(totalMax);
            document.getElementById('res-overall-pct').textContent = `${overallPct.toFixed(1)}%`;
            document.getElementById('res-overall-grade').textContent = card.overall_grade || '-';

            const statusBadge = document.getElementById('res-overall-status-badge');
            const overallStatus = card.overall_status || card.academic_status;
            if (overallStatus === 'PASS') {
                statusBadge.className = 'badge badge-success';
                statusBadge.textContent = 'Overall PASS';
            } else if (overallStatus === 'FAIL') {
                statusBadge.className = 'badge badge-danger';
                statusBadge.textContent = 'Needs Improvement (FAIL)';
            } else {
                statusBadge.className = 'badge badge-primary';
                statusBadge.textContent = 'Academic Record';
            }

            const tbody = document.getElementById('tbl-marks-body');
            if (card.marks_records && card.marks_records.length > 0) {
                tbody.innerHTML = card.marks_records.map(rec => {
                    const statusClass = rec.status === 'PASS' ? 'badge-success' : 'badge-danger';
                    const pct = rec.percentage !== undefined ? rec.percentage : (rec.max_marks > 0 ? (rec.marks_obtained / rec.max_marks * 100) : 0);
                    
                    // Standard Institutional Grading Scale
                    let grade = rec.grade;
                    if (!grade || grade === 'N/A' || grade === 'F' && rec.status === 'PASS') {
                        if (pct >= 90) grade = 'A+';
                        else if (pct >= 80) grade = 'A';
                        else if (pct >= 70) grade = 'B';
                        else if (pct >= 60) grade = 'C';
                        else if (pct >= 40) grade = 'D';
                        else grade = 'F';
                    }
                    
                    // Ensure grade accurately reflects score percentage if misclassified
                    if (pct >= 80 && pct < 90 && grade === 'B') {
                        grade = 'A';
                    }

                    return `
                        <tr>
                            <td><strong>${rec.exam_name || 'Terminal Exam'}</strong></td>
                            <td>${rec.subject || 'Core Subject'}</td>
                            <td style="font-weight: 600;">${rec.marks_obtained}</td>
                            <td>${rec.max_marks}</td>
                            <td style="font-weight: 700;">${pct.toFixed(1)}%</td>
                            <td><span class="badge badge-primary" style="font-weight:700;">${grade}</span></td>
                            <td><span class="badge ${statusClass}">${rec.status}</span></td>
                        </tr>
                    `;
                }).join('');
            } else {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No examination marks recorded yet.</td></tr>`;
            }
        }
    } catch (err) {
        console.error("Failed to load student marks data", err);
    }
}

async function loadAnnouncementsData() {
    try {
        const res = await API.get('/api/announcements');
        const container = document.getElementById('announcements-container');
        if (!container) return;

        const isStaff = STATE.user && (STATE.user.role === 'admin' || STATE.user.role === 'teacher');

        if (res && res.success && res.announcements && res.announcements.length > 0) {
            container.innerHTML = res.announcements.map(ann => `
                <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border); border-left: 4px solid var(--accent-gold); padding: 1.25rem; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                        <h4 style="font-weight: 700; font-size: 1.05rem;">${ann.title}</h4>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 0.75rem; color: var(--text-muted);">${ann.created_at || 'Recently'}</span>
                            ${isStaff ? `
                            <button class="btn btn-outline" style="padding: 2px 6px; font-size: 0.75rem; color: var(--danger); border-color: var(--danger);" onclick="deleteAnnouncementProfile('${ann.announcement_id}')" title="Delete Announcement">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                            ` : ''}
                        </div>
                    </div>
                    <p style="font-size: 0.9rem; color: var(--text-main); line-height: 1.5; margin-bottom: 8px;">${ann.message}</p>
                    <div style="font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 1rem;">
                        <span><i class="fa-solid fa-user"></i> Posted by: <strong>${ann.posted_by || 'Admin'}</strong></span>
                        <span><i class="fa-solid fa-tag"></i> Target: <strong>${ann.target_role || 'All'}</strong></span>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No campus announcements available at present.</div>`;
        }
    } catch (err) {
        console.error("Failed to load announcements", err);
    }
}

async function deleteAnnouncementProfile(announcementId) {
    showConfirmModal("Confirm Deletion", "Are you sure you want to delete this campus announcement broadcast?", async () => {
        const res = await API.delete(`/api/announcements/${announcementId}`);
        if (res && res.success) {
            showToast("Deleted", "Announcement deleted successfully.", "success");
            loadAnnouncementsData();
        } else {
            showToast("Error", res.message || "Failed to delete announcement.", "error");
        }
    });
}
