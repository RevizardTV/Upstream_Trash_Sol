// View Switcher Router
function switchView(viewId) {
  // Hide all views
  document.querySelectorAll('.view').forEach(view => {
    view.classList.remove('active');
  });

  // Remove active state from navigation buttons
  document.querySelectorAll('.nav-links button').forEach(btn => {
    btn.classList.remove('active');
  });

  // Show target view
  document.getElementById(viewId).classList.add('active');

  // Update active navigation button
  if (viewId === 'home-view') document.getElementById('nav-home').classList.add('active');
  if (viewId === 'login-view') document.getElementById('nav-login').classList.add('active');
  if (viewId === 'payment-view') document.getElementById('nav-payment').classList.add('active');
}

// Pickup Form Handler
function handlePickupSubmit(event) {
  event.preventDefault();

  const category = document.getElementById('waste-type').value;
  const weight = parseFloat(document.getElementById('weight').value) || 0;
  const rate = category === 'E-Waste' ? 25 : 12; // Example price per kg
  const total = weight * rate;

  // Update payment view DOM dynamically
  document.getElementById('summary-category').textContent = category;
  document.getElementById('summary-weight').textContent = weight + ' kg';
  document.getElementById('summary-total').textContent = '₹' + total;

  // Navigate directly to payout summary view
  switchView('payment-view');
}

// Login Form Handler
function handleLoginSubmit(event) {
  event.preventDefault();
  const email = document.getElementById('email').value;
  alert('Logged in successfully as ' + email);
  switchView('home-view');
}