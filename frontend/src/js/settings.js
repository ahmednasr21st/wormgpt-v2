// settings.js
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    const settingsUsername = document.getElementById('settingsUsername');
    const settingsEmail = document.getElementById('settingsEmail');
    const settingsPlan = document.getElementById('settingsPlan');
    const saveAiPreferencesBtn = document.querySelector('.settings-section button');
    const deleteAccountBtn = document.querySelector('.delete-account');

    // Fetch user info
    try {
        const response = await fetch(`${API_BASE_URL}/user/profile`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            const userData = await response.json();
            settingsUsername.textContent = userData.username;
            settingsEmail.textContent = userData.email;
            settingsPlan.textContent = formatPlanName(userData.plan); // Format for display
            // Set AI preferences if loaded from backend
            // document.getElementById('tonePreference').value = userData.ai_tone || 'neutral';
            // document.getElementById('historyRetention').value = userData.history_retention || '30days';
        } else {
            console.error('Failed to fetch user profile:', await response.json());
        }
    } catch (error) {
        console.error('Error fetching user profile:', error);
    }

    function formatPlanName(plan) {
        switch (plan) {
            case 'free': return 'Free Access';
            case 'pro': return 'Pro Protocol';
            case 'vip': return 'VIP Exoskeleton';
            default: return 'Unknown';
        }
    }

    if (saveAiPreferencesBtn) {
        saveAiPreferencesBtn.addEventListener('click', async () => {
            alert('AI Preferences saved! (Backend integration needed)');
            // Implement API call to save preferences to backend
            /*
            const tone = document.getElementById('tonePreference').value;
            const history = document.getElementById('historyRetention').value;
            try {
                const response = await fetch(`${API_BASE_URL}/user/preferences`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ ai_tone: tone, history_retention: history })
                });
                if (response.ok) {
                    alert('AI preferences updated successfully!');
                } else {
                    alert('Failed to update AI preferences.');
                }
            } catch (error) {
                console.error('Error updating AI preferences:', error);
                alert('An error occurred.');
            }
            */
        });
    }

    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', async () => {
            if (confirm('WARNING: This action is irreversible. All your data will be permanently deleted. Are you absolutely sure you want to delete your account?')) {
                alert('Account deletion initiated! (Backend integration needed)');
                // Implement API call to delete account
                /*
                try {
                    const response = await fetch(`${API_BASE_URL}/user/delete`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) {
                        alert('Your account has been deleted.');
                        localStorage.removeItem('token');
                        window.location.href = 'index.html';
                    } else {
                        alert('Failed to delete account.');
                    }
                } catch (error) {
                    console.error('Error deleting account:', error);
                    alert('An error occurred.');
                }
                */
            }
        });
    }

    // Logout functionality (reused from auth.js, ensure auth.js is loaded)
    const logoutBtnSettings = document.getElementById('logoutBtnSettings');
    if (logoutBtnSettings) {
        logoutBtnSettings.addEventListener('click', async (e) => {
            e.preventDefault();
            localStorage.removeItem('token');
            window.location.href = 'index.html';
        });
    }
});
