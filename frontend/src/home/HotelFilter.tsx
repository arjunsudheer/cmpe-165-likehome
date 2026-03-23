import { useEffect, useMemo, useState } from "react";
import type { Hotel } from "./Hotel";
import "./HotelFilter.css";

interface Props {
  hotels: Hotel[];
  onFilter: (filtered: Hotel[]) => void;
}

export default function HotelFilter({ hotels, onFilter }: Props) {
  const [maxPrice, setMaxPrice] = useState(1000);
  const [minRating, setMinRating] = useState(0);
  const [selected, setSelected] = useState<string[]>([]);

  // Derive unique amenities from whatever hotel list is active
  const allAmenities = useMemo(() => {
    const set = new Set<string>();
    hotels.forEach((h) => h.amenities.forEach((a) => set.add(a)));
    return Array.from(set).sort();
  }, [hotels]);

  // Reset amenity selection when the hotel list changes (new search)
  useEffect(() => { setSelected([]); }, [hotels]);

  // Re-filter immediately on any state change — no apply button required
  useEffect(() => {
    const filtered = hotels.filter((h) => {
      const priceOk = h.price_per_night <= maxPrice;
      const ratingOk = h.rating >= minRating;
      const amenitiesOk =
        selected.length === 0 || selected.every((a) => h.amenities.includes(a));
      return priceOk && ratingOk && amenitiesOk;
    });
    onFilter(filtered);
  }, [hotels, maxPrice, minRating, selected]);

  const toggle = (amenity: string) =>
    setSelected((prev) =>
      prev.includes(amenity) ? prev.filter((a) => a !== amenity) : [...prev, amenity],
    );

  const hasActive = maxPrice < 1000 || minRating > 0 || selected.length > 0;

  return (
    <aside className="filter-panel">
      <div className="filter-header">
        <h3 className="filter-title">Filters</h3>
        {hasActive && (
          <button
            className="filter-reset"
            onClick={() => { setMaxPrice(1000); setMinRating(0); setSelected([]); }}
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
        <div className="filter-range-ends"><span>$50</span><span>$1,000</span></div>
      </div>

      {/* Rating selector */}
      <div className="filter-section">
        <label className="filter-section-label">Minimum rating</label>
        <div className="filter-stars">
          {[0, 1, 2, 3, 4].map((r) => (
            <button
              key={r}
              className={"filter-star-btn" + (minRating === r ? " active" : "")}
              onClick={() => setMinRating(r)}
            >
              {r === 0 ? "Any" : `${r}★+`}
            </button>
          ))}
        </div>
      </div>

      {/* Amenity checkboxes */}
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
