// Subjects and Courses Management Frontend Script

let currentSubjectsList = [];
let facultyOptionsList = [];
let courseOptionsList = [];

document.addEventListener("DOMContentLoaded", () => {
    // Buttons for modal triggers
    const btnAddSub = document.getElementById('btn-open-add-subject-modal');
    if (btnAddSub) btnAddSub.addEventListener('click', openAddSubjectModal);

    const btnAddCourse = document.getElementById('btn-open-add-course-modal');
    if (btnAddCourse) btnAddCourse.addEventListener('click', openAddCourseModal);

    // Close buttons
    const btnCloseAddSub = document.getElementById('btn-close-subject-modal');
    const btnCancelAddSub = document.getElementById('btn-cancel-subject-modal');
    if (btnCloseAddSub) btnCloseAddSub.addEventListener('click', closeAddSubjectModal);
    if (btnCancelAddSub) btnCancelAddSub.addEventListener('click', closeAddSubjectModal);

    const btnCloseEditSub = document.getElementById('btn-close-edit-subject-modal');
    const btnCancelEditSub = document.getElementById('btn-cancel-edit-subject-modal');
    if (btnCloseEditSub) btnCloseEditSub.addEventListener('click', closeEditSubjectModal);
    if (btnCancelEditSub) btnCancelEditSub.addEventListener('click', closeEditSubjectModal);

    const btnCloseAssign = document.getElementById('btn-close-assign-fac-modal');
    const btnCancelAssign = document.getElementById('btn-cancel-assign-fac-modal');
    if (btnCloseAssign) btnCloseAssign.addEventListener('click', closeAssignFacultyModal);
    if (btnCancelAssign) btnCancelAssign.addEventListener('click', closeAssignFacultyModal);

    const btnCloseCourse = document.getElementById('btn-close-course-modal');
    const btnCancelCourse = document.getElementById('btn-cancel-course-modal');
    if (btnCloseCourse) btnCloseCourse.addEventListener('click', closeAddCourseModal);
    if (btnCancelCourse) btnCancelCourse.addEventListener('click', closeAddCourseModal);

    // Forms
    const addSubForm = document.getElementById('add-subject-form');
    if (addSubForm) addSubForm.addEventListener('submit', handleAddSubjectSubmit);

    const editSubForm = document.getElementById('edit-subject-form');
    if (editSubForm) editSubForm.addEventListener('submit', handleEditSubjectSubmit);

    const assignFacForm = document.getElementById('assign-faculty-form');
    if (assignFacForm) assignFacForm.addEventListener('submit', handleAssignFacultySubmit);

    const addCourseForm = document.getElementById('add-course-form');
    if (addCourseForm) addCourseForm.addEventListener('submit', handleAddCourseSubmit);

    // Search and Filters
    const searchInput = document.getElementById('subject-search-input');
    const deptFilter = document.getElementById('subject-dept-filter');
    const semFilter = document.getElementById('subject-sem-filter');

    if (searchInput) {
        let debounceTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                loadSubjectsList();
            }, 300);
        });
    }

    if (deptFilter) deptFilter.addEventListener('change', loadSubjectsList);
    if (semFilter) semFilter.addEventListener('change', loadSubjectsList);

    // Initial load options and subjects
    loadAuxiliaryOptions();
});

async function loadAuxiliaryOptions() {
    try {
        const facRes = await apiFetch('/api/faculty');
        if (facRes && facRes.success) {
            facultyOptionsList = facRes.faculty || [];
        }

        const crsRes = await apiFetch('/api/courses');
        if (crsRes && crsRes.success) {
            courseOptionsList = crsRes.courses || [];
        }
    } catch (err) {
        console.error("Error loading auxiliary options:", err);
    }
}

/**
 * Load & Render Subjects List
 */
async function loadSubjectsList() {
    const searchInput = document.getElementById('subject-search-input');
    const deptFilter = document.getElementById('subject-dept-filter');
    const semFilter = document.getElementById('subject-sem-filter');
    const container = document.getElementById('subjects-list-container');

    const search = searchInput ? searchInput.value.trim() : '';
    const dept = deptFilter ? deptFilter.value.trim() : '';
    const sem = semFilter ? semFilter.value.trim() : '';

    try {
        let params = [];
        if (search) params.push(`search=${encodeURIComponent(search)}`);
        if (dept) params.push(`department=${encodeURIComponent(dept)}`);
        if (sem) params.push(`semester=${encodeURIComponent(sem)}`);
        const qStr = params.length ? `?${params.join('&')}` : '';

        const res = await apiFetch(`/api/subjects${qStr}`);
        if (res && res.success) {
            currentSubjectsList = res.subjects || [];
            renderSubjectsList(currentSubjectsList);
            updateSubjectCategoryCounts(currentSubjectsList);
        } else {
            if (container) {
                container.innerHTML = `<div class="empty-category-notice glassmorphism" style="padding: 2rem; text-align: center; color: var(--danger);">Failed to load subjects directory.</div>`;
            }
        }
    } catch (err) {
        console.error("Error loading subjects:", err);
        if (container) {
            container.innerHTML = `<div class="empty-category-notice glassmorphism" style="padding: 2rem; text-align: center; color: var(--danger);">Error loading subjects list.</div>`;
        }
    }
}

function updateSubjectCategoryCounts(subjects) {
    const counts = {
        'Computer Engineering': 0,
        'Information Technology': 0,
        'Electrical Engineering': 0,
        'Mechanical Engineering': 0
    };

    subjects.forEach(sub => {
        if (counts[sub.department] !== undefined) {
            counts[sub.department]++;
        }
    });

    const cComp = document.getElementById('count-sub-computer');
    const cIT = document.getElementById('count-sub-it');
    const cElec = document.getElementById('count-sub-electrical');
    const cMech = document.getElementById('count-sub-mechanical');

    if (cComp) cComp.textContent = `${counts['Computer Engineering']} Subjects`;
    if (cIT) cIT.textContent = `${counts['Information Technology']} Subjects`;
    if (cElec) cElec.textContent = `${counts['Electrical Engineering']} Subjects`;
    if (cMech) cMech.textContent = `${counts['Mechanical Engineering']} Subjects`;
}

function renderSubjectsList(subjects) {
    const container = document.getElementById('subjects-list-container');
    if (!container) return;

    if (!subjects || subjects.length === 0) {
        container.innerHTML = `
            <div class="empty-category-notice glassmorphism" style="padding: 3rem; text-align: center; color: var(--text-muted);">
                <i class="fa-solid fa-book-bookmark" style="font-size: 2.5rem; color: var(--accent-gold); margin-bottom: 1rem;"></i>
                <h3>No Subjects Found</h3>
                <p>No subjects match the specified search or filter criteria.</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="table-container glassmorphism" style="overflow-x: auto;">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Subject Code</th>
                        <th>Subject Title</th>
                        <th>Department</th>
                        <th>Course / Branch</th>
                        <th>Semester</th>
                        <th>Credits</th>
                        <th>Assigned Faculty</th>
                        <th style="text-align: right;">Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    const isAdmin = STATE && STATE.user && STATE.user.role === 'admin';

    subjects.forEach(sub => {
        const facName = sub.faculty_name || 'Unassigned';

        let actionCell = `
            <span class="badge badge-green" style="font-size: 0.75rem;"><i class="fa-solid fa-circle-check"></i> Active</span>
        `;

        if (isAdmin) {
            actionCell = `
                <div style="display: flex; justify-content: flex-end; gap: 6px;">
                    <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem; color: var(--accent-gold); border-color: var(--accent-gold);" onclick="openAssignFacultyModal('${sub.subject_id || sub.subject_code}', '${sub.subject_name || sub.name}')" title="Assign Faculty">
                        <i class="fa-solid fa-user-check"></i> Assign
                    </button>
                    <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem;" onclick="openEditSubjectModal('${sub.subject_id || sub.subject_code}')" title="Edit Subject">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                    <button class="btn btn-outline" style="padding: 4px 8px; font-size: 0.8rem; color: var(--danger); border-color: var(--danger);" onclick="deleteSubject('${sub.subject_id || sub.subject_code}', '${sub.subject_name || sub.name}')" title="Delete Subject">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            `;
        }

        html += `
            <tr>
                <td><strong style="color: var(--accent-gold);">${sub.subject_code}</strong></td>
                <td><strong style="color: var(--text-main);">${sub.subject_name || sub.name}</strong></td>
                <td><span class="badge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 4px 10px; border-radius: 6px; font-weight: 600;">${sub.department}</span></td>
                <td><span style="font-size: 0.85rem; color: var(--text-muted);">${sub.course_code || 'General'}</span></td>
                <td><span class="badge" style="background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); font-weight: 600;">Sem ${sub.semester}</span></td>
                <td><strong>${sub.credits} Credits</strong></td>
                <td>
                    <div style="font-size: 0.85rem; display: flex; align-items: center; gap: 6px;">
                        <i class="fa-solid fa-chalkboard-user" style="color: ${sub.faculty_name ? 'var(--success)' : 'var(--text-muted)'};"></i>
                        <span>${facName}</span>
                    </div>
                </td>
                <td style="text-align: right;">
                    ${actionCell}
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
 * Add Subject Modal
 */
function openAddSubjectModal() {
    const form = document.getElementById('add-subject-form');
    if (form) form.reset();

    // Populate faculty dropdown
    const facSelect = document.getElementById('sub-faculty');
    if (facSelect) {
        let opts = '<option value="">-- No Faculty Assigned --</option>';
        facultyOptionsList.forEach(f => {
            opts += `<option value="${f.reference_id || f.user_id}">${f.name} (${f.department})</option>`;
        });
        facSelect.innerHTML = opts;
    }

    // Populate course dropdown
    const crsSelect = document.getElementById('sub-course');
    if (crsSelect) {
        let opts = '<option value="">-- Select Course Plan --</option>';
        courseOptionsList.forEach(c => {
            opts += `<option value="${c.course_code}">${c.course_code} - ${c.course_name}</option>`;
        });
        crsSelect.innerHTML = opts;
    }

    const modal = document.getElementById('add-subject-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeAddSubjectModal() {
    const modal = document.getElementById('add-subject-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleAddSubjectSubmit(e) {
    e.preventDefault();

    const payload = {
        subject_code: document.getElementById('sub-code').value.trim(),
        subject_name: document.getElementById('sub-name').value.trim(),
        department: document.getElementById('sub-dept').value.trim(),
        course_code: document.getElementById('sub-course').value.trim(),
        semester: parseInt(document.getElementById('sub-sem').value),
        credits: parseInt(document.getElementById('sub-credits').value),
        faculty_id: document.getElementById('sub-faculty').value || None
    };

    if (!payload.subject_code || !payload.subject_name || !payload.department) {
        showToast("Validation Error", "Please fill in all mandatory fields.", "error");
        return;
    }

    try {
        const res = await apiFetch('/api/subjects', 'POST', payload);
        if (res && res.success) {
            showToast("Subject Added", res.message || "Subject added successfully!", "success");
            closeAddSubjectModal();
            loadSubjectsList();
        } else {
            showToast("Error", res.message || "Failed to add subject.", "error");
        }
    } catch (err) {
        console.error("Error adding subject:", err);
        showToast("Error", "An error occurred while adding subject.", "error");
    }
}

/**
 * Edit Subject Modal
 */
function openEditSubjectModal(subId) {
    const sub = currentSubjectsList.find(s => s.subject_id == subId || s.subject_code == subId);
    if (!sub) return;

    document.getElementById('edit-sub-id').value = sub.subject_id || sub.subject_code;
    document.getElementById('edit-sub-code').value = sub.subject_code;
    document.getElementById('edit-sub-name').value = sub.subject_name || sub.name;
    document.getElementById('edit-sub-dept').value = sub.department;
    document.getElementById('edit-sub-course').value = sub.course_code || '';
    document.getElementById('edit-sub-sem').value = sub.semester || 1;
    document.getElementById('edit-sub-credits').value = sub.credits || 4;

    const facSelect = document.getElementById('edit-sub-faculty');
    if (facSelect) {
        let opts = '<option value="">-- No Faculty Assigned --</option>';
        facultyOptionsList.forEach(f => {
            const fid = f.reference_id || f.user_id;
            const selected = (sub.faculty_id == fid || sub.faculty_name == f.name) ? 'selected' : '';
            opts += `<option value="${fid}" ${selected}>${f.name} (${f.department})</option>`;
        });
        facSelect.innerHTML = opts;
    }

    const modal = document.getElementById('edit-subject-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeEditSubjectModal() {
    const modal = document.getElementById('edit-subject-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleEditSubjectSubmit(e) {
    e.preventDefault();

    const subId = document.getElementById('edit-sub-id').value;
    const payload = {
        subject_code: document.getElementById('edit-sub-code').value.trim(),
        subject_name: document.getElementById('edit-sub-name').value.trim(),
        department: document.getElementById('edit-sub-dept').value.trim(),
        course_code: document.getElementById('edit-sub-course').value.trim(),
        semester: parseInt(document.getElementById('edit-sub-sem').value),
        credits: parseInt(document.getElementById('edit-sub-credits').value),
        faculty_id: document.getElementById('edit-sub-faculty').value || null
    };

    try {
        const res = await apiFetch(`/api/subjects/${subId}`, 'PUT', payload);
        if (res && res.success) {
            showToast("Subject Updated", res.message || "Subject updated successfully!", "success");
            closeEditSubjectModal();
            loadSubjectsList();
        } else {
            showToast("Error", res.message || "Failed to update subject.", "error");
        }
    } catch (err) {
        console.error("Error updating subject:", err);
        showToast("Error", "An error occurred while updating subject.", "error");
    }
}

/**
 * Assign Faculty Modal
 */
function openAssignFacultyModal(subId, subName) {
    document.getElementById('assign-sub-id').value = subId;
    document.getElementById('assign-sub-title').textContent = subName;

    const facSelect = document.getElementById('assign-fac-select');
    if (facSelect) {
        let opts = '<option value="">-- Select Faculty Member --</option>';
        facultyOptionsList.forEach(f => {
            opts += `<option value="${f.reference_id || f.user_id}">${f.name} - ${f.department} (${f.designation || 'Faculty'})</option>`;
        });
        facSelect.innerHTML = opts;
    }

    const modal = document.getElementById('assign-faculty-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeAssignFacultyModal() {
    const modal = document.getElementById('assign-faculty-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleAssignFacultySubmit(e) {
    e.preventDefault();

    const subId = document.getElementById('assign-sub-id').value;
    const facId = document.getElementById('assign-fac-select').value;

    if (!facId) {
        showToast("Selection Error", "Please select a faculty member.", "error");
        return;
    }

    try {
        const res = await apiFetch(`/api/subjects/${subId}/assign_faculty`, 'POST', { faculty_id: facId });
        if (res && res.success) {
            showToast("Faculty Assigned", res.message || "Faculty assigned to subject successfully!", "success");
            closeAssignFacultyModal();
            loadSubjectsList();
        } else {
            showToast("Error", res.message || "Failed to assign faculty.", "error");
        }
    } catch (err) {
        console.error("Error assigning faculty:", err);
        showToast("Error", "An error occurred while assigning faculty.", "error");
    }
}

/**
 * Delete Subject
 */
async function deleteSubject(subId, subName) {
    showConfirmModal("Confirm Subject Deletion", `Are you sure you want to delete subject '${subName}'?\nThis will remove the subject definition.`, async () => {
        try {
            const res = await apiFetch(`/api/subjects/${subId}`, 'DELETE');
            if (res && res.success) {
                showToast("Subject Deleted", res.message || "Subject deleted successfully.", "success");
                loadSubjectsList();
            } else {
                showToast("Error", res.message || "Failed to delete subject.", "error");
            }
        } catch (err) {
            console.error("Error deleting subject:", err);
            showToast("Error", "An error occurred while deleting subject.", "error");
        }
    });
}

/**
 * Course Modal Handlers
 */
function openAddCourseModal() {
    const modal = document.getElementById('add-course-modal');
    const form = document.getElementById('add-course-form');
    if (form) form.reset();
    if (modal) modal.classList.remove('hidden');
}

function closeAddCourseModal() {
    const modal = document.getElementById('add-course-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleAddCourseSubmit(e) {
    e.preventDefault();

    const payload = {
        course_code: document.getElementById('course-code').value.trim(),
        course_name: document.getElementById('course-name').value.trim(),
        department: document.getElementById('course-dept').value.trim(),
        duration_years: parseInt(document.getElementById('course-duration').value || 4)
    };

    if (!payload.course_code || !payload.course_name || !payload.department) {
        showToast("Validation Error", "Please fill in all mandatory fields.", "error");
        return;
    }

    try {
        const res = await apiFetch('/api/courses', 'POST', payload);
        if (res && res.success) {
            showToast("Course Created", res.message || "Degree Course created successfully!", "success");
            closeAddCourseModal();
            loadAuxiliaryOptions();
        } else {
            showToast("Error", res.message || "Failed to create course.", "error");
        }
    } catch (err) {
        console.error("Error creating course:", err);
        showToast("Error", "An error occurred while creating course.", "error");
    }
}
