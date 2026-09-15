document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("staffLoginForm");
    if (!form) return;

    let timerInterval = null;
    let authSessionData = null;

    let otpSection = document.getElementById("staffOtpSection");
    if (!otpSection) {
        otpSection = document.createElement("div");
        otpSection.id = "staffOtpSection";
        otpSection.className = "hidden space-y-4 mt-4 pt-4 border-t border-slate-700";
        otpSection.innerHTML = `
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Enter 6-Digit Staff OTP</label>
                <input type="text" id="staffOtpCode" maxlength="6" placeholder="123456" 
                       class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white font-mono text-center text-lg tracking-widest focus:outline-none focus:border-emerald-500">
                <p id="staffLoginTimerText" class="text-xs text-slate-400 mt-2 font-mono text-center">Expires in 60s | Max 3 Attempts Allowed</p>
            </div>
            <button type="button" id="confirmStaffOtpBtn" 
                    class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-700 text-slate-900 font-bold py-3 rounded-lg transition shadow-lg shadow-emerald-500/20">
                Confirm OTP & Log In
            </button>
        `;
        form.appendChild(otpSection);
    }

    const submitBtn = document.getElementById("staffLoginSubmitBtn");

    function startTimer() {
        let timeLeft = 60;
        const timerDisplay = document.getElementById("staffLoginTimerText");
        const verifyBtn = document.getElementById("confirmStaffOtpBtn");

        verifyBtn.disabled = false;
        timerDisplay.className = "text-xs text-slate-400 mt-2 font-mono text-center";

        if (timerInterval) clearInterval(timerInterval);

        timerInterval = setInterval(() => {
            timeLeft--;
            timerDisplay.textContent = `Expires in ${timeLeft}s | Max 3 Attempts Allowed`;

            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                timerDisplay.textContent = "Code expired. Please request a new OTP.";
                timerDisplay.className = "text-xs text-rose-400 mt-2 font-mono text-center";
                verifyBtn.disabled = true;
                submitBtn.classList.remove("hidden");
                submitBtn.disabled = false;
                submitBtn.textContent = "Resend Staff OTP";
            }
        }, 1000);
    }

    // STEP 1: Verify Password & Request OTP
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;

        if (!email || !password) {
            alert("Please fill in both email and password.");
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = "Verifying Credentials...";

            const loginRes = await fetch("/api/staff/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email, password })
            });

            const loginData = await loginRes.json();
            if (!loginRes.ok) {
                alert("Login failed: " + (loginData.detail || "Invalid credentials"));
                submitBtn.disabled = false;
                submitBtn.textContent = "Send Staff OTP";
                return;
            }

            authSessionData = loginData;

            submitBtn.textContent = "Sending Verification Email...";
            const otpRes = await fetch("/api/auth/request-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email_address: email, type: "staff" })
            });

            if (otpRes.ok) {
                alert(`OTP code dispatched to ${email}. Check your inbox!`);
                submitBtn.classList.add("hidden");
                otpSection.classList.remove("hidden");
                startTimer();
            } else {
                const otpErr = await otpRes.json();
                alert("Failed to send OTP: " + (otpErr.detail || "Server error"));
                submitBtn.disabled = false;
                submitBtn.textContent = "Send Staff OTP";
            }
        } catch (err) {
            console.error("Staff authentication error:", err);
            alert("Network issue during login process.");
            submitBtn.disabled = false;
            submitBtn.textContent = "Send Staff OTP";
        }
    });

    // STEP 2: Confirm OTP & Authorize Session
    document.getElementById("confirmStaffOtpBtn").addEventListener("click", async () => {
        const email = document.getElementById("loginEmail").value.trim();
        const otpCode = document.getElementById("staffOtpCode").value.trim();
        const timerDisplay = document.getElementById("staffLoginTimerText");

        if (otpCode.length !== 6) {
            alert("Please enter the 6-digit verification code.");
            return;
        }

        try {
            const verifyRes = await fetch("/api/auth/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email_address: email, otp_code: otpCode })
            });

            const verifyData = await verifyRes.json();

            if (verifyRes.ok && authSessionData) {
                if (timerInterval) clearInterval(timerInterval);
                localStorage.setItem("staff_id", authSessionData.staff_id);
                localStorage.setItem("staff_email", authSessionData.email);
                localStorage.setItem("assigned_pincode", authSessionData.assigned_pincode);
                
                alert("Staff verification successful!");
                window.location.href = "/staff-dashboard";
            } else {
                timerDisplay.textContent = verifyData.detail || "Invalid code.";
                timerDisplay.className = "text-xs text-rose-400 mt-2 font-mono text-center";
            }
        } catch (err) {
            console.error("OTP verification error:", err);
            alert("Failed to confirm OTP verification code.");
        }
    });
});