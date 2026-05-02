import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./SettingsPage.css";

export default function SettingsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  useEffect(() => {
    if (!auth.isAuthenticated) {
      navigate("/login");
      return;
    }
    
    // Fetch settings
    fetch("/auth/settings", {
      headers: {
        Authorization: `Bearer ${auth.token}`,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.send_reminder_email !== undefined) {
          setNotificationsEnabled(data.send_reminder_email);
        }
      })
      .catch((err) => console.error("Failed to fetch settings", err));
  }, [auth.isAuthenticated, auth.token, navigate]);

  if (!auth.isAuthenticated) return null;

  const handleToggle = async () => {
    const newValue = !notificationsEnabled;
    // Optimistic update
    setNotificationsEnabled(newValue);
    
    try {
      const res = await fetch("/auth/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${auth.token}`,
        },
        body: JSON.stringify({ send_reminder_email: newValue }),
      });
      if (!res.ok) {
        // Revert on failure
        setNotificationsEnabled(!newValue);
      }
    } catch (error) {
      console.error("Failed to update settings", error);
      setNotificationsEnabled(!newValue);
    }
  };

  return (
    <div className="settings-page">
      <div className="settings-container">
        <h1 className="settings-page-title">Settings</h1>

        {/* Notifications */}
        <div className="settings-card card">
          <h2 className="settings-section-title">Notifications</h2>
          <div className="settings-row">
            <div className="settings-row-info">
              <span className="settings-row-label">Booking Reminders</span>
              <span className="settings-row-desc">
                Receive reminders about your upcoming bookings via in-app notifications.
              </span>
            </div>
            <button
              className={`toggle-btn${notificationsEnabled ? " toggle-btn--on" : ""}`}
              onClick={handleToggle}
              aria-pressed={notificationsEnabled}
              aria-label="Toggle booking reminders"
            >
              <span className="toggle-knob" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
