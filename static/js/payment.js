document.addEventListener("DOMContentLoaded", async () => {
    // 1. Check Session Authentication (Cookie or Storage Fallback)
    const hasCookie = document.cookie.includes("session_authenticated=true");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");
    const userId = localStorage.getItem("user_id");

    if (!hasCookie && !verifiedEmail && !userId) {
        window.location.href = "/login";
        return;
    }

    // 2. Fetch User Profile Data
    if (userId || verifiedEmail) {
        try {
            const param = userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;
            const response = await fetch(`/api/user/profile?${param}`);
            const result = await response.json();

            if (response.ok && result.profile) {
                document.getElementById("profileName").textContent = result.profile.full_name;
                document.getElementById("profileEmail").textContent = result.profile.email;
            } else {
                fallbackProfileInfo(verifiedEmail);
            }
        } catch (err) {
            console.error("Failed to load user profile:", err);
            fallbackProfileInfo(verifiedEmail);
        }
    } else {
        fallbackProfileInfo(null);
    }
});

function fallbackProfileInfo(email) {
    const nameEl = document.getElementById("profileName");
    const emailEl = document.getElementById("profileEmail");
    
    if (nameEl) nameEl.textContent = "Eco User";
    if (emailEl) emailEl.textContent = email || "user@ecorecycle.com";
}