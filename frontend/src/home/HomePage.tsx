import { useEffect, useRef, useState } from "react";
import SearchHero, { type SearchHeroHandle, type SearchValues } from "./SearchHero";
import HotelFilter from "./HotelFilter";
import type { Hotel } from "./Hotel";
import { CARD_GRADIENTS } from "../constants";
import "./HomePage.css";

type SortField = "name" | "price" | "rating";
type SortOrder = "asc" | "desc";

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
          <span className="review-count">
            {hotel.review_count} review{hotel.review_count !== 1 ? "s" : ""}
          </span>
          <span className="view-link">View details →</span>
        </div>
      </div>
    </a>
  );
}

// ── Sorting helpers ────────────────────────────────────────────────────────────

const SORT_LABELS: Record<SortField, string> = {
  name: "Name",
  price: "Price",
  rating: "Rating",
};

function sortHotels(hotels: Hotel[], field: SortField, order: SortOrder): Hotel[] {
  return [...hotels].sort((a, b) => {
    let cmp = 0;
    if (field === "name") {
      cmp = a.name.localeCompare(b.name);
    } else if (field === "price") {
      cmp = a.price_per_night - b.price_per_night;
    } else if (field === "rating") {
      cmp = a.rating - b.rating;
    }
    return order === "asc" ? cmp : -cmp;
  });
}

// ── SortBar component ──────────────────────────────────────────────────────────

function SortBar({
  field,
  order,
  onChange,
}: {
  field: SortField;
  order: SortOrder;
  onChange: (field: SortField, order: SortOrder) => void;
}) {
  const handleFieldClick = (f: SortField) => {
    if (f === field) {
      // Same field → toggle direction
      onChange(f, order === "asc" ? "desc" : "asc");
    } else {
      // New field → default to ascending (descending for rating feels more natural)
      onChange(f, f === "rating" ? "desc" : "asc");
    }
  };

  return (
    <div className="sort-bar">
      <span className="sort-label">Sort by:</span>
      {(Object.keys(SORT_LABELS) as SortField[]).map((f) => {
        const active = f === field;
        return (
          <button
            key={f}
            className={`sort-btn${active ? " sort-btn--active" : ""}`}
            onClick={() => handleFieldClick(f)}
            aria-pressed={active}
          >
            {SORT_LABELS[f]}
            {active && (
              <span className="sort-arrow" aria-hidden="true">
                {order === "asc" ? " ↑" : " ↓"}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

// ── HomePage ───────────────────────────────────────────────────────────────────

export default function HomePage() {
  const heroRef = useRef<SearchHeroHandle>(null);

  const [allHotels, setAllHotels] = useState<Hotel[]>([]);
  const [filtered, setFiltered] = useState<Hotel[]>([]);
  const [displayed, setDisplayed] = useState<Hotel[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [resultCount, setResultCount] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  // Sorting state
  const [sortField, setSortField] = useState<SortField>("rating");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  // Re-sort whenever the filtered list or sort settings change
  useEffect(() => {
    setDisplayed(sortHotels(filtered, sortField, sortOrder));
  }, [filtered, sortField, sortOrder]);

  const handleSortChange = (field: SortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);
  };

  // Load all hotels on mount
  useEffect(() => {
    fetch("/hotels/")
      .then((r) => r.json())
      .then((data) => {
        const hotels: Hotel[] = data.results ?? [];
        setAllHotels(hotels);
        setFiltered(hotels);
      })
      .catch(() => setError("Failed to load hotels."))
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = async ({ destination, checkIn, checkOut, guests }: SearchValues) => {
    setSearching(true);
    setError("");
    try {
      const params = new URLSearchParams({
        destination,
        check_in: checkIn,
        check_out: checkOut,
      });
      const res = await fetch(`/hotels/search?${params}`);
      const data = await res.json();
      if (!res.ok) { setError(data.error || "Search failed."); return; }

      const hotels: Hotel[] = data.results ?? [];
      setAllHotels(hotels);
      setFiltered(hotels);
      setResultCount(hotels.length);
      setHasSearched(true);

      sessionStorage.setItem(
        "lh_search",
        JSON.stringify({ checkIn, checkOut, guests })
      );
    } catch {
      setError("Network error — please try again.");
    } finally {
      setSearching(false);
    }
  };

  const handleClear = () => {
    heroRef.current?.clear();
    setResultCount(null);
    setHasSearched(false);
    setError("");
    sessionStorage.removeItem("lh_search");

    setLoading(true);
    fetch("/hotels/")
      .then((r) => r.json())
      .then((data) => {
        const hotels: Hotel[] = data.results ?? [];
        setAllHotels(hotels);
        setFiltered(hotels);
      })
      .catch(() => setError("Failed to load hotels."))
      .finally(() => setLoading(false));
  };

  return (
    <div className="home-page">
      <SearchHero
        ref={heroRef}
        onSearch={handleSearch}
        isLoading={searching}
        resultCount={resultCount}
      />

      <div className="home-body">
        <HotelFilter hotels={allHotels} onFilter={setFiltered} />

        <section className="hotel-grid-section">
          <div className="hotel-grid-header">
            <h2>
              {hasSearched
                ? `${displayed.length} hotel${displayed.length !== 1 ? "s" : ""} found`
                : "Popular stays"}
            </h2>

            <div className="hotel-grid-header-actions">
              {hasSearched && displayed.length !== allHotels.length && (
                <span className="filter-count">
                  {displayed.length} of {allHotels.length} shown
                </span>
              )}
              {hasSearched && (
                <button className="clear-search-btn" onClick={handleClear}>
                  ✕ Clear search &amp; filters
                </button>
              )}
            </div>
          </div>

          {/* Sort bar sits just above the grid */}
          <SortBar field={sortField} order={sortOrder} onChange={handleSortChange} />

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
              {hasSearched && (
                <button className="btn btn-secondary" onClick={handleClear} style={{ marginTop: 16 }}>
                  Clear search
                </button>
              )}
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
