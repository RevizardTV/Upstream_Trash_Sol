document.addEventListener("DOMContentLoaded", async () => {
    // Check authentication
    const userId = localStorage.getItem("user_id");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");

    if (!userId && !verifiedEmail) {
        window.location.href = "/login";
        return;
    }

    const tableBody = document.getElementById("pendingPaymentsTableBody");
    const totalDisplay = document.getElementById("totalPendingAmount");

    try {
        const param = userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;
        const response = await fetch(`/api/recycling/pending-payments?${param}`);
        const result = await response.json();

        if (!response.ok || result.status !== "success") {
            throw new Error(result.detail || "Failed to load pending payments.");
        }

        // Render Total Pending Amount
        if (totalDisplay) {
            totalDisplay.textContent = `₹${result.total_pending_amount.toFixed(2)}`;
        }

        // Render Table Rows
        if (tableBody) {
            if (result.entries.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-4 text-gray-400">
                            No pending recycling payouts found.
                        </td>
                    </tr>`;
                return;
            }

                tableBody.innerHTML = result.entries.map(entry => {
                const formattedDate = entry.created_at 
                    ? new Date(entry.created_at).toLocaleDateString() 
                    : "N/A";

                return `
                    <tr class="border-b border-slate-700/50 hover:bg-slate-800/40">
                        <td class="p-4 text-emerald-400 font-mono font-medium">#${entry.entry_id}</td>
                        <td class="p-4 text-slate-300 capitalize">${entry.waste_category}</td>
                        <td class="p-4 text-slate-300">${entry.weight_kg} kg</td>
                        <td class="p-4 font-bold text-emerald-400">₹${entry.payout_amount.toFixed(2)}</td>
                        <td class="p-4 text-slate-400 text-xs font-mono">${formattedDate}</td>
                    </tr>
                `;
            }).join("");
        }

    } catch (err) {
        console.error("Error fetching pending payments:", err);
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4 text-red-400">
                        Error loading entries: ${err.message}
                    </td>
                </tr>`;tableBody
        }
    }
});