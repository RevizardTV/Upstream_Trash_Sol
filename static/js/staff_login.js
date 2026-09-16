document.addEventListener('DOMContentLoaded', () => {
    const staffLoginForm = document.getElementById('staffLoginForm');
    const staffOtpForm = document.getElementById('staffOtpForm');
    const errorMessage = document.getElementById('errorMessage');
    const otpTimer = document.getElementById('otpTimer');
    const otpAttemptsDisplay = document.getElementById('otpAttempts');
    const changeCredentialsBtn = document.getElementById('changeCredentialsBtn');

    let countdownInterval = null;
    let attemptsLeft = 3;
    let timerSeconds = 300; // 5-minute OTP lifecycle

    const showError = (msg) => {
        if (!errorMessage) return;
        if (msg) {
            errorMessage.textContent = msg;
            errorMessage.classList.remove('hidden');
        } else {
            errorMessage.textContent = '';
            errorMessage.classList.add('hidden');
        }
    };

    const startTimer = () => {
        clearInterval(countdownInterval);
        timerSeconds = 300;
        
        const updateDisplay = () => {
            const minutes = Math.floor(timerSeconds / 60);
            const seconds = timerSeconds % 60;
            if (otpTimer) {
                otpTimer.textContent = `Code expires in: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            }

            if (timerSeconds <= 0) {
                clearInterval(countdownInterval);
                if (otpTimer) otpTimer.textContent = 'OTP code expired. Please request a new code.';
                document.getElementById('verifyOtpBtn').disabled = true;
            }
            timerSeconds--;
        };

        updateDisplay();
        countdownInterval = setInterval(updateDisplay, 1000);
    };

    const updateAttemptsUI = () => {
        if (!otpAttemptsDisplay) return;
        if (attemptsLeft < 3) {
            otpAttemptsDisplay.textContent = `Attempts remaining: ${attemptsLeft}`;
            otpAttemptsDisplay.classList.remove('hidden');
        } else {
            otpAttemptsDisplay.classList.add('hidden');
        }
    };

    if (!staffLoginForm) return;

    // Step 1: Verify Password & Reveal Inline OTP Form
    staffLoginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        showError('');

        const emailInput = document.getElementById('loginEmail');
        const passwordInput = document.getElementById('loginPassword');
        const submitBtn = document.getElementById('staffLoginSubmitBtn');

        const email = emailInput ? emailInput.value.trim() : '';
        const password = passwordInput ? passwordInput.value.trim() : '';

        if (!email || !password) {
            showError('Please enter both email and password.');
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-xs"></i> Verifying...`;
        }

        try {
            const response = await fetch('/api/staff/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok && data.status === 'otp_required') {
                sessionStorage.setItem('staff_id', data.staff_id);
                sessionStorage.setItem('staff_email', data.email);
                sessionStorage.setItem('assigned_pincode', data.assigned_pincode);

                // Disable credentials form inputs to lock during verification
                emailInput.disabled = true;
                passwordInput.disabled = true;
                submitBtn.disabled = true;
                submitBtn.innerHTML = `<i class="fa-solid fa-check text-xs"></i> Password Verified`;

                // Reveal Inline OTP form directly under login
                staffOtpForm.classList.remove('hidden');
                document.getElementById('otpCode').focus();

                // Reset attempts & start countdown timer
                attemptsLeft = 3;
                updateAttemptsUI();
                startTimer();
            } else {
                showError(data.detail || 'Invalid staff credentials. Please try again.');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane text-xs"></i> Authenticate & Send Code`;
                }
            }
        } catch (error) {
            console.error('Error during staff login:', error);
            showError('A network error occurred while attempting to log in.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane text-xs"></i> Authenticate & Send Code`;
            }
        }
    });

    // Step 2: Verify OTP
    if (staffOtpForm) {
        staffOtpForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            showError('');

            const otpInput = document.getElementById('otpCode');
            const verifyBtn = document.getElementById('verifyOtpBtn');
            const email = sessionStorage.getItem('staff_email');
            const otpCode = otpInput ? otpInput.value.trim() : '';

            if (!otpCode || otpCode.length !== 6) {
                showError('Please enter a valid 6-digit OTP code.');
                return;
            }

            if (verifyBtn) {
                verifyBtn.disabled = true;
                verifyBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-xs"></i> Checking Code...`;
            }

            try {
                const response = await fetch('/api/auth/verify-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email_address: email,
                        otp_code: otpCode
                    })
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    window.location.href = '/staff-dashboard';
                } else {
                    attemptsLeft--;
                    updateAttemptsUI();

                    if (attemptsLeft <= 0) {
                        showError('Maximum attempts reached. Please reload and re-authenticate.');
                        verifyBtn.disabled = true;
                        otpInput.disabled = true;
                        clearInterval(countdownInterval);
                    } else {
                        showError(data.detail || 'Invalid OTP code.');
                        if (verifyBtn) {
                            verifyBtn.disabled = false;
                            verifyBtn.innerHTML = `<i class="fa-solid fa-right-to-bracket text-xs"></i> Verify OTP & Access Portal`;
                        }
                    }
                }
            } catch (error) {
                console.error('Error during OTP verification:', error);
                showError('A network error occurred while verifying OTP.');
                if (verifyBtn) {
                    verifyBtn.disabled = false;
                    verifyBtn.innerHTML = `<i class="fa-solid fa-right-to-bracket text-xs"></i> Verify OTP & Access Portal`;
                }
            }
        });
    }

    // Return to credentials editing
    if (changeCredentialsBtn) {
        changeCredentialsBtn.addEventListener('click', () => {
            clearInterval(countdownInterval);
            showError('');

            document.getElementById('loginEmail').disabled = false;
            document.getElementById('loginPassword').disabled = false;
            
            const submitBtn = document.getElementById('staffLoginSubmitBtn');
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane text-xs"></i> Authenticate & Send Code`;

            staffOtpForm.classList.add('hidden');
        });
    }
});