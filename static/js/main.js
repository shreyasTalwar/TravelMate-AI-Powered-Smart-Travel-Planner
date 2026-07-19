document.addEventListener('DOMContentLoaded', () => {
    // Mobile navigation toggle
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.getElementById('nav-links');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            
            // Toggle hamburger icon state
            const spans = menuToggle.querySelectorAll('span');
            spans.forEach(span => span.classList.toggle('active'));
        });
    }

    // Flash notifications auto-dismiss
    const flashAlerts = document.querySelectorAll('.flash-alert');
    flashAlerts.forEach(alert => {
        // Dismiss on click close button
        const closeBtn = alert.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            });
        }
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 0.5s ease-out';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }
        }, 5000);
    });

    // Profile Image Upload Preview
    const profileImageInput = document.getElementById('profile_image');
    const profileAvatar = document.querySelector('.profile-avatar');
    const avatarPlaceholder = document.querySelector('.profile-avatar-placeholder');
    
    if (profileImageInput) {
        profileImageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (profileAvatar) {
                        profileAvatar.src = e.target.result;
                    } else if (avatarPlaceholder) {
                        // If placeholder exists instead of img element, swap them
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'profile-avatar';
                        avatarPlaceholder.parentNode.replaceChild(img, avatarPlaceholder);
                    }
                }
                reader.readAsDataURL(file);
            }
        });
    }
});
