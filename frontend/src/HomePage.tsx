import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import HotelFilter from "./hotel/HotelFilter";
import type { Hotel } from "./types/Hotel";
import "./HomePage.css";

type SearchResponse = {
  results: Array<{
    id: number;
    name: string;
    city: string;
    address: string;
    price_per_night: number;
    rating: number;
  }>;
};

function toHotel(result: SearchResponse["results"][number]): Hotel {
  return {
    id: result.id,
    name: result.name,
    location: result.city,
    address: result.address,
    rating: result.rating,
    description: `${result.name} in ${result.city}`,
    pricePerNight: result.price_per_night,
    amenities: [],
  };
}

export default function HomePage() {
  const [destination, setDestination] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState("1");
  const [searchResults, setSearchResults] = useState<Hotel[]>([]);
  const [displayedHotels, setDisplayedHotels] = useState<Hotel[]>([]);
  const [status, setStatus] = useState("Enter a destination and dates to search hotels.");
  const [isLoading, setIsLoading] = useState(false);

  const handleFilter = (filtered: Hotel[]) => {
    setDisplayedHotels(filtered);
  };

  const canSearch = useMemo(
    () => Boolean(destination.trim() && checkIn && checkOut),
    [checkIn, checkOut, destination],
  );

  const handleSearch = async () => {
    if (!canSearch) {
      setStatus("Destination, check-in, and check-out are required.");
      return;
    }

    setIsLoading(true);
    setStatus("");

    try {
      const params = new URLSearchParams({
        destination: destination.trim(),
        check_in: checkIn,
        check_out: checkOut,
      });
      const res = await fetch(`/hotels/search?${params.toString()}`);
      const data = (await res.json()) as SearchResponse | { error?: string };

      if (!res.ok) {
        setSearchResults([]);
        setDisplayedHotels([]);
        setStatus(data && "error" in data ? data.error || "Search failed." : "Search failed.");
        return;
      }

      const hotels = (data as SearchResponse).results.map(toHotel);
      setSearchResults(hotels);
      setDisplayedHotels(hotels);
      setStatus(
        hotels.length > 0
          ? `Found ${hotels.length} hotel${hotels.length === 1 ? "" : "s"} in ${destination.trim()}.`
          : `No hotels found in ${destination.trim()}.`,
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setSearchResults([]);
      setDisplayedHotels([]);
      setStatus(`Network error: ${message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="home">
      {/* Nav */}
      <nav className="nav">
        <span className="nav-logo">JigSaw Nights</span>
        <div className="nav-links">
          {/* temp route buttons - REMOVE ALL temp-links LATER */}
          <Link to="/register" className="temp-link">Register</Link>
          <Link to="/rewards" className="temp-link">Rewards</Link>
          <Link to="/checkout" className="temp-link">Checkout</Link>
          <Link to="/conflict" className="temp-link">Conflict</Link>
          <Link to="/hotel/1" className="temp-link">Hotel</Link>
          <Link to="/booking" className="temp-link">Booking</Link>
          {/* real nav links */}
          <Link to="/register" className="signin-link">Sign In</Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="hero">
        <h1 className="hero-title">Find your perfect stay</h1>
        <p className="hero-subtitle">Search deals on hotels, homes, and more</p>

        <div className="search-bar">
          <div className="search-field search-field-wide">
            <label>Destination</label>
            <input type="text" placeholder="Where are you going?" value={destination} onChange={e => setDestination(e.target.value)} />
          </div>
          <div className="search-field">
            <label>Check in</label>
            <input type="date" value={checkIn} onChange={e => setCheckIn(e.target.value)} />
          </div>
          <div className="search-field">
            <label>Check out</label>
            <input type="date" value={checkOut} onChange={e => setCheckOut(e.target.value)} />
          </div>
          <div className="search-field search-field-narrow">
            <label>Guests</label>
            <select value={guests} onChange={e => setGuests(e.target.value)}>
              <option>1</option>
              <option>2</option>
              <option>3</option>
              <option>4</option>
            </select>
          </div>
          <button className="search-btn" onClick={handleSearch} disabled={isLoading}>
            {isLoading ? "Searching..." : "Search"}
          </button>
        </div>
        <p className="hero-subtitle">{status}</p>
      </div>

      {/* Hotels Section */}
      <div className="section">
        <h2 className="section-title">Popular stays near you</h2>
        <p className="section-subtitle">Hand-picked hotels with great reviews</p>

        <div className="layout">
          <aside className="sidebar">
            <HotelFilter hotels={searchResults} onFilter={handleFilter} />
          </aside>

          {/*hotel grid */}
          <div className="main-content">
            {displayedHotels.length === 0 ? (
              <p className="no-results">No hotels match your filters.</p>
            ) : (
              <div className="hotel-grid">
                {displayedHotels.map(hotel => (
                  <Link key={hotel.id} to={`/hotel/${hotel.id}`} className="hotel-card">
                    <div className="hotel-image" />
                    <div className="hotel-info">
                      <div className="hotel-top">
                        <div>
                          <p className="hotel-name">{hotel.name}</p>
                          <p className="hotel-city">{hotel.location}</p>
                        </div>
                        <span className="hotel-rating">{hotel.rating}</span>
                      </div>
                      <p className="hotel-desc">{hotel.description}</p>
                      {hotel.address && <p className="hotel-desc">{hotel.address}</p>}
                      {hotel.amenities.length > 0 && (
                        <div className="hotel-amenities">
                          {hotel.amenities.map(a => (
                            <span key={a} className="amenity-tag">{a}</span>
                          ))}
                        </div>
                      )}
                      <p className="hotel-price">
                        ${hotel.pricePerNight} <span className="per-night">/ night</span>
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer at bottom*/}
      <div className="footer">
        JigSaw Nights // CMPE 165 Project
      </div>
    </div>
  );
}
