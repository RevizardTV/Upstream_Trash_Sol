document.addEventListener('DOMContentLoaded', () => {
    const staffLoginForm = document.getElementById('staffLoginForm');
    const staffOtpForm = document.getElementById('staffOtpForm');

    if (!staffLoginForm) return;

    // Phase 1: Submit Credentials & Receive OTP
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

            if (response.ok && data.status === 'otp_required') {
                // Store temporary metadata in sessionStorage
                sessionStorage.setItem('staff_id', data.staff_id);
                sessionStorage.setItem('staff_email', data.email);
                sessionStorage.setItem('assigned_pincode', data.assigned_pincode);

                // Update UI to OTP mode
                document.getElementById('credentialsSection').classList.add('hidden');
                staffOtpForm.classList.remove('hidden');

                const subtitle = document.getElementById('portalSubtitle');
                if (subtitle) {
                    subtitle.textContent = `OTP sent to ${data.email}`;
                }
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

    // Phase 2: Submit OTP Code & Retrieve Authorization Cookie
    if (staffOtpForm) {
        staffOtpForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const otpInput = document.getElementById('otpCode');
            const verifyBtn = document.getElementById('verifyOtpBtn');
            const email = sessionStorage.getItem('staff_email');
            const otpCode = otpInput ? otpInput.value.trim() : '';

            if (!otpCode || otpCode.length !== 6) {
                alert('Please enter a valid 6-digit OTP code.');
                return;
            }

            if (verifyBtn) {
                verifyBtn.disabled = true;
                verifyBtn.textContent = 'Verifying...';
            }

            try {
                const response = await fetch('/api/auth/verify-otp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email_address: email,
                        otp_code: otpCode
                    })
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    // Redirect directly to dashboard once the staff_authenticated cookie is set
                    window.location.href = '/staff-dashboard';
                } else {
                    alert(data.detail || 'Invalid or expired OTP code.');
                }
            } catch (error) {
                console.error('Error during OTP verification:', error);
                alert('A network error occurred while verifying OTP.');
            } finally {
                if (verifyBtn) {
                    verifyBtn.disabled = false;
                    verifyBtn.textContent = 'Verify OTP & Access Portal';
                }
            }
        });
    }
});