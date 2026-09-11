// 1. Tip Guidance Dictionary
const tips = {
    plastic: "Separate PET bottles from soft films. Ensure items are clean and dry for maximum payout value.",
    metal: "Copper and aluminum offer top payouts. Clean off heavy rust or non-metal fittings to maintain grade value.",
    paper: "Flatten cardboard boxes and keep them dry. Wet paper adds heavy unusable weight.",
    ewaste: "Disconnect batteries and salvage high-value circuit boards separately where allowed.",
    landfill: "💡 Charge reduction tip: Thoroughly drain liquid & organic moisture before disposal. Water content inflates total mass and fee costs by up to 40%."
};

// 2. Global Tip Popup Activator
window.showTip = function(category) {
    const panel = document.getElementById("infoPanel");
    const title = document.getElementById("infoTitle");
    const content = document.getElementById("infoContent");

    if (panel && title && content) {
        title.textContent = category.toUpperCase() + " Optimization & Value Guide";
        content.textContent = tips[category] || "No specialized tip for this category.";
        panel.classList.remove("hidden");
    }
};

document.addEventListener("DOMContentLoaded", () => {
    const weightInput = document.getElementById("weightInput");
    const radios = document.querySelectorAll('input[name="material"]');
    const estDisplay = document.getElementById("estimatedTotal");
    const form = document.getElementById("paymentRegisterForm");

    // 3. Dynamic Price Calculator
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

    // 4. Form Submission Handler
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
            const entryType = selected.dataset.type || (payout < 0 ? "charge" : "payout");

            // User ID Resolution Sequence
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

            // Post Data Entry
            const payload = {
                user_id: parseInt(userId),
                waste_category: selected.value,
                weight_kg: weight,
                payout_amount: payout,
                entry_type: entryType
            };

            try {
                const response = await fetch("/api/recycling/entry", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (response.ok) {
                    alert(`Drop-off recorded successfully! Entry ID: ${result.entry_id}`);
                    form.reset();
                    calculate();
                } else {
                    alert(`Submission error: ${result.detail || 'Unknown error'}`);
                }
            } catch (err) {
                console.error("Submission Failure:", err);
                alert("Failed to submit entry. Check console logs.");
            }
        });
    }
});