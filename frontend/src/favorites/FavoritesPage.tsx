import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { CARD_GRADIENTS } from "../constants";
import { type SavedSearch } from "../settings/savedSearches";
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
  const [activeTab, setActiveTab] = useState<"hotels" | "searches">("hotels");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!auth.isAuthenticated) { navigate("/login"); return; }

    const fetchData = async () => {
      try {
        const [favRes, searchRes] = await Promise.all([
          fetch("/favorites/", { headers: auth.authHeader() }),
          fetch("/saved-searches/", { headers: auth.authHeader() })
        ]);

        if (!favRes.ok) throw new Error("Failed to load favorites");
        if (!searchRes.ok) throw new Error("Failed to load saved searches");

        const [favData, searchData] = await Promise.all([favRes.json(), searchRes.json()]);
        
        setFavorites(Array.isArray(favData) ? favData : []);
        setSavedSearches(searchData.results || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Network error.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [auth, navigate]);

  const handleRemoveHotel = async (hotelId: number) => {
    const r = await fetch(`/favorites/${hotelId}`, {
      method: "DELETE",
      headers: auth.authHeader(),
    });
    if (r.ok) setFavorites((prev) => prev.filter((h) => h.hotel_id !== hotelId));
  };

  const handleDeleteSearch = async (id: string) => {
    const r = await fetch(`/saved-searches/${id}`, {
      method: "DELETE",
      headers: auth.authHeader(),
    });
    if (r.ok) setSavedSearches((prev) => prev.filter((s) => s.id !== id));
  };

  const loadSavedSearch = (s: SavedSearch) => {
    navigate(`/?destination=${encodeURIComponent(s.destination)}&check_in=${s.checkIn}&check_out=${s.checkOut}&guests=${s.guests}&saved_search_id=${s.id}`);
  };

  return (
    <div className="fav-page">
      <div className="fav-container">
        <div className="fav-header">
          <h1 className="fav-title">Saved Items</h1>
          <div className="fav-tabs">
            <button 
              className={`fav-tab ${activeTab === "hotels" ? "active" : ""}`}
              onClick={() => setActiveTab("hotels")}
            >
              Hotels {favorites.length > 0 && <span className="fav-count">{favorites.length}</span>}
            </button>
            <button 
              className={`fav-tab ${activeTab === "searches" ? "active" : ""}`}
              onClick={() => setActiveTab("searches")}
            >
              Searches {savedSearches.length > 0 && <span className="fav-count">{savedSearches.length}</span>}
            </button>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="fav-skeletons">
            {[1, 2, 3].map((i) => <div key={i} className="fav-skeleton" />)}
          </div>
        ) : activeTab === "hotels" ? (
          favorites.length === 0 ? (
            <EmptyState 
              icon="♡" 
              title="No saved hotels yet" 
              desc="Tap the heart on any hotel page to save it here." 
              link="/" 
              linkText="Browse Hotels" 
            />
          ) : (
            <div className="fav-grid">
              {favorites.map((hotel) => (
                <FavoriteCard key={hotel.hotel_id} hotel={hotel} onRemove={handleRemoveHotel} />
              ))}
            </div>
          )
        ) : (
          savedSearches.length === 0 ? (
            <EmptyState 
              icon="🔍" 
              title="No saved searches yet" 
              desc="Search for hotels and save your filters for later." 
              link="/" 
              linkText="Start Searching" 
            />
          ) : (
            <div className="search-list">
              {savedSearches.map((s) => (
                <div key={s.id} className="search-item card">
                  <div className="search-info" onClick={() => loadSavedSearch(s)}>
                    <div className="search-destination">📍 {s.destination}</div>
                    <div className="search-meta">
                      {s.checkIn} → {s.checkOut} · {s.guests} guest{s.guests !== 1 ? "s" : ""}
                    </div>
                    <div className="search-date">Saved {new Date(s.savedAt).toLocaleDateString()}</div>
                  </div>
                  <button 
                    className="search-delete-btn" 
                    onClick={() => handleDeleteSearch(s.id)}
                    aria-label="Delete saved search"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )
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

function EmptyState({ icon, title, desc, link, linkText }: { icon: string, title: string, desc: string, link: string, linkText: string }) {
  return (
    <div className="fav-empty">
      <div className="fav-empty-icon">{icon}</div>
      <h2>{title}</h2>
      <p>{desc}</p>
      <Link to={link} className="btn btn-primary">{linkText}</Link>
    </div>
  );
}
