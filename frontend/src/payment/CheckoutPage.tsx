import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./CheckoutPage.css";

interface BookingDetail {
  id: number;
  booking_number: string;
  title: string;
  hotel_name: string | null;
  hotel_city: string | null;
  room_type: string | null;
  start_date: string;
  end_date: string;
  total_price: string;
  status: string;
}

const RATE = 100; // 100 pts = $1

export default function CheckoutPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [sp] = useSearchParams();
  const bookingId = sp.get("booking_id");

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [balance, setBalance] = useState(0);
  const [pts, setPts] = useState(0);
  const [inputVal, setInputVal] = useState("");
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [earnedPts, setEarnedPts] = useState(0);

  useEffect(() => {
    if (!auth.isAuthenticated) { navigate("/login"); return; }
    if (!bookingId) { setError("No booking ID provided."); setLoading(false); return; }

    const h = { "Content-Type": "application/json", ...auth.authHeader() };

    Promise.all([
      fetch(`/reservations/${bookingId}`, { headers: h }).then((r) => r.json()),
      fetch("/rewards/balance", { headers: h }).then((r) => r.json()),
    ])
      .then(([b, bal]) => {
        if (b.error) { setError(b.error); return; }
        setBooking(b);
        setBalance(bal.total_points ?? 0);
      })
      .catch(() => setError("Failed to load checkout data."))
      .finally(() => setLoading(false));
  }, [auth.isAuthenticated, bookingId, navigate]);

  const bookingTotal = booking ? parseFloat(booking.total_price) : 0;
  const maxPts = Math.min(balance, Math.floor(bookingTotal * RATE));
  const discount = pts / RATE;
  const finalTotal = Math.max(0, bookingTotal - discount);
  const pct = maxPts > 0 ? (pts / maxPts) * 100 : 0;

  const handleSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = Math.min(parseInt(e.target.value), maxPts);
    setPts(v);
    setInputVal(v > 0 ? String(v) : "");
  };

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, "");
    setInputVal(raw);
    setPts(raw ? Math.min(parseInt(raw), maxPts) : 0);
  };

  const handleConfirm = async () => {
    if (!booking) return;
    setConfirming(true);
    setError("");
    const h = { "Content-Type": "application/json", ...auth.authHeader() };

    try {
      // Optionally redeem points first
      if (pts > 0) {
        const r = await fetch("/rewards/redeem", {
          method: "POST",
          headers: h,
          body: JSON.stringify({ booking_id: booking.id, points: pts }),
        });
        const d = await r.json();
        if (!r.ok) { setError(d.error || "Redemption failed."); return; }
      }

      // Confirm booking
      const r2 = await fetch(`/reservations/${booking.id}/confirm`, { method: "POST", headers: h });
      const d2 = await r2.json();
      if (!r2.ok) { setError(d2.error || "Confirmation failed."); return; }

      setEarnedPts(d2.points_earned ?? 0);
      setDone(true);
    } catch {
      setError("Network error — please try again.");
    } finally {
      setConfirming(false);
    }
  };

  if (loading) return <div className="checkout-loading">Loading checkout…</div>;
  if (error) return <div className="checkout-error alert alert-error">{error}</div>;

  if (done && booking) {
    return (
      <div className="checkout-page">
        <div className="checkout-success card">
          <div className="success-icon">✓</div>
          <h2>Booking Confirmed!</h2>
          <p className="success-ref">{booking.booking_number}</p>
          <div className="success-details">
            {[
              ["Hotel", booking.hotel_name ?? "—"],
              ["Dates", `${booking.start_date} → ${booking.end_date}`],
              ["Total charged", `$${finalTotal.toFixed(2)}`],
              ...(pts > 0 ? [["Points used", `${pts.toLocaleString()} pts`]] : []),
              ...(earnedPts > 0 ? [["Points earned", `+${earnedPts.toLocaleString()} pts`]] : []),
            ].map(([k, v]) => (
              <div key={k} className="success-row">
                <span>{k}</span><strong>{v}</strong>
              </div>
            ))}
          </div>
          <Link to="/" className="btn btn-primary" style={{ marginTop: 24 }}>Back to Hotels</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="checkout-container">
        <h1 className="checkout-title">Checkout</h1>

        {/* Booking summary */}
        {booking && (
          <div className="checkout-section card">
            <h2>Booking Summary</h2>
            <div className="summary-rows">
              {[
                ["Hotel", booking.hotel_name ?? "—"],
                ["City", booking.hotel_city ?? "—"],
                ["Trip", booking.title],
                ["Check-in", booking.start_date],
                ["Check-out", booking.end_date],
                ["Room", booking.room_type ?? "—"],
              ].map(([k, v]) => (
                <div key={k} className="summary-row">
                  <span>{k}</span><strong>{v}</strong>
                </div>
              ))}
              <div className="summary-row summary-row-total">
                <span>Room total</span>
                <strong>${bookingTotal.toFixed(2)}</strong>
              </div>
            </div>
          </div>
        )}

        {/* Rewards redemption */}
        {balance > 0 && booking && (
          <div className="checkout-section card">
            <div className="rewards-header">
              <h2>Use Rewards</h2>
              <span className="rewards-balance-chip">{balance.toLocaleString()} pts available</span>
            </div>

            <input
              type="range"
              className="pts-slider"
              min={0}
              max={maxPts}
              step={10}
              value={pts}
              onChange={handleSlider}
              style={{ background: `linear-gradient(to right,var(--c-primary) 0%,var(--c-primary) ${pct}%,#e2e8f0 ${pct}%,#e2e8f0 100%)` }}
            />
            <div className="slider-labels">
              <span>0</span>
              {pts > 0 && <span className="slider-live">{pts.toLocaleString()} pts → −${discount.toFixed(2)}</span>}
              <span>{maxPts.toLocaleString()}</span>
            </div>

            <div className="pts-input-row">
              <label className="form-label">Or type exact amount</label>
              <input className="form-input pts-input" type="text" placeholder="0" value={inputVal} onChange={handleInput} onBlur={() => { const v = Math.min(parseInt(inputVal)||0,maxPts); setPts(v); setInputVal(v>0?String(v):""); }} />
            </div>
          </div>
        )}

        {/* Final total + confirm */}
        {booking && (
          <div className="checkout-section card checkout-final">
            <div className="final-rows">
              <div className="final-row"><span>Room total</span><span>${bookingTotal.toFixed(2)}</span></div>
              {pts > 0 && <div className="final-row final-row-discount"><span>Rewards discount</span><span>−${discount.toFixed(2)}</span></div>}
              <div className="final-row final-row-total"><span>Total due</span><strong>${finalTotal.toFixed(2)}</strong></div>
            </div>

            {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}

            <button className="btn btn-primary btn-lg" onClick={handleConfirm} disabled={confirming} style={{ width: "100%" }}>
              {confirming ? "Confirming…" : "Confirm Booking"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
