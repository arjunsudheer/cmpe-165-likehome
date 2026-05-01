import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useEffect, useState, useRef } from "react";
import "./Navbar.css";

interface Notification {
  id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

function applyTheme(theme: "dark" | "light") {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("lh_theme", theme);
}

// eslint-disable-next-line react-refresh/only-export-components
export function initTheme() {
  const saved = localStorage.getItem("lh_theme") as "dark" | "light" | null;
  applyTheme(saved ?? "dark");
}

export default function Navbar() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    return (localStorage.getItem("lh_theme") as "dark" | "light") ?? "dark";
  });
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!auth.isAuthenticated || !auth.token) return;

    const fetchNotifications = () => {
      fetch("/auth/notifications", {
        headers: { Authorization: `Bearer ${auth.token}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to fetch notifications");
          return res.json();
        })
        .then((data) => setNotifications(data))
        .catch((err) => console.error("Failed to fetch notifications:", err));
    };

    // Fetch immediately on mount or auth change
    fetchNotifications();

    // Poll every 60 seconds to get new notifications without a reload
    const intervalId = setInterval(fetchNotifications, 60000);

    return () => clearInterval(intervalId);
  }, [auth.isAuthenticated, auth.token]);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const handleMarkRead = async (id: number) => {
    try {
      await fetch(`/auth/notifications/${id}/mark-read`, {
        method: "POST",
        headers: { Authorization: `Bearer ${auth.token}` },
      });
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error("Failed to mark notification as read", err);
    }
  };

  const toggleTheme = () => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  };

  const handleLogout = () => {
    auth.logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-logo">
          LikeHome
        </NavLink>

        <nav className="navbar-links">
          <NavLink
            to="/"
            end
            className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
          >
            Hotels
          </NavLink>
          <NavLink
            to="/rewards"
            className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
          >
            Rewards
          </NavLink>

          {auth.isAuthenticated ? (
            <>
              <NavLink
                to="/my-bookings"
                className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
              >
                My Bookings
              </NavLink>
              <NavLink
                to="/favorites"
                className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
              >
                Saved
              </NavLink>
              <NavLink
                to="/settings"
                className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
              >
                Settings
              </NavLink>

              <span className="nav-divider" aria-hidden="true" />
              <div className="nav-notifications" ref={dropdownRef}>
                <button
                  className="notification-bell"
                  onClick={() => setShowNotifications(!showNotifications)}
                  aria-label="Toggle notifications"
                >
                  🔔
                  {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
                </button>
                {showNotifications && (
                  <div className="notification-dropdown">
                    <div className="notification-header">Notifications</div>
                    <div className="notification-list">
                      {notifications.length === 0 ? (
                        <div className="notification-empty">No new notifications</div>
                      ) : (
                        notifications.map((n) => (
                          <div 
                            key={n.id} 
                            className={`notification-item ${!n.is_read ? 'unread' : ''}`}
                            onClick={() => !n.is_read && handleMarkRead(n.id)}
                          >
                            <p>{n.message}</p>
                            <span className="notification-time">{new Date(n.created_at).toLocaleString()}</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
              <span className="nav-divider" aria-hidden="true" />
              <span className="nav-name">{auth.name || auth.email}</span>
              <button className="nav-logout-btn" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <NavLink
              to="/login"
              className={({ isActive }) =>
                "btn btn-primary nav-login" + (isActive ? " active" : "")
              }
            >
              Login
            </NavLink>
          )}

          {/* Theme toggle */}
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
        </nav>
      </div>
    </header>
  );
}
