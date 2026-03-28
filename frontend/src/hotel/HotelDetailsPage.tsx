import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { AMENITY_ICONS, CARD_GRADIENTS } from "../constants";
import "./HotelDetailsPage.css";

interface HotelDetail {
  id: number;
  name: string;
  city: string;
  address: string;
  price_per_night: number;
  rating: number;
  review_count: number;
  photos: { id: number; url: string; alt_text: string }[];
  amenities: string[];
  room_types: { type: string; count: number }[];
  reviews: { id: number; user_id: number; title: string; content: string; rating: number }[];
}

function Stars({ rating }: { rating: number }) {
  const filled = Math.round(rating);
  return (
    <span className="stars">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= filled ? "star filled" : "star"}>★</span>
      ))}
    </span>
  );
}

export default function HotelDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const auth = useAuth();

  const [hotel, setHotel] = useState<HotelDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activePhoto, setActivePhoto] = useState(0);

  useEffect(() => {
    if (!id) return;
    fetch(`/hotels/${id}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.error) { setError(data.error); return; }
        setHotel(data);
      })
      .catch(() => setError("Failed to load hotel details."))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    document.body.classList.add("has-sticky-bar");
    return () => document.body.classList.remove("has-sticky-bar");
  }, []);

  const handleReserve = () => {
    if (!auth.isAuthenticated) {
      navigate(`/login`);
      return;
    }
    navigate(`/booking/${id}`);
  };

  if (loading) {
    return (
      <div className="hdp-loading">
        <div className="hdp-skeleton" />
        <div className="hdp-skeleton hdp-skeleton-short" />
      </div>
    );
  }

  if (error || !hotel) {
    return <div className="hdp-error alert alert-error">{error || "Hotel not found."}</div>;
  }

  const gradient = CARD_GRADIENTS[hotel.id % CARD_GRADIENTS.length];

  return (
    <div className="hdp">
      {/* Gallery */}
      <div className="hdp-gallery">
        {hotel.photos.length > 0 ? (
          <>
            <div className="hdp-main-photo">
              <img src={hotel.photos[activePhoto].url} alt={hotel.photos[activePhoto].alt_text} />
            </div>
            {hotel.photos.length > 1 && (
              <div className="hdp-thumbs">
                {hotel.photos.map((p, i) => (
                  <button
                    key={p.id}
                    className={`hdp-thumb${i === activePhoto ? " active" : ""}`}
                    onClick={() => setActivePhoto(i)}
                  >
                    <img src={p.url} alt={p.alt_text} />
                  </button>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="hdp-photo-placeholder" style={{ background: gradient }} />
        )}
      </div>

      <div className="hdp-body">
        {/* Info + Reserve */}
        <div className="hdp-header">
          <div>
            <h1 className="hdp-name">{hotel.name}</h1>
            <p className="hdp-location">📍 {hotel.address}, {hotel.city}</p>
            <div className="hdp-rating-row">
              <Stars rating={hotel.rating} />
              <span className="hdp-rating-num">{hotel.rating.toFixed(1)}</span>
              <span className="hdp-review-count">({hotel.review_count} reviews)</span>
            </div>
          </div>

          <div className="hdp-reserve-block">
            <div className="hdp-price">
              <span className="hdp-price-num">${hotel.price_per_night.toFixed(0)}</span>
              <span className="hdp-price-label">/ night</span>
            </div>
            <button className="btn btn-primary btn-lg hdp-reserve-btn" onClick={handleReserve}>
              Reserve
            </button>
            {!auth.isAuthenticated && (
              <p className="hdp-login-hint">You'll be asked to sign in first.</p>
            )}
          </div>
        </div>

        <div className="hdp-grid">
          {/* Amenities */}
          {hotel.amenities.length > 0 && (
            <section className="hdp-section">
              <h2 className="hdp-section-title">Amenities</h2>
              <div className="hdp-amenities">
                {hotel.amenities.map((a) => (
                  <div key={a} className="hdp-amenity">
                    <span className="hdp-amenity-icon">{AMENITY_ICONS[a] || "✓"}</span>
                    <span>{a}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Room types */}
          {hotel.room_types.length > 0 && (
            <section className="hdp-section">
              <h2 className="hdp-section-title">Room Types</h2>
              <div className="hdp-rooms">
                {hotel.room_types.map((rt) => {
                  const mult = rt.type === "SINGLE" ? .85 : rt.type === "TRIPLE" ? 1.35 : rt.type === "QUAD" ? 1.7 : 1;
                  return (
                    <div key={rt.type} className="hdp-room-card">
                      <div className="hdp-room-type">{rt.type.charAt(0) + rt.type.slice(1).toLowerCase()}</div>
                      <div className="hdp-room-avail">{rt.count} available</div>
                      <div className="hdp-room-price">${(hotel.price_per_night * mult).toFixed(0)}<span>/night</span></div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* Reviews */}
          <section className="hdp-section hdp-section-full">
            <h2 className="hdp-section-title">
              Guest Reviews
              {hotel.review_count > 0 && (
                <span className="hdp-review-badge">{hotel.rating.toFixed(1)} ★</span>
              )}
            </h2>
            {hotel.reviews.length === 0 ? (
              <p className="hdp-no-reviews">No reviews yet — be the first to stay!</p>
            ) : (
              <div className="hdp-reviews">
                {hotel.reviews.map((rv) => (
                  <div key={rv.id} className="hdp-review">
                    <div className="hdp-review-top">
                      <div>
                        <span className="hdp-review-title">{rv.title}</span>
                        <Stars rating={rv.rating} />
                      </div>
                      <span className="hdp-review-user">Guest #{rv.user_id}</span>
                    </div>
                    <p className="hdp-review-content">{rv.content}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>

      {/* Sticky bottom reserve bar */}
      <div className="hdp-sticky-bar">
        <span className="hdp-sticky-price">${hotel.price_per_night.toFixed(0)}<span>/night</span></span>
        <button className="btn btn-primary" onClick={handleReserve}>Reserve Now</button>
      </div>
    </div>
  );
}
