/**
 * EcoRecycle - Unified Single Page Application Controller
 */

// --- GLOBAL FETCH AUTHENTICATION INTERCEPTOR ---
(function () {
    const originalFetch = window.fetch;

    window.fetch = async function (...args) {
        const response = await originalFetch.apply(this, args);

        if (response.status === 401) {
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = "/login";
        }

        return response;
    };
})();

// 1. Tip Guidance Dictionary
const RECYCLING_TIPS = {
    plastic: "Separate PET bottles from soft films. Ensure items are clean and dry for maximum payout value.",
    metal: "Copper and aluminum offer top payouts. Clean off heavy rust or non-metal fittings to maintain grade value.",
    paper: "Flatten cardboard boxes and keep them dry. Wet paper adds heavy unusable weight.",
    ewaste: "Disconnect batteries and salvage high-value circuit boards separately where allowed.",
    landfill: "💡 Charge reduction tip: Thoroughly drain liquid & organic moisture before disposal. Water content inflates total mass and fee costs by up to 40%."
};

// --- AUTHENTICATION HELPERS ---
function getAuthParam() {
    const userId = localStorage.getItem("user_id");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");

    if (!userId && !verifiedEmail) {
        return "";
    }
    return userId ? `user_id=${encodeURIComponent(userId)}` : `email=${encodeURIComponent(verifiedEmail)}`;
}

window.logout = function() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/logout";
};

window.showTip = function(category) {
    const panel = document.getElementById("infoPanel");
    const title = document.getElementById("infoTitle");
    const content = document.getElementById("infoContent");

    if (panel && title && content) {
        title.textContent = category.toUpperCase() + " Optimization & Value Guide";
        content.textContent = RECYCLING_TIPS[category] || "No specialized tip for this category.";
        panel.classList.remove("hidden");
    }
};

// --- API DATA LOADERS ---
async function loadDashboardMetrics() {
    const param = getAuthParam();
    if (!param && !document.cookie.includes("session=")) {
        console.warn("[PaymentHub] Aborting loadDashboardMetrics: No active session/credentials found.");
        return;
    }

    const queryStr = param ? `?${param}` : "";

    try {
        const profileRes = await fetch(`/api/user/profile${queryStr}`);
        if (profileRes.ok) {
            const profileData = await profileRes.json();
            const profile = profileData.profile || {};
            const name = profile.full_name || "User";
            const email = profile.email || "";
            
            const nameEl = document.getElementById("profileName") || document.getElementById("userNameDisplay");
            const emailEl = document.getElementById("profileEmail") || document.getElementById("userEmailDisplay");
            const upiEl = document.getElementById("userUpiDisplay");

            if (nameEl) nameEl.textContent = name;
            if (emailEl) emailEl.textContent = email;
            if (upiEl) upiEl.textContent = profile.upi_id || "Not Linked";
        }
    } catch (err) {
        console.error("Failed to load user profile name:", err);
    }

    try {
        const response = await fetch(`/api/recycling/summary${queryStr}`);
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
}

async function loadPendingPayments() {
    const param = getAuthParam();
    if (!param && !document.cookie.includes("session=")) {
        console.warn("[PaymentHub] Aborting loadPendingPayments: No active session/credentials found.");
        return;
    }

    const queryStr = param ? `?${param}` : "";

    const tableBody = document.getElementById("pendingPaymentsTableBody");
    const container = document.getElementById("pendingPaymentsContainer");
    const totalDisplay = document.getElementById("totalPendingAmount");

    try {
        const response = await fetch(`/api/recycling/pending-payments${queryStr}`);
        const result = await response.json();

        if (!response.ok || result.status !== "success") {
            throw new Error(result.detail || "Failed to load pending payments.");
        }

        if (totalDisplay) {
            totalDisplay.textContent = `₹${result.total_pending_amount.toFixed(2)}`;
        }

        if (tableBody) {
            if (result.entries.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-6 text-slate-400">
                            No pending recycling payouts found.
                        </td>
                    </tr>`;
            } else {
                tableBody.innerHTML = result.entries.map(entry => {
                    const formattedDate = entry.created_at 
                        ? new Date(entry.created_at).toLocaleDateString() 
                        : "N/A";

                    const isCharge = entry.payout_amount < 0;
                    const displayAmt = Math.abs(entry.payout_amount).toFixed(2);
                    const amtClass = isCharge ? "text-rose-400 font-bold" : "text-emerald-400 font-bold";
                    const prefix = isCharge ? "-₹" : "+₹";

                    return `
                        <tr class="border-b border-slate-700/50 hover:bg-slate-800/40">
                            <td class="p-4 text-emerald-400 font-mono font-medium">#${entry.entry_id}</td>
                            <td class="p-4 text-slate-300 capitalize">${entry.waste_category}</td>
                            <td class="p-4 text-slate-300">${entry.weight_kg} kg</td>
                            <td class="p-4 ${amtClass}">${prefix}${displayAmt}</td>
                            <td class="p-4 text-slate-400 text-xs font-mono">${formattedDate}</td>
                        </tr>
                    `;
                }).join("");
            }
        }

        if (container) {
            container.innerHTML = "";
            if (result.entries.length === 0) {
                container.innerHTML = `<p class="text-slate-400 text-center py-4">No pending transactions found.</p>`;
            } else {
                result.entries.forEach(item => {
                    const row = document.createElement("div");
                    row.className = "flex justify-between items-center p-3 bg-slate-800 rounded-lg mb-2 border border-slate-700";
                    const isCharge = item.payout_amount < 0;
                    const amtClass = isCharge ? "text-rose-400 font-bold" : "text-emerald-400 font-bold";
                    const prefix = isCharge ? "-₹" : "+₹";

                    row.innerHTML = `
                        <div>
                            <p class="font-bold text-white capitalize">${item.waste_category}</p>
                            <p class="text-xs text-slate-400">Weight: ${item.weight_kg} kg | Status: <span class="text-amber-400 font-semibold">${item.status}</span></p>
                        </div>
                        <div class="text-right">
                            <p class="font-mono ${amtClass}">${prefix}${Math.abs(item.payout_amount).toFixed(2)}</p>
                            ${item.status === 'approved' ? `<a href="/api/recycling/receipt/${item.entry_id}" class="text-xs text-indigo-400 hover:underline">Receipt PDF</a>` : ''}
                        </div>
                    `;
                    container.appendChild(row);
                });
            }
        }
    } catch (err) {
        console.error("Error fetching pending payments:", err);
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-6 text-rose-400">
                        Error loading entries: ${err.message}
                    </td>
                </tr>`;
        }
    }
}

async function loadReviewedRequests() {
    const param = getAuthParam();
    if (!param && !document.cookie.includes("session=")) {
        console.warn("[PaymentHub] Aborting loadReviewedRequests: No active session/credentials found.");
        return;
    }

    const queryStr = param ? `?${param}` : "";

    try {
        const res = await fetch(`/api/recycling/reviewed-requests${queryStr}`);
        const data = await res.json();

        if (res.ok && data.status === "success") {
            const tbody = document.getElementById("reviewedTableBody");
            const totalEl = document.getElementById("approvedTotalDisplay");

            if (totalEl) totalEl.textContent = `₹${data.total_approved_earnings.toFixed(2)}`;
            if (!tbody) return;

            tbody.innerHTML = "";

            if (data.entries.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-500">No reviewed requests found.</td></tr>`;
                return;
            }

            data.entries.forEach(entry => {
                const isApproved = entry.status === "approved";
                const isCharge = entry.payout_amount < 0;
                const statusBadge = isApproved
                    ? `<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">Approved</span>`
                    : `<span class="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">Declined</span>`;

                const downloadBtn = isApproved 
                    ? `<a href="/api/recycling/receipt/${entry.entry_id}" download class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/40 rounded-lg text-xs font-medium transition">
                        <i class="fa-solid fa-file-pdf"></i> Receipt
                    </a>`
                    : `<span class="text-xs text-slate-500">${entry.rejection_reason || 'N/A'}</span>`;

                const amtClass = isCharge ? 'text-rose-400' : 'text-emerald-400';
                const prefix = isCharge ? '-₹' : '+₹';

                const tr = document.createElement("tr");
                tr.className = "border-b border-slate-700/40 hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="py-3.5 px-4 font-mono text-slate-400">#${entry.entry_id}</td>
                    <td class="py-3.5 px-4 font-semibold text-white capitalize">${entry.waste_category}</td>
                    <td class="py-3.5 px-4 font-mono text-slate-300">${entry.weight_kg.toFixed(2)} kg</td>
                    <td class="py-3.5 px-4 font-bold ${isApproved ? amtClass : 'text-slate-400'}">${prefix}${Math.abs(entry.payout_amount).toFixed(2)}</td>
                    <td class="py-3.5 px-4">${statusBadge}</td>
                    <td class="py-3.5 px-4 text-right">${downloadBtn}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Failed to load reviewed requests:", err);
    }
}

// --- TAB SWITCHER & ROUTER LOGIC ---
window.switchTab = function(targetViewId) {
    document.querySelectorAll('.view-panel').forEach(panel => panel.classList.add('hidden'));

    const activePanel = document.getElementById(targetViewId);
    if (activePanel) activePanel.classList.remove('hidden');

    document.querySelectorAll('#spaNav .nav-btn').forEach(btn => {
        if (btn.getAttribute('data-view') === targetViewId) {
            btn.classList.add('bg-emerald-500/10', 'text-emerald-400', 'border', 'border-emerald-500/20');
            btn.classList.remove('text-slate-400');
        } else {
            btn.classList.remove('bg-emerald-500/10', 'text-emerald-400', 'border', 'border-emerald-500/20');
            btn.classList.add('text-slate-400');
        }
    });

    if (targetViewId === 'view-options') loadDashboardMetrics();
    if (targetViewId === 'view-pending') loadPendingPayments();
    if (targetViewId === 'view-reviewed') loadReviewedRequests();
};

// --- FORM CALCULATOR & EVENT INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    const userId = localStorage.getItem("user_id");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");
    const hasAuthCookie = document.cookie.split(';').some(c => c.trim().startsWith('session='));

    if (!userId && !verifiedEmail && !hasAuthCookie) {
        console.warn("[PaymentHub] Unauthenticated user state detected. Halting initialization.");
        return;
    }

    switchTab('view-options');

    document.querySelectorAll('#spaNav .nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const viewTarget = btn.getAttribute('data-view');
            switchTab(viewTarget);
        });
    });

    const weightInput = document.getElementById("weightInput");
    const stationInput = document.getElementById("stationInput");
    const radios = document.querySelectorAll('input[name="material"]');
    const estDisplay = document.getElementById("estimatedTotal");
    const form = document.getElementById("paymentRegisterForm");

    function calculate() {
        const selected = document.querySelector('input[name="material"]:checked');
        const rate = parseFloat(selected?.dataset.rate || 0);
        const weight = parseFloat(weightInput?.value || 0);
        const total = rate * weight;

        if (!estDisplay) return;

        if (total < 0) {
            estDisplay.textContent = `-₹${Math.abs(total).toFixed(2)} (Fee Charge)`;
            estDisplay.className = "text-lg font-bold text-rose-400";
        } else {
            estDisplay.textContent = `+₹${total.toFixed(2)} (Payout)`;
            estDisplay.className = "text-lg font-bold text-emerald-400";
        }
    }

    if (weightInput) weightInput.addEventListener("input", calculate);
    radios.forEach(r => r.addEventListener("change", calculate));

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const selected = document.querySelector('input[name="material"]:checked');
            const weight = parseFloat(weightInput?.value || 0);

            if (!selected || isNaN(weight) || weight <= 0) {
                alert("Please select a category and enter a valid weight in kilograms.");
                return;
            }

            const rate = parseFloat(selected.dataset.rate);
            const payout = rate * weight;
            const wasteCategory = selected.dataset.category || selected.value || "Plastic";
            const accountSelect = form.querySelector("select");

            let currentUserId = localStorage.getItem("user_id");

            if (!currentUserId) {
                const currentEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");
                if (!currentEmail && !hasAuthCookie) {
                    alert("Your session has expired. Please log in again.");
                    window.location.href = "/login";
                    return;
                }

                try {
                    const queryStr = currentEmail ? `?email=${encodeURIComponent(currentEmail)}` : "";
                    const profileRes = await fetch(`/api/user/profile${queryStr}`);
                    if (profileRes.ok) {
                        const profileData = await profileRes.json();
                        if (profileData?.profile?.id) {
                            currentUserId = profileData.profile.id;
                            localStorage.setItem("user_id", currentUserId);
                        }
                    }
                } catch (err) {
                    console.error("User resolution error:", err);
                }
            }

            const payload = {
                user_id: currentUserId ? parseInt(currentUserId) : null,
                waste_category: wasteCategory,
                weight_kg: weight,
                payout_amount: payout,
                station_id: stationInput ? stationInput.value.trim() : null,
                payout_method: accountSelect ? accountSelect.value : "upi"
            };

            try {
                const response = await fetch("/api/recycling/entry", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (response.ok) {
                    alert(`Drop-off recorded successfully! Entry ID: #${result.entry_id}`);
                    form.reset();
                    calculate();
                    switchTab('view-pending');
                } else {
                    alert(`Submission error: ${result.detail || 'Unknown error'}`);
                }
            } catch (err) {
                console.error("Submission Failure:", err);
                alert(`Submission failed: ${err.message}`);
            }
        });
    }
});