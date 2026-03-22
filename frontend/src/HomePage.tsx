import { useState } from "react";
import { Link } from "react-router-dom";
import HotelFilter from "./hotel/HotelFilter";
import type { Hotel } from "./types/Hotel";
import "./HomePage.css";

const MOCK_HOTELS: Hotel[] = [
  {
    id: 1,
    name: "The Grand Palace",
    location: "San Francisco",
    rating: 4.8,
    description: "Luxury hotel in the heart of the city",
    pricePerNight: 129,
    amenities: ["wifi", "pool", "gym", "restaurant"],
  },
  {
    id: 2,
    name: "Seaside Resort",
    location: "Santa Cruz",
    rating: 4.6,
    description: "Beachfront resort with ocean views",
    pricePerNight: 189,
    amenities: ["wifi", "pool", "spa", "parking", "pet-friendly"],
  },
  {
    id: 3,
    name: "Mountain View Lodge",
    location: "Lake Tahoe",
    rating: 4.7,
    description: "Cozy lodge surrounded by nature",
    pricePerNight: 159,
    amenities: ["wifi", "parking", "restaurant", "pet-friendly"],
  },
  {
    id: 4,
    name: "Budget Inn Downtown",
    location: "San Jose",
    rating: 3.5,
    description: "Affordable stay near downtown",
    pricePerNight: 69,
    amenities: ["wifi", "parking"],
  },
  {
    id: 5,
    name: "The Ritz Plaza",
    location: "Napa Valley",
    rating: 5.0,
    description: "Five star luxury with vineyard views",
    pricePerNight: 349,
    amenities: ["wifi", "pool", "spa", "gym", "restaurant", "parking"],
  },
  {
    id: 6,
    name: "Coastal Breeze Inn",
    location: "Monterey",
    rating: 4.3,
    description: "Charming inn steps from the beach",
    pricePerNight: 109,
    amenities: ["wifi", "parking", "pet-friendly"],
  },
];

export default function HomePage() {
  const [destination, setDestination] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState("1");
  const [displayedHotels, setDisplayedHotels] = useState<Hotel[]>(MOCK_HOTELS);

  const handleFilter = (filtered: Hotel[]) => {
    setDisplayedHotels(filtered);
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
          <Link to="/hotel" className="temp-link">Hotel</Link>
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
          <button className="search-btn">Search</button>
        </div>
      </div>

      {/* Hotels Section */}
      <div className="section">
        <h2 className="section-title">Popular stays near you</h2>
        <p className="section-subtitle">Hand-picked hotels with great reviews</p>

        <div className="layout">
          <aside className="sidebar">
            <HotelFilter hotels={MOCK_HOTELS} onFilter={handleFilter} />
          </aside>

          {/*hotel grid */}
          <div className="main-content">
            {displayedHotels.length === 0 ? (
              <p className="no-results">No hotels match your filters.</p>
            ) : (
              <div className="hotel-grid">
                {displayedHotels.map(hotel => (
                  <div key={hotel.id} className="hotel-card">
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
                      <div className="hotel-amenities">
                        {hotel.amenities.map(a => (
                          <span key={a} className="amenity-tag">{a}</span>
                        ))}
                      </div>
                      <p className="hotel-price">
                        ${hotel.pricePerNight} <span className="per-night">/ night</span>
                      </p>
                    </div>
                  </div>
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
