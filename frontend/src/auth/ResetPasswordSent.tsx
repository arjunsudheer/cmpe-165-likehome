import { Link, useLocation } from "react-router-dom";
import "./Auth.css";

type LocationState = { email?: string; devToken?: string };

export default function ResetPasswordSent() {
  const location = useLocation();
  const state = (location.state || {}) as LocationState;
  const email = state.email || "your inbox";
  const devToken = state.devToken;

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-brand-logo">LikeHome</div>
          <h1>Check your email.</h1>
          <p>
            If an account exists for that address, we have sent steps to reset your password.
            Open the message on any device to continue.
          </p>
        </div>
      </div>

      <div className="auth-card">
        <h2>Almost there</h2>
        <p className="auth-sub">
          Look for an email sent to <strong>{email}</strong>. Follow the link inside to set a
          new password.
        </p>

        <div className="alert alert-info" style={{ marginBottom: 20 }}>
          Did not get it? Wait a few minutes, check spam, or{" "}
          <Link to="/forgot-password">try again</Link>.
        </div>

        {devToken && (
          <div className="alert alert-info" style={{ marginBottom: 20 }}>
            <strong>Development:</strong> your reset token is shown below. In production, this
            would only appear in email.
            <div
              style={{
                marginTop: 10,
                wordBreak: "break-all",
                fontFamily: "monospace",
                fontSize: 13,
              }}
            >
              {devToken}
            </div>
            <Link
              to={`/reset-password?token=${encodeURIComponent(devToken)}`}
              style={{ display: "inline-block", marginTop: 12 }}
            >
              Open reset page with this token →
            </Link>
          </div>
        )}

        <Link to="/login" className="btn btn-secondary btn-lg auth-submit">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
