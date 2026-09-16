document.addEventListener('DOMContentLoaded', () => {
    const staffLoginForm = document.getElementById('staffLoginForm');
    
    if (!staffLoginForm) return;

    staffLoginForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const emailInput = document.getElementById('loginEmail');
        const passwordInput = document.getElementById('loginPassword');
        const submitBtn = document.getElementById('staffLoginSubmitBtn');

        const email = emailInput ? emailInput.value.trim() : '';
        const password = passwordInput ? passwordInput.value.trim() : '';

        if (!email || !password) {
            alert('Please enter both email and password.');
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Authenticating...';
        }

        try {
            const response = await fetch('/api/staff/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                // Store staff details in session storage
                if (data.staff_id) sessionStorage.setItem('staff_id', data.staff_id);
                if (data.email) sessionStorage.setItem('staff_email', data.email);
                if (data.assigned_pincode) sessionStorage.setItem('assigned_pincode', data.assigned_pincode);

                // Redirect directly to the staff dashboard
                window.location.href = '/staff-dashboard';
            } else {
                alert(data.detail || 'Invalid staff credentials. Please try again.');
            }
        } catch (error) {
            console.error('Error during staff login:', error);
            alert('A network error occurred while attempting to log in.');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Log In to Dashboard';
            }
        }
    });
});