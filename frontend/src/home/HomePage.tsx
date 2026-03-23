import { useEffect, useState } from "react";
import SearchHero from "./SearchHero";
import HotelFilter from "./HotelFilter";
import type { Hotel } from "./Hotel";
import { CARD_GRADIENTS } from "../constants";
import "./HomePage.css";

function StarRow({ rating }: { rating: number }) {
  return (
    <span className="star-row" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= Math.round(rating) ? "star filled" : "star"}>★</span>
      ))}
    </span>
  );
}

function HotelCard({ hotel, index }: { hotel: Hotel; index: number }) {
  const gradient = CARD_GRADIENTS[index % CARD_GRADIENTS.length];

  return (
    // Opens hotel details in a new tab per spec
    <a
      href={`/hotel/${hotel.id}`}
      target="_blank"
      rel="noopener noreferrer"
      className="hotel-card"
    >
      <div className="hotel-card-image">
        {hotel.primary_photo ? (
          <img src={hotel.primary_photo} alt={hotel.name} loading="lazy" />
        ) : (
          <div className="hotel-card-placeholder" style={{ background: gradient }} />
        )}
        <div className="hotel-card-price">
          ${hotel.price_per_night.toFixed(0)}<span>/night</span>
        </div>
      </div>

      <div className="hotel-card-body">
        <div className="hotel-card-top">
          <div>
            <h3 className="hotel-card-name">{hotel.name}</h3>
            <p className="hotel-card-city">📍 {hotel.city}</p>
          </div>
          <div className="hotel-card-rating">
            <StarRow rating={hotel.rating} />
            <span className="rating-num">{hotel.rating.toFixed(1)}</span>
          </div>
        </div>

        {hotel.amenities.length > 0 && (
          <div className="hotel-card-amenities">
            {hotel.amenities.slice(0, 4).map((a) => (
              <span key={a} className="amenity-chip">{a}</span>
            ))}
            {hotel.amenities.length > 4 && (
              <span className="amenity-chip amenity-more">+{hotel.amenities.length - 4}</span>
            )}
          </div>
        )}

        <div className="hotel-card-footer">
          <span className="review-count">{hotel.review_count} review{hotel.review_count !== 1 ? "s" : ""}</span>
          <span className="view-link">View details →</span>
        </div>
      </div>
    </a>
  );
}

export default function HomePage() {
  const [allHotels, setAllHotels] = useState<Hotel[]>([]);
  const [displayed, setDisplayed] = useState<Hotel[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [resultCount, setResultCount] = useState<number | null>(null);
  const [error, setError] = useState("");

  // Load all hotels on mount — default view
  useEffect(() => {
    fetch("/hotels/")
      .then((r) => r.json())
      .then((data) => {
        const hotels: Hotel[] = data.results ?? [];
        setAllHotels(hotels);
        setDisplayed(hotels);
      })
      .catch(() => setError("Failed to load hotels."))
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = async (destination: string, checkIn: string, checkOut: string) => {
    setSearching(true);
    setError("");
    try {
      const params = new URLSearchParams({ destination, check_in: checkIn, check_out: checkOut });
      const res = await fetch(`/hotels/search?${params}`);
      const data = await res.json();
      if (!res.ok) { setError(data.error || "Search failed."); return; }
      const hotels: Hotel[] = data.results ?? [];
      setAllHotels(hotels);
      setDisplayed(hotels);
      setResultCount(hotels.length);
    } catch {
      setError("Network error — please try again.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="home-page">
      <SearchHero onSearch={handleSearch} isLoading={searching} resultCount={resultCount} />

      <div className="home-body">
        <HotelFilter hotels={allHotels} onFilter={setDisplayed} />

        <section className="hotel-grid-section">
          <div className="hotel-grid-header">
            <h2>
              {resultCount !== null
                ? `${displayed.length} hotel${displayed.length !== 1 ? "s" : ""} found`
                : "Popular stays"}
            </h2>
            {resultCount !== null && displayed.length !== allHotels.length && (
              <span className="filter-count">{displayed.length} of {allHotels.length} shown</span>
            )}
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          {loading ? (
            <div className="hotel-grid">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="hotel-card hotel-card-skeleton" />
              ))}
            </div>
          ) : displayed.length === 0 ? (
            <div className="empty-state">
              <p>No hotels match your filters.</p>
            </div>
          ) : (
            <div className="hotel-grid">
              {displayed.map((h, i) => (
                <HotelCard key={h.id} hotel={h} index={i} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
