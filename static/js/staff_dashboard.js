document.addEventListener("DOMContentLoaded", () => {
    const staffEmail = localStorage.getItem("staff_email");
    const assignedPincode = localStorage.getItem("assigned_pincode");

    if (!staffEmail || !assignedPincode) {
        alert("Unauthorized access. Please log in first.");
        window.location.href = "/staff-login";
        return;
    }

    document.getElementById("staffEmailDisplay").textContent = staffEmail;
    document.getElementById("districtZoneDisplay").textContent = `${assignedPincode} (District Prefix: ${assignedPincode.slice(0, 3)})`;

    loadDistrictUsers();

    document.getElementById("filterBtn").addEventListener("click", loadDistrictUsers);
    document.getElementById("resetBtn").addEventListener("click", () => {
        document.getElementById("searchInput").value = "";
        document.getElementById("pinInput").value = "";
        loadDistrictUsers();
    });

    document.getElementById("logoutBtn").addEventListener("click", () => {
        localStorage.clear();
        window.location.href = "/staff-login";
    });
});

async function loadDistrictUsers() {
    const assignedPincode = localStorage.getItem("assigned_pincode");
    const search = document.getElementById("searchInput").value.trim();
    const exactPin = document.getElementById("pinInput").value.trim();

    let url = `/api/admin/district-users?staff_pincode=${encodeURIComponent(assignedPincode)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (exactPin) url += `&exact_pincode=${encodeURIComponent(exactPin)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();

        if (res.ok) {
            renderTable(data.profiles);
        } else {
            console.error("Error fetching district data:", data.detail);
        }
    } catch (err) {
        console.error("Network error fetching district records:", err);
    }
}

function renderTable(profiles) {
    const tbody = document.getElementById("userTableBody");
    const countSpan = document.getElementById("recordCount");
    tbody.innerHTML = "";
    countSpan.textContent = `${profiles.length} found`;

    if (profiles.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-slate-500">No household profiles match your query in this district.</td></tr>`;
        return;
    }

    profiles.forEach(user => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-800/40 transition";
        tr.innerHTML = `
            <td class="p-3 font-mono text-slate-400">#${user.id}</td>
            <td class="p-3 font-semibold text-white">${user.full_name}</td>
            <td class="p-3">${user.email}</td>
            <td class="p-3"><span class="bg-slate-800 text-amber-400 px-2 py-0.5 rounded border border-slate-700 font-mono">${user.postal_code}</span></td>
            <td class="p-3 capitalize">${user.premise_type}</td>
            <td class="p-3 font-mono text-slate-400">${user.upi_id || "N/A"}</td>
            <td class="p-3 text-right">
                <button onclick="reviewUser(${user.id}, '${user.full_name}')" class="bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500 hover:text-slate-950 px-2.5 py-1 rounded text-xs transition font-semibold">
                    Review User
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Action Handler for Review User Button
async function reviewUser(userId, userName) {
    const action = confirm(`Approve account for ${userName} (ID #${userId})?\n\nClick 'OK' to Approve, or 'Cancel' to Reject.`);
    const decision = action ? "approve" : "decline";

    try {
        const res = await fetch(`/api/staff/users/${userId}/review`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: decision })
        });

        const data = await res.json();
        if (res.ok) {
            alert(`Success: Profile status updated to ${decision.toUpperCase()}`);
            loadDistrictUsers();
        } else {
            alert(`Error: ${data.detail || 'Review failed'}`);
        }
    } catch (err) {
        console.error("Staff review error:", err);
        alert(`Failed to complete review: ${err.message}`);
    }
}