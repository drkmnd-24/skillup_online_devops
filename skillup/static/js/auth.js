// Simple stubs matching earlier behavior (session-based hybrid login)
async function login(event) {
  event.preventDefault();
  const knox_id = document.getElementById("knox_id").value.trim();
  const password = document.getElementById("password").value.trim();
  const serverError = document.getElementById("server-error");
  serverError.textContent = "";
  if (!knox_id || password.length < 8) {
    serverError.textContent = "Invalid Knox ID or Password";
    return;
  }
  try {
    const res = await fetch("/api/hybrid-login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ knox_id, password }),
      credentials: "include",
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem("knox_id", knox_id);
      alert("Login successful");
      window.location.href = "/index/";
    } else {
      serverError.textContent = data.detail || "Login failed";
    }
  } catch (e) {
    serverError.textContent = "Internal Server Error, please contact the admin team";
  }
}

export function logout() {
  localStorage.removeItem("knox_id");
  window.location.href = "/login/";
}

async function register(event) {
  event.preventDefault();
  alert("Register endpoint wired in backend serializers; build your UI here as needed.");
}

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) loginForm.addEventListener("submit", login);

  const togglePassword = document.getElementById("toggle-password");
  const passwordField = document.getElementById("password");
  if (togglePassword && passwordField) {
    togglePassword.addEventListener("change", function () {
      passwordField.type = this.checked ? "text" : "password";
    });
  }

  const registerForm = document.getElementById("register-form");
  if (registerForm) registerForm.addEventListener("submit", register);
});
