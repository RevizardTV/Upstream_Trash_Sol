document.getElementById('login-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  alert('Logged in successfully as ' + email);
  window.location.href = '/';
});