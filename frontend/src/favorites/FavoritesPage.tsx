import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { CARD_GRADIENTS } from "../constants";
import type { SavedSearch } from "../settings/savedSearches";
import "./FavoritesPage.css";

interface FavoriteHotel {
  hotel_id: number;
  name: string;
  city: string;
  price_per_night: string;
  rating: string;
}

export default function FavoritesPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [favorites, setFavorites] = useState<FavoriteHotel[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savedSearchError, setSavedSearchError] = useState("");

  useEffect(() => {
    if (!auth.isAuthenticated) { navigate("/login"); return; }

    const h = auth.authHeader();
    Promise.all([
      fetch("/favorites/", { headers: h }).then((r) => {
        if (!r.ok) throw new Error(`Failed to load favorites: ${r.status}`);
        return r.json();
      }),
      fetch("/saved-searches/", { headers: h }).then((r) => r.json()),
    ])
      .then(([favData, searchData]) => {
        if (Array.isArray(favData)) setFavorites(favData);
        else setError(favData.error || "Failed to load favorites.");
        setSavedSearches(searchData.results ?? []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Network error."))
      .finally(() => setLoading(false));
  }, [auth, navigate]);

  const handleRemove = async (hotelId: number) => {
    const r = await fetch(`/favorites/${hotelId}`, {
      method: "DELETE",
      headers: auth.authHeader(),
    });
    if (r.ok) setFavorites((prev) => prev.filter((h) => h.hotel_id !== hotelId));
  };

  const handleDeleteSearch = async (id: string) => {
    try {
      await fetch(`/saved-searches/${id}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json", ...auth.authHeader() },
      });
    } catch {
      setSavedSearchError("Network error — please try again.");
      return;
    }
    setSavedSearches((prev) => prev.filter((s) => s.id !== id));
  };

  const loadSavedSearch = (savedSearch: SavedSearch) => {
    navigate(
      `/?destination=${encodeURIComponent(savedSearch.destination)}&check_in=${savedSearch.checkIn}&check_out=${savedSearch.checkOut}&guests=${savedSearch.guests}&saved_search_id=${savedSearch.id}`,
    );
  };

  return (
    <div className="fav-page">
      <div className="fav-container">
        <h1 className="fav-title">Saved</h1>

        {error && <div className="alert alert-error">{error}</div>}

        <section className="fav-section" aria-labelledby="saved-hotels-heading">
          <h2 id="saved-hotels-heading" className="fav-section-title">Hotels</h2>
          {loading ? (
            <div className="fav-skeletons">
              {[1, 2, 3].map((i) => <div key={i} className="fav-skeleton" />)}
            </div>
          ) : favorites.length === 0 ? (
            <div className="fav-empty fav-empty--compact">
              <div className="fav-empty-icon">♡</div>
              <h3>No saved hotels yet</h3>
              <p>Tap the heart on any hotel page to save it here.</p>
              <Link to="/" className="btn btn-primary">Browse Hotels</Link>
            </div>
          ) : (
            <div className="fav-grid">
              {favorites.map((hotel) => (
                <FavoriteCard key={hotel.hotel_id} hotel={hotel} onRemove={handleRemove} />
              ))}
            </div>
          )}
        </section>

        <section className="fav-section" aria-labelledby="saved-searches-heading">
          <h2 id="saved-searches-heading" className="fav-section-title">Saved searches</h2>
          {savedSearchError && <div className="alert alert-error">{savedSearchError}</div>}
          {savedSearches.length === 0 ? (
            <p className="saved-searches-empty">
              No saved searches yet. Search for hotels and save your filters.
            </p>
          ) : (
            <ul className="saved-searches-list">
              {savedSearches.map((s) => (
                <li key={s.id} className="saved-search-item">
                  <div className="saved-search-info">
                    <span
                      className="saved-search-destination"
                      role="link"
                      tabIndex={0}
                      onClick={() => loadSavedSearch(s)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          loadSavedSearch(s);
                        }
                      }}
                    >
                      {s.destination}
                    </span>
                    <span className="saved-search-meta">
                      {s.checkIn} → {s.checkOut} · {s.guests} guest{s.guests !== 1 ? "s" : ""}
                    </span>
                    <span className="saved-search-date">
                      Saved {s.savedAt ? new Date(s.savedAt).toLocaleDateString() : "—"}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="saved-search-delete"
                    onClick={() => handleDeleteSearch(s.id)}
                    aria-label={`Delete saved search for ${s.destination}`}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function FavoriteCard({ hotel, onRemove }: { hotel: FavoriteHotel; onRemove: (id: number) => void }) {
  const gradient = CARD_GRADIENTS[hotel.hotel_id % CARD_GRADIENTS.length];
  const rating = parseFloat(hotel.rating);
  const filled = Math.round(rating);

  return (
    <div className="fav-card card">
      <div className="fav-card-banner" style={{ background: gradient }} />
      <div className="fav-card-body">
        <div className="fav-card-header">
          <div>
            <Link to={`/hotel/${hotel.hotel_id}`} className="fav-card-name">
              {hotel.name}
            </Link>
            <p className="fav-card-city">📍 {hotel.city}</p>
          </div>
          <button
            className="fav-remove-btn"
            onClick={() => onRemove(hotel.hotel_id)}
            aria-label={`Remove ${hotel.name} from favorites`}
            title="Remove from saved"
          >
            ♥
          </button>
        </div>

        <div className="fav-card-footer">
          <span className="fav-stars">
            {[1, 2, 3, 4, 5].map((n) => (
              <span key={n} className={n <= filled ? "star filled" : "star"}>★</span>
            ))}
            <span className="fav-rating-num">{rating.toFixed(1)}</span>
          </span>
          <span className="fav-price">
            <strong>${parseFloat(hotel.price_per_night).toFixed(0)}</strong>
            <span className="fav-price-label">/night</span>
          </span>
        </div>

        <Link to={`/hotel/${hotel.hotel_id}`} className="btn btn-primary fav-view-btn">
          View Hotel
        </Link>
      </div>
    </div>
  );
}
