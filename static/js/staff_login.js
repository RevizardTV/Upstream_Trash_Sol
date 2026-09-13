document.getElementById("staffLoginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
        email: document.getElementById("loginEmail").value,
        password: document.getElementById("loginPassword").value
    };

    try {
        const res = await fetch("/api/staff/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok) {
            localStorage.setItem("staff_id", data.staff_id);
            localStorage.setItem("staff_email", data.email);
            localStorage.setItem("assigned_pincode", data.assigned_pincode);
            window.location.href = "/staff-dashboard";
        } else {
            alert("Authentication failed: " + (data.detail || "Invalid credentials"));
        }
    } catch (err) {
        console.error("Staff login error:", err);
    }
});