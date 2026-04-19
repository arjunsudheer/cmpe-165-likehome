import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { SAVED_SEARCHES_KEY, readSavedSearches, type SavedSearch } from "./savedSearches";
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

function deleteSavedSearch(id: string): SavedSearch[] {
  const updated = readSavedSearches().filter((s) => s.id !== id);
  try { localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(updated)); } catch { /* ignore */ }
  return updated;
}

export default function SettingsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [notificationsEnabled, setNotificationsEnabled] = useState(readNotifPref);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(readSavedSearches);

  useEffect(() => {
    if (!auth.isAuthenticated) {
      navigate("/login");
      return;
    }
  }, [auth.isAuthenticated, navigate]);

  if (!auth.isAuthenticated) return null;

  const handleToggle = () => {
    const newValue = !notificationsEnabled;
    try { localStorage.setItem(NOTIF_KEY, String(newValue)); } catch { /* ignore */ }
    setNotificationsEnabled(newValue);
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
