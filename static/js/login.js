const API_URL = "/api/auth";
const otpTimer = document.getElementById("otpTimer");
let otpIntervalId = null;

async function apiPost(endpoint, bodyData) {
    const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Something went wrong!");
    return data;
}

const state = {
    get step() { return sessionStorage.getItem('login_step') || 'phone'; },
    set step(val) { sessionStorage.setItem('login_step', val); },
    get email() { return sessionStorage.getItem('pending_email') || ''; },
    set email(val) { sessionStorage.setItem('pending_email', val); }
};

const ViewManager = {
    render() {
        const emailForm = document.getElementById('emailForm');
        const otpForm = document.getElementById('otpForm');
        
        if (state.step === 'otp') {
            if (emailForm) emailForm.style.display = 'none';
            if (otpForm) otpForm.style.display = 'block';
            startCountdownTimer(60);
        } else {
            if (emailForm) emailForm.style.display = 'block';
            if (otpForm) otpForm.style.display = 'none';
        }

        const errEl = document.getElementById('errorMessage');
        if (errEl) errEl.textContent = "";
    }
};

function startCountdownTimer(durationSeconds) {
    if (otpIntervalId) clearInterval(otpIntervalId);
    if (!otpTimer) return;

    let timeRemaining = durationSeconds;
    function tick() {
        if (timeRemaining <= 0) {
            clearInterval(otpIntervalId);
            otpTimer.textContent = "Code expired. Please request a new one.";
            otpTimer.style.color = "red";
            return;
        }
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        otpTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        otpTimer.style.color = "";
        timeRemaining--;
    }
    tick();
    otpIntervalId = setInterval(tick, 1000);
}

async function handleSendOTP(event) {
    event.preventDefault();
    const emailInput = document.getElementById('emailInput');
    const targetEmail = emailInput ? emailInput.value.trim() : '';
    if (!targetEmail) return;
    
    try {
        await apiPost('/request-otp', { email_address: targetEmail });
        state.email = targetEmail;
        state.step = 'otp';
        ViewManager.render();
    } catch (err) {
        const errContainer = document.getElementById('errorMessage');
        if (errContainer) errContainer.textContent = err.message;
    }
}

async function handleVerifyOTP(event) {
    event.preventDefault();
    const otpInput = document.getElementById('otpInput');
    const code = otpInput ? otpInput.value.trim() : '';
    const errorDisplay = document.getElementById('errorMessage');
    if (errorDisplay) errorDisplay.textContent = "";
    
    try {
        const response = await apiPost('/verify-otp', { email_address: state.email, otp_code: code });
        
        if (response.status === "success" || response.success) {
            if (otpIntervalId) clearInterval(otpIntervalId);
    
            // Fixed ReferenceError by using state.email instead of undefined emailInput.value
            sessionStorage.setItem("verified_email", state.email);
            localStorage.setItem("user_email", state.email);
            sessionStorage.removeItem('pending_email');
            sessionStorage.removeItem('login_step');
    
            window.location.href = "/payment"; 
        }
    } catch (err) {
        if (errorDisplay) errorDisplay.textContent = err.message;
        if (otpInput) otpInput.value = '';
    }
}

window.addEventListener('DOMContentLoaded', ViewManager.render);