// frontend/src/Register.jsx
import { useState } from "react";
import "./Register.css";

export default function Register() {
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("");

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = "Please enter your name";
    if (!/^\S+@\S+\.\S+$/.test(form.email)) e.email = "Please enter a valid email";
    if (form.password.length < 6) e.password = "Password must be at least 6 characters";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleChange = (k) => (ev) =>
    setForm({ ...form, [k]: ev.target.value });

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    setStatus("");
    if (!validate()) return;

    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json();
        setStatus("Failed: " + (data.message || res.statusText));
        return;
      }
      setStatus("Registration successful!");
      setForm({ name: "", email: "", password: "" });
    } catch (err) {
      setStatus("Network error: " + err.message);
    }
  };

  return (
    <div className="register-container">
      {/* Left side */}
      <div className="register-brand">
        <h2>LikeHome</h2>
        <p>Find your perfect home and build your dream life</p>
        
        <div className="register-features">
          <div className="feature">
            <div className="feature-icon">🏠</div>
            <div className="feature-text">
              <h3>Wide Selection</h3>
              <p>Browse thousands of properties</p>
            </div>
          </div>
          
          <div className="feature">
            <div className="feature-icon">🔒</div>
            <div className="feature-text">
              <h3>Safe & Secure</h3>
              <p>Your data is protected with us</p>
            </div>
          </div>
          
          <div className="feature">
            <div className="feature-icon">⚡</div>
            <div className="feature-text">
              <h3>Quick Process</h3>
              <p>Register and start in minutes</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right side */}
      <div className="register-card">
        <div className="register-content">
          <div className="register-header">
            <h1>Create Account</h1>
            <p>Join us today and start exploring</p>
          </div>

          <form onSubmit={handleSubmit} noValidate className="register-form">
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input
                id="name"
                type="text"
                value={form.name}
                onChange={handleChange("name")}
                placeholder="John Doe"
                className={errors.name ? "input-error" : ""}
              />
              {errors.name && <span className="error-message">{errors.name}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={handleChange("email")}
                placeholder="your@email.com"
                className={errors.email ? "input-error" : ""}
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={form.password}
                onChange={handleChange("password")}
                placeholder="At least 6 characters"
                className={errors.password ? "input-error" : ""}
              />
              {errors.password && (
                <span className="error-message">{errors.password}</span>
              )}
            </div>

            <button type="submit" className="submit-button">
              Create Account
            </button>
          </form>

          {status && (
            <div className={`status-message ${status.includes("successful") ? "success" : "error"}`}>
              {status}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}