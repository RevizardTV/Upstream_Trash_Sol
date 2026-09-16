(function () {
    const userId = localStorage.getItem("user_id");
    const verifiedEmail = sessionStorage.getItem("verified_email") || localStorage.getItem("verified_email");
    
    // Check if a backend session cookie exists
    const hasSessionCookie = document.cookie.split(";").some(item => item.trim().startsWith("session="));

    // Allow entry if EITHER frontend storage OR backend session cookie is present
    if (!userId && !verifiedEmail && !hasSessionCookie) {
        window.location.replace("/login");
    }
})();