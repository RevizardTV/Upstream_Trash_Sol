document.addEventListener("DOMContentLoaded", async () => {
    const userId = localStorage.getItem("user_id");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");

    if (!userId && !verifiedEmail) {
        window.location.href = "/login";
        return;
    }

    const param = userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;

    try {
        const res = await fetch(`/api/recycling/reviewed-requests?${param}`);
        const data = await res.json();

        if (res.ok && data.status === "success") {
            const tbody = document.getElementById("reviewedTableBody");
            const totalEl = document.getElementById("approvedTotalDisplay");

            if (totalEl) totalEl.textContent = `₹${data.total_approved_earnings.toFixed(2)}`;
            tbody.innerHTML = "";

            if (data.entries.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-500">No reviewed requests found.</td></tr>`;
                return;
            }

            data.entries.forEach(entry => {
                const isApproved = entry.status === "approved";
                const statusBadge = isApproved
                    ? `<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">Approved</span>`
                    : `<span class="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">Declined</span>`;

                const tr = document.createElement("tr");
                tr.className = "border-b border-slate-700/40 hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="py-3.5 px-4 font-mono text-slate-400">#${entry.entry_id}</td>
                    <td class="py-3.5 px-4 font-semibold text-white capitalize">${entry.waste_category}</td>
                    <td class="py-3.5 px-4 font-mono text-slate-300">${entry.weight_kg.toFixed(2)} kg</td>
                    <td class="py-3.5 px-4 font-bold ${isApproved ? 'text-emerald-400' : 'text-slate-400'}">₹${entry.payout_amount.toFixed(2)}</td>
                    <td class="py-3.5 px-4">${statusBadge}</td>
                    <td class="py-3.5 px-4 text-right text-xs text-slate-400">${entry.rejection_reason || 'N/A'}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Failed to load reviewed requests:", err);
    }
});