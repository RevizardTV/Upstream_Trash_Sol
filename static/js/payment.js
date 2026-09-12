document.addEventListener("DOMContentLoaded", async () => {
    // 1. Authenticate user access
    const hasCookie = document.cookie.includes("session_authenticated=true");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");
    const userId = localStorage.getItem("user_id");

    if (!hasCookie && !verifiedEmail && !userId) {
        window.location.href = "/login";
        return;
    }

    // 2. Fetch User Profile Info
    if (userId || verifiedEmail) {
        try {
            const param = userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;
            const response = await fetch(`/api/user/profile?${param}`);
            const result = await response.json();

            if (response.ok && result.profile) {
                const nameEl = document.getElementById("profileName");
                const emailEl = document.getElementById("profileEmail");
                if (nameEl) nameEl.textContent = result.profile.full_name;
                if (emailEl) emailEl.textContent = result.profile.email;
            }
        } catch (err) {
            console.error("Failed to load user profile:", err);
        }
    }

    // 3. Fetch Recycling Entries & Compute Live Earnings
    try {
        const param = userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;
        const response = await fetch(`/api/recycling/pending-payments?${param}`);
        const result = await response.json();

        if (response.ok && result.status === "success") {
            const pendingTotal = result.total_pending_amount || 0;
            const entriesCount = result.count || 0;

            // Compute total weight to calculate eco points (1 kg = 10 pts)
            const totalWeight = result.entries.reduce((sum, item) => sum + (parseFloat(item.weight_kg) || 0), 0);
            const ecoPoints = Math.round(totalWeight * 10);

            // Update UI Counters
            const totalEarningsEl = document.getElementById("totalEarnings");
            const pendingReleaseEl = document.getElementById("pendingRelease");
            const ecoCreditsEl = document.getElementById("ecoCredits");
            const pendingCardCountEl = document.getElementById("pendingCardCount");

            if (totalEarningsEl) totalEarningsEl.textContent = `₹${pendingTotal.toFixed(2)}`;
            if (pendingReleaseEl) pendingReleaseEl.textContent = `₹${pendingTotal.toFixed(2)}`;
            if (ecoCreditsEl) ecoCreditsEl.textContent = `${ecoPoints} pts`;
            if (pendingCardCountEl) pendingCardCountEl.textContent = `View ${entriesCount} Pending`;
        }
    } catch (err) {
        console.error("Failed to load recycling entries:", err);
    }
});