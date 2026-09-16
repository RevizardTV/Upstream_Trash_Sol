// SPA Navigation Switcher
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
}

// Category Tips Dictionary
const categoryTips = {
    plastic: "Ensure bottles are rinsed and flattened. Caps can be included.",
    metal: "Separate aluminum cans from heavy steel scrap for accurate weighing.",
    paper: "Keep cardboard dry and flattened. Waxed milk cartons are not accepted.",
    ewaste: "Disconnect batteries and salvage high-value circuit boards separately where allowed.",
    landfill: "Non-recyclable waste incurs a PAYT tipping fee of ₹12/kg."
};

// Inline Info Box Toggle (Restricted strictly to the Register view)
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

// Live Payout / Fee Calculation Listener
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

// Global Event Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Nav Click Handlers
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.getAttribute('data-view');
            if (view) switchTab(view);
        });
    });

    // Inputs calculation binding
    const weightInput = document.getElementById('weightInput');
    if (weightInput) {
        weightInput.addEventListener('input', updateLiveCalculation);
    }

    document.querySelectorAll('input[name="material"]').forEach(radio => {
        radio.addEventListener('change', updateLiveCalculation);
    });

    // Default View Startup
    switchTab('view-options');
});

// Logout Placeholder
function logout() {
    if (typeof authGuardLogout === 'function') {
        authGuardLogout();
    } else {
        window.location.href = '/login.html';
    }
}