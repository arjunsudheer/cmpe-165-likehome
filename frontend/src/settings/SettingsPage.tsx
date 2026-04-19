import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./SettingsPage.css";

const NOTIF_KEY = "lh_notifications_enabled";

function readNotifPref(): boolean {
  try {
    const raw = localStorage.getItem(NOTIF_KEY);
    return raw === null ? true : raw === "true";
  } catch {
    return true;
  }
}

export default function SettingsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [notificationsEnabled, setNotificationsEnabled] = useState(readNotifPref);

  useEffect(() => {
    if (!auth.isAuthenticated) navigate("/login");
  }, [auth.isAuthenticated, navigate]);

  const handleToggle = () => {
    const newValue = !notificationsEnabled;
    try { localStorage.setItem(NOTIF_KEY, String(newValue)); } catch { /* ignore */ }
    setNotificationsEnabled(newValue);
  };

  return (
    <div className="settings-page">
      <div className="settings-container">
        <h1 className="settings-page-title">Settings</h1>

        <div className="settings-card card">
          <h2 className="settings-section-title">Notifications</h2>

          <div className="settings-row">
            <div className="settings-row-info">
              <span className="settings-row-label">Email notifications</span>
              <span className="settings-row-desc">
                Receive booking confirmations, updates, and reminders by email.
              </span>
            </div>
            <button
              className={`toggle-btn${notificationsEnabled ? " toggle-btn--on" : ""}`}
              onClick={handleToggle}
              aria-pressed={notificationsEnabled}
              aria-label="Toggle email notifications"
            >
              <span className="toggle-knob" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
