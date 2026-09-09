document.getElementById("confirmBtn").addEventListener("click", () => {
    alert("Payment payout request recorded!");
});

document.getElementById("logoutBtn").addEventListener("click", () => {
    sessionStorage.clear();
    window.location.replace("/login");
});