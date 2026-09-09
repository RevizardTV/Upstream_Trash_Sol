document.addEventListener("DOMContentLoaded", () => {
    // 1. Session Auth Check
    const isAuthenticated = document.cookie.includes("session_authenticated=true");
    if (!isAuthenticated) {
        window.location.href = "/login";
        return;
    }

    // 2. Programmatic Navigation Handlers (Optional parameter passing)
    window.navigateToRegister = (defaultCategory = '') => {
        const url = defaultCategory ? `/register-payment?category=${defaultCategory}` : '/register-payment';
        window.location.href = url;
    };

    window.navigateToPending = (filterStatus = '') => {
        const url = filterStatus ? `/pending-payments?status=${filterStatus}` : '/pending-payments';
        window.location.href = url;
    };
});