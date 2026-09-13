document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("staffLoginForm");
    if (!form) return;

    // Dynamically inject OTP verification container
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
            </div>
            <button type="button" id="confirmStaffOtpBtn" 
                    class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-900 font-bold py-3 rounded-lg transition shadow-lg shadow-emerald-500/20">
                Confirm OTP & Log In
            </button>
        `;
        form.appendChild(otpSection);
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.textContent = "Send Staff OTP";

    let authSessionData = null;

    // STEP 1: Validate staff password & dispatch OTP
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

            // 1. Verify credentials against staff login endpoint
            const loginRes = await fetch("/api/staff/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const loginData = await loginRes.json();
            if (!loginRes.ok) {
                alert("Login failed: " + (loginData.detail || "Invalid credentials"));
                submitBtn.disabled = false;
                submitBtn.textContent = "Send Staff OTP";
                return;
            }

            // Cache staff profile details for post-OTP setup
            authSessionData = loginData;

            // 2. Dispatch OTP email
            submitBtn.textContent = "Sending Verification Email...";
            const otpRes = await fetch("/api/auth/request-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email_address: email })
            });

            if (otpRes.ok) {
                alert(`OTP code dispatched to ${email}. Check your inbox!`);
                submitBtn.classList.add("hidden");
                otpSection.classList.remove("hidden");
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

    // STEP 2: Verify OTP and proceed to dashboard
    document.getElementById("confirmStaffOtpBtn").addEventListener("click", async () => {
        const email = document.getElementById("loginEmail").value.trim();
        const otpCode = document.getElementById("staffOtpCode").value.trim();

        if (otpCode.length !== 6) {
            alert("Please enter the 6-digit verification code sent to your email.");
            return;
        }

        try {
            const verifyRes = await fetch("/api/auth/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email_address: email, otp_code: otpCode })
            });

            const verifyData = await verifyRes.json();

            if (verifyRes.ok && authSessionData) {
                // Save staff details to storage
                localStorage.setItem("staff_id", authSessionData.staff_id);
                localStorage.setItem("staff_email", authSessionData.email);
                localStorage.setItem("assigned_pincode", authSessionData.assigned_pincode);
                
                alert("Staff verification successful!");
                window.location.href = "/staff-dashboard";
            } else {
                alert("OTP verification failed: " + (verifyData.detail || "Invalid code"));
            }
        } catch (err) {
            console.error("OTP verification error:", err);
            alert("Failed to confirm OTP verification code.");
        }
    });
});