// auth.js
const API_BASE_URL = 'https://api.wormgpt.site/api'; // Replace with your backend URL in production

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const showRegisterLink = document.getElementById('showRegister');
    const showLoginLink = document.getElementById('showLogin');
    const googleLoginBtn = document.getElementById('googleLoginBtn');
    const authMessage = document.getElementById('authMessage');

    // Logout buttons (used in other pages too)
    const logoutBtnChat = document.getElementById('logoutBtn');
    const logoutBtnSub = document.getElementById('logoutBtnSub');
    const logoutBtnSettings = document.getElementById('logoutBtnSettings');

    if (logoutBtnChat) logoutBtnChat.addEventListener('click', handleLogout);
    if (logoutBtnSub) logoutBtnSub.addEventListener('click', handleLogout);
    if (logoutBtnSettings) logoutBtnSettings.addEventListener('click', handleLogout);


    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            authMessage.classList.add('hidden');
        });
    }

    if (showLoginLink) {
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            registerForm.classList.add('hidden');
            loginForm.classList.remove('hidden');
            authMessage.classList.add('hidden');
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = e.target.loginUsername.value;
            const password = e.target.loginPassword.value;

            try {
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();

                if (response.ok) {
                    localStorage.setItem('token', data.access_token);
                    showMessage(authMessage, data.message, 'success');
                    window.location.href = 'chat.html'; // Redirect to chat page
                } else {
                    showMessage(authMessage, data.message, 'error');
                }
            } catch (error) {
                console.error('Login error:', error);
                showMessage(authMessage, 'An error occurred during login.', 'error');
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = e.target.registerUsername.value;
            const email = e.target.registerEmail.value;
            const password = e.target.registerPassword.value;
            const confirmPassword = e.target.confirmPassword.value;

            if (password !== confirmPassword) {
                showMessage(authMessage, 'Passwords do not match.', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                const data = await response.json();

                if (response.ok) {
                    showMessage(authMessage, data.message + ' You can now login.', 'success');
                    // Optionally switch to login form
                    registerForm.classList.add('hidden');
                    loginForm.classList.remove('hidden');
                } else {
                    showMessage(authMessage, data.message, 'error');
                }
            } catch (error) {
                console.error('Registration error:', error);
                showMessage(authMessage, 'An error occurred during registration.', 'error');
            }
        });
    }

    if (googleLoginBtn) {
        googleLoginBtn.addEventListener('click', () => {
            // Redirect to backend Google OAuth initiation endpoint
            window.location.href = `${API_BASE_URL}/auth/google`;
        });
    }

    // Function to handle logout
    async function handleLogout(e) {
        e.preventDefault();
        const token = localStorage.getItem('token');
        if (!token) {
            console.warn('No token found, redirecting to login anyway.');
            localStorage.removeItem('token');
            window.location.href = 'index.html';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            // Even if the backend logout fails, clear client-side token
            localStorage.removeItem('token');
            if (response.ok) {
                console.log('Logged out successfully.');
            } else {
                console.error('Backend logout failed:', await response.json());
            }
        } catch (error) {
            console.error('Error during logout:', error);
        } finally {
            window.location.href = 'index.html'; // Always redirect to login page
        }
    }


    function showMessage(element, message, type) {
        element.textContent = message;
        element.className = `message ${type}`; // Reset classes and add new ones
        element.classList.remove('hidden');
    }

    // Check if user is logged in (has token) and redirect from index.html
    const token = localStorage.getItem('token');
    if (token && window.location.pathname.includes('index.html')) {
        // You might want to validate the token with the backend here for robustness
        window.location.href = 'chat.html';
    }
});
