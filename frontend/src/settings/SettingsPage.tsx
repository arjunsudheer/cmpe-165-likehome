import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { readSavedSearches, type SavedSearch } from "./savedSearches";
import "./SettingsPage.css";

async function deleteSavedSearch(id: string, token: string) {
    await fetch(`/saved-searches/${id}`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    })
  }

export default function SettingsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(readSavedSearches);
  const [error, setError] = useState("")

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
      fetch("/saved-searches/", {
        headers: { Authorization: `Bearer ${auth.token}` },
      })
        .then((res) => res.json())
        .then((data) => setSavedSearches(data.results ?? []))
        .catch((err) => console.error("Failed to fetch saved searches", err));
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

  const handleDelete = async(id: string) => {
    try {
      await deleteSavedSearch(id, auth.token,);
    }
    catch { setError("Network error — please try again."); }
    setSavedSearches(prev => prev.filter(s => s.id !== id));
  };

  const loadSavedSearch = (savedSearch: SavedSearch) => {
    navigate(`/?destination=${encodeURIComponent(savedSearch.destination)}&checkIn=${savedSearch.checkIn}&checkOut=${savedSearch.checkOut}&guests=${savedSearch.guests}&savedSearchId=${savedSearch.id}`);
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
          {error && <div className="alert alert-error">{error}</div>}
          {savedSearches.length === 0 ? (
            <p className="saved-searches-empty">
              No saved searches yet. Search for hotels and save your filters.
            </p>
          ) : (
            <ul className="saved-searches-list">
              {savedSearches.map((s) => (
                <li key={s.id} className="saved-search-item">
                  <div className="saved-search-info">
                    <span className="saved-search-destination" onClick={() => loadSavedSearch(s)}>{s.destination}</span>
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
