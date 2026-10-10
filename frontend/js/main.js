// Main UI Assembly, Theme, Toast, Global Search, and Notification Loader

document.addEventListener("DOMContentLoaded", () => {
    // 1. Restore sidebar collapse state from storage
    if (localStorage.getItem('sidebar_collapsed') === 'true') {
        document.body.classList.add('sidebar-collapsed');
    }

    // 2. Load shared layout components
    assembleLayout();
    
    // 3. Initialize theme mode
    initTheme();
});

// Load Sidebar, Navbar, and Footer dynamically on placeholders
async function assembleLayout() {
    const sidebarContainer = document.getElementById('sidebar-container');
    const headerContainer = document.getElementById('header-container');

    const fetches = [
        sidebarContainer ? fetch('/components/sidebar.html') : Promise.resolve(null),
        headerContainer ? fetch('/components/navbar.html') : Promise.resolve(null),
        fetch('/components/modal.html')
    ];

    const [sidebarRes, headerRes, modalRes] = await Promise.all(fetches);
    
    if (sidebarContainer && sidebarRes && sidebarRes.ok) {
        sidebarContainer.innerHTML = await sidebarRes.text();
        
        // Connect Logout Button
        const logoutBtn = document.getElementById('btn-logout');
        if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
        
        // Connect Change Password triggers
        const changePwTrigger = document.getElementById('btn-trigger-change-pw');
        if (changePwTrigger) changePwTrigger.addEventListener('click', openChangePasswordModal);
        
        // Connect Sidebar Collapse Toggle
        const collapseBtn = document.getElementById('sidebar-collapse-btn');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => {
                const isCollapsed = document.body.classList.toggle('sidebar-collapsed');
                localStorage.setItem('sidebar_collapsed', isCollapsed ? 'true' : 'false');
            });
        }

        // Highlight Active Sidebar Item matching path
        highlightActiveNav();
        updateSidebarHeaderUI();
        fetchSidebarBadges();
    }
    
    if (headerContainer && headerRes && headerRes.ok) {
        headerContainer.innerHTML = await headerRes.text();
        
        // Connect Theme Toggler
        const toggler = document.getElementById('theme-toggler');
        if (toggler) toggler.onclick = toggleTheme;
        
        // Connect Header Profile Dropdown
        initHeaderProfileDropdown();
        
        // Connect Global Live Search
        initGlobalSearch();

        // Connect Notification Bell Dropdown
        initNotificationBell();

        // Connect Mobile Menu Toggle
        const mobileTrigger = document.getElementById('mobile-menu-trigger');
        if (mobileTrigger) {
            mobileTrigger.addEventListener('click', () => {
                document.body.classList.toggle('mobile-menu-open');
            });
        }
        
        updateSidebarHeaderUI();
    }
    
    // Load shared modals
    if (modalRes && modalRes.ok) {
        const div = document.createElement('div');
        div.innerHTML = await modalRes.text();
        document.body.appendChild(div);
        initChangePasswordModal();
    }
    
    // Initialize Chatbot if trigger exists
    initChatbot();
}

function highlightActiveNav() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const link = item.querySelector('a');
        if (link) {
            const href = link.getAttribute('href');
            if (href && currentPath.includes(href) && href !== '#') {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        }
    });
}

// Fetch real backend counts for sidebar badges
async function fetchSidebarBadges() {
    try {
        const res = await API.get('/api/analytics');
        if (res && res.metrics) {
            const badgeStu = document.getElementById('sidebar-badge-students');
            if (badgeStu) badgeStu.textContent = res.metrics.total_students || '0';
        }
    } catch (e) {
        console.warn("Could not load sidebar badge metrics", e);
    }
}

// Header Profile Dropdown Wiring
function initHeaderProfileDropdown() {
    const profileBtn = document.getElementById('header-user-profile');
    const menu = document.getElementById('profile-dropdown-menu');
    const logoutBtn = document.getElementById('btn-navbar-logout');
    const changePwBtn = document.getElementById('btn-navbar-change-pw');

    if (profileBtn && menu) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!menu.contains(e.target) && !profileBtn.contains(e.target)) {
                menu.classList.add('hidden');
            }
        });
    }

    if (logoutBtn) logoutBtn.addEventListener('click', (e) => { e.preventDefault(); handleLogout(); });
    if (changePwBtn) changePwBtn.addEventListener('click', (e) => { e.preventDefault(); openChangePasswordModal(); });
}

// Notification Bell Wiring
function initNotificationBell() {
    const bellBtn = document.getElementById('notification-bell-btn');
    const dropdown = document.getElementById('notification-dropdown');
    const badge = document.getElementById('notification-badge');
    const listContainer = document.getElementById('notification-items-list');

    if (!bellBtn || !dropdown) return;

    bellBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const willOpen = dropdown.classList.contains('hidden');
        dropdown.classList.toggle('hidden');

        if (willOpen && listContainer) {
            listContainer.innerHTML = `<div class="text-muted" style="text-align: center; padding: 12px; font-size: 0.8rem;"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>`;
            const res = await API.get('/api/announcements');
            if (res && res.success && res.announcements && res.announcements.length > 0) {
                if (badge) {
                    badge.textContent = res.announcements.length;
                    badge.classList.remove('hidden');
                }
                listContainer.innerHTML = res.announcements.map(a => `
                    <div style="padding: 8px; border-bottom: 1px solid var(--border-color); cursor: pointer;" onclick="window.location.href='/pages/admin/dashboard.html'">
                        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--accent-gold);">
                            <span>${a.department || 'General'}</span>
                            <span>${(a.created_at || '').substring(0, 10)}</span>
                        </div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-main); margin: 2px 0;">${a.title}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); line-height: 1.3;">${(a.message || '').substring(0, 70)}...</div>
                    </div>
                `).join('');
            } else {
                if (badge) badge.classList.add('hidden');
                listContainer.innerHTML = `<div class="text-muted" style="text-align: center; padding: 12px; font-size: 0.8rem;">No active announcements</div>`;
            }
        }
    });

    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });
}

// Global Search Wiring
function initGlobalSearch() {
    const searchInput = document.getElementById('global-search-input');
    const resultsDropdown = document.getElementById('global-search-results');
    const clearBtn = document.getElementById('search-clear-btn');
    if (!searchInput || !resultsDropdown) return;

    let debounceTimer;

    searchInput.addEventListener('input', (e) => {
        const q = e.target.value.trim();
        if (clearBtn) clearBtn.classList.toggle('hidden', q.length === 0);

        clearTimeout(debounceTimer);
        if (q.length < 1) {
            resultsDropdown.classList.add('hidden');
            return;
        }

        debounceTimer = setTimeout(async () => {
            const res = await API.get(`/api/search?q=${encodeURIComponent(q)}`);
            if (res && res.success && res.results) {
                renderSearchResults(res.results, resultsDropdown);
            } else {
                resultsDropdown.classList.add('hidden');
            }
        }, 250);
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearBtn.classList.add('hidden');
            resultsDropdown.classList.add('hidden');
        });
    }

    document.addEventListener('click', (e) => {
        if (!resultsDropdown.contains(e.target) && e.target !== searchInput) {
            resultsDropdown.classList.add('hidden');
        }
    });
}

function renderSearchResults(results, dropdown) {
    const content = dropdown.querySelector('.search-results-content') || dropdown;
    let html = '';
    let totalCount = 0;

    if (results.students && results.students.length > 0) {
        totalCount += results.students.length;
        html += `<div class="search-section-title"><i class="fa-solid fa-user-graduate"></i> Students</div>`;
        html += results.students.map(s => `
            <a href="/pages/admin/students.html?id=${s.student_id}" class="search-result-item">
                <i class="fa-solid fa-user"></i>
                <div>
                    <div style="font-weight: 600; font-size: 0.82rem;">${s.name} (${s.student_id})</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted);">${s.department || 'General'}</div>
                </div>
            </a>
        `).join('');
    }

    if (results.faculty && results.faculty.length > 0) {
        totalCount += results.faculty.length;
        html += `<div class="search-section-title"><i class="fa-solid fa-chalkboard-user"></i> Faculty</div>`;
        html += results.faculty.map(f => `
            <a href="/pages/admin/faculty.html?search=${encodeURIComponent(f.name)}" class="search-result-item">
                <i class="fa-solid fa-user-tie"></i>
                <div>
                    <div style="font-weight: 600; font-size: 0.82rem;">${f.name}</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted);">${f.department || 'Department'}</div>
                </div>
            </a>
        `).join('');
    }

    if (results.subjects && results.subjects.length > 0) {
        totalCount += results.subjects.length;
        html += `<div class="search-section-title"><i class="fa-solid fa-book-open"></i> Subjects</div>`;
        html += results.subjects.map(sub => `
            <a href="/pages/admin/subjects.html?code=${sub.subject_code}" class="search-result-item">
                <i class="fa-solid fa-book"></i>
                <div>
                    <div style="font-weight: 600; font-size: 0.82rem;">${sub.subject_code} - ${sub.subject_name}</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted);">${sub.department || ''}</div>
                </div>
            </a>
        `).join('');
    }

    if (results.announcements && results.announcements.length > 0) {
        totalCount += results.announcements.length;
        html += `<div class="search-section-title"><i class="fa-solid fa-bullhorn"></i> Announcements</div>`;
        html += results.announcements.map(a => `
            <a href="/pages/admin/dashboard.html" class="search-result-item">
                <i class="fa-solid fa-bullhorn"></i>
                <div>
                    <div style="font-weight: 600; font-size: 0.82rem;">${a.title}</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted);">${(a.message || '').substring(0, 50)}...</div>
                </div>
            </a>
        `).join('');
    }

    if (totalCount === 0) {
        html = `<div style="text-align: center; padding: 16px; color: var(--text-muted); font-size: 0.8rem;"><i class="fa-solid fa-circle-question" style="font-size: 1.5rem; margin-bottom: 4px;"></i><br>No matching records found.</div>`;
    }

    content.innerHTML = html;
    dropdown.classList.remove('hidden');
}

// Global Toast Alerts
function showToast(title, message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-message glassmorphism border-${type}`;
    toast.innerHTML = `
        <div class="toast-header">
            <i class="fa-solid ${type === 'success' ? 'fa-circle-check text-green' : (type === 'error' ? 'fa-circle-xmark text-red' : 'fa-circle-exclamation text-yellow')}"></i>
            <strong>${title}</strong>
            <button class="toast-close">&times;</button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    container.appendChild(toast);
    
    toast.querySelector('.toast-close').onclick = () => toast.remove();
    setTimeout(() => toast.remove(), 4000);
}

// Theme Engine (Dark & Light Mode)
function initTheme() {
    const savedTheme = localStorage.getItem('theme_mode') || 'dark';
    applyTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem('theme_mode', newTheme);
}

function applyTheme(mode) {
    const icon = document.getElementById('theme-toggler-icon');
    if (mode === 'light') {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        if (icon) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            icon.style.color = '#f59e0b';
        }
    } else {
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        if (icon) {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            icon.style.color = '';
        }
    }
}

// Authentication & Logout handlers
async function handleLogout() {
    showConfirmModal("Confirm Sign Out", "Are you sure you want to end your current session?", async () => {
        try {
            await API.post('/api/auth/logout');
        } catch (e) {
            console.warn("Logout API error:", e);
        }
        STATE.user = null;
        window.location.href = '/login.html';
    });
}

function updateSidebarHeaderUI() {
    if (!STATE.user) return;
    const userName = STATE.user.name || STATE.user.username || 'User';
    const userRole = STATE.user.role || 'student';

    const nameEls = [document.getElementById('nav-user-name'), document.getElementById('header-user-username'), document.getElementById('dropdown-user-fullname')];
    const roleEls = [document.getElementById('nav-user-role'), document.getElementById('header-user-role-badge'), document.getElementById('dropdown-user-role')];
    const avatarEls = [document.getElementById('nav-user-avatar'), document.getElementById('header-user-avatar')];

    nameEls.forEach(el => { if (el) el.textContent = userName; });
    roleEls.forEach(el => { if (el) el.textContent = userRole.toUpperCase(); });
    avatarEls.forEach(el => {
        if (el) {
            const initial = userName.charAt(0).toUpperCase();
            el.textContent = initial;
        }
    });

    // Enforce role-based sidebar link visibility
    document.querySelectorAll('.nav-item[data-roles]').forEach(item => {
        const allowedRoles = item.getAttribute('data-roles').split(',');
        if (allowedRoles.includes(userRole)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function openChangePasswordModal() {
    const modal = document.getElementById('change-pw-modal');
    if (modal) modal.classList.remove('hidden');
}

function initChangePasswordModal() {
    const modal = document.getElementById('change-pw-modal');
    if (!modal) return;

    const closeBtn = document.getElementById('btn-close-change-modal');
    const cancelBtn = document.getElementById('btn-cancel-change-modal');
    const form = document.getElementById('change-password-form');

    const closeModal = () => modal.classList.add('hidden');

    if (closeBtn) closeBtn.onclick = closeModal;
    if (cancelBtn) cancelBtn.onclick = closeModal;

    if (form) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const current_password = document.getElementById('change-current-pw').value;
            const new_password = document.getElementById('change-new-pw').value;
            if (!current_password || !new_password) {
                showToast('Error', 'Please fill in all password fields.', 'error');
                return;
            }
            try {
                const res = await API.post('/api/auth/change_password', { current_password, new_password });
                if (res && res.success) {
                    showToast('Success', 'Password changed successfully.', 'success');
                    form.reset();
                    closeModal();
                } else {
                    showToast('Error', res.message || 'Failed to change password.', 'error');
                }
            } catch (err) {
                showToast('Error', err.message || 'Password update failed.', 'error');
            }
        };
    }
}

// Global Confirmation Modal
function showConfirmModal(title, message, onConfirm) {
    let modal = document.getElementById('confirm-action-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'confirm-action-modal';
        modal.className = 'modal-wrapper hidden';
        modal.innerHTML = `
            <div class="modal-card glassmorphism" style="width: 100%; max-width: 420px; padding: 1.5rem; border-radius: 14px; text-align: center;">
                <div style="font-size: 2.5rem; color: var(--accent-gold); margin-bottom: 0.5rem;"><i class="fa-solid fa-triangle-exclamation"></i></div>
                <h3 id="confirm-modal-title" style="margin-bottom: 0.5rem; font-weight: 700; color: var(--text-main);">Confirm Action</h3>
                <p id="confirm-modal-message" style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1.5rem;">Are you sure?</p>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button id="btn-cancel-confirm" type="button" class="btn btn-secondary btn-sm" style="padding: 6px 14px;">Cancel</button>
                    <button id="btn-proceed-confirm" type="button" class="btn btn-primary btn-sm" style="padding: 6px 14px; background: var(--danger); border-color: var(--danger); color: white;">Yes, Proceed</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    const titleEl = modal.querySelector('#confirm-modal-title');
    const msgEl = modal.querySelector('#confirm-modal-message');
    const cancelBtn = modal.querySelector('#btn-cancel-confirm');
    const proceedBtn = modal.querySelector('#btn-proceed-confirm');

    if (titleEl) titleEl.textContent = title || "Confirm Action";
    if (msgEl) msgEl.textContent = message || "Are you sure you want to proceed?";

    modal.classList.remove('hidden');

    if (cancelBtn) cancelBtn.onclick = () => { modal.classList.add('hidden'); };
    if (proceedBtn) proceedBtn.onclick = async () => {
        modal.classList.add('hidden');
        if (typeof onConfirm === 'function') await onConfirm();
    };
}

// Global Loading Overlay Spinner
function showLoading(msg = "Loading data...") {
    const overlay = document.getElementById('global-loading-overlay');
    const textEl = document.getElementById('loading-overlay-text');
    if (textEl) textEl.textContent = msg;
    if (overlay) overlay.classList.remove('hidden');
}

function hideLoading() {
    const overlay = document.getElementById('global-loading-overlay');
    if (overlay) overlay.classList.add('hidden');
}

// Render Accessible Empty State inside Containers/Tables
function renderEmptyState(container, title = "No records found", message = "There are no entries matching your current view criteria.", colSpan = 6) {
    if (!container) return;
    if (container.tagName === 'TBODY') {
        container.innerHTML = `
            <tr>
                <td colspan="${colSpan}" style="text-align: center; padding: 2rem;">
                    <div style="font-size: 2rem; color: var(--text-muted); margin-bottom: 6px;"><i class="fa-solid fa-folder-open"></i></div>
                    <div style="font-weight: 700; color: var(--text-main); font-size: 0.95rem;">${title}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">${message}</div>
                </td>
            </tr>
        `;
    } else {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; background: rgba(255,255,255,0.02); border: 1px dashed var(--glass-border); border-radius: 10px;">
                <div style="font-size: 2rem; color: var(--text-muted); margin-bottom: 6px;"><i class="fa-solid fa-folder-open"></i></div>
                <div style="font-weight: 700; color: var(--text-main); font-size: 0.95rem;">${title}</div>
                <div style="font-size: 0.8rem; color: var(--text-muted);">${message}</div>
            </div>
        `;
    }
}
