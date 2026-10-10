// Faculty Management Frontend Module

let currentFacultyList = [];
let allSubjectsList = [];

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    // Add Event Listeners
    const btnAddModal = document.getElementById('btn-open-add-faculty-modal');
    if (btnAddModal) {
        btnAddModal.addEventListener('click', openAddFacultyModal);
    }

    const btnCloseAdd = document.getElementById('btn-close-faculty-modal');
    const btnCancelAdd = document.getElementById('btn-cancel-faculty-modal');
    if (btnCloseAdd) btnCloseAdd.addEventListener('click', closeAddFacultyModal);
    if (btnCancelAdd) btnCancelAdd.addEventListener('click', closeAddFacultyModal);

    const btnCloseEdit = document.getElementById('btn-close-edit-faculty-modal');
    const btnCancelEdit = document.getElementById('btn-cancel-edit-faculty-modal');
    if (btnCloseEdit) btnCloseEdit.addEventListener('click', closeEditFacultyModal);
    if (btnCancelEdit) btnCancelEdit.addEventListener('click', closeEditFacultyModal);

    const btnCloseProfile = document.getElementById('btn-close-faculty-profile-modal');
    if (btnCloseProfile) btnCloseProfile.addEventListener('click', closeFacultyProfileModal);

    const btnCloseAssign = document.getElementById('btn-close-assign-subject-modal');
    const btnCancelAssign = document.getElementById('btn-cancel-assign-subject-modal');
    if (btnCloseAssign) btnCloseAssign.addEventListener('click', closeAssignSubjectModal);
    if (btnCancelAssign) btnCancelAssign.addEventListener('click', closeAssignSubjectModal);

    // Form Submissions
    const addForm = document.getElementById('add-faculty-form');
    if (addForm) {
        addForm.addEventListener('submit', handleAddFacultySubmit);
    }

    const editForm = document.getElementById('edit-faculty-form');
    if (editForm) {
        editForm.addEventListener('submit', handleEditFacultySubmit);
    }

    const assignForm = document.getElementById('assign-subject-form');
    if (assignForm) {
        assignForm.addEventListener('submit', handleAssignSubjectSubmit);
    }

    // Search and Filter Listeners
    const searchInput = document.getElementById('faculty-search-input');
    const deptFilter = document.getElementById('faculty-dept-filter');

    if (searchInput) {
        let debounceTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                loadFacultyMembers();
            }, 300);
        });
    }

    if (deptFilter) {
        deptFilter.addEventListener('change', () => {
            loadFacultyMembers();
        });
    }

    // Department category cards click filters
    document.querySelectorAll('.dept-cat-card').forEach(card => {
        card.addEventListener('click', () => {
            const dept = card.getAttribute('data-dept');
            if (deptFilter) {
                deptFilter.value = deptFilter.value === dept ? '' : dept;
                loadFacultyMembers();
            }
        });
    });
});

/**
 * Fetch and load faculty members list
 */
async function loadFacultyMembers() {
    const searchInput = document.getElementById('faculty-search-input');
    const deptFilter = document.getElementById('faculty-dept-filter');
    const container = document.getElementById('faculty-list-container');

    const search = searchInput ? searchInput.value.trim() : '';
    const dept = deptFilter ? deptFilter.value.trim() : '';

    try {
        let queryParams = [];
        if (search) queryParams.push(`search=${encodeURIComponent(search)}`);
        if (dept) queryParams.push(`department=${encodeURIComponent(dept)}`);
        const queryString = queryParams.length ? `?${queryParams.join('&')}` : '';

        const response = await apiFetch(`/api/faculty${queryString}`);
        
        if (response && response.success) {
            currentFacultyList = response.faculty || [];
            renderFacultyList(currentFacultyList);
            updateDepartmentCounts(currentFacultyList);
        } else {
            if (container) {
                container.innerHTML = `<div class="empty-category-notice glassmorphism" style="padding: 2rem; text-align: center; color: var(--danger);">Failed to load faculty members.</div>`;
            }
        }
    } catch (err) {
        console.error("Error loading faculty members:", err);
        if (container) {
            container.innerHTML = `<div class="empty-category-notice glassmorphism" style="padding: 2rem; text-align: center; color: var(--danger);">An error occurred while loading faculty members.</div>`;
        }
    }
}

/**
 * Update Department Faculty Counter Badges
 */
function updateDepartmentCounts(facultyList) {
    const counts = {
        'Computer Engineering': 0,
        'Information Technology': 0,
        'Electrical Engineering': 0,
        'Mechanical Engineering': 0
    };

    facultyList.forEach(fac => {
        if (counts[fac.department] !== undefined) {
            counts[fac.department]++;
        }
    });

    const cComp = document.getElementById('count-dept-computer');
    const cIT = document.getElementById('count-dept-it');
    const cElec = document.getElementById('count-dept-electrical');
    const cMech = document.getElementById('count-dept-mechanical');

    if (cComp) cComp.textContent = `${counts['Computer Engineering']} Faculty`;
    if (cIT) cIT.textContent = `${counts['Information Technology']} Faculty`;
    if (cElec) cElec.textContent = `${counts['Electrical Engineering']} Faculty`;
    if (cMech) cMech.textContent = `${counts['Mechanical Engineering']} Faculty`;
}

/**
 * Render Faculty Data Table
 */
function renderFacultyList(facultyList) {
    const container = document.getElementById('faculty-list-container');
    if (!container) return;

    if (!facultyList || facultyList.length === 0) {
        container.innerHTML = `
            <div class="empty-category-notice glassmorphism" style="padding: 3rem; text-align: center; color: var(--text-muted);">
                <i class="fa-solid fa-user-slash" style="font-size: 2.5rem; color: var(--accent-gold); margin-bottom: 1rem;"></i>
                <h3>No Faculty Members Found</h3>
                <p>No faculty records match the selected filter or search criteria.</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="table-container glassmorphism" style="width: 100%; overflow-x: auto;">
            <table class="data-table" style="width: 100%;">
                <thead>
                    <tr>
                        <th style="white-space: nowrap;">Faculty Code / ID</th>
                        <th style="white-space: nowrap;">Name</th>
                        <th style="white-space: nowrap;">Department</th>
                        <th style="white-space: nowrap;">Designation</th>
                        <th style="white-space: nowrap;">Email & Phone</th>
                        <th style="text-align: right; white-space: nowrap;">Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    const isAdmin = STATE && STATE.user && STATE.user.role === 'admin';

    facultyList.forEach(fac => {
        const facId = fac.reference_id || `USER#${fac.user_id}`;
        const designation = fac.designation || 'Assistant Professor';
        const dept = fac.department || 'N/A';
        const phone = fac.phone || 'N/A';
        
        let actionButtons = `
            <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem;" onclick="viewFacultyProfile('${fac.user_id}')" title="View Profile">
                <i class="fa-solid fa-address-card"></i> Profile
            </button>
        `;

        if (isAdmin) {
            actionButtons += `
                <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem; color: var(--accent-gold); border-color: var(--accent-gold);" onclick="openAssignSubjectModal('${fac.reference_id || fac.user_id}', '${fac.name}')" title="Assign Subject">
                    <i class="fa-solid fa-book-bookmark"></i> Assign
                </button>
                <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem;" onclick="openEditFacultyModal('${fac.user_id}')" title="Edit Faculty">
                    <i class="fa-solid fa-pen-to-square"></i>
                </button>
                <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem; color: var(--danger); border-color: var(--danger);" onclick="deleteFacultyMember('${fac.user_id}', '${fac.name}')" title="Delete Faculty">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            `;
        }

        html += `
            <tr>
                <td><strong style="color: var(--accent-blue);">${facId}</strong></td>
                <td>
                    <div style="font-weight: 600;">${fac.name || fac.username}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">@${fac.username}</div>
                </td>
                <td><span class="badge badge-dept" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 4px 10px; border-radius: 6px; font-weight: 600;">${dept}</span></td>
                <td><span style="font-size: 0.85rem;">${designation}</span></td>
                <td>
                    <div style="font-size: 0.85rem;"><i class="fa-solid fa-envelope" style="color: var(--text-muted); font-size: 0.75rem;"></i> ${fac.email}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);"><i class="fa-solid fa-phone" style="font-size: 0.7rem;"></i> ${phone}</div>
                </td>
                <td style="text-align: right;">
                    <div style="display: flex; justify-content: flex-end; gap: 6px;">
                        ${actionButtons}
                    </div>
                </td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * Add Faculty Modal Handler
 */
function openAddFacultyModal() {
    const modal = document.getElementById('add-faculty-modal');
    const form = document.getElementById('add-faculty-form');
    if (form) form.reset();
    if (modal) modal.classList.remove('hidden');
}

function closeAddFacultyModal() {
    const modal = document.getElementById('add-faculty-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleAddFacultySubmit(e) {
    e.preventDefault();
    
    const payload = {
        username: document.getElementById('fac-username').value.trim(),
        password: document.getElementById('fac-password').value.trim(),
        name: document.getElementById('fac-name').value.trim(),
        email: document.getElementById('fac-email').value.trim(),
        phone: document.getElementById('fac-phone').value.trim(),
        department: document.getElementById('fac-dept').value.trim(),
        designation: document.getElementById('fac-designation').value.trim(),
        qualification: document.getElementById('fac-qualification').value.trim(),
        reference_id: document.getElementById('fac-ref-id').value.trim()
    };

    if (!payload.username || !payload.password || !payload.name || !payload.email || !payload.department) {
        showToast("Validation Error", "Please fill in all mandatory fields.", "error");
        return;
    }

    try {
        const res = await apiFetch('/api/faculty', 'POST', payload);
        if (res && res.success) {
            showToast("Faculty Added", res.message || "Faculty added successfully!", "success");
            closeAddFacultyModal();
            loadFacultyMembers();
        } else {
            showToast("Error", res.message || "Failed to add faculty member.", "error");
        }
    } catch (err) {
        console.error("Error adding faculty:", err);
        showToast("Error", "An error occurred while adding faculty.", "error");
    }
}

/**
 * Edit Faculty Modal Handler
 */
function openEditFacultyModal(userId) {
    const fac = currentFacultyList.find(f => f.user_id == userId);
    if (!fac) return;

    document.getElementById('edit-fac-user-id').value = fac.user_id;
    document.getElementById('edit-fac-username').value = fac.username;
    document.getElementById('edit-fac-name').value = fac.name || '';
    document.getElementById('edit-fac-email').value = fac.email || '';
    document.getElementById('edit-fac-phone').value = fac.phone || '';
    document.getElementById('edit-fac-dept').value = fac.department || 'Computer Engineering';
    document.getElementById('edit-fac-designation').value = fac.designation || 'Assistant Professor';
    document.getElementById('edit-fac-qualification').value = fac.qualification || 'M.Tech / Ph.D';

    const modal = document.getElementById('edit-faculty-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeEditFacultyModal() {
    const modal = document.getElementById('edit-faculty-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleEditFacultySubmit(e) {
    e.preventDefault();
    
    const userId = document.getElementById('edit-fac-user-id').value;
    const payload = {
        name: document.getElementById('edit-fac-name').value.trim(),
        email: document.getElementById('edit-fac-email').value.trim(),
        phone: document.getElementById('edit-fac-phone').value.trim(),
        department: document.getElementById('edit-fac-dept').value.trim(),
        designation: document.getElementById('edit-fac-designation').value.trim(),
        qualification: document.getElementById('edit-fac-qualification').value.trim()
    };

    try {
        const res = await apiFetch(`/api/faculty/${userId}`, 'PUT', payload);
        if (res && res.success) {
            showToast("Faculty Updated", res.message || "Faculty updated successfully!", "success");
            closeEditFacultyModal();
            loadFacultyMembers();
        } else {
            showToast("Error", res.message || "Failed to update faculty member.", "error");
        }
    } catch (err) {
        console.error("Error updating faculty:", err);
        showToast("Error", "An error occurred while updating faculty.", "error");
    }
}

/**
 * View Faculty Profile Modal
 */
async function viewFacultyProfile(userIdOrRef) {
    try {
        const res = await apiFetch(`/api/faculty/${userIdOrRef}`);
        if (!res || !res.success) {
            showToast("Error", res.message || "Could not load faculty details.", "error");
            return;
        }

        const fac = res.faculty;
        document.getElementById('det-fac-name').textContent = fac.name || fac.username;
        document.getElementById('det-fac-id').textContent = fac.reference_id || `USER#${fac.user_id}`;
        document.getElementById('det-fac-dept').textContent = fac.department || 'N/A';
        document.getElementById('det-fac-designation').textContent = fac.designation || 'Assistant Professor';
        document.getElementById('det-fac-qualification').textContent = fac.qualification || 'N/A';
        document.getElementById('det-fac-email').textContent = fac.email || 'N/A';
        document.getElementById('det-fac-phone').textContent = fac.phone || 'N/A';
        document.getElementById('det-fac-username').textContent = `@${fac.username}`;
        document.getElementById('det-fac-joining').textContent = fac.joining_date || 'N/A';

        // Render assigned subjects
        const subjectsContainer = document.getElementById('det-fac-subjects-list');
        if (subjectsContainer) {
            if (fac.assigned_subjects && fac.assigned_subjects.length > 0) {
                let html = '<ul style="list-style: none; padding: 0; display: flex; flex-direction: column; gap: 8px;">';
                fac.assigned_subjects.forEach(sub => {
                    html += `
                        <li style="background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border); padding: 10px 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: var(--accent-gold);">${sub.subject_code}</strong> - <span>${sub.name || sub.subject_name}</span>
                            </div>
                            <span style="font-size: 0.8rem; color: var(--text-muted);">${sub.department || ''}</span>
                        </li>
                    `;
                });
                html += '</ul>';
                subjectsContainer.innerHTML = html;
            } else {
                subjectsContainer.innerHTML = `<p style="color: var(--text-muted); font-style: italic;">No subjects assigned yet.</p>`;
            }
        }

        const modal = document.getElementById('faculty-profile-modal');
        if (modal) modal.classList.remove('hidden');
    } catch (err) {
        console.error("Error viewing faculty profile:", err);
        showToast("Error", "An error occurred while fetching faculty details.", "error");
    }
}

function closeFacultyProfileModal() {
    const modal = document.getElementById('faculty-profile-modal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Assign Subject Modal
 */
async function openAssignSubjectModal(facultyId, facultyName) {
    document.getElementById('assign-fac-id').value = facultyId;
    document.getElementById('assign-fac-name').textContent = facultyName;

    const select = document.getElementById('assign-subject-select');
    if (select) {
        select.innerHTML = '<option value="">Loading available subjects...</option>';
    }

    try {
        const defaultSubjects = [
            { code: "CS101", name: "Data Structures & Algorithms" },
            { code: "CS102", name: "Database Management Systems" },
            { code: "IT201", name: "Web Application Architecture" },
            { code: "IT202", name: "Computer Networks & Security" },
            { code: "EE301", name: "Electrical Power Systems" },
            { code: "ME401", name: "Thermodynamics & Heat Transfer" }
        ];

        if (select) {
            let options = '<option value="">-- Select Subject --</option>';
            defaultSubjects.forEach(s => {
                options += `<option value="${s.code}">${s.code} - ${s.name}</option>`;
            });
            select.innerHTML = options;
        }

        const modal = document.getElementById('assign-subject-modal');
        if (modal) modal.classList.remove('hidden');
    } catch (err) {
        console.error("Error setting up assign subject modal:", err);
    }
}

function closeAssignSubjectModal() {
    const modal = document.getElementById('assign-subject-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleAssignSubjectSubmit(e) {
    e.preventDefault();

    const facultyId = document.getElementById('assign-fac-id').value;
    const subjectId = document.getElementById('assign-subject-select').value;

    if (!subjectId) {
        showToast("Selection Error", "Please select a subject to assign.", "error");
        return;
    }

    try {
        const res = await apiFetch(`/api/faculty/${encodeURIComponent(facultyId)}/assign_subject`, 'POST', { subject_id: subjectId });
        if (res && res.success) {
            showToast("Subject Assigned", res.message || "Subject assigned successfully!", "success");
            closeAssignSubjectModal();
            loadFacultyMembers();
        } else {
            showToast("Error", res.message || "Failed to assign subject.", "error");
        }
    } catch (err) {
        console.error("Error assigning subject:", err);
        showToast("Error", "An error occurred while assigning subject.", "error");
    }
}

/**
 * Delete Faculty Member
 */
async function deleteFacultyMember(userId, name) {
    showConfirmModal("Confirm Faculty Deletion", `Are you sure you want to delete faculty member '${name}'?\nThis will remove their account and login permissions.`, async () => {
        try {
            const res = await apiFetch(`/api/faculty/${userId}`, 'DELETE');
            if (res && res.success) {
                showToast("Faculty Deleted", res.message || "Faculty member deleted successfully.", "success");
                loadFacultyMembers();
            } else {
                showToast("Error", res.message || "Failed to delete faculty member.", "error");
            }
        } catch (err) {
            console.error("Error deleting faculty:", err);
            showToast("Error", "An error occurred while deleting faculty member.", "error");
        }
    });
}
