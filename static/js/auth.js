// Validation logic for the Register page ONLY.
// This file is separate from script.js (the main app's logic) on purpose --
// keeps auth-page concerns isolated from the resume/JD analysis features.

const registerForm = document.getElementById('registerForm');

if (registerForm) {
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const confirmInput = document.getElementById('confirmPassword');

  const usernameError = document.getElementById('usernameError');
  const passwordError = document.getElementById('passwordError');
  const confirmError = document.getElementById('confirmError');
  const strengthBar = document.getElementById('strengthBar');
  const submitBtn = document.getElementById('submitBtn');

  function validateUsername() {
    const value = usernameInput.value.trim();
    const pattern = /^[a-zA-Z0-9_]{3,20}$/;

    if (!value) {
      usernameError.textContent = '';
      return false;
    }
    if (!pattern.test(value)) {
      usernameError.textContent = 'Username must be 3-20 characters: letters, numbers, underscore only.';
      return false;
    }
    usernameError.textContent = '';
    return true;
  }

  function checkPasswordStrength(password) {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score; // 0 to 4
  }

  function validatePassword() {
    const value = passwordInput.value;
    const score = checkPasswordStrength(value);

    // Update the strength bar visually
    const percentages = ['5%', '25%', '50%', '75%', '100%'];
    const colors = ['#C2703B', '#C2703B', '#D4A03B', '#8FA83B', '#0F9D8C'];
    strengthBar.style.width = value ? percentages[score] : '0%';
    strengthBar.style.background = colors[score];

    if (!value) {
      passwordError.textContent = '';
      return false;
    }
    if (value.length < 8) {
      passwordError.textContent = 'Password must be at least 8 characters.';
      return false;
    }
    if (!/[A-Z]/.test(value)) {
      passwordError.textContent = 'Password must include at least 1 uppercase letter.';
      return false;
    }
    if (!/[0-9]/.test(value)) {
      passwordError.textContent = 'Password must include at least 1 number.';
      return false;
    }
    if (!/[^A-Za-z0-9]/.test(value)) {
      passwordError.textContent = 'Password must include at least 1 special character.';
      return false;
    }
    passwordError.textContent = '';
    return true;
  }

  function validateConfirmPassword() {
    if (!confirmInput.value) {
      confirmError.textContent = '';
      return false;
    }
    if (confirmInput.value !== passwordInput.value) {
      confirmError.textContent = 'Passwords do not match.';
      return false;
    }
    confirmError.textContent = '';
    return true;
  }

  function updateSubmitState() {
    const isValid =
      validateUsername() &&
      validatePassword() &&
      validateConfirmPassword();
    submitBtn.disabled = !isValid;
  }

  usernameInput.addEventListener('input', updateSubmitState);
  passwordInput.addEventListener('input', updateSubmitState);
  confirmInput.addEventListener('input', updateSubmitState);

  registerForm.addEventListener('submit', (e) => {
    const isValid =
      validateUsername() &&
      validatePassword() &&
      validateConfirmPassword();

    if (!isValid) {
      e.preventDefault(); // stop submission if something's still invalid
    }
  });

  // Start with the button enabled-looking but real validation runs on input;
  // this just makes sure the very first render is checked once too.
  updateSubmitState();
}
