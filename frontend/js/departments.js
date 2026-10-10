// Departments Management Script - Smart Student Management System

document.addEventListener("DOMContentLoaded", async () => {
    const authOk = await checkAuth(['admin', 'teacher']);
    if (authOk) {
        const titleEl = document.getElementById('header-view-title');
        const subTitleEl = document.getElementById('header-view-subtitle');
        if (titleEl) titleEl.textContent = "Departments Directory";
        if (subTitleEl) subTitleEl.textContent = "Manage academic departments & branches";
        
        // Setup UI for Admin role
        if (STATE.user.role === 'admin') {
            const addSection = document.getElementById('admin-add-section');
            if (addSection) addSection.classList.remove('hidden');
            
            // Bind add submit
            const form = document.getElementById('add-dept-form');
            if (form) form.onsubmit = handleAddDepartment;
        }
        
        await loadDepartments();
    }
});

async function loadDepartments() {
    // 1. Fetch departments
    const depts = await API.get('/api/departments');
    if (!depts) {
        showToast("Error", "Could not load departments list.", "error");
        return;
    }
    
    // 2. Fetch students to get enrollment counts
    const students = await API.get('/api/students') || [];
    const counts = {};
    depts.forEach(d => {
        counts[d.name] = 0;
    });
    students.forEach(s => {
        if (counts[s.department] !== undefined) {
            counts[s.department]++;
        }
    });
    
    // 3. Render list of department cards
    const container = document.getElementById('departments-list-container');
    if (!container) return;
    container.innerHTML = '';
    
    if (depts.length === 0) {
        container.innerHTML = '<div class="empty-category-notice glassmorphism" style="grid-column: span 3; padding: 2rem; text-align: center;"><i class="fa-solid fa-folder-open"></i> No departments created yet.</div>';
        return;
    }
    
    const icons = {
        'Computer Engineering': 'fa-laptop-code',
        'Information Technology': 'fa-network-wired',
        'Electrical Engineering': 'fa-bolt-lightning',
        'Mechanical Engineering': 'fa-gears'
    };
    
    const gradients = [
        'linear-gradient(135deg, #3b82f6, #1d4ed8)', // Blue
        'linear-gradient(135deg, #10b981, #047857)', // Green
        'linear-gradient(135deg, #f59e0b, #b45309)', // Gold
        'linear-gradient(135deg, #ec4899, #be185d)', // Pink
        'linear-gradient(135deg, #8b5cf6, #5b21b6)', // Purple
        'linear-gradient(135deg, #06b6d4, #0891b2)'  // Cyan
    ];
    
    depts.forEach((dept, index) => {
        const icon = icons[dept.name] || 'fa-building';
        const grad = gradients[index % gradients.length];
        const studentCount = counts[dept.name] || 0;
        
        const card = document.createElement('div');
        card.className = 'glassmorphism dept-details-card';
        card.style.position = 'relative';
        card.style.overflow = 'hidden';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.gap = '1.25rem';
        card.style.padding = '1.5rem';
        card.style.borderRadius = '16px';
        card.style.transition = 'transform 0.25s, box-shadow 0.25s';
        
        // Add hover styles dynamically via event listeners to keep stylesheet clean
        card.onmouseenter = () => {
            card.style.transform = 'translateY(-4px)';
            card.style.boxShadow = '0 12px 24px rgba(0,0,0,0.3)';
        };
        card.onmouseleave = () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = 'var(--card-shadow)';
        };
        
        let deleteBtnHTML = '';
        if (STATE.user.role === 'admin') {
            deleteBtnHTML = `
                <button class="btn-delete-dept" onclick="handleDeleteDepartment(${dept.dept_id}, '${dept.name.replace(/'/g, "\\'")}')" title="Delete Department" style="position: absolute; top: 12px; right: 12px; background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 4px; border-radius: 4px; font-size: 0.85rem; transition: color 0.2s;">
                    <i class="fa-solid fa-trash-can" onmouseenter="this.parentElement.style.color='#ef4444'" onmouseleave="this.parentElement.style.color='var(--text-muted)'"></i>
                </button>
            `;
        }
        
        card.innerHTML = `
            ${deleteBtnHTML}
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: ${grad}; color: white; font-size: 1.5rem; flex-shrink: 0;">
                    <i class="fa-solid ${icon}"></i>
                </div>
                <div>
                    <h3 style="font-size: 1.12rem; font-weight: 700; color: var(--text-main); margin-bottom: 2px;">${dept.name}</h3>
                    <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">Department</span>
                </div>
            </div>
            <div style="border-top: 1px solid var(--glass-border); padding-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 0.8rem; color: var(--text-muted);">
                    Enrolled Students
                </div>
                <div style="font-size: 1.2rem; font-weight: 800; color: var(--accent-gold);">
                    ${studentCount}
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

async function handleAddDepartment(e) {
    e.preventDefault();
    const input = document.getElementById('new-dept-name');
    const name = input.value.strip ? input.value.strip() : input.value.trim();
    
    if (!name) return;
    
    const res = await API.post('/api/departments', { name });
    if (res && res.success) {
        showToast("Success", `Department "${name}" created successfully.`, "success");
        input.value = '';
        await loadDepartments();
    } else {
        showToast("Error", res.message || "Failed to create department.", "error");
    }
}

async function handleDeleteDepartment(id, name) {
    showConfirmModal("Confirm Department Deletion", `Are you sure you want to delete the department "${name}"?`, async () => {
        const res = await API.delete(`/api/departments/${id}`);
        if (res && res.success) {
            showToast("Success", "Department deleted successfully.", "success");
            await loadDepartments();
        } else {
            showToast("Delete Failed", res.message || "Could not delete department.", "error");
        }
    });
}
