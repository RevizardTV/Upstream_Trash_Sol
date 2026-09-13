document.addEventListener("DOMContentLoaded", async () => {
    const userId = localStorage.getItem("user_id");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");

    if (!userId && !verifiedEmail) {
        window.location.href = "/login";
        return;
    }

    try {
        const param = userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;
        const response = await fetch(`/api/recycling/summary?${param}`);
        const result = await response.json();

        if (response.ok && result.status === "success") {
            // Update Dashboard Metrics
            document.getElementById("totalEarnings").textContent = `₹${result.total_earnings.toFixed(2)}`;
            document.getElementById("pendingRelease").textContent = `₹${result.pending_release.toFixed(2)}`;
            document.getElementById("ecoCredits").textContent = `${result.eco_credits} pts`;

            // Filter pending entries for the queue card count
            const pendingCount = result.entries.filter(e => e.status === "pending").length;
            const cardEl = document.getElementById("pendingCardCount");
            if (cardEl) cardEl.textContent = `View ${pendingCount} Pending`;
        }
    } catch (err) {
        console.error("Failed to load metrics:", err);
    }
});