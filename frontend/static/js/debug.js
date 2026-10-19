/**
 * EcoRecycle Admin Debug Console Tool with Interactive Key Prompt
 */
function getAdminKey() {
    let key = sessionStorage.getItem('eco_em_reset_key');
    if (!key) {
        key = prompt("🔐 Enter Admin Emergency Reset Key (EM_RESET_KEY):");
        if (key) {
            sessionStorage.setItem('eco_em_reset_key', key.trim());
        }
    }
    return sessionStorage.getItem('eco_em_reset_key') || '';
}

function getHeaders() {
    const adminKey = getAdminKey();
    if (!adminKey) {
        console.warn("⚠️ Operation cancelled: No admin key provided.");
        return null;
    }
    return {
        'Content-Type': 'application/json',
        'x-secret-key': adminKey
    };
}

window.dbDebug = {
    async users() {
        const headers = getHeaders();
        if (!headers) return;
        const res = await fetch('/api/admin/inspect/users', { headers });
        const data = await res.json();
        if (res.status === 403) {
            console.error("❌ Unauthorized: Invalid admin key.");
            sessionStorage.removeItem('eco_em_reset_key'); // Clear bad key
            return;
        }
        console.log(`👤 Users Table (${data.rows?.length || 0} records):`);
        console.table(data.rows);
        return data.rows;
    },

    async staff() {
        const headers = getHeaders();
        if (!headers) return;
        const res = await fetch('/api/admin/inspect/staff', { headers });
        const data = await res.json();
        if (res.status === 403) {
            console.error("❌ Unauthorized: Invalid admin key.");
            sessionStorage.removeItem('eco_em_reset_key');
            return;
        }
        console.log(`🛡️ Staff Table (${data.rows?.length || 0} records):`);
        console.table(data.rows);
        return data.rows;
    },

    async recycling() {
        const headers = getHeaders();
        if (!headers) return;
        const res = await fetch('/api/admin/inspect/recycling', { headers });
        const data = await res.json();
        if (res.status === 403) {
            console.error("❌ Unauthorized: Invalid admin key.");
            sessionStorage.removeItem('eco_em_reset_key');
            return;
        }
        console.log(`♻️ Recycling Entries Table (${data.rows?.length || 0} records):`);
        console.table(data.rows);
        return data.rows;
    },

    async wipeAllData() {
        const headers = getHeaders();
        if (!headers) return;
        if (!confirm("🚨 DANGER: Are you sure you want to delete ALL data from users, staff, and recycling tables?")) return;
        
        const res = await fetch('/api/admin/wipe-all-data', {
            method: 'POST',
            headers
        });
        const data = await res.json();
        if (res.status === 403) {
            console.error("❌ Unauthorized: Invalid admin key.");
            sessionStorage.removeItem('eco_em_reset_key');
            return;
        }
        console.log("🔥 WIPE RESULT:", data);
        return data;
    },

    async resetRedis() {
        const headers = getHeaders();
        if (!headers) return;
        
        const res = await fetch('/api/admin/reset-redis', {
            method: 'POST',
            headers
        });
        const data = await res.json();
        if (res.status === 403) {
            console.error("❌ Unauthorized: Invalid admin key.");
            sessionStorage.removeItem('eco_em_reset_key');
            return;
        }
        console.log("⚡ REDIS RESET RESULT:", data);
        return data;
    },

    clearKey() {
        sessionStorage.removeItem('eco_em_reset_key');
        console.log("🧹 Stored admin key cleared from session storage.");
    },

    help() {
        console.log(`
        💡 EcoRecycle Debug Commands (Interactive Prompt):
        --------------------------------------------------
        1. dbDebug.users()       - Show all users (prompts for key)
        2. dbDebug.staff()       - Show all staff members
        3. dbDebug.recycling()   - Show all recycling entries
        4. dbDebug.wipeAllData() - Delete all data from tables instantly
        5. dbDebug.resetRedis()  - Reset/flush Redis immediately
        6. dbDebug.clearKey()    - Clear the stored admin session key
        --------------------------------------------------
        `);
    }
};

console.log("🛠️ Interactive Admin Debugger Loaded! Type `dbDebug.help()` in your browser console.");