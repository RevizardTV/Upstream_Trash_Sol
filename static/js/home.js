const goToLoginBtn = document.getElementById("goToLogin");

if (goToLoginBtn) {
    goToLoginBtn.addEventListener("click", () => {
        window.location.href = "/login";
    });
}

// Global Console Utility Functions
window.wipeDatabase = async function() {
    if (!confirm("Are you sure you want to wipe all profile and queued trash data? This action cannot be undone.")) {
        console.log("Database wipe cancelled.");
        return;
    }

    try {
        const response = await fetch("/api/admin/wipe-database", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
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

window.showProfiles = async function() {
    try {
        const response = await fetch("/api/admin/show-profiles");
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

window.showData = async function(table = "Profile") {
    try {
        const response = await fetch(`/api/admin/show-data?table=${encodeURIComponent(table)}`);
        const result = await response.json();

        if (response.ok) {
            console.log(`📊 Table Data for [${result.table}] (${result.count} rows):`);
            console.table(result.data);
            return result.data;
        } else {
            console.error("❌ Failed to fetch table data:", result.detail);
        }
    } catch (err) {
        console.error("❌ Error executing showData():", err);
    }
};

console.log("🛠️ Admin Console Commands Ready: `wipeDatabase()`, `showProfiles()`, `showData('Profile')` or `showData('Trash')`");