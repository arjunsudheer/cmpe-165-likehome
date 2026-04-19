import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Navbar.css";

export default function Navbar() {
  const auth = useAuth();
  const navigate = useNavigate();

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
          {/* Page navigation links */}
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
                to="/settings"
                className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
              >
                Settings
              </NavLink>

              {/* Vertical divider clearly separates page links from account area */}
              <span className="nav-divider" aria-hidden="true" />

              {/* Plain text — not a link, not a button */}
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
        </nav>
      </div>
    </header>
  );
}
