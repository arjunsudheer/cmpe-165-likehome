import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useEffect, useState } from "react";
import "./Navbar.css";

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

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

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
