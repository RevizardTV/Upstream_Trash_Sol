document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const email = document.getElementById("email").value;

    // Simulate auth state setting upon successful login
    sessionStorage.setItem("auth", "true");
    sessionStorage.setItem("user_email", email);

    window.location.href = "/payment";
});