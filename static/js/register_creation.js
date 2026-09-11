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

const regState = {
    get step() { return sessionStorage.getItem('reg_step') || 'form'; },
    set step(val) { sessionStorage.setItem('reg_step', val); },
    get profileData() { 
        const raw = sessionStorage.getItem('temp_profile_data');
        return raw ? JSON.parse(raw) : null;
    },
    set profileData(val) { 
        sessionStorage.setItem('temp_profile_data', JSON.stringify(val)); 
    }
};

const ViewManager = {
    render() {
        const profileForm = document.getElementById('profileRegisterForm');
        const otpForm = document.getElementById('otpForm');
        
        if (regState.step === 'otp') {
            if (profileForm) profileForm.style.display = 'none';
            if (otpForm) otpForm.style.display = 'block';
            startCountdownTimer(60);
        } else {
            if (profileForm) profileForm.style.display = 'block';
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
            otpTimer.textContent = "OTP expired. Please refresh and re-submit.";
            otpTimer.style.color = "#f87171";
            return;
        }
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        otpTimer.textContent = `OTP Expires in ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        otpTimer.style.color = "";
        timeRemaining--;
    }
    tick();
    otpIntervalId = setInterval(tick, 1000);
}

async function handleProfileSubmit(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('submitBtn');
    const errContainer = document.getElementById('errorMessage');
    if (errContainer) errContainer.textContent = "";

    const payload = {
        email: document.getElementById("email").value.trim(),
        full_name: document.getElementById("fullName").value.trim(),
        phone_number: document.getElementById("phoneNumber").value.trim(),
        city: document.getElementById("city").value.trim(),
        postal_code: document.getElementById("postalCode").value.trim(),
        premise_type: document.getElementById("premiseType").value,
        household_size: parseInt(document.getElementById("householdSize").value, 10),
        upi_id: document.getElementById("upiId").value.trim() || null
    };

    submitBtn.disabled = true;
    submitBtn.innerText = "Dispatching OTP...";

    try {
        await apiPost('/request-otp', { email_address: payload.email });
        
        regState.profileData = payload;
        regState.step = 'otp';
        ViewManager.render();
    } catch (err) {
        if (errContainer) errContainer.textContent = err.message;
        submitBtn.disabled = false;
        submitBtn.innerText = "Send OTP & Register Profile";
    }
}

async function handleVerifyAndSaveProfile(event) {
    event.preventDefault();
    const code = document.getElementById('otpInput').value.trim();
    const errorDisplay = document.getElementById('errorMessage');
    const alertBox = document.getElementById('statusAlert');
    const verifyBtn = document.getElementById('verifyBtn');
    
    if (errorDisplay) errorDisplay.textContent = "";

    const cachedData = regState.profileData;
    if (!cachedData || !cachedData.email) {
        if (errorDisplay) errorDisplay.textContent = "Profile session expired. Please reload and submit again.";
        return;
    }

    verifyBtn.disabled = true;
    verifyBtn.innerText = "Verifying & Saving Profile...";

    try {
        // Step A: Verify OTP
        await apiPost('/verify-otp', { 
            email_address: cachedData.email, 
            otp_code: code 
        });

        // Step B: Complete profile and get user_id
        const result = await apiPost('/complete-profile', cachedData);

        if (otpIntervalId) clearInterval(otpIntervalId);

        // Save Auth Identifiers to both storage layers
        sessionStorage.setItem("verified_email", cachedData.email);
        localStorage.setItem("verified_email", cachedData.email);
        
        if (result.user_id) {
            localStorage.setItem("user_id", result.user_id);
        }

        // Cleanup temporary registration session state
        sessionStorage.removeItem('temp_profile_data');
        sessionStorage.removeItem('reg_step');

        if (alertBox) {
            alertBox.className = "mb-4 p-3 rounded-xl text-xs text-center border bg-emerald-500/20 border-emerald-500 text-emerald-300";
            alertBox.innerText = "Profile verified and created successfully! Redirecting to payment dashboard...";
            alertBox.classList.remove("hidden");
        }

        setTimeout(() => {
            window.location.href = "/payment";
        }, 500);

    } catch (err) {
        if (errorDisplay) errorDisplay.textContent = err.message;
        verifyBtn.disabled = false;
        verifyBtn.innerText = "Verify OTP & Finalize Profile";
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const savedEmail = urlParams.get("email") || sessionStorage.getItem("verified_email");
    const emailField = document.getElementById("email");
    if (savedEmail && emailField) {
        emailField.value = savedEmail;
    }

    ViewManager.render();
});