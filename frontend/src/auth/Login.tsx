import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../context/AuthContext";
import "./Auth.css";

interface Errs { email?: string; password?: string; }

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const [form, setForm] = useState({ email: params.get("email") || "", password: "" });
  const [errs, setErrs] = useState<Errs>({});
  const [apiError, setApiError] = useState("");
  const [hint, setHint] = useState("");
  const [loading, setLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

  useEffect(() => {
    if (params.get("hint") === "exists") {
      setHint("An account with that email already exists — sign in below.");
    }
  }, [params]);

  const set = (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  const validate = () => {
    const e: Errs = {};
    if (!/^\S+@\S+\.\S+$/.test(form.email)) e.email = "Enter a valid email";
    if (!form.password) e.password = "Password is required";
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
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();

      if (res.status === 404) {
        navigate("/register?email=" + encodeURIComponent(form.email));
        return;
      }
      if (!res.ok) { setApiError(data.error || "Login failed."); return; }
      handleSuccess(data);
    } catch {
      setApiError("Network error — please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
    if (!credentialResponse.credential) return;
    setApiError("");
    try {
      const res = await fetch("/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });
      const data = await res.json();
      if (!res.ok) { setApiError(data.error || "Google sign-in failed."); return; }
      handleSuccess(data);
    } catch {
      setApiError("Network error — please try again.");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <h1>LikeHome</h1>
        <p>Welcome back — your next great stay is waiting.</p>
        <ul className="auth-perks">
          <li>📋 View all your bookings</li>
          <li>🎁 Redeem rewards at checkout</li>
          <li>🔔 Instant booking updates</li>
        </ul>
      </div>

      <div className="auth-card">
        <h2>Sign In</h2>
        <p className="auth-sub">
          No account? <Link to="/register">Create one free</Link>
        </p>

        {hint && <div className="alert alert-info">{hint}</div>}
        {apiError && <div className="alert alert-error">{apiError}</div>}

        <form onSubmit={handleSubmit} noValidate className="auth-form">
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
              placeholder="Your password"
              value={form.password}
              onChange={set("password")}
              autoComplete="current-password"
            />
            {errs.password && <span className="form-error">{errs.password}</span>}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg auth-submit"
            disabled={loading}
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        {/* Only render Google button when a client ID is configured */}
        {googleClientId && (
          <>
            <div className="auth-divider">or continue with</div>
            <div className="google-btn-wrapper">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => setApiError("Google sign-in failed — please try again.")}
                text="signin_with"
                shape="rectangular"
                width="320"
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
