document.addEventListener("DOMContentLoaded", () => {
    loadDistrictProfiles();

    const filterForm = document.getElementById("filterForm");
    if (filterForm) {
        filterForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const searchVal = document.getElementById("searchInput")?.value.trim() || "";
            const pinVal = document.getElementById("pincodeInput")?.value.trim() || "";
            loadDistrictProfiles(searchVal, pinVal);
        });
    }
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

async function loadDistrictProfiles(searchQuery = "", exactPin = "") {
    // Removed hardcoded officer credential fallback
    const staffEmail = localStorage.getItem("staff_email") || sessionStorage.getItem("staff_email") || getCookie("staff_email");
    const staffPincode = localStorage.getItem("assigned_pincode") || sessionStorage.getItem("assigned_pincode") || getCookie("staff_pincode");

    if (!staffEmail || !staffPincode) {
        window.location.href = "/staff-login";
        return;
    }
    
    const officerEmailEl = document.getElementById("officerEmail");
    const zonePrefixEl = document.getElementById("districtZonePrefix");
    const prefixEl = document.getElementById("districtPrefix");

    if (officerEmailEl) officerEmailEl.textContent = staffEmail;
    if (zonePrefixEl) zonePrefixEl.textContent = staffPincode;
    if (prefixEl) prefixEl.textContent = staffPincode.substring(0, 3);

    const tbody = document.getElementById("householdProfilesTbody") || document.getElementById("staffProfilesTbody") || document.getElementById("districtUsersList");
    
    if (!tbody) {
        console.error("Table body or container element not found in DOM.");
        return;
    }

    let url = `/api/admin/district-users?staff_pincode=${encodeURIComponent(staffPincode)}`;
    if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
    if (exactPin) url += `&exact_pincode=${encodeURIComponent(exactPin)}`;

    try {
        const res = await fetch(url);

        if (res.status === 401 || res.status === 403) {
            window.location.href = "/staff-login";
            return;
        }

        const data = await res.json();
        
        const countBadge = document.getElementById("profilesCountBadge");
        if (countBadge) {
            countBadge.textContent = `${data.count || (data.profiles ? data.profiles.length : 0)} found`;
        }

        tbody.innerHTML = "";

        if (!data.profiles || data.profiles.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="py-12 text-center text-slate-500">
                        <i class="fa-solid fa-folder-open text-3xl mb-2 opacity-40"></i>
                        <p class="text-xs font-medium">No household profiles found for this district prefix.</p>
                    </td>
                </tr>
            `;
            return;
        }

        for (const user of data.profiles) {
            let pendingEntries = [];
            try {
                const entriesRes = await fetch(`/api/admin/user-pending-entries/${user.id}`);
                if (entriesRes.ok) {
                    const entriesData = await entriesRes.json();
                    pendingEntries = entriesData.entries || [];
                }
            } catch (e) {
                console.warn(`Could not load pending entries for user #${user.id}`, e);
            }

            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-800/40 transition cursor-pointer group border-b border-slate-800/50";
            tr.onclick = () => toggleDropdown(`dropdown-user-${user.id}`);

            tr.innerHTML = `
                <td class="py-4 px-6 font-mono text-slate-400 text-xs">#${user.id}</td>
                <td class="py-4 px-6 font-semibold text-white group-hover:text-amber-400 transition">${escapeHtml(user.full_name)}</td>
                <td class="py-4 px-6 text-slate-300">${escapeHtml(user.email)}</td>
                <td class="py-4 px-6">
                    <span class="bg-slate-800 border border-slate-700/80 px-2.5 py-1 rounded-md font-mono text-xs text-amber-400">
                        ${escapeHtml(user.postal_code)}
                    </span>
                </td>
                <td class="py-4 px-6 text-slate-300 capitalize">${escapeHtml(user.premise_type || 'House')}</td>
                <td class="py-4 px-6 font-mono text-xs text-slate-400">${escapeHtml(user.upi_id || 'N/A')}</td>
                <td class="py-4 px-6 text-right">
                    <button class="inline-flex items-center gap-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 px-3 py-1.5 rounded-xl font-bold text-xs transition">
                        <span>Pending Requests</span>
                        <span class="bg-amber-500 text-slate-950 font-extrabold rounded-full px-2 py-0.5 text-[10px]">
                            ${pendingEntries.length}
                        </span>
                        <i class="fa-solid fa-chevron-down text-[10px] ml-1 transition-transform"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);

            const dropdownTr = document.createElement("tr");
            dropdownTr.id = `dropdown-user-${user.id}`;
            dropdownTr.className = "accordion-content hidden bg-slate-950/80 border-b border-slate-800/80";
            
            let nestedContent = `
                <td colspan="7" class="p-4 sm:p-6">
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-inner">
                        <div class="flex items-center justify-between mb-3 px-1">
                            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                                <i class="fa-solid fa-box-archive text-amber-400"></i>
                                Pending Recycling Requests for Household #${user.id}
                            </h3>
                            <span class="text-[11px] text-slate-500">Requires officer verification</span>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs border-collapse">
                                <thead>
                                    <tr class="bg-slate-950/60 text-slate-400 border-b border-slate-800 uppercase font-semibold">
                                        <th class="py-2.5 px-4">Trash ID</th>
                                        <th class="py-2.5 px-4">Trash Category</th>
                                        <th class="py-2.5 px-4">Weight (in KG)</th>
                                        <th class="py-2.5 px-4">Estimated Payout Amount</th>
                                        <th class="py-2.5 px-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-800/60">
            `;

            if (pendingEntries.length === 0) {
                nestedContent += `
                    <tr>
                        <td colspan="5" class="py-6 text-center text-slate-500 italic">
                            No active pending requests for this household.
                        </td>
                    </tr>
                `;
            } else {
                pendingEntries.forEach(entry => {
                    nestedContent += `
                        <tr class="hover:bg-slate-800/30 transition">
                            <td class="py-3 px-4 font-mono text-slate-400">#TRASH-${entry.entry_id}</td>
                            <td class="py-3 px-4 font-semibold text-white capitalize">${escapeHtml(entry.waste_category)}</td>
                            <td class="py-3 px-4 font-mono text-slate-300">${entry.weight_kg.toFixed(2)} kg</td>
                            <td class="py-3 px-4 font-bold text-emerald-400">₹${entry.payout_amount.toFixed(2)}</td>
                            <td class="py-3 px-4 text-right">
                                <div class="inline-flex items-center gap-2">
                                    <button onclick="reviewEntry(event, ${entry.entry_id}, 'approve')" class="bg-lime-500 hover:bg-lime-400 text-slate-950 font-extrabold px-3.5 py-1.5 rounded-lg shadow-md transition text-[11px] tracking-wide uppercase">
                                        Approve
                                    </button>
                                    <button onclick="reviewEntry(event, ${entry.entry_id}, 'decline')" class="bg-red-600 hover:bg-red-500 text-white font-extrabold px-3.5 py-1.5 rounded-lg shadow-md transition text-[11px] tracking-wide uppercase">
                                        Decline
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                });
            }

            nestedContent += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </td>
            `;
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
    event.stopPropagation();
    const staffId = localStorage.getItem("staff_id") || sessionStorage.getItem("staff_id");

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
            const searchVal = document.getElementById("searchInput")?.value.trim() || "";
            const pinVal = document.getElementById("pincodeInput")?.value.trim() || "";
            loadDistrictProfiles(searchVal, pinVal);
        } else {
            alert(data.detail || "Failed to update entry.");
        }
    } catch (err) {
        console.error("Failed to review entry:", err);
    }
}

function resetFilters() {
    const searchInput = document.getElementById("searchInput");
    const pincodeInput = document.getElementById("pincodeInput");
    if (searchInput) searchInput.value = "";
    if (pincodeInput) pincodeInput.value = "";
    loadDistrictProfiles();
}

function logoutStaff() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/staff-login";
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}