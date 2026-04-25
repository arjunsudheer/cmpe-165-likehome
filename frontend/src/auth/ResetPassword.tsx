import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  AUTH_API_RESET_PASSWORD,
  AUTH_API_VALIDATE_RESET_PASSWORD,
} from "../constants";
import "./Auth.css";

interface Errs { password?: string; confirm?: string; }
type TokenStatus = "checking" | "valid" | "invalid";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = useMemo(() => (params.get("token") || "").trim(), [params]);

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errs, setErrs] = useState<Errs>({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<TokenStatus>(
    token ? "checking" : "invalid",
  );

  useEffect(() => {
    if (!token) {
      setTokenStatus("invalid");
      return;
    }

    let cancelled = false;

    const validateToken = async () => {
      setTokenStatus("checking");
      try {
        const res = await fetch(
          `${AUTH_API_VALIDATE_RESET_PASSWORD}?token=${encodeURIComponent(token)}`,
        );
        const data = await res.json();

        if (cancelled) return;

        if (!res.ok) {
          setApiError(data.error || "This reset link is invalid or has expired");
          setTokenStatus("invalid");
          return;
        }

        setApiError("");
        setTokenStatus("valid");
      } catch {
        if (cancelled) return;
        setApiError("Could not verify this reset link. Please try again.");
        setTokenStatus("invalid");
      }
    };

    void validateToken();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const validate = () => {
    const e: Errs = {};
    if (password.length < 6) e.password = "At least 6 characters";
    if (password !== confirm) e.confirm = "Passwords do not match";
    setErrs(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    setApiError("");
    if (!token) {
      setApiError("This reset link is missing a token. Open the link from your email again.");
      return;
    }
    if (tokenStatus !== "valid") {
      setApiError("This reset link is invalid or has expired");
      return;
    }
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await fetch(AUTH_API_RESET_PASSWORD, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setApiError(data.error || "Could not update password.");
        setTokenStatus("invalid");
        return;
      }
      setDone(true);
    } catch {
      setApiError("Network error — please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="auth-page">
        <div className="auth-brand">
          <div className="auth-brand-content">
            <div className="auth-brand-logo">LikeHome</div>
            <h1>You are all set.</h1>
            <p>Your password is updated. Use it the next time you sign in.</p>
          </div>
        </div>

        <div className="auth-card">
          <h2>Password updated</h2>
          <p className="auth-sub">Sign in below with your new password whenever you are ready.</p>
          <div className="alert alert-info" style={{ marginBottom: 20 }}>
            You can now sign in with your new password.
          </div>
          <button
            type="button"
            className="btn btn-primary btn-lg auth-submit"
            onClick={() => navigate("/login?hint=password-reset")}
          >
            Continue to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-brand-logo">LikeHome</div>
          <h1>Choose a new password.</h1>
          <p>Use at least six characters. Avoid reusing passwords from other sites.</p>
        </div>
      </div>

      <div className="auth-card">
        <h2>New password</h2>
        <p className="auth-sub">
          Wrong place? <Link to="/forgot-password">Request a new link</Link>
        </p>

        {!token && (
          <div className="alert alert-error" style={{ marginBottom: 16 }}>
            This page needs a valid reset link.{" "}
            <Link to="/forgot-password">Start over</Link>.
          </div>
        )}

        {token && tokenStatus === "checking" && (
          <div className="alert alert-info" style={{ marginBottom: 16 }}>
            Checking your reset link...
          </div>
        )}

        {apiError && <div className="alert alert-error">{apiError}</div>}

        {tokenStatus === "valid" && (
          <form onSubmit={handleSubmit} noValidate className="auth-form">
            <div className="form-group">
              <label className="form-label">New password</label>
              <input
                className={`form-input${errs.password ? " error" : ""}`}
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />
              {errs.password && <span className="form-error">{errs.password}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Confirm password</label>
              <input
                className={`form-input${errs.confirm ? " error" : ""}`}
                type="password"
                placeholder="Re-enter password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
              />
              {errs.confirm && <span className="form-error">{errs.confirm}</span>}
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg auth-submit"
              disabled={loading}
            >
              {loading ? "Saving…" : "Update password"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
