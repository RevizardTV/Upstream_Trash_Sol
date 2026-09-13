document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("staffRegisterForm");
    if (!form) return;

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
            </div>
            <button type="button" id="confirmStaffRegOtpBtn" 
                    class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-900 font-bold py-3 rounded-lg transition shadow-lg shadow-emerald-500/20">
                Verify Code & Complete Registration
            </button>
        `;
        form.appendChild(otpSection);
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.textContent = "Send Authorization Code";

    let isOtpSent = false;

    // STEP 1: Request OTP email
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

            const data = await res.json();

            if (res.ok) {
                alert(`Authorization code sent to ${email}. Check your inbox!`);
                isOtpSent = true;
                submitBtn.classList.add("hidden");
                otpSection.classList.remove("hidden");
            } else {
                alert("Failed to send code: " + (data.detail || "Error requesting OTP"));
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

    // STEP 2: Verify OTP and complete registration
    document.getElementById("confirmStaffRegOtpBtn").addEventListener("click", async () => {
        const email = document.getElementById("email").value.trim();
        const otpCode = document.getElementById("staffRegOtpCode").value.trim();

        if (otpCode.length !== 6) {
            alert("Please enter the full 6-digit verification code.");
            return;
        }

        try {
            // 1. Verify OTP code
            const verifyRes = await fetch("/api/auth/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email_address: email, otp_code: otpCode })
            });

            const verifyData = await verifyRes.json();
            if (!verifyRes.ok) {
                alert("Verification failed: " + (verifyData.detail || "Invalid code"));
                return;
            }

            // 2. Submit Staff Account Data
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

            const regData = await regRes.json();

            if (regRes.ok) {
                alert("Staff account registered and verified successfully!");
                window.location.href = "/staff-login";
            } else {
                alert("Registration failed: " + (regData.detail || "Unknown error"));
            }
        } catch (err) {
            console.error("Staff registration final submit error:", err);
            alert("Failed to submit registration data.");
        }
    });
});