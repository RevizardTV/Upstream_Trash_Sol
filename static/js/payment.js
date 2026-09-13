document.addEventListener("DOMContentLoaded", async () => {
    const userId = localStorage.getItem("user_id");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");

    if (!userId && !verifiedEmail) {
        window.location.href = "/login";
        return;
    }

    const param = userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;

    // 1. Fetch & Load Profile Name
    try {
        const profileRes = await fetch(`/api/user/profile?${param}`);
        if (profileRes.ok) {
            const profileData = await profileRes.json();
            const name = profileData.profile?.full_name || "User";
            
            // Try updating common DOM target IDs for the name element
            const nameTargets = ["profileName", "userName", "userDisplayName"];
            nameTargets.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = name;
            });
        }
    } catch (err) {
        console.error("Failed to load user profile name:", err);
    }

    // 2. Fetch Dashboard Metrics
    try {
        const response = await fetch(`/api/recycling/summary?${param}`);
        const result = await response.json();

        if (response.ok && result.status === "success") {
            const earningsEl = document.getElementById("totalEarnings");
            const pendingEl = document.getElementById("pendingRelease");
            const creditsEl = document.getElementById("ecoCredits");

            if (earningsEl) earningsEl.textContent = `₹${result.total_earnings.toFixed(2)}`;
            if (pendingEl) pendingEl.textContent = `₹${result.pending_release.toFixed(2)}`;
            if (creditsEl) creditsEl.textContent = `${result.eco_credits} pts`;

            const pendingCount = result.entries.filter(e => e.status === "pending").length;
            const cardEl = document.getElementById("pendingCardCount");
            if (cardEl) cardEl.textContent = `View ${pendingCount} Pending`;
        }
    } catch (err) {
        console.error("Failed to load metrics:", err);
    }
});