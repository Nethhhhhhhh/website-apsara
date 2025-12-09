document.addEventListener('DOMContentLoaded', () => {
    // Initialize Toast Container if not exists
    if (!document.querySelector('.toast-container')) {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Avatar Upload Logic
    const avatarContainer = document.getElementById('avatar-container');
    const avatarInput = document.getElementById('avatar-input');
    const avatarOverlay = document.getElementById('avatar-overlay');

    if (avatarContainer && avatarInput) {
        avatarContainer.addEventListener('click', () => avatarInput.click());

        avatarContainer.addEventListener('mouseover', () => avatarOverlay.style.opacity = '1');
        avatarContainer.addEventListener('mouseout', () => avatarOverlay.style.opacity = '0');

        avatarInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                showToast("Uploading", "Updating profile picture...", "success");
                const response = await fetch('/api/profile/upload-avatar', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (data.status === 'success') {
                    // Update Image Source
                    const img = document.getElementById('profile-img');
                    if (img) {
                        img.src = data.url;
                    } else {
                        window.location.reload();
                    }
                    showToast("Success", "Profile picture updated!", "success");
                } else {
                    showToast("Error", "Upload failed: " + data.message, "error");
                }
            } catch (err) {
                console.error(err);
                showToast("Error", "Upload failed.", "error");
            }
        });
    }
});

function showToast(title, message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'toast-error' : 'toast-success'}`;

    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:1.2rem;" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

async function updateProfile() {
    const fullName = document.getElementById('full_name').value;
    const currentPass = document.getElementById('current_password').value;
    const newPass = document.getElementById('new_password').value;
    const confirmPass = document.getElementById('confirm_password').value;

    const formData = new FormData();
    formData.append('full_name', fullName);
    if (currentPass) formData.append('password', currentPass);
    if (newPass) formData.append('new_password', newPass);
    if (confirmPass) formData.append('confirm_password', confirmPass);

    try {
        const response = await fetch('/api/profile/update', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.status === 'success') {
            showToast("Success", data.message, "success");
            document.getElementById('current_password').value = '';
            document.getElementById('new_password').value = '';
            document.getElementById('confirm_password').value = '';
        } else {
            showToast("Error", data.message, "error");
        }
    } catch (err) {
        showToast("Error", "Failed to update profile", "error");
    }
}

function checkStrength() {
    const pass = document.getElementById('new_password').value;
    const bar = document.getElementById('strength-bar');
    const text = document.getElementById('strength-text');

    let strength = 0;
    if (pass.length > 5) strength += 20;
    if (pass.match(/[A-Z]/)) strength += 20;
    if (pass.match(/[0-9]/)) strength += 20;
    if (pass.match(/[^a-zA-Z0-9]/)) strength += 20;
    if (pass.length > 10) strength += 20;

    bar.style.width = strength + '%';

    if (strength < 40) {
        bar.style.background = 'var(--secondary-red)';
        text.innerText = "Weak";
        text.style.color = 'var(--secondary-red)';
    } else if (strength < 80) {
        bar.style.background = 'orange';
        text.innerText = "Medium";
        text.style.color = 'orange';
    } else {
        bar.style.background = '#4ade80';
        text.innerText = "Strong";
        text.style.color = '#4ade80';
    }
}
