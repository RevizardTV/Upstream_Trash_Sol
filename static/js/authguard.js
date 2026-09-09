(function () {
    const isAuthenticated = sessionStorage.getItem('auth') === 'true';

    if (!isAuthenticated) {
        console.warn("Unauthorized access. Redirecting to login...");
        window.location.replace("/login");
    }
})();