// frontend/static/js/redis_check.js

window.checkRedisEntries = async function() {
    try {
        console.log("🔍 Fetching Redis entries from backend...");
        const response = await fetch('http://localhost:8000/api/redis/entries', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }

        const data = await response.json();
        console.log("📊 --- Redis Entries Inspection ---");
        console.table(data.entries || data);
        return data;
    } catch (error) {
        console.error("❌ Failed to fetch Redis entries:", error);
    }
};

// Log a helper message to the browser console when loaded
console.log("💡 Redis Inspector ready! Type `checkRedisEntries()` in your browser console to view all entries.");