import { forwardRef, useImperativeHandle, useState } from "react";
import { useAuth } from "../context/AuthContext";
import "./SearchHero.css";
import type { SortField, SortOrder } from "./HomePage";

export interface SearchValues {
  destination: string;
  checkIn: string;
  checkOut: string;
  guests: number;
  savedSearchId?: string
}

/** Exposed to HomePage so the Clear button can reset all fields */
export interface SearchHeroHandle {
  clear: () => void;
}

interface Props {
  onSearch: (values: SearchValues) => void;
  isLoading: boolean;
  resultCount: number | null;
  filters: {
    maxPrice: number,
    minRating: number,
    selectedAmenities: string[]
  },
  sortSettings: {
    sortField: SortField,
    sortOrder: SortOrder
  },
  initialValues?: SearchValues | null;
}

const SearchHero = forwardRef<SearchHeroHandle, Props>(
  ({ onSearch, isLoading, resultCount, filters, sortSettings, initialValues }, ref) => {
    const [destination, setDestination] = useState(initialValues?.destination ?? "");
    const [checkIn, setCheckIn] = useState(initialValues?.checkIn ?? "");
    const [checkOut, setCheckOut] = useState(initialValues?.checkOut ?? "");
    const [guests, setGuests] = useState(initialValues?.guests ?? 1);
    const [error, setError] = useState("");
    const [savedSuccess, setSavedSuccess] = useState("")
    const auth = useAuth();

    // initialValues are applied on mount via useState initializers above

    const today = new Date().toISOString().split("T")[0];
    const canSearch = destination.trim() && checkIn && checkOut;

    useImperativeHandle(ref, () => ({
      clear: () => {
        setDestination("");
        setCheckIn("");
        setCheckOut("");
        setGuests(1);
      },
    }));

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      if (canSearch) {
        onSearch({ destination: destination.trim(), checkIn, checkOut, guests });
      }
    };

    const handleSaveSearch = async () => {
      if (!canSearch) return;
      try {
        const body = JSON.stringify({
          destination: destination.trim(),
          check_in: checkIn,
          check_out: checkOut,
          guests: String(guests),
          max_price: filters.maxPrice,
          min_rating: filters.minRating,
          amenities: filters.selectedAmenities,
          sort_field: sortSettings.sortField,
          sort_order: sortSettings.sortOrder
        });
        const res = await fetch(`/saved-searches/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...auth.authHeader() },
          body,
        });
        const data = await res.json();
        if (!res.ok) { setError(data.error || "Failed to save search."); return; }
        setError("");
        setSavedSuccess("Search successfully saved.")
      }
      catch { setError("Network error — please try again."); }
    };

    return (
      <section className="search-hero">
        <div className="search-hero-content">
          <h1 className="search-hero-title">
            Find your perfect <span className="highlight">night</span>
          </h1>
          <p className="search-hero-sub">
            Enter a destination, dates, and guests to discover your ideal stay.
          </p>

          <form className="search-bar" onSubmit={handleSubmit}>
            <div className="search-field search-field-wide">
              <label htmlFor="sh-dest">Destination</label>
              <input
                id="sh-dest"
                type="text"
                placeholder="City or hotel name"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
              />
            </div>

            <div className="search-field">
              <label htmlFor="sh-checkin">Check-in</label>
              <input
                id="sh-checkin"
                type="date"
                min={today}
                value={checkIn}
                onChange={(e) => setCheckIn(e.target.value)}
              />
            </div>

            <div className="search-field">
              <label htmlFor="sh-checkout">Check-out</label>
              <input
                id="sh-checkout"
                type="date"
                min={checkIn || today}
                value={checkOut}
                onChange={(e) => setCheckOut(e.target.value)}
              />
            </div>

            <div className="search-field search-field-narrow">
              <label htmlFor="sh-guests">Guests</label>
              <input
                id="sh-guests"
                type="number"
                min={1}
                max={8}
                value={guests}
                onChange={(e) =>
                  setGuests(Math.max(1, Math.min(8, parseInt(e.target.value) || 1)))
                }
              />
            </div>

            <button
              type="submit"
              className="search-submit"
              disabled={!canSearch || isLoading}
            >
              {isLoading ? "Searching…" : "Search"}
            </button>
            <button
              type="button"
              className="search-save"
              disabled={!canSearch}
              onClick={handleSaveSearch}
              title="Save this search"
            >
              Save
            </button>
          </form>

          {resultCount !== null && (
            <p className="search-result-count">
              {resultCount === 0
                ? "No hotels found — try a different city."
                : `${resultCount} hotel${resultCount === 1 ? "" : "s"} found`}
            </p>
          )}
          {error && <div className="alert alert-error">{error}</div>}
          {savedSuccess && <div className="alert alert-success">{savedSuccess}</div>}
        </div>
      </section>
    );
  }
);

SearchHero.displayName = "SearchHero";
export default SearchHero;
