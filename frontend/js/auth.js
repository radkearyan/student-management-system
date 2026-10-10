// Session, Authentication, and Role Access Control - Smart Student Management System

// Global Application State (Loaded across pages)
const STATE = {
    user: null,
    activeView: 'dashboard'
};

// Map backend role names to their frontend page folder.
// 'teacher' is stored in DB as role but pages live under /pages/faculty/
function getRolePath(role) {
    if (role === 'teacher') return 'faculty';
    return role; // 'admin', 'student', 'parent' map directly
}

// Check if user is authenticated and has the correct role
async function checkAuth(allowedRoles = []) {
    const res = await API.get('/api/auth/session');
    if (res && res.success) {
        STATE.user = res.user;
        
        // If allowedRoles is provided, verify role
        if (allowedRoles.length > 0 && !allowedRoles.includes(STATE.user.role)) {
            // Redirect to their respective dashboard if they don't have access to this page
            showToast("Access Denied", "Redirecting to your workspace...", "error");
            setTimeout(() => {
                window.location.href = `/pages/${getRolePath(STATE.user.role)}/dashboard.html`;
            }, 1500);
            return false;
        }
        
        updateSidebarHeaderUI();
        return true;
    } else {
        // Not logged in, redirect to login
        const isLoginPage = window.location.pathname.endsWith('login.html');
        if (!isLoginPage) {
            window.location.href = '/login.html';
        }
        return false;
    }
}

// Redirect if already logged in (used on login.html)
async function redirectIfSessionActive() {
    const res = await API.get('/api/auth/session');
    if (res && res.success) {
        window.location.href = `/pages/${getRolePath(res.user.role)}/dashboard.html`;
    }
}

// Update UI headers and avatar elements based on active user
function updateSidebarHeaderUI() {
    if (!STATE.user) return;
    
    const navName = document.getElementById('nav-user-name');
    const navRole = document.getElementById('nav-user-role');
    const headerUsername = document.getElementById('header-user-username');
    
    if (navName) navName.textContent = STATE.user.username;
    if (navRole) navRole.textContent = STATE.user.role;
    if (headerUsername) headerUsername.textContent = STATE.user.username;
    
    updateUserAvatarUI(STATE.user.profile_pic, STATE.user.username);
    configureRoleAccess();
}

function configureRoleAccess() {
    if (!STATE.user) return;
    const role = STATE.user.role;
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const rolesAllowed = item.getAttribute('data-roles');
        if (rolesAllowed) {
            const allowedList = rolesAllowed.split(',');
            if (!allowedList.includes(role)) {
                item.classList.add('hidden');
            } else {
                item.classList.remove('hidden');
            }
        } else {
            item.classList.remove('hidden');
        }
    });
}

function updateUserAvatarUI(profilePic, username) {
    const avatarLetter = (username || "A").substring(0, 1).toUpperCase();
    const navAvatar = document.getElementById('nav-user-avatar');
    const headerAvatar = document.getElementById('header-user-avatar');
    
    if (profilePic) {
        if (navAvatar) {
            navAvatar.style.backgroundImage = `url(${profilePic})`;
            navAvatar.style.backgroundSize = 'cover';
            navAvatar.style.backgroundPosition = 'center';
            navAvatar.textContent = '';
        }
        if (headerAvatar) {
            headerAvatar.style.backgroundImage = `url(${profilePic})`;
            headerAvatar.style.backgroundSize = 'cover';
            headerAvatar.style.backgroundPosition = 'center';
            headerAvatar.textContent = '';
        }
    } else {
        if (navAvatar) {
            navAvatar.style.backgroundImage = 'none';
            navAvatar.textContent = avatarLetter;
        }
        if (headerAvatar) {
            headerAvatar.style.backgroundImage = 'none';
            headerAvatar.textContent = avatarLetter;
        }
    }
}

// Global Log Out Action
async function handleLogout() {
    const res = await API.post('/api/auth/logout');
    if (res && res.success) {
        STATE.user = null;
        showToast("Signed Out", "You have been logged out.", "success");
        setTimeout(() => {
            window.location.href = '/login.html';
        }, 1000);
    }
}
