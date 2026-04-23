import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { SAVED_SEARCHES_KEY, readSavedSearches, type SavedSearch } from "./savedSearches";
import "./SettingsPage.css";

function deleteSavedSearch(id: string): SavedSearch[] {
  const updated = readSavedSearches().filter((s) => s.id !== id);
  try { localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(updated)); } catch { /* ignore */ }
  return updated;
}

export default function SettingsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(readSavedSearches);

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

  const handleDelete = (id: string) => {
    setSavedSearches(deleteSavedSearch(id));
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

        {/* Saved Searches */}
        <div className="settings-card card">
          <h2 className="settings-section-title">Saved Searches</h2>
          {savedSearches.length === 0 ? (
            <p className="saved-searches-empty">
              No saved searches yet. Search for hotels and save your filters.
            </p>
          ) : (
            <ul className="saved-searches-list">
              {savedSearches.map((s) => (
                <li key={s.id} className="saved-search-item">
                  <div className="saved-search-info">
                    <span className="saved-search-destination">{s.destination}</span>
                    <span className="saved-search-meta">
                      {s.checkIn} → {s.checkOut} · {s.guests} guest{s.guests !== 1 ? "s" : ""}
                    </span>
                    <span className="saved-search-date">
                      Saved {new Date(s.savedAt).toLocaleDateString()}
                    </span>
                  </div>
                  <button
                    className="saved-search-delete"
                    onClick={() => handleDelete(s.id)}
                    aria-label={`Delete saved search for ${s.destination}`}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
