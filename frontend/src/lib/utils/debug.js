/**
 * EcoRecycle Admin Debug Console Tool (Auto-verified via Config/Env)
 */
const adminKey = import.meta.env.PUBLIC_EM_RESET_KEY || '';

function getHeaders() {
    if (!adminKey) {
        console.error("❌ PUBLIC_EM_RESET_KEY is missing from your .env file!");
    }
    return {
        'Content-Type': 'application/json',
        'x-secret-key': adminKey
    };
}

window.dbDebug = {
    async users() {
        const res = await fetch('/api/admin/inspect/users', { headers: getHeaders() });
        const data = await res.json();
        console.log(`👤 Users Table (${data.rows.length} records):`);
        console.table(data.rows);
        return data.rows;
    },

    async staff() {
        const res = await fetch('/api/admin/inspect/staff', { headers: getHeaders() });
        const data = await res.json();
        console.log(`🛡️ Staff Table (${data.rows.length} records):`);
        console.table(data.rows);
        return data.rows;
    },

    async recycling() {
        const res = await fetch('/api/admin/inspect/recycling', { headers: getHeaders() });
        const data = await res.json();
        console.log(`♻️ Recycling Entries Table (${data.rows.length} records):`);
        console.table(data.rows);
        return data.rows;
    },

    async wipeAllData() {
        if (!confirm("🚨 DANGER: Are you sure you want to delete ALL data from users, staff, and recycling tables?")) return;
        const res = await fetch('/api/admin/wipe-all-data', {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        console.log("🔥 WIPE RESULT:", data);
        return data;
    },

    async resetRedis() {
        const res = await fetch('/api/admin/reset-redis', {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        console.log("⚡ REDIS RESET RESULT:", data);
        return data;
    },

    help() {
        console.log(`
        💡 EcoRecycle Debug Commands (Auto-Authenticated):
        --------------------------------------------------
        1. dbDebug.users()       - Show all users
        2. dbDebug.staff()       - Show all staff members
        3. dbDebug.recycling()   - Show all recycling entries
        4. dbDebug.wipeAllData() - Delete all data from tables instantly
        5. dbDebug.resetRedis()  - Reset/flush Redis immediately
        --------------------------------------------------
        `);
    }
};

console.log("🛠️ Admin Debugger Loaded! Type `dbDebug.help()` in your browser console to get started.");