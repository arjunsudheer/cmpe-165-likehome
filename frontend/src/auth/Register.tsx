import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import GoogleAuthButton from "./GoogleAuthButton";
import "./Auth.css";

interface Errs { name?: string; email?: string; password?: string; }

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  // Pre-fill email when redirected from Login's "email not found" path
  const [form, setForm] = useState({
    name: "",
    email: params.get("email") || "",
    password: "",
  });
  const [errs, setErrs] = useState<Errs>({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

  const set = (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  const validate = () => {
    const e: Errs = {};
    if (!form.name.trim()) e.name = "Name is required";
    if (!/^\S+@\S+\.\S+$/.test(form.email)) e.email = "Enter a valid email";
    if (form.password.length < 6) e.password = "At least 6 characters";
    setErrs(e);
    return Object.keys(e).length === 0;
  };

  const handleSuccess = (data: {
    access_token: string; user_id: number; email: string; name: string | null;
  }) => {
    login({ token: data.access_token, userId: data.user_id, email: data.email, name: data.name });
    navigate("/");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);

    try {
      const res = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();

      if (res.status === 409) {
        navigate("/login?hint=exists&email=" + encodeURIComponent(form.email));
        return;
      }
      if (!res.ok) { setApiError(data.error || "Registration failed."); return; }
      handleSuccess(data);
    } catch {
      setApiError("Network error — please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-brand-logo">
            LikeHome
          </div>
          <h1>Find your perfect stay.</h1>
          <p>Create an account to start booking hotels and earning rewards on every stay.</p>
          <ul className="auth-perks">
            <li>🏨 Thousands of hotels worldwide</li>
            <li>🎁 Earn rewards on every booking</li>
            <li>💳 Save cards for fast checkout</li>
            <li>⚡ Instant booking confirmation</li>
          </ul>
        </div>
      </div>

      <div className="auth-card">
        <h2>Create Account</h2>
        <p className="auth-sub">
          Already have an account? <Link to="/login">Sign in</Link>
          {" · "}
          {/* Mirror the login screen so users can choose Google before creating a password. */}
          <Link to="/google-login">Use Google sign-in</Link>
        </p>

        {apiError && <div className="alert alert-error">{apiError}</div>}

        <form onSubmit={handleSubmit} noValidate className="auth-form">
          <div className="form-group">
            <label className="form-label">Full name</label>
            <input
              className={`form-input${errs.name ? " error" : ""}`}
              type="text"
              placeholder="Jane Smith"
              value={form.name}
              onChange={set("name")}
              autoComplete="name"
            />
            {errs.name && <span className="form-error">{errs.name}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">Email address</label>
            <input
              className={`form-input${errs.email ? " error" : ""}`}
              type="email"
              placeholder="jane@example.com"
              value={form.email}
              onChange={set("email")}
              autoComplete="email"
            />
            {errs.email && <span className="form-error">{errs.email}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className={`form-input${errs.password ? " error" : ""}`}
              type="password"
              placeholder="At least 6 characters"
              value={form.password}
              onChange={set("password")}
              autoComplete="new-password"
            />
            {errs.password && <span className="form-error">{errs.password}</span>}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg auth-submit"
            disabled={loading}
          >
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        {/* Only render Google button when a client ID is configured */}
        {googleClientId && (
          <>
            <div className="auth-divider">or continue with</div>
            <div className="google-btn-wrapper">
              <GoogleAuthButton onError={setApiError} text="signup_with" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
