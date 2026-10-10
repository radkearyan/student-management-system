// Students Directory and Detail Profiling Manager

let DEPARTMENTS_CACHE = null;
let dropdownsPopulated = false;

// ─── Add Student Modal Wiring ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const openBtn    = document.getElementById('btn-open-add-student-modal');
    const closeBtn   = document.getElementById('btn-close-student-modal');
    const cancelBtn  = document.getElementById('btn-cancel-student-modal');
    const modal      = document.getElementById('add-student-modal');
    const form       = document.getElementById('add-student-form');

    if (openBtn && modal) {
        openBtn.addEventListener('click', () => {
            form.reset();
            modal.classList.remove('hidden');
        });
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
            form.reset();
        });
    }

    if (cancelBtn && modal) {
        cancelBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
            form.reset();
        });
    }

    // Close on backdrop click
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
                form.reset();
            }
        });
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = form.querySelector('[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enrolling...';

            const payload = {
                student_id: document.getElementById('stu-id').value.trim(),
                name:       document.getElementById('stu-name').value.trim(),
                dob:        document.getElementById('stu-dob').value,
                gender:     document.getElementById('stu-gender').value,
                email:      document.getElementById('stu-email').value.trim(),
                phone:      document.getElementById('stu-phone').value.trim(),
                department: document.getElementById('stu-dept').value,
                course:     document.getElementById('stu-course').value.trim()
            };

            const res = await API.post('/api/students', payload);

            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;

            if (res && res.success) {
                showToast('Student Enrolled', res.message || 'Student added successfully.', 'success');
                modal.classList.add('hidden');
                form.reset();
                loadStudentsRegistry();
            } else {
                showToast('Enrollment Failed', res.message || 'Failed to add student. Please try again.', 'error');
            }
        });
    }
    // Live search & filter listeners
    const searchInput = document.getElementById('student-search-input');
    const deptFilterSelect = document.getElementById('student-dept-filter');
    if (searchInput) {
        searchInput.addEventListener('input', () => loadStudentsRegistry());
    }
    if (deptFilterSelect) {
        deptFilterSelect.addEventListener('change', () => loadStudentsRegistry());
    }

    // Edit modal wiring
    const editModal = document.getElementById('edit-student-modal');
    const editCloseBtn = document.getElementById('btn-close-edit-student-modal');
    const editCancelBtn = document.getElementById('btn-cancel-edit-student-modal');
    const editForm = document.getElementById('edit-student-form');

    if (editCloseBtn && editModal) {
        editCloseBtn.onclick = () => editModal.classList.add('hidden');
    }
    if (editCancelBtn && editModal) {
        editCancelBtn.onclick = () => editModal.classList.add('hidden');
    }

    if (editForm) {
        editForm.onsubmit = async (e) => {
            e.preventDefault();
            const sid = document.getElementById('edit-stu-id').value;
            const payload = {
                name: document.getElementById('edit-stu-name').value.trim(),
                dob: document.getElementById('edit-stu-dob').value,
                gender: document.getElementById('edit-stu-gender').value,
                email: document.getElementById('edit-stu-email').value.trim(),
                phone: document.getElementById('edit-stu-phone').value.trim(),
                department: document.getElementById('edit-stu-dept').value,
                course: document.getElementById('edit-stu-course').value.trim(),
                status: document.getElementById('edit-stu-status').value
            };

            const res = await API.put(`/api/students/${sid}`, payload);
            if (res && res.success) {
                showToast("Success", "Student updated successfully.", "success");
                editModal.classList.add('hidden');
                loadStudentsRegistry();
            } else {
                showToast("Error", res.message || "Failed to update student.", "error");
            }
        };
    }
});
// ─────────────────────────────────────────────────────────────────────────────

async function getCachedDepartments() {
    if (!DEPARTMENTS_CACHE) {
        DEPARTMENTS_CACHE = await API.get('/api/departments') || [];
    }
    return DEPARTMENTS_CACHE;
}

function populateDepartmentDropdownsOnce(depts) {
    if (dropdownsPopulated) return;

    const isTeacher = STATE.user && STATE.user.role === 'teacher' && STATE.user.department;
    const facultyDept = isTeacher ? STATE.user.department : null;

    const icons = {
        'Computer Engineering': 'fa-laptop-code',
        'Information Technology': 'fa-network-wired',
        'Electrical Engineering': 'fa-bolt-lightning',
        'Mechanical Engineering': 'fa-gears',
        'Civil Engineering': 'fa-building'
    };

    if (isTeacher) {
        depts = depts.filter(d => d.name === facultyDept);
        if (depts.length === 0) depts = [{ name: facultyDept }];
    }
    
    // 1. Filter dropdown
    const filterSelect = document.getElementById('student-dept-filter');
    if (filterSelect) {
        if (isTeacher) {
            filterSelect.innerHTML = `<option value="${facultyDept}">${facultyDept} (My Department)</option>`;
            filterSelect.disabled = true;
        } else {
            filterSelect.innerHTML = '<option value="">All Departments</option>';
            depts.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.name;
                opt.textContent = d.name;
                filterSelect.appendChild(opt);
            });
        }
    }

    // 2. Form select in add/edit student modal
    const formSelect = document.getElementById('stu-dept');
    if (formSelect) {
        if (isTeacher) {
            formSelect.innerHTML = `<option value="${facultyDept}">${facultyDept}</option>`;
            formSelect.disabled = true;
        } else {
            formSelect.innerHTML = '';
            depts.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.name;
                opt.textContent = d.name;
                formSelect.appendChild(opt);
            });
        }
    }

    // 3. Render department cards
    const cardsContainer = document.querySelector('.department-category-cards');
    if (cardsContainer) {
        if (isTeacher) {
            const icon = icons[facultyDept] || 'fa-building';
            cardsContainer.innerHTML = `
                <div class="dept-card active glassmorphism" data-dept-card="${facultyDept}" style="cursor: default; grid-column: 1 / -1; max-width: 480px;">
                    <div class="dept-card-icon" style="background: rgba(16, 185, 129, 0.15); color: var(--success);"><i class="fa-solid ${icon}"></i></div>
                    <div class="dept-card-info">
                        <h4>${facultyDept} <span style="font-size: 0.72rem; background: var(--accent-blue); color: white; padding: 2px 8px; border-radius: 12px; margin-left: 6px;"><i class="fa-solid fa-lock"></i> Your Assigned Branch</span></h4>
                        <span class="dept-student-count" id="count-dept-${facultyDept.toLowerCase().replace(/[^a-z0-9]/g, '')}">0 Students</span>
                    </div>
                </div>
            `;
        } else {
            cardsContainer.innerHTML = `
                <div class="dept-card active glassmorphism" data-dept-card="All" onclick="filterByDeptCard('All')">
                    <div class="dept-card-icon"><i class="fa-solid fa-graduation-cap"></i></div>
                    <div class="dept-card-info">
                        <h4>All Branches</h4>
                        <span class="dept-student-count" id="count-dept-all">0 Students</span>
                    </div>
                </div>
            `;
            
            depts.forEach(d => {
                const icon = icons[d.name] || 'fa-building';
                const shortName = d.name.replace('Engineering', 'Engg').replace('Technology', 'Tech');
                cardsContainer.innerHTML += `
                    <div class="dept-card glassmorphism" data-dept-card="${d.name}" onclick="filterByDeptCard('${d.name}')">
                        <div class="dept-card-icon"><i class="fa-solid ${icon}"></i></div>
                        <div class="dept-card-info">
                            <h4>${shortName}</h4>
                            <span class="dept-student-count" id="count-dept-${d.name.toLowerCase().replace(/[^a-z0-9]/g, '')}">0 Students</span>
                        </div>
                    </div>
                `;
            });
        }
    }
    
    dropdownsPopulated = true;
}

async function loadStudentsRegistry() {
    const isTeacher = STATE.user && STATE.user.role === 'teacher' && STATE.user.department;
    const facultyDept = isTeacher ? STATE.user.department : null;

    const searchVal = document.getElementById('student-search-input').value;
    const deptFilter = isTeacher ? facultyDept : document.getElementById('student-dept-filter').value;
    
    let url = `/api/students?search=${encodeURIComponent(searchVal)}`;
    if (deptFilter) {
        url += `&department=${encodeURIComponent(deptFilter)}`;
    }
    const students = await API.get(url);
    if (!students) return;

    let depts = await getCachedDepartments();
    if (isTeacher) {
        depts = depts.filter(d => d.name === facultyDept);
        if (depts.length === 0) depts = [{ name: facultyDept }];
    }
    populateDepartmentDropdownsOnce(depts);

    // Filter department count indicator calculations
    const counts = {};
    depts.forEach(d => {
        counts[d.name] = 0;
    });
    students.forEach(s => {
        if (counts[s.department] !== undefined) {
            counts[s.department]++;
        }
    });

    const countAll = document.getElementById('count-dept-all');
    if (countAll) countAll.textContent = `${students.length} Students`;
    
    depts.forEach(d => {
        const id = `count-dept-${d.name.toLowerCase().replace(/[^a-z0-9]/g, '')}`;
        const el = document.getElementById(id);
        if (el) el.textContent = `${counts[d.name]} Students`;
    });

    updateActiveDeptCardUI();

    // Render grouped lists by department
    const container = document.getElementById('students-grouped-container');
    if (!container) return;
    container.innerHTML = '';

    const departments = depts.map(d => d.name);

    let totalRendered = 0;

    departments.forEach(dept => {
        if (deptFilter && deptFilter !== dept) return;

        const deptStudents = students.filter(s => s.department === dept);
        
        if (deptStudents.length === 0 && deptFilter) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-category-notice glassmorphism';
            emptyDiv.innerHTML = `<i class="fa-solid fa-folder-open"></i> <span>No students registered in ${dept} matching search.</span>`;
            container.appendChild(emptyDiv);
            return;
        }

        if (deptStudents.length === 0) return;

        totalRendered += deptStudents.length;

        const groupEl = document.createElement('div');
        groupEl.className = 'dept-group-panel glassmorphism mb-4';
        
        const icons = {
            "Computer Engineering": "fa-laptop-code",
            "Information Technology": "fa-network-wired",
            "Electrical Engineering": "fa-bolt",
            "Mechanical Engineering": "fa-gears"
        };
        const iconClass = icons[dept] || "fa-graduation-cap";

        groupEl.innerHTML = `
            <div class="dept-group-header">
                <div class="dept-group-title">
                    <i class="fa-solid ${iconClass}"></i> 
                    <span>${dept}</span>
                    <span class="dept-count-badge">${deptStudents.length}</span>
                </div>
                <button class="btn btn-outline btn-small btn-toggle-group"><i class="fa-solid fa-chevron-up"></i></button>
            </div>
            <div class="dept-group-body table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Student ID</th>
                            <th>Name</th>
                            <th>Course Plan</th>
                            <th>Email</th>
                            <th>Phone</th>
                            <th style="width: 150px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${deptStudents.map(s => `
                            <tr>
                                <td><strong>${s.student_id}</strong></td>
                                <td>${s.name}</td>
                                <td>${s.course}</td>
                                <td>${s.email}</td>
                                <td>${s.phone}</td>
                                <td>
                                    <div style="display: flex; gap: 6px;">
                                        <button class="btn btn-outline btn-small btn-view-details" data-id="${s.student_id}"><i class="fa-solid fa-eye"></i> View</button>
                                        <button class="btn btn-secondary btn-small btn-edit-student" data-id="${s.student_id}"><i class="fa-solid fa-pen-to-square"></i> Edit</button>
                                        ${STATE.user.role === 'admin' ? `<button class="btn btn-danger btn-small btn-delete-student" data-id="${s.student_id}"><i class="fa-solid fa-trash"></i></button>` : ''}
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        container.appendChild(groupEl);
    });

    if (totalRendered === 0) {
        container.innerHTML = '<div class="empty-category-notice glassmorphism"><i class="fa-solid fa-magnifying-glass"></i> No students matching your search criteria.</div>';
    }

    // Connect Collapsible accordions
    container.querySelectorAll('.btn-toggle-group').forEach(btn => {
        btn.onclick = () => {
            const panel = btn.closest('.dept-group-panel');
            const body = panel.querySelector('.dept-group-body');
            const icon = btn.querySelector('i');
            body.classList.toggle('hidden');
            if (body.classList.contains('hidden')) {
                icon.className = 'fa-solid fa-chevron-down';
            } else {
                icon.className = 'fa-solid fa-chevron-up';
            }
        };
    });

    // View buttons
    container.querySelectorAll('.btn-view-details').forEach(btn => {
        btn.onclick = () => openStudentDetailsModal(btn.getAttribute('data-id'));
    });

    // Edit buttons
    container.querySelectorAll('.btn-edit-student').forEach(btn => {
        btn.onclick = () => openEditStudentModal(btn.getAttribute('data-id'));
    });

    // Delete buttons
    container.querySelectorAll('.btn-delete-student').forEach(btn => {
        btn.onclick = () => deleteStudent(btn.getAttribute('data-id'));
    });
}

function updateActiveDeptCardUI() {
    const filterEl = document.getElementById('student-dept-filter');
    if (!filterEl) return;
    const activeDept = filterEl.value;
    document.querySelectorAll('.dept-cat-card').forEach(card => {
        if (card.getAttribute('data-dept') === activeDept) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
}

async function deleteStudent(studentId) {
    showConfirmModal("Confirm Student Deletion", `Are you sure you want to delete student ${studentId}?`, async () => {
        const res = await API.delete(`/api/students/${studentId}`);
        if (res && res.success) {
            showToast("Success", "Student records cleared.", "success");
            loadStudentsRegistry();
        } else {
            showToast("Error", res.message || "Failed to delete student.", "error");
        }
    });
}

async function openEditStudentModal(studentId) {
    const student = await API.get(`/api/students/${studentId}`);
    if (!student) {
        showToast("Error", "Could not fetch student details for editing", "error");
        return;
    }

    const modal = document.getElementById('edit-student-modal');
    if (!modal) return;

    document.getElementById('edit-stu-id').value = student.student_id;
    document.getElementById('edit-stu-name').value = student.name;
    document.getElementById('edit-stu-dob').value = student.dob;
    document.getElementById('edit-stu-gender').value = student.gender || 'Male';
    document.getElementById('edit-stu-email').value = student.email;
    document.getElementById('edit-stu-phone').value = student.phone;
    document.getElementById('edit-stu-dept').value = student.department;
    document.getElementById('edit-stu-course').value = student.course;
    document.getElementById('edit-stu-status').value = student.status || 'Active';

    modal.classList.remove('hidden');
}

// Detailed Student Profile Overlay
async function openStudentDetailsModal(studentId) {
    const student = await API.get(`/api/students/${studentId}`);
    if (!student) {
        showToast("Error", "Could not fetch details", "error");
        return;
    }

    const modal = document.getElementById('student-details-modal');
    if (!modal) return;

    // Populate Fields
    document.getElementById('det-student-name').textContent = student.name;
    document.getElementById('det-avatar-name').textContent = student.name;
    document.getElementById('det-avatar-role').textContent = student.course;
    
    // Fallback avatar
    const initials = student.name.split(' ').map(n=>n[0]).join('').toUpperCase();
    const fallback = document.getElementById('det-avatar-fallback');
    const avatarImg = document.getElementById('det-avatar-img');
    
    if (student.profile_pic) {
        avatarImg.src = student.profile_pic;
        avatarImg.classList.remove('hidden');
        fallback.classList.add('hidden');
    } else {
        avatarImg.classList.add('hidden');
        fallback.textContent = initials;
        fallback.classList.remove('hidden');
    }

    document.getElementById('det-id').textContent = student.student_id;
    document.getElementById('det-dept').textContent = student.department;
    document.getElementById('det-course').textContent = student.course;
    document.getElementById('det-dob').textContent = student.dob;
    document.getElementById('det-gender').textContent = student.gender;
    document.getElementById('det-email').textContent = student.email;
    document.getElementById('det-phone').textContent = student.phone;

    document.getElementById('det-bio').textContent = student.bio || "No biography added yet.";
    document.getElementById('det-skills').textContent = student.skills || "Not specified";
    document.getElementById('det-achievements').textContent = student.achievements || "None listed";
    document.getElementById('det-blood-group').textContent = student.blood_group || "Not specified";
    document.getElementById('det-emergency-contact').textContent = student.emergency_contact || "Not specified";
    document.getElementById('det-address').textContent = student.address || "No address provided";

    // Set up Student ID card badge preview
    const cardName = document.getElementById('id-card-name');
    const cardId = document.getElementById('id-card-id-val');
    const cardDept = document.getElementById('id-card-dept-val');
    const cardPhone = document.getElementById('id-card-phone-val');
    
    if (cardName) cardName.textContent = student.name.toUpperCase();
    if (cardId) cardId.textContent = student.student_id;
    if (cardDept) cardDept.textContent = student.department.substring(0, 15);
    if (cardPhone) cardPhone.textContent = student.phone;
    
    const idAvatarImg = document.getElementById('id-card-avatar-img');
    const idAvatarIcon = document.getElementById('id-card-avatar-icon');
    if (idAvatarImg && idAvatarIcon) {
        if (student.profile_pic) {
            idAvatarImg.src = student.profile_pic;
            idAvatarImg.classList.remove('hidden');
            idAvatarIcon.classList.add('hidden');
        } else {
            idAvatarImg.classList.add('hidden');
            idAvatarIcon.classList.remove('hidden');
        }
    }

    // Load grading marks lists & ML Dropout prediction gauge
    const performance = await API.get(`/api/students/${studentId}/performance`);
    if (performance && performance.success) {
        const gaugeEl = document.getElementById('ai-gauge-val');
        const riskEl = document.getElementById('ai-risk-badge');
        
        if (gaugeEl) gaugeEl.textContent = performance.ai_prediction.performance_score;
        if (riskEl) riskEl.textContent = performance.ai_prediction.status;
        
        const container = document.getElementById('ai-risk-status-container');
        if (container) {
            container.className = 'ai-stat-risk-card glassmorphism';
            if (performance.ai_prediction.status === 'High Risk') {
                container.classList.add('bg-red-glow');
            } else if (performance.ai_prediction.status === 'Moderate Risk') {
                container.classList.add('bg-yellow-glow');
            } else {
                container.classList.add('bg-green-glow');
            }
        }

        // Draw Confidence graphs
        const confBars = document.getElementById('ai-confidence-bars');
        if (confBars) {
            confBars.innerHTML = '';
            Object.entries(performance.ai_prediction.probabilities).forEach(([cls, pct]) => {
                const bar = document.createElement('div');
                bar.className = 'confidence-bar-row';
                bar.innerHTML = `
                    <span class="bar-label">${cls}</span>
                    <div class="bar-progress-track">
                        <div class="bar-progress-fill" style="width: ${pct * 100}%;"></div>
                    </div>
                    <span class="bar-percentage">${Math.round(pct * 100)}%</span>
                `;
                confBars.appendChild(bar);
            });
        }

        const recommendationText = document.getElementById('ai-recommendation-text');
        if (recommendationText) recommendationText.textContent = performance.ai_prediction.suggestion;

        // Populate table entries
        const gradesBody = document.getElementById('det-grades-table-body');
        if (gradesBody) {
            gradesBody.innerHTML = '';
            if (performance.marks_history.length === 0) {
                gradesBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No marks logs uploaded yet.</td></tr>';
            } else {
                performance.marks_history.forEach(g => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${g.exam_name}</strong></td>
                        <td>${g.subject}</td>
                        <td>${g.marks_obtained}</td>
                        <td>100</td>
                        <td><span class="grade-badge">${g.grade}</span></td>
                        <td>${g.date}</td>
                    `;
                    gradesBody.appendChild(tr);
                });
            }
        }
    }

    // Modal show
    modal.classList.remove('hidden');
    
    // Bind Tab switching
    document.querySelectorAll('[data-detail-tab]').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('[data-detail-tab]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const activePane = btn.getAttribute('data-detail-tab');
            const contents = ['profile-tab', 'ai-tab', 'grades-tab', 'id-card-tab'];
            contents.forEach(pane => {
                const paneEl = document.getElementById(pane);
                if (paneEl) {
                    if (pane === activePane) paneEl.classList.remove('hidden');
                    else paneEl.classList.add('hidden');
                }
            });
        };
    });

    // Wire close buttons
    const closeBtn = document.getElementById('btn-close-details-modal');
    const closeFooter = document.getElementById('btn-close-details-modal-footer');
    if (closeBtn) closeBtn.onclick = () => modal.classList.add('hidden');
    if (closeFooter) closeFooter.onclick = () => modal.classList.add('hidden');

    // Wire profile picture change triggers
    const changeAvatarTrigger = document.getElementById('btn-change-avatar');
    const fileInput = document.getElementById('profile-pic-input');
    
    if (changeAvatarTrigger && fileInput) {
        changeAvatarTrigger.onclick = () => {
            // Restrictions: student can only change their own photo
            if (STATE.user.role === 'student' && STATE.user.reference_id !== studentId) return;
            fileInput.click();
        };

        fileInput.onchange = async () => {
            if (fileInput.files.length === 0) return;
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('profile_pic', file);

            try {
                const res = await fetch(`/api/students/${studentId}/upload-profile-pic`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Success", "Profile photo updated successfully.", "success");
                    // Refresh overlay modal
                    openStudentDetailsModal(studentId);
                } else {
                    showToast("Upload Failed", data.message || "Failed to save photo.", "error");
                }
            } catch (err) {
                console.error(err);
                showToast("Connection Error", "Could not send picture file to server.", "error");
            }
        };
    }

    // Profile updates form binders
    const editBtn = document.getElementById('btn-edit-extra-info');
    const cancelBtn = document.getElementById('btn-cancel-extra-info');
    const displayPanel = document.getElementById('extra-info-display');
    const formPanel = document.getElementById('extra-info-form');
    
    if (editBtn && cancelBtn && displayPanel && formPanel) {
        editBtn.onclick = () => {
            document.getElementById('edit-bio').value = document.getElementById('det-bio').textContent.replace('No bio added yet.', '');
            document.getElementById('edit-skills').value = document.getElementById('det-skills').textContent.replace('Not specified', '');
            document.getElementById('edit-achievements').value = document.getElementById('det-achievements').textContent.replace('None listed', '');
            
            // Blood group and Emergency contact checks
            const b = document.getElementById('det-blood-group').textContent;
            const ec = document.getElementById('det-emergency-contact').textContent;
            document.getElementById('edit-blood-group').value = b === 'Not specified' ? '' : b;
            document.getElementById('edit-emergency-contact').value = ec === 'Not specified' ? '' : ec;
            document.getElementById('edit-address').value = document.getElementById('det-address').textContent.replace('No address provided', '');

            displayPanel.classList.add('hidden');
            formPanel.classList.remove('hidden');
        };

        cancelBtn.onclick = () => {
            formPanel.classList.add('hidden');
            displayPanel.classList.remove('hidden');
        };

        formPanel.onsubmit = async (e) => {
            e.preventDefault();
            const payload = {
                bio: document.getElementById('edit-bio').value,
                skills: document.getElementById('edit-skills').value,
                achievements: document.getElementById('edit-achievements').value,
                blood_group: document.getElementById('edit-blood-group').value,
                emergency_contact: document.getElementById('edit-emergency-contact').value,
                address: document.getElementById('edit-address').value
            };

            const res = await API.put(`/api/students/${studentId}`, payload);
            if (res && res.success) {
                showToast("Profile Updated", "Personal information saved successfully.", "success");
                openStudentDetailsModal(studentId);
                cancelBtn.click();
            } else {
                showToast("Error", res.message || "Failed to update profile details.", "error");
            }
        };
    }
}

// ─── Department Card Filter ───────────────────────────────────────────────────
function filterByDeptCard(dept) {
    if (STATE.user && STATE.user.role === 'teacher' && STATE.user.department) {
        return;
    }
    const filterEl = document.getElementById('student-dept-filter');
    if (filterEl) {
        filterEl.value = dept === 'All' ? '' : dept;
    }

    // Update active state on cards
    document.querySelectorAll('.dept-card').forEach(card => {
        const cardDept = card.getAttribute('data-dept-card');
        if (cardDept === dept) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });

    loadStudentsRegistry();
}
// ─────────────────────────────────────────────────────────────────────────────
