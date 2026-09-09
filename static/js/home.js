const goToLoginBtn = document.getElementById("goToLogin");

if (goToLoginBtn) {
    goToLoginBtn.addEventListener("click", () => {
        window.location.href = "/login";
    });
}