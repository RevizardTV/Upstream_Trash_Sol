const goToLoginBtn = document.getElementById("goToLogin");

if (goToLoginBtn) {
    goToLoginBtn.addEventListener("click", () => {
        window.location.href = "/login";
    });
}

// Utility function to fetch secret key if missing
function getAdminKey(providedSecret) {
    return providedSecret || prompt("Enter Administrative Secret Key (EM_RESET_KEY):");
}

// Global Console Utility Commands
window.wipeDatabase = async function(providedSecret) {
    if (!confirm("Are you sure you want to wipe all profiles, staff records, and queued trash data? This action cannot be undone.")) {
        console.log("Database wipe cancelled.");
        return;
    }

    const secretKey = getAdminKey(providedSecret);
    if (!secretKey) return console.warn("⚠️ Operation cancelled: Missing administrative authorization token.");

    try {
        const response = await fetch("/api/admin/wipe-database", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "X-Admin-Secret": secretKey
            }
        });
        const result = await response.json();

        if (response.ok) {
            console.warn("🧹 DATABASE WIPED SUCCESSFULLY:", result.message);
        } else {
            console.error("❌ Wipe failed:", result.detail);
        }
    } catch (err) {
        console.error("❌ Error executing wipeDatabase():", err);
    }
};

window.showProfiles = async function(providedSecret) {
    const secretKey = getAdminKey(providedSecret);
    if (!secretKey) return console.warn("⚠️ Operation cancelled: Missing administrative authorization token.");

    try {
        const response = await fetch("/api/admin/show-profiles", {
            headers: { "X-Admin-Secret": secretKey }
        });
        const result = await response.json();

        if (response.ok) {
            console.log(`📋 User Profiles Found (${result.count}):`);
            console.table(result.profiles);
            return result.profiles;
        } else {
            console.error("❌ Failed to fetch profiles:", result.detail);
        }
    } catch (err) {
        console.error("❌ Error executing showProfiles():", err);
    }
};

window.showStaff = async function(providedSecret) {
    const secretKey = getAdminKey(providedSecret);
    if (!secretKey) return console.warn("⚠️ Operation cancelled: Missing administrative authorization token.");

    try {
        const response = await fetch("/api/admin/show-staff", {
            headers: { "X-Admin-Secret": secretKey }
        });
        const result = await response.json();

        if (response.ok) {
            console.log(`👷 Staff Profiles Found (${result.count}):`);
            console.table(result.staff);
            return result.staff;
        } else {
            console.error("❌ Failed to fetch staff profiles:", result.detail);
        }
    } catch (err) {
        console.error("❌ Error executing showStaff():", err);
    }
};

window.showData = async function(table = "Profile", providedSecret) {
    const secretKey = getAdminKey(providedSecret);
    if (!secretKey) return console.warn("⚠️ Operation cancelled: Missing administrative authorization token.");

    try {
        const response = await fetch(`/api/admin/show-data?table=${encodeURIComponent(table)}`, {
            headers: { "X-Admin-Secret": secretKey }
        });
        const result = await response.json();

        if (response.ok) {
            console.log(`📊 Table Data for [${result.table || table}] (${result.count} rows):`);
            console.table(result.data || result.profiles || result.staff);
            return result.data || result.profiles || result.staff;
        } else {
            console.error("❌ Failed to fetch table data:", result.detail);
        }
    } catch (err) {
        console.error("❌ Error executing showData():", err);
    }
};

console.log("🛠️ Protected Admin Console Commands Ready: `wipeDatabase('SECRET')`, `showProfiles('SECRET')`, `showStaff('SECRET')`, or `showData('Profile', 'SECRET')`");