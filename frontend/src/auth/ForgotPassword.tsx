import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AUTH_API_FORGOT_PASSWORD } from "../constants";
import "./Auth.css";

interface Errs { email?: string; }

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [errs, setErrs] = useState<Errs>({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const e: Errs = {};
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) e.email = "Enter a valid email";
    setErrs(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await fetch(AUTH_API_FORGOT_PASSWORD, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setApiError(data.error || "Something went wrong.");
        return;
      }
      navigate("/forgot-password/sent", {
        state: {
          email: email.trim(),
          devToken: typeof data.reset_token === "string" ? data.reset_token : undefined,
        },
      });
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
          <div className="auth-brand-logo">LikeHome</div>
          <h1>Reset your password.</h1>
          <p>
            We will email you a secure link to choose a new password. It only takes a minute.
          </p>
          <ul className="auth-perks">
            <li>🔒 Links expire after one hour</li>
            <li>✉️ Check spam if you do not see our message</li>
            <li>↩️ You can request another link anytime</li>
          </ul>
        </div>
      </div>

      <div className="auth-card">
        <h2>Forgot password</h2>
        <p className="auth-sub">
          Remembered it? <Link to="/login">Back to sign in</Link>
        </p>

        {apiError && <div className="alert alert-error">{apiError}</div>}

        <form onSubmit={handleSubmit} noValidate className="auth-form">
          <div className="form-group">
            <label className="form-label">Email address</label>
            <input
              className={`form-input${errs.email ? " error" : ""}`}
              type="email"
              placeholder="jane@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
            {errs.email && <span className="form-error">{errs.email}</span>}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg auth-submit"
            disabled={loading}
          >
            {loading ? "Sending…" : "Send reset link"}
          </button>
        </form>
      </div>
    </div>
  );
}
