let currentUser = null;

function switchTab(viewId) {
    const panels = document.querySelectorAll('.view-panel');
    panels.forEach(panel => panel.classList.add('hidden'));

    const target = document.getElementById(viewId);
    if (target) {
        target.classList.remove('hidden');
    }

    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
        if (btn.getAttribute('data-view') === viewId) {
            btn.classList.add('bg-slate-800', 'text-white');
            btn.classList.remove('text-slate-400');
        } else {
            btn.classList.remove('bg-slate-800', 'text-white');
            btn.classList.add('text-slate-400');
        }
    });

    if (viewId === 'view-pending') fetchPendingPayments();
    if (viewId === 'view-reviewed') fetchReviewedRequests();
    if (viewId === 'view-options') fetchUserSummary();
}

const categoryTips = {
    plastic: "Ensure bottles are rinsed and flattened. Caps can be included.",
    metal: "Separate aluminum cans from heavy steel scrap for accurate weighing.",
    paper: "Keep cardboard dry and flattened. Waxed milk cartons are not accepted.",
    ewaste: "Disconnect batteries and salvage high-value circuit boards separately where allowed.",
    landfill: "Non-recyclable waste incurs a PAYT tipping fee of ₹12/kg."
};

function showTip(category) {
    const infoContainer = document.getElementById('inlineCategoryInfo');
    const titleEl = document.getElementById('inlineInfoTitle');
    const contentEl = document.getElementById('inlineInfoContent');

    if (infoContainer && categoryTips[category]) {
        titleEl.textContent = `${category.toUpperCase()} Optimization & Value Guide`;
        contentEl.textContent = categoryTips[category];
        infoContainer.classList.remove('hidden');
    }
}

function updateLiveCalculation() {
    const selectedMaterial = document.querySelector('input[name="material"]:checked');
    const weightInput = document.getElementById('weightInput');
    const totalDisplay = document.getElementById('estimatedTotal');

    if (!selectedMaterial || !weightInput || !totalDisplay) return;

    const rate = parseFloat(selectedMaterial.getAttribute('data-rate')) || 0;
    const type = selectedMaterial.getAttribute('data-type');
    const weight = parseFloat(weightInput.value) || 0;

    const total = rate * weight;

    if (type === 'charge') {
        totalDisplay.textContent = `₹${Math.abs(total).toFixed(2)} (Disposal Fee)`;
        totalDisplay.className = "text-lg font-bold text-rose-400";
    } else {
        totalDisplay.textContent = `₹${total.toFixed(2)} (Payout)`;
        totalDisplay.className = "text-lg font-bold text-emerald-400";
    }
}

async function loadUserProfile() {
    const storedEmail = localStorage.getItem('user_email') || sessionStorage.getItem('user_email');
    if (!storedEmail) {
        document.getElementById('profileName').textContent = "User Session";
        document.getElementById('profileEmail').textContent = "No session email set";
        return;
    }

    try {
        const response = await fetch(`/api/user/profile?email=${encodeURIComponent(storedEmail)}`);
        if (!response.ok) throw new Error("Failed to load user profile");
        
        const data = await response.json();
        if (data.status === 'success' && data.profile) {
            currentUser = data.profile;
            document.getElementById('profileName').textContent = currentUser.full_name || "Eco Member";
            document.getElementById('profileEmail').textContent = currentUser.email || storedEmail;
            
            const upiDisplay = document.getElementById('userUpiDisplay');
            if (upiDisplay) {
                upiDisplay.textContent = currentUser.upi_id ? `UPI: ${currentUser.upi_id}` : '';
            }
            
            fetchUserSummary();
        }
    } catch (err) {
        console.error("Error fetching profile:", err);
        document.getElementById('profileName').textContent = "Profile Error";
    }
}

async function fetchUserSummary() {
    if (!currentUser) return;

    try {
        const res = await fetch(`/api/recycling/summary?user_id=${currentUser.id}`);
        if (!res.ok) return;

        const data = await res.json();
        
        document.getElementById('totalEarnings').textContent = `₹${parseFloat(data.total_earnings || 0).toFixed(2)}`;
        document.getElementById('pendingRelease').textContent = `₹${parseFloat(data.pending_release || 0).toFixed(2)}`;
        document.getElementById('ecoCredits').textContent = `${data.eco_credits || 0} pts`;
        
        const pendingCount = (data.entries || []).filter(e => e.status === 'pending').length;
        const pendingCard = document.getElementById('pendingCardCount');
        if (pendingCard) pendingCard.textContent = `View ${pendingCount} Pending`;
    } catch (err) {
        console.error("Failed to load user summary:", err);
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    if (!currentUser) {
        alert("User profile not loaded properly. Please log in again.");
        return;
    }

    const selectedMaterial = document.querySelector('input[name="material"]:checked');
    const weightInput = document.getElementById('weightInput');
    const stationInput = document.getElementById('stationInput');
    const payoutMethodSelect = document.getElementById('payoutMethodSelect');

    if (!selectedMaterial || !weightInput || !weightInput.value) {
        alert("Please select a category and fill in weight.");
        return;
    }

    const rate = parseFloat(selectedMaterial.getAttribute('data-rate')) || 0;
    const weight = parseFloat(weightInput.value) || 0;
    const payoutAmount = rate * weight;

    const payload = {
        user_id: currentUser.id,
        waste_category: selectedMaterial.getAttribute('data-category') || selectedMaterial.value,
        weight_kg: weight,
        payout_amount: payoutAmount,
        station_id: stationInput ? stationInput.value || "STATION-GENERIC" : "STATION-GENERIC",
        payout_method: payoutMethodSelect ? payoutMethodSelect.value : "upi"
    };

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting...`;

    try {
        const res = await fetch('/api/recycling/entry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            alert("Waste entry registered successfully!");
            document.getElementById('paymentRegisterForm').reset();
            updateLiveCalculation();
            fetchUserSummary();
            switchTab('view-pending');
        } else {
            alert(`Error: ${data.detail || "Submission failed"}`);
        }
    } catch (err) {
        console.error("Error submitting entry:", err);
        alert("Failed to reach server. Please check your network connection.");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Submit Entry`;
    }
}

async function fetchPendingPayments() {
    if (!currentUser) return;
    
    const tbody = document.getElementById('pendingPaymentsTableBody');
    const totalPendingDisplay = document.getElementById('totalPendingAmount');

    try {
        const res = await fetch(`/api/recycling/pending-payments?user_id=${currentUser.id}`);
        const data = await res.json();

        if (res.ok && data.entries) {
            totalPendingDisplay.textContent = `₹${parseFloat(data.total_pending_amount || 0).toFixed(2)}`;
            
            if (data.entries.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-slate-400">No pending transactions in queue.</td></tr>`;
                return;
            }

            tbody.innerHTML = data.entries.map(entry => {
                const isCharge = entry.payout_amount < 0;
                const formattedAmt = `${isCharge ? '-' : ''}₹${Math.abs(entry.payout_amount).toFixed(2)}`;
                const amtClass = isCharge ? 'text-rose-400 font-semibold' : 'text-emerald-400 font-semibold';
                const createdDate = entry.created_at ? new Date(entry.created_at).toLocaleString() : 'Recent';

                return `
                    <tr class="hover:bg-slate-800/40 transition">
                        <td class="p-4 font-mono text-xs text-slate-300">#${entry.entry_id}</td>
                        <td class="p-4 font-medium text-white">${entry.waste_category}</td>
                        <td class="p-4 text-slate-300">${entry.weight_kg} kg</td>
                        <td class="p-4 ${amtClass}">${formattedAmt}</td>
                        <td class="p-4 text-xs text-slate-400">${createdDate}</td>
                    </tr>
                `;
            }).join('');
        }
    } catch (err) {
        console.error("Failed to load pending payments:", err);
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-rose-400">Failed to retrieve entries.</td></tr>`;
    }
}

async function fetchReviewedRequests() {
    if (!currentUser) return;

    const tbody = document.getElementById('reviewedTableBody');
    const approvedTotalDisplay = document.getElementById('approvedTotalDisplay');

    try {
        const res = await fetch(`/api/recycling/reviewed-requests?user_id=${currentUser.id}`);
        const data = await res.json();

        if (res.ok && data.entries) {
            approvedTotalDisplay.textContent = `₹${parseFloat(data.total_approved_earnings || 0).toFixed(2)}`;

            if (data.entries.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-500">No reviewed entries found.</td></tr>`;
                return;
            }

            tbody.innerHTML = data.entries.map(e => {
                const isApproved = e.status === 'approved';
                const statusBadge = isApproved 
                    ? `<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs px-2.5 py-1 rounded-full font-medium inline-flex items-center gap-1.5">
                        <i class="fa-solid fa-circle-check text-[10px]"></i> Approved
                       </span>`
                    : `<span class="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs px-2.5 py-1 rounded-full font-medium inline-flex items-center gap-1.5" title="${e.rejection_reason || ''}">
                        <i class="fa-solid fa-circle-xmark text-[10px]"></i> Declined
                       </span>`;

                const recordContent = isApproved
                    ? `<a href="/api/recycling/receipt/${e.entry_id}" target="_blank" class="text-xs text-emerald-400 hover:text-emerald-300 border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 rounded-lg transition inline-flex items-center justify-center gap-2 font-medium">
                        <i class="fa-solid fa-file-arrow-down text-sm shrink-0"></i> <span>Receipt</span>
                      </a>`
                    : `<span class="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg inline-flex items-center gap-2 font-medium max-w-xs text-left" title="${e.rejection_reason || 'Declined'}">
                        <i class="fa-solid fa-triangle-exclamation text-xs shrink-0"></i>
                        <span class="truncate">${e.rejection_reason || 'Declined'}</span>
                      </span>`;

                return `
                    <tr class="border-b border-slate-700/40 hover:bg-slate-800/30 transition">
                        <td class="py-3.5 px-4 font-mono text-xs text-slate-400">#${e.entry_id}</td>
                        <td class="py-3.5 px-4 font-medium text-white">${e.waste_category}</td>
                        <td class="py-3.5 px-4 text-slate-300">${e.weight_kg} kg</td>
                        <td class="py-3.5 px-4 font-semibold text-emerald-400">₹${parseFloat(e.payout_amount).toFixed(2)}</td>
                        <td class="py-3.5 px-4">${statusBadge}</td>
                        <td class="py-3.5 px-4 text-right flex justify-end items-center">${recordContent}</td>
                    </tr>
                `;
            }).join('');
        }
    } catch (err) {
        console.error("Failed to load reviewed requests:", err);
        tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-rose-400">Failed to load reviewed requests.</td></tr>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.getAttribute('data-view');
            if (view) switchTab(view);
        });
    });

    const weightInput = document.getElementById('weightInput');
    if (weightInput) {
        weightInput.addEventListener('input', updateLiveCalculation);
    }

    document.querySelectorAll('input[name="material"]').forEach(radio => {
        radio.addEventListener('change', updateLiveCalculation);
    });

    const registerForm = document.getElementById('paymentRegisterForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleFormSubmit);
    }

    loadUserProfile();
    switchTab('view-options');
});

// Fixed logout routine to clear local and session storages
function logout() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/login';
}