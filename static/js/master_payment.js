/**
 * EcoRecycle - Unified Single Page Application Controller
 */

// --- GLOBAL FETCH AUTHENTICATION INTERCEPTOR ---
// Automatically catches 401 Unauthorized responses from backend API calls
// and forces a redirect to the login page.
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
        window.location.href = "/login";
        return null;
    }
    return userId ? `user_id=${userId}` : `email=${encodeURIComponent(verifiedEmail)}`;
}

// Global Logout Action
// Revokes backend session in Redis and clears cookies via server redirect
window.logout = function() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/logout";
};

// Global Tip Popup Activator
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

// 1. Profile & Dashboard Summary Retrieval API
async function loadDashboardMetrics() {
    const param = getAuthParam();
    if (!param) return;

    // Fetch Profile Name & Email
    try {
        const profileRes = await fetch(`/api/user/profile?${param}`);
        if (profileRes.ok) {
            const profileData = await profileRes.json();
            const name = profileData.profile?.full_name || "User";
            const email = profileData.profile?.email || "";
            
            const nameEl = document.getElementById("profileName");
            const emailEl = document.getElementById("profileEmail");
            if (nameEl) nameEl.textContent = name;
            if (emailEl) emailEl.textContent = email;
        }
    } catch (err) {
        console.error("Failed to load user profile name:", err);
    }

    // Fetch Metrics Summary
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
}

// 2. Pending Queue Data Fetcher API
async function loadPendingPayments() {
    const param = getAuthParam();
    if (!param) return;

    const tableBody = document.getElementById("pendingPaymentsTableBody");
    const totalDisplay = document.getElementById("totalPendingAmount");

    try {
        const response = await fetch(`/api/recycling/pending-payments?${param}`);
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
                    <td colspan="5" class="text-center py-6 text-rose-400">
                        Error loading entries: ${err.message}
                    </td>
                </tr>`;
        }
    }
}

// 3. Reviewed Requests Data Fetcher API
async function loadReviewedRequests() {
    const param = getAuthParam();
    if (!param) return;

    try {
        const res = await fetch(`/api/recycling/reviewed-requests?${param}`);
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
                const statusBadge = isApproved
                    ? `<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">Approved</span>`
                    : `<span class="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded-full text-xs font-semibold">Declined</span>`;

                // Download button rendering for approved transactions
                const downloadBtn = isApproved 
                    ? `<a href="/api/recycling/receipt/${entry.entry_id}" download class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/40 rounded-lg text-xs font-medium transition">
                        <i class="fa-solid fa-file-pdf"></i> Receipt
                    </a>`
                    : `<span class="text-xs text-slate-500">${entry.rejection_reason || 'N/A'}</span>`;

                const tr = document.createElement("tr");
                tr.className = "border-b border-slate-700/40 hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="py-3.5 px-4 font-mono text-slate-400">#${entry.entry_id}</td>
                    <td class="py-3.5 px-4 font-semibold text-white capitalize">${entry.waste_category}</td>
                    <td class="py-3.5 px-4 font-mono text-slate-300">${entry.weight_kg.toFixed(2)} kg</td>
                    <td class="py-3.5 px-4 font-bold ${isApproved ? 'text-emerald-400' : 'text-slate-400'}">₹${entry.payout_amount.toFixed(2)}</td>
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
    // Hide all panels
    document.querySelectorAll('.view-panel').forEach(panel => panel.classList.add('hidden'));

    // Show target panel
    const activePanel = document.getElementById(targetViewId);
    if (activePanel) activePanel.classList.remove('hidden');

    // Update active state on sidebar navigation buttons
    document.querySelectorAll('#spaNav .nav-btn').forEach(btn => {
        if (btn.getAttribute('data-view') === targetViewId) {
            btn.classList.add('bg-emerald-500/10', 'text-emerald-400', 'border', 'border-emerald-500/20');
            btn.classList.remove('text-slate-400');
        } else {
            btn.classList.remove('bg-emerald-500/10', 'text-emerald-400', 'border', 'border-emerald-500/20');
            btn.classList.add('text-slate-400');
        }
    });

    // Lazy load dataset depending on the current tab
    if (targetViewId === 'view-options') loadDashboardMetrics();
    if (targetViewId === 'view-pending') loadPendingPayments();
    if (targetViewId === 'view-reviewed') loadReviewedRequests();
};

// --- FORM CALCULATOR & EVENT INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    // Initialize default view state and load metrics
    switchTab('view-options');

    // Attach Sidebar Navigation Events
    document.querySelectorAll('#spaNav .nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const viewTarget = btn.getAttribute('data-view');
            switchTab(viewTarget);
        });
    });

    // Form Elements Initialization
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
            estDisplay.textContent = `-$${Math.abs(total).toFixed(2)} (Fee Charge)`;
            estDisplay.className = "text-lg font-bold text-rose-400";
        } else {
            estDisplay.textContent = `$${total.toFixed(2)} (Payout)`;
            estDisplay.className = "text-lg font-bold text-emerald-400";
        }
    }

    if (weightInput) weightInput.addEventListener("input", calculate);
    radios.forEach(r => r.addEventListener("change", calculate));

    // Register Form Handling & Direct Database Submission
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

            let userId = localStorage.getItem("user_id");

            if (!userId) {
                const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");
                if (verifiedEmail) {
                    try {
                        const profileRes = await fetch(`/api/user/profile?email=${encodeURIComponent(verifiedEmail)}`);
                        if (profileRes.ok) {
                            const profileData = await profileRes.json();
                            if (profileData?.profile?.id) {
                                userId = profileData.profile.id;
                                localStorage.setItem("user_id", userId);
                            }
                        }
                    } catch (err) {
                        console.error("User resolution error:", err);
                    }
                }
            }

            if (!userId) {
                alert("Unable to verify user profile. Please log in first.");
                return;
            }

            // Payload constructed with Station ID and Target Payout Account
            const payload = {
                user_id: parseInt(userId),
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
                    switchTab('view-pending'); // Automatically switch to Pending Queue on success
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