document.addEventListener("DOMContentLoaded", () => {
    loadUserProfile();
    fetchPendingRequests();
    fetchReviewedRequests();
});

// Tab Switching Handler
function switchTab(tab) {
    const pendingView = document.getElementById('view-pending');
    const reviewedView = document.getElementById('view-reviewed');
    const pendingBtn = document.getElementById('tabPendingBtn');
    const reviewedBtn = document.getElementById('tabReviewedBtn');

    if (tab === 'pending') {
        pendingView.classList.remove('hidden');
        reviewedView.classList.add('hidden');
        pendingBtn.className = "pb-3 text-sm font-semibold border-b-2 border-emerald-400 text-emerald-400 flex items-center gap-2 transition";
        reviewedBtn.className = "pb-3 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 transition";
    } else {
        pendingView.classList.add('hidden');
        reviewedView.classList.remove('hidden');
        reviewedBtn.className = "pb-3 text-sm font-semibold border-b-2 border-emerald-400 text-emerald-400 flex items-center gap-2 transition";
        pendingBtn.className = "pb-3 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 transition";
    }
}

// Fetch Profile Details
async function loadUserProfile() {
    try {
        const res = await fetch('/api/user/profile');
        if (!res.ok) throw new Error('Failed to load profile');
        const data = await res.json();
        document.getElementById('userInfo').innerText = `Logged in as: ${data.username || 'User'}`;
    } catch (err) {
        console.error(err);
        document.getElementById('userInfo').innerText = 'User Session Active';
    }
}

// Fetch Pending Requests
async function fetchPendingRequests() {
    const tbody = document.getElementById('pendingTableBody');
    try {
        const res = await fetch('/api/recycling/pending');
        if (!res.ok) throw new Error('Failed to fetch pending requests');
        const data = await res.json();

        if (!data.entries || data.entries.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-500">No pending requests found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.entries.map(e => `
            <tr class="border-b border-slate-700/40 hover:bg-slate-800/30 transition">
                <td class="py-3 px-4 font-mono text-xs text-slate-400">#${e.entry_id}</td>
                <td class="py-3 px-4 font-medium text-white">${e.waste_category}</td>
                <td class="py-3 px-4 text-slate-300">${e.weight_kg} kg</td>
                <td class="py-3 px-4 font-semibold text-emerald-400">₹${parseFloat(e.payout_amount || 0).toFixed(2)}</td>
                <td class="py-3 px-4">
                    <span class="bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs px-2.5 py-1 rounded-full font-medium">
                        Pending
                    </span>
                </td>
                <td class="py-3 px-4 text-right">
                    <button onclick="cancelRequest(${e.entry_id})" class="text-xs text-rose-400 hover:text-rose-300 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg transition">
                        Cancel
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error(err);
        tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-rose-400">Failed to load data.</td></tr>`;
    }
}

// Fetch Reviewed Requests
async function fetchReviewedRequests() {
    const tbody = document.getElementById('reviewedTableBody');
    try {
        const res = await fetch('/api/recycling/reviewed');
        if (!res.ok) throw new Error('Failed to fetch reviewed requests');
        const data = await res.json();

        if (!data.entries || data.entries.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-500">No reviewed requests found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.entries.map(e => {
            const isApproved = e.status === 'approved';
            
            const statusBadge = isApproved 
                ? `<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs px-2.5 py-1 rounded-full font-medium">Approved</span>`
                : `<span class="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs px-2.5 py-1 rounded-full font-medium">Declined</span>`;

            // Record Column Logic: Receipt link for approved, Rejection reason for declined
            const recordContent = isApproved
                ? `<a href="/api/recycling/receipt/${e.entry_id}" target="_blank" class="text-xs text-emerald-400 hover:text-emerald-300 border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 rounded-lg transition inline-flex items-center gap-1">
                    <i class="fa-solid fa-file-arrow-down"></i> Receipt
                  </a>`
                : `<span class="text-xs text-rose-400/90 bg-rose-500/5 border border-rose-500/20 px-2.5 py-1 rounded-lg inline-block text-right" title="${e.rejection_reason || 'Declined'}">
                    <i class="fa-solid fa-circle-xmark mr-1"></i>${e.rejection_reason || 'Declined by officer'}
                  </span>`;

            return `
                <tr class="border-b border-slate-700/40 hover:bg-slate-800/30 transition">
                    <td class="py-3 px-4 font-mono text-xs text-slate-400">#${e.entry_id}</td>
                    <td class="py-3 px-4 font-medium text-white">${e.waste_category}</td>
                    <td class="py-3 px-4 text-slate-300">${e.weight_kg} kg</td>
                    <td class="py-3 px-4 font-semibold text-emerald-400">₹${parseFloat(e.payout_amount || 0).toFixed(2)}</td>
                    <td class="py-3 px-4">${statusBadge}</td>
                    <td class="py-3 px-4 text-right">${recordContent}</td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error(err);
        tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-rose-400">Failed to load data.</td></tr>`;
    }
}

// Cancel Request Handler
async function cancelRequest(entryId) {
    if (!confirm(`Are you sure you want to cancel entry #${entryId}?`)) return;

    try {
        const res = await fetch(`/api/recycling/cancel/${entryId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Cancellation failed');
        fetchPendingRequests();
    } catch (err) {
        console.error(err);
        alert('Failed to cancel request.');
    }
}