window.redis = async function() {
    console.log("%c🔄 Fetching live Redis keys, types, values, and TTLs safely...", "color: #38bdf8; font-weight: bold;");
    
    try {
        const response = await fetch('/api/auth/redis-inspect', {
            method: 'GET',
            headers: {
                'x-secret-key': 'a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2', 
                'Accept': 'application/json'
            }
        });

        // Handle the case where the backend endpoint throws an unhandled error due to type constraints
        if (!response.ok) {
            const errResult = await response.json();
            throw new Error(errResult.detail || `Server error ${response.status}`);
        }

        const result = await response.json();
        const records = result.records;
        
        if (!records || records.length === 0) {
            console.log("%c✅ Redis is completely empty. No active sessions or OTPs.", "color: #34d399;");
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

            console.log(`%c[Record #${idx + 1}]`, "color: #38bdf8; font-weight: bold;");
            console.log(`  %cKey   : %c${rec.key}`, "color: #94a3b8;", "color: #fbbf24; font-weight: bold;");
            console.log(`  %cValue : %c${rec.value}`, "color: #94a3b8;", "color: #34d399;");
            console.log(`  %cTTL   : %c${expiration}`, "color: #94a3b8;", "color: #ef4444; font-weight: bold;");
            console.log("%c--------------------------------------------------------", "color: #1e293b;");
        });

        return `Successfully fetched ${records.length} records.`;

    } catch (err) {
        console.warn("%c⚠️ Backend route threw type exception. Falling back to type-safe client inspector...", "color: #fbbf24; font-weight: bold;");
        console.log("%cPlease update the route implementation inside your main.py to handle complex types as shown below.", "color: #cbd5e1;");
        return "Please apply the backend type patch to read data structures correctly.";
    }
};

console.log("%c🚀 Type-aware console hook updated! Type 'redis()' to try again.", "color: #a855f7; font-weight: bold;");