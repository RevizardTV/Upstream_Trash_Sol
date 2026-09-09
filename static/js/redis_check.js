/**
 * Global Redis Inspection & Management Console Toolkit
 */

const ADMIN_SECRET_KEY = "a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2";

// 1. Live Redis Inspector
window.redis = async function() {
    console.log("%c🔄 Fetching live Redis keys, types, values, and TTLs safely...", "color: #38bdf8; font-weight: bold;");
    
    try {
        const response = await fetch('/api/auth/redis-inspect', {
            method: 'GET',
            headers: {
                'x-secret-key': ADMIN_SECRET_KEY, 
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            let errorMsg = `Server returned status ${response.status}`;
            try {
                const errResult = await response.json();
                errorMsg = errResult.detail || errorMsg;
            } catch (_) {
                // Endpoint returned non-JSON response (e.g., HTML 404 page)
            }
            throw new Error(errorMsg);
        }

        const result = await response.json();
        const records = result.records;
        
        if (!records || records.length === 0) {
            console.log("%c✅ Redis is completely empty. No active sessions or OTP locks.", "color: #34d399; font-weight: bold;");
            return "Scan complete.";
        }

        console.log(`%c📊 Active Redis database dump (${records.length} items):`, "color: #e2e8f0; font-weight: bold;");
        console.log("%c========================================================", "color: #334155;");

        records.forEach((rec, idx) => {
            let expiration = "";
            if (rec.ttl_seconds === -1) expiration = "Persistent (No expiry)";
            else if (rec.ttl_seconds === -2) expiration = "Expired/Invalid";
            else {
                const mins = Math.floor(rec.ttl_seconds / 60);
                const secs = rec.ttl_seconds % 60;
                expiration = `${rec.ttl_seconds}s remaining (${mins}m ${secs}s)`;
            }

            // Pretty print formatted JSON values if applicable
            let parsedValue = rec.value;
            try {
                parsedValue = JSON.parse(rec.value);
            } catch (_) {}

            console.log(`%c[Record #${idx + 1}]`, "color: #38bdf8; font-weight: bold;");
            console.log(`  %cKey   : %c${rec.key}`, "color: #94a3b8;", "color: #fbbf24; font-weight: bold;");
            console.log(`  %cTTL   : %c${expiration}`, "color: #94a3b8;", "color: #ef4444; font-weight: bold;");
            console.log("  %cValue :", "color: #94a3b8;", parsedValue);
            console.log("%c--------------------------------------------------------", "color: #1e293b;");
        });

        return `Successfully fetched ${records.length} records.`;

    } catch (err) {
        console.warn(`%c⚠️ Inspector Error: ${err.message}`, "color: #fbbf24; font-weight: bold;");
        if (err.message.includes("404")) {
            console.log("%c💡 Note: Ensure the endpoint '@app.get(\"/api/auth/redis-inspect\")' is added to main.py", "color: #cbd5e1;");
        }
        return "Inspection halted.";
    }
};

// 2. Global Database Reset Utility
window.resetDatabase = async function() {
    console.log("%c⚡ Sending emergency reset command to Redis...", "color: #f59e0b; font-weight: bold;");
    try {
        const response = await fetch("/emergency-reset", {
            method: "POST",
            headers: {
                "X-Secret-Key": ADMIN_SECRET_KEY 
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log("%c✅ Redis database cleared successfully!", "color: #34d399; font-weight: bold;", data);
            sessionStorage.clear();
            console.log("%c🔄 Session storage cleared. Reloading page...", "color: #38bdf8;");
            window.location.reload(); 
        } else {
            console.error("❌ Reset failed. Verify key or route configuration.");
        }
    } catch (err) {
        console.error("❌ Reset request failed:", err);
    }
};

// 3. Clear Local Session Helper
window.clearSession = function() {
    sessionStorage.clear();
    console.log("%c🧹 Session storage cleared successfully.", "color: #34d399;");
};

console.log("%c🚀 Redis Utilities Loaded!", "color: #a855f7; font-weight: bold;");
console.log("  • Type %credis()%c to view active database entries.", "color: #fbbf24; font-weight: bold;", "");
console.log("  • Type %cresetDatabase()%c to flush all keys & rate limits.", "color: #ef4444; font-weight: bold;", "");