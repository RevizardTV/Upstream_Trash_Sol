// static/js/authguard.js
(function () {
    const userId = localStorage.getItem("user_id");
    const email = localStorage.getItem("email") || localStorage.getItem("verified_email");

    // Check for cookie session
    const hasCookie = document.cookie.split(';').some(c => c.trim().startsWith('session=') || c.trim().startsWith('user_id='));

    // If NO valid identity exists
    if (!userId && !email && !hasCookie) {
        // 1. Clear any broken state
        localStorage.clear();
        sessionStorage.clear();

        // 2. Redirect immediately
        window.location.replace("/login");

        // 3. Throw an error to freeze further JS execution in this tick
        throw new Error("Unauthorized access. Redirecting to login...");
    }
})();