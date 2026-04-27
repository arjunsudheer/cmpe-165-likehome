import { Link, useSearchParams } from "react-router-dom";
import { useState } from "react";
import GoogleAuthButton from "./GoogleAuthButton";
import "./Auth.css";

export default function GoogleLoginPage() {
  const [params] = useSearchParams();
  const [apiError, setApiError] = useState("");
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";
  // Derive the hint from the URL so the page stays in sync without an extra render.
  const hint = params.get("hint") === "exists"
    ? "Your account already exists. You can continue with the same Google account below."
    : "";

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-brand-logo">
            LikeHome
          </div>
          <h1>Sign in with one tap.</h1>
          <p>Use your Google account to sign in quickly or create your LikeHome account on first use.</p>
          <ul className="auth-perks">
            <li>🔐 Verified Google identity token</li>
            <li>⚡ Automatic account creation on first sign-in</li>
            <li>🏨 Instant access to bookings, rewards, and checkout</li>
            <li>🧩 Falls back cleanly to email sign-in when you need it</li>
          </ul>
        </div>
      </div>

      <div className="auth-card">
        <h2>Continue with Google</h2>
        <p className="auth-sub">
          Prefer email instead? <Link to="/login">Sign in manually</Link> or <Link to="/register">create an account</Link>
        </p>

        {hint && <div className="alert alert-info">{hint}</div>}
        {apiError && <div className="alert alert-error">{apiError}</div>}

        {googleClientId ? (
          <>
            <div className="auth-divider">google sign-in</div>
            <div className="google-btn-wrapper">
              <GoogleAuthButton onError={setApiError} text="continue_with" />
            </div>
          </>
        ) : (
          <>
            <div className="alert alert-info">
              Google sign-in is not configured in this frontend environment yet.
            </div>
            <p className="auth-sub">
              Add <code>VITE_GOOGLE_CLIENT_ID</code> to the frontend environment, or use the regular <Link to="/login">email login page</Link>.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
