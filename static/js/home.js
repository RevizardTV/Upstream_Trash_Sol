document.getElementById('pickup-form').addEventListener('submit', function(e) {
  e.preventDefault();

  const category = document.getElementById('waste-type').value;
  const weight = document.getElementById('weight').value;

  // Pass payload to payment page via URL query parameters
  window.location.href = `/payment?category=${encodeURIComponent(category)}&weight=${encodeURIComponent(weight)}`;
});