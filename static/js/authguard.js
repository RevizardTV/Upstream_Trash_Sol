(function () {
    // 1. Fetch all possible auth indicators
    const userId = localStorage.getItem("user_id");
    const email = localStorage.getItem("email") || localStorage.getItem("verified_email");
    
    // Check cookies for session/user_id
    const hasSessionCookie = document.cookie.split(";").some(item => {
        const cookie = item.trim();
        return cookie.startsWith("session=") || cookie.startsWith("user_id=");
    });

    // 2. If NO valid auth indicators are found, redirect immediately
    if (!userId && !email && !hasSessionCookie) {
        // Use location.replace so the user cannot click 'Back' to return to this page
        window.location.replace("/login");
    }
})();