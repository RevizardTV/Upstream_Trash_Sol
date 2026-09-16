/**
 * AuthGuard - Validates authentication state against backend endpoints 
 * rather than relying on tamperable sessionStorage values.
 */
(async function checkAuthSession() {
    const currentPath = window.location.pathname;

    // Endpoints that do not require authentication checks
    const publicPaths = ["/", "/login", "/register-profile", "/register-staff", "/staff-login"];
    if (publicPaths.includes(currentPath)) return;

    try {
        let checkEndpoint = "/api/user/profile";
        if (currentPath.includes("staff")) {
            checkEndpoint = "/api/admin/district-users?staff_pincode=000"; // Light verification route for staff
        }

        const response = await fetch(checkEndpoint, {
            method: "GET",
            headers: { "Cache-Control": "no-cache" }
        });

        if (response.status === 401 || response.status === 403) {
            console.warn("Unauthorized session detected by server. Redirecting...");
            window.location.href = currentPath.includes("staff") ? "/staff-login" : "/login";
        }
    } catch (err) {
        console.error("AuthGuard session check error:", err);
    }
})();