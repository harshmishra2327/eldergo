// ==================== AUTHENTICATION HELPER ====================
// This script checks login state and updates navbar accordingly

function updateNavbarBasedOnLogin() {
    const username = localStorage.getItem('eldergo_username');
    const role = localStorage.getItem('eldergo_role');
    
    // Find the navbar login/register buttons
    const navLoginBtn = document.querySelector('.nav-login-btn');
    const navRegisterBtn = document.querySelector('.nav-register-btn');
    
    if (username && role) {
        // User is logged in - show Dashboard and Logout
        if (navLoginBtn) {
            navLoginBtn.innerHTML = '<i class="fa-solid fa-right-from-bracket me-1"></i> Logout';
            navLoginBtn.href = '#';
            navLoginBtn.onclick = function(e) {
                e.preventDefault();
                logout();
                return false;
            };
            navLoginBtn.className = 'btn btn-outline-primary nav-login-btn';
        }
        
        // Replace Register button with Dashboard button if it exists
        if (navRegisterBtn) {
            navRegisterBtn.innerHTML = '<i class="fa-solid fa-gauge-high me-1"></i> Dashboard';
            navRegisterBtn.href = role === 'admin' ? '/admin-dashboard' : (role === 'companion' ? '/companion-dashboard' : '/client-dashboard');
            navRegisterBtn.className = 'btn btn-primary nav-dashboard-btn';
            navRegisterBtn.onclick = null;
        }
    } else {
        // User is not logged in - show Login and Register
        if (navLoginBtn) {
            navLoginBtn.innerHTML = 'Login';
            navLoginBtn.href = '/login';
            navLoginBtn.onclick = null;
            navLoginBtn.className = 'btn btn-outline-primary nav-login-btn';
        }
        if (navRegisterBtn) {
            navRegisterBtn.innerHTML = 'Register';
            navRegisterBtn.href = '/register';
            navRegisterBtn.className = 'btn btn-primary nav-register-btn';
            navRegisterBtn.onclick = null;
        }
    }
}

function logout() {
    fetch('/api/logout', { method: 'POST' })
        .then(() => {
            localStorage.removeItem('eldergo_username');
            localStorage.removeItem('eldergo_role');
            window.location.href = '/';
        })
        .catch(() => {
            localStorage.removeItem('eldergo_username');
            localStorage.removeItem('eldergo_role');
            window.location.href = '/';
        });
}

// Run on page load
document.addEventListener('DOMContentLoaded', function() {
    updateNavbarBasedOnLogin();
});

