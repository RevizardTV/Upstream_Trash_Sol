document.getElementById("staffRegisterForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
        full_name: document.getElementById("fullName").value,
        email: document.getElementById("email").value,
        assigned_pincode: document.getElementById("assignedPincode").value,
        password: document.getElementById("password").value
    };

    try {
        const res = await fetch("/api/staff/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok) {
            alert("Staff account registered successfully!");
            window.location.href = "/staff-login";
        } else {
            alert("Registration failed: " + (data.detail || "Unknown error"));
        }
    } catch (err) {
        console.error("Staff registration error:", err);
    }
});