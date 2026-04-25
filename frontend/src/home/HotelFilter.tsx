import { useEffect, useState } from "react";
import type { Hotel } from "./Hotel";
import "./HotelFilter.css";

interface Props {
  hotels: Hotel[];
  onFilter: (filtered: Hotel[]) => void;
  onFiltersChange: (filters: any) => void; 
}

export default function HotelFilter({ hotels, onFilter, onFiltersChange }: Props) {
  const [maxPrice, setMaxPrice] = useState(1000);
  const [minRating, setMinRating] = useState(0);
  const [selected, setSelected] = useState<string[]>([]);

  // Derive unique amenities from the active hotel list
  const allAmenities = Array.from(
    new Set(hotels.flatMap((h) => h.amenities))
  ).sort();

  // React derived-state pattern: detect prop identity change during render
  // and reset amenity selections without a separate useEffect.
  const [prevHotels, setPrevHotels] = useState(hotels);
  if (prevHotels !== hotels) {
    setPrevHotels(hotels);
    // Calling setState during render (not inside an effect) is explicitly
    // supported by React for derived state — it re-renders once, not twice.
    setSelected([]);
  }

  // Re-filter whenever any filter value or hotel list changes
  useEffect(() => {
    const filtered = hotels.filter((h) => {
      const priceOk = h.price_per_night <= maxPrice;
      const ratingOk = h.rating >= minRating;
      const amenitiesOk =
        selected.length === 0 ||
        selected.every((a) => h.amenities.includes(a));
      return priceOk && ratingOk && amenitiesOk;
    });
    
    onFilter(filtered);
    onFiltersChange({maxPrice:maxPrice, minRating:minRating, selectedAmenities:selected})
  }, [hotels, maxPrice, minRating, selected, onFilter]);

  const toggle = (amenity: string) =>
    setSelected((prev) =>
      prev.includes(amenity) ? prev.filter((a) => a !== amenity) : [...prev, amenity]
    );

  const hasActive = maxPrice < 1000 || minRating > 0 || selected.length > 0;

  return (
    <aside className="filter-panel">
      <div className="filter-header">
        <h3 className="filter-title">Filters</h3>
        {hasActive && (
          <button
            className="filter-reset"
            onClick={() => {
              setMaxPrice(1000);
              setMinRating(0);
              setSelected([]);
            }}
          >
            Clear all
          </button>
        )}
      </div>

      {/* Price slider */}
      <div className="filter-section">
        <label className="filter-section-label">
          Max price <span className="filter-value">${maxPrice}/night</span>
        </label>
        <input
          type="range"
          min={50}
          max={1000}
          step={10}
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
          className="filter-range"
        />
        <div className="filter-range-ends">
          <span>$50</span>
          <span>$1,000</span>
        </div>
      </div>

      {/* Rating buttons */}
      <div className="filter-section">
        <label className="filter-section-label">Minimum rating</label>
        <div className="filter-stars">
          {[0, 1, 2, 3, 4].map((r) => (
            <button
              key={r}
              className={"filter-star-btn" + (minRating === r ? " active" : "")}
              onClick={() => setMinRating(r)}
              style={r > 0 ? { display: "flex", gap: "2px", letterSpacing: "1px" } : {}}
            >
              {r === 0 ? "Any" : (
                <>
                  {Array.from({ length: r }).map((_, i) => <span key={`f-${i}`} style={{ color: "var(--c-star)" }}>★</span>)}
                  {Array.from({ length: 5 - r }).map((_, i) => <span key={`e-${i}`} style={{ color: "var(--c-border)" }}>★</span>)}
                  <span style={{ marginLeft: "4px" }}>&amp; up</span>
                </>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Amenity checkboxes — only shown after a search returns amenity data */}
      {allAmenities.length > 0 && (
        <div className="filter-section">
          <label className="filter-section-label">Amenities</label>
          <ul className="filter-amenity-list">
            {allAmenities.map((a) => (
              <li key={a}>
                <label className="filter-checkbox-label">
                  <input
                    type="checkbox"
                    checked={selected.includes(a)}
                    onChange={() => toggle(a)}
                  />
                  <span>{a}</span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}
