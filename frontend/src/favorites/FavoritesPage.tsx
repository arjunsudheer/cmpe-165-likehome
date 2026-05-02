import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { CARD_GRADIENTS } from "../constants";
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!auth.isAuthenticated) { navigate("/login"); return; }

    fetch("/favorites/", { headers: auth.authHeader() })
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load favorites: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (Array.isArray(data)) setFavorites(data);
        else setError(data.error || "Failed to load favorites.");
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

  return (
    <div className="fav-page">
      <div className="fav-container">
        <h1 className="fav-title">Saved Hotels</h1>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="fav-skeletons">
            {[1, 2, 3].map((i) => <div key={i} className="fav-skeleton" />)}
          </div>
        ) : favorites.length === 0 ? (
          <div className="fav-empty">
            <div className="fav-empty-icon">♡</div>
            <h2>No saved hotels yet</h2>
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
