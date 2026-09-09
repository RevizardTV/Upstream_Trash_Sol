// Parse query parameters from the URL
const urlParams = new URLSearchParams(window.location.search);
const category = urlParams.get('category') || 'E-Waste';
const weight = parseFloat(urlParams.get('weight')) || 10;

const rate = category === 'E-Waste' ? 25 : 12;
const total = weight * rate;

// Render dynamic fields
document.getElementById('summary-category').textContent = category;
document.getElementById('summary-weight').textContent = weight + ' kg';
document.getElementById('summary-total').textContent = '₹' + total;

document.getElementById('confirm-btn').addEventListener('click', function() {
  alert('Pickup request & payout record confirmed!');
  window.location.href = '/';
});