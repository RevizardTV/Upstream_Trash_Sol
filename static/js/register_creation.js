document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("profileForm");
    if (!form) return;

    // Inject OTP UI elements if not present in the HTML template
    let otpSection = document.getElementById("otpSection");
    if (!otpSection) {
        otpSection = document.createElement("div");
        otpSection.id = "otpSection";
        otpSection.className = "hidden space-y-4 mt-4 pt-4 border-t border-slate-700";
        otpSection.innerHTML = `
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Enter 6-Digit OTP Code</label>
                <input type="text" id="otpCode" maxlength="6" placeholder="123456" 
                       class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white font-mono text-center text-lg tracking-widest focus:outline-none focus:border-emerald-500">
            </div>
            <button type="button" id="verifyAndSubmitBtn" 
                    class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-900 font-bold py-3 rounded-lg transition shadow-lg shadow-emerald-500/20">
                Verify OTP & Complete Registration
            </button>
        `;
        form.appendChild(otpSection);
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.textContent = "Send Verification Code";

    let isOtpSent = false;

    // STEP 1: Send OTP to user's email
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (isOtpSent) return;

        const email = document.getElementById("email").value.trim();
        if (!email) {
            alert("Please provide a valid email address.");
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = "Sending Code...";

            const res = await fetch("/api/auth/request-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email_address: email })
            });

            const data = await res.json();

            if (res.ok) {
                alert("Verification code sent to your email!");
                isOtpSent = true;
                submitBtn.classList.add("hidden");
                otpSection.classList.remove("hidden");
            } else {
                alert("OTP Request Failed: " + (data.detail || "Unable to send code."));
                submitBtn.disabled = false;
                submitBtn.textContent = "Send Verification Code";
            }
        } catch (err) {
            console.error("OTP generation error:", err);
            alert("Failed to communicate with authentication server.");
            submitBtn.disabled = false;
            submitBtn.textContent = "Send Verification Code";
        }
    });

    // STEP 2: Verify OTP and save profile
    document.getElementById("verifyAndSubmitBtn").addEventListener("click", async () => {
        const email = document.getElementById("email").value.trim();
        const otpCode = document.getElementById("otpCode").value.trim();

        if (otpCode.length !== 6) {
            alert("Please enter a valid 6-digit OTP code.");
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
                alert("Verification failed: " + (verifyData.detail || "Invalid code."));
                return;
            }

            // 2. Submit Profile Details
            const profilePayload = {
                email: email,
                full_name: document.getElementById("fullName")?.value || "",
                phone_number: document.getElementById("phoneNumber")?.value || "",
                city: document.getElementById("city")?.value || "",
                postal_code: document.getElementById("postalCode")?.value || "",
                premise_type: document.getElementById("premiseType")?.value || "house",
                household_size: parseInt(document.getElementById("householdSize")?.value || 1),
                upi_id: document.getElementById("upiId")?.value || null
            };

            const saveRes = await fetch("/api/auth/complete-profile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(profilePayload)
            });

            const saveData = await saveRes.json();

            if (saveRes.ok) {
                localStorage.setItem("user_id", saveData.user_id);
                localStorage.setItem("verified_email", email);
                alert("Email verified and profile created successfully!");
                window.location.href = "/payment";
            } else {
                alert("Profile saving failed: " + (saveData.detail || "Unknown error"));
            }
        } catch (err) {
            console.error("Profile creation error:", err);
            alert("Network error processing registration.");
        }
    });
});