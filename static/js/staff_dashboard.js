document.addEventListener("DOMContentLoaded", () => {
    loadDistrictProfiles();
});

async function loadDistrictProfiles(searchQuery = "", exactPin = "") {
    const staffPincode = localStorage.getItem("assigned_pincode") || "641001";
    let url = `/api/admin/district-users?staff_pincode=${encodeURIComponent(staffPincode)}`;
    if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
    if (exactPin) url += `&exact_pincode=${encodeURIComponent(exactPin)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        const tbody = document.getElementById("staffProfilesTbody");
        tbody.innerHTML = "";

        if (!data.profiles || data.profiles.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-500">No household profiles found.</td></tr>`;
            return;
        }

        for (const user of data.profiles) {
            // Fetch pending trash entries count for each household
            const entriesRes = await fetch(`/api/admin/user-pending-entries/${user.id}`);
            const entriesData = await entriesRes.json();
            const pendingEntries = entriesData.entries || [];

            // Main Household Row
            const tr = document.createElement("tr");
            tr.className = "border-b border-slate-700/40 hover:bg-slate-800/50 cursor-pointer transition";
            tr.onclick = () => toggleDropdown(`dropdown-${user.id}`);

            tr.innerHTML = `
                <td class="py-3.5 px-4 font-mono text-slate-400">#${user.id}</td>
                <td class="py-3.5 px-4 font-semibold text-white">${user.full_name}</td>
                <td class="py-3.5 px-4 text-slate-300">${user.email}</td>
                <td class="py-3.5 px-4 font-mono text-amber-400">${user.postal_code}</td>
                <td class="py-3.5 px-4 text-slate-300 capitalize">${user.premise_type}</td>
                <td class="py-3.5 px-4 font-mono text-xs text-slate-400">${user.upi_id || 'N/A'}</td>
                <td class="py-3.5 px-4 text-center">
                    <span class="inline-flex items-center justify-center bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded-full px-3 py-1 font-bold text-xs">
                        Pending Requests <span class="ml-2 bg-amber-500 text-slate-950 rounded-full w-5 h-5 flex items-center justify-center font-extrabold text-[11px]">${pendingEntries.length}</span>
                    </span>
                </td>
            `;
            tbody.appendChild(tr);

            // Nested Dropdown Row for Trash Review
            const dropdownTr = document.createElement("tr");
            dropdownTr.id = `dropdown-${user.id}`;
            dropdownTr.className = "hidden bg-slate-950/60 border-b border-slate-700/60";
            
            let nestedContent = `
                <td colspan="7" class="p-4">
                    <div class="bg-slate-900 border border-slate-700/80 rounded-xl p-4 shadow-inner">
                        <table class="w-full text-left text-xs">
                            <thead>
                                <tr class="text-slate-400 border-b border-slate-800 uppercase font-semibold">
                                    <th class="pb-2 px-3">Trash ID</th>
                                    <th class="pb-2 px-3">Trash Category</th>
                                    <th class="pb-2 px-3">Weight (in KG)</th>
                                    <th class="pb-2 px-3">Estimated Payout Amount</th>
                                    <th class="pb-2 px-3 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            if (pendingEntries.length === 0) {
                nestedContent += `<tr><td colspan="5" class="py-4 text-center text-slate-500 italic">No active pending requests for this user.</td></tr>`;
            } else {
                pendingEntries.forEach(entry => {
                    nestedContent += `
                        <tr class="border-b border-slate-800/60 hover:bg-slate-800/30">
                            <td class="py-2.5 px-3 font-mono text-slate-400">#${entry.entry_id}</td>
                            <td class="py-2.5 px-3 font-semibold text-white capitalize">${entry.waste_category}</td>
                            <td class="py-2.5 px-3 font-mono text-slate-300">${entry.weight_kg.toFixed(2)} kg</td>
                            <td class="py-2.5 px-3 font-bold text-emerald-400">₹${entry.payout_amount.toFixed(2)}</td>
                            <td class="py-2.5 px-3 text-right space-x-2">
                                <button onclick="reviewEntry(event, ${entry.entry_id}, 'approve')" class="bg-lime-500 hover:bg-lime-600 text-slate-950 font-bold px-3 py-1.5 rounded-md transition uppercase text-[11px]">Approve</button>
                                <button onclick="reviewEntry(event, ${entry.entry_id}, 'decline')" class="bg-red-600 hover:bg-red-700 text-white font-bold px-3 py-1.5 rounded-md transition uppercase text-[11px]">Decline</button>
                            </td>
                        </tr>
                    `;
                });
            }

            nestedContent += `</tbody></table></div></td>`;
            dropdownTr.innerHTML = nestedContent;
            tbody.appendChild(dropdownTr);
        }
    } catch (err) {
        console.error("Error loading district profiles:", err);
    }
}

function toggleDropdown(id) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle("hidden");
}

async function reviewEntry(event, entryId, action) {
    event.stopPropagation(); // Prevents row collapse click trigger
    const staffId = localStorage.getItem("staff_id");

    let rejectionReason = null;
    if (action === "decline") {
        rejectionReason = prompt("Enter reason for declining this request:") || "Declined by staff officer";
    }

    try {
        const res = await fetch(`/api/staff/entries/${entryId}/review`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                action: action,
                rejection_reason: rejectionReason,
                staff_id: staffId ? parseInt(staffId) : null
            })
        });

        const data = await res.json();
        if (res.ok && data.status === "success") {
            // Reload the table view to instantly update DB state and pending badge count
            loadDistrictProfiles();
        } else {
            alert(data.detail || "Failed to update entry.");
        }
    } catch (err) {
        console.error("Failed to review entry:", err);
    }
}