import { useState } from "react";
import "./SearchHero.css";

interface Props {
  onSearch: (destination: string, checkIn: string, checkOut: string) => void;
  isLoading: boolean;
  resultCount: number | null;
}

export default function SearchHero({ onSearch, isLoading, resultCount }: Props) {
  const [destination, setDestination] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");

  const today = new Date().toISOString().split("T")[0];
  const canSearch = destination.trim() && checkIn && checkOut;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (canSearch) onSearch(destination.trim(), checkIn, checkOut);
  };

  return (
    <section className="search-hero">
      <div className="search-hero-content">
        <h1 className="search-hero-title">Find your perfect stay</h1>
        <p className="search-hero-sub">
          Search hundreds of hotels — all three fields required to search.
        </p>

        <form className="search-bar" onSubmit={handleSubmit}>
          <div className="search-field search-field-wide">
            <label htmlFor="destination">Destination</label>
            <input
              id="destination"
              type="text"
              placeholder="City or hotel name"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            />
          </div>

          <div className="search-field">
            <label htmlFor="check-in">Check-in</label>
            <input
              id="check-in"
              type="date"
              min={today}
              value={checkIn}
              onChange={(e) => setCheckIn(e.target.value)}
            />
          </div>

          <div className="search-field">
            <label htmlFor="check-out">Check-out</label>
            <input
              id="check-out"
              type="date"
              min={checkIn || today}
              value={checkOut}
              onChange={(e) => setCheckOut(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="search-submit"
            disabled={!canSearch || isLoading}
          >
            {isLoading ? "Searching…" : "Search"}
          </button>
        </form>

        {resultCount !== null && (
          <p className="search-result-count">
            {resultCount === 0
              ? "No hotels found — try a different city."
              : `${resultCount} hotel${resultCount === 1 ? "" : "s"} found`}
          </p>
        )}
      </div>
    </section>
  );
}
