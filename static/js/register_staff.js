document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("staffRegisterForm");
    if (!form) return;

    let timerInterval = null;
    let isOtpSent = false;

    // Dynamically inject OTP verification container
    let otpSection = document.getElementById("staffRegOtpSection");
    if (!otpSection) {
        otpSection = document.createElement("div");
        otpSection.id = "staffRegOtpSection";
        otpSection.className = "hidden space-y-4 mt-4 pt-4 border-t border-slate-700";
        otpSection.innerHTML = `
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Enter 6-Digit Staff Verification Code</label>
                <input type="text" id="staffRegOtpCode" maxlength="6" placeholder="123456" 
                       class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white font-mono text-center text-lg tracking-widest focus:outline-none focus:border-emerald-500">
                <p id="staffRegTimerText" class="text-xs text-slate-400 mt-2 font-mono text-center">Expires in 60s | Max 3 Attempts Allowed</p>
            </div>
            <button type="button" id="confirmStaffRegOtpBtn" 
                    class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-700 text-slate-900 font-bold py-3 rounded-lg transition shadow-lg shadow-emerald-500/20">
                Verify Code & Complete Registration
            </button>
        `;
        form.appendChild(otpSection);
    }

    const submitBtn = document.getElementById("submitBtn");

    function startTimer() {
        let timeLeft = 60;
        const timerDisplay = document.getElementById("staffRegTimerText");
        const verifyBtn = document.getElementById("confirmStaffRegOtpBtn");

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
                isOtpSent = false;
                submitBtn.classList.remove("hidden");
                submitBtn.disabled = false;
                submitBtn.textContent = "Resend Authorization Code";
            }
        }, 1000);
    }

    // STEP 1: Request OTP
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (isOtpSent) return;

        const email = document.getElementById("email").value.trim();
        const fullName = document.getElementById("fullName").value.trim();
        const assignedPincode = document.getElementById("assignedPincode").value.trim();
        const password = document.getElementById("password").value;

        if (!email || !fullName || !assignedPincode || !password) {
            alert("Please fill in all registration fields.");
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = "Sending Verification Code...";

            const res = await fetch("/api/auth/request-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email_address: email, type: "staff" })
            });

            const contentType = res.headers.get("content-type");
            let data = {};
            if (contentType && contentType.includes("application/json")) {
                data = await res.json();
            } else {
                const textErr = await res.text();
                data = { detail: textErr || `Server returned HTTP ${res.status}` };
            }

            if (res.ok) {
                alert(`Authorization code sent to ${email}. Check your inbox!`);
                isOtpSent = true;
                submitBtn.classList.add("hidden");
                otpSection.classList.remove("hidden");
                startTimer();
            } else {
                alert("Failed to send code: " + (data.detail || "Rate limit or server error."));
                submitBtn.disabled = false;
                submitBtn.textContent = "Send Authorization Code";
            }
        } catch (err) {
            console.error("Staff registration OTP error:", err);
            alert("Network error. Unable to dispatch verification code.");
            submitBtn.disabled = false;
            submitBtn.textContent = "Send Authorization Code";
        }
    });

    // STEP 2: Verify OTP and Register Staff
    document.getElementById("confirmStaffRegOtpBtn").addEventListener("click", async () => {
        const email = document.getElementById("email").value.trim();
        const otpCode = document.getElementById("staffRegOtpCode").value.trim();
        const timerDisplay = document.getElementById("staffRegTimerText");

        if (otpCode.length !== 6) {
            alert("Please enter the full 6-digit verification code.");
            return;
        }

        try {
            // 1. Verify OTP
            const verifyRes = await fetch("/api/auth/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email_address: email, otp_code: otpCode })
            });

            const verifyData = await verifyRes.json();
            if (!verifyRes.ok) {
                timerDisplay.textContent = verifyData.detail || "Invalid code.";
                timerDisplay.className = "text-xs text-rose-400 mt-2 font-mono text-center";
                return;
            }

            // 2. Register Staff Account
            const payload = {
                full_name: document.getElementById("fullName").value.trim(),
                email: email,
                assigned_pincode: document.getElementById("assignedPincode").value.trim(),
                password: document.getElementById("password").value
            };

            const regRes = await fetch("/api/staff/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const contentType = regRes.headers.get("content-type");
            let regData = {};
            if (contentType && contentType.includes("application/json")) {
                regData = await regRes.json();
            } else {
                const rawText = await regRes.text();
                regData = { detail: rawText || "Server Internal Error" };
            }

            if (regRes.ok) {
                if (timerInterval) clearInterval(timerInterval);
                alert("Staff account registered and verified successfully!");
                window.location.href = "/staff-login";
            } else {
                alert("Registration failed: " + (regData.detail || "Unknown error"));
            }
        } catch (err) {
            console.error("Staff registration submit error:", err);
            alert("Failed to submit registration data.");
        }
    });
});