import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import CreditCardForm, { type SavedCard } from "./CreditCardForm";
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
  expires_at?: string;
}

const RATE = 100; // 100 pts = $1

function formatTime(ms: number) {
  const totSec = Math.floor(ms / 1000);
  const m = Math.floor(totSec / 60);
  const s = totSec % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function CheckoutPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [sp] = useSearchParams();
  const bookingId = sp.get("booking_id");

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [balance, setBalance] = useState(0);
  const [pts, setPts] = useState(0);       // points currently selected to redeem
  const [inputVal, setInputVal] = useState(""); // dollar input value
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [earnedPts, setEarnedPts] = useState(0);
  const [animatedEarnedPts, setAnimatedEarnedPts] = useState(0);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [redirectLeft, setRedirectLeft] = useState<number | null>(null);

  // Credit card state
  const [selectedCard, setSelectedCard] = useState<SavedCard | null>(null);

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
  }, [auth, bookingId, navigate]);

  // Timer effect
  useEffect(() => {
    if (!booking || !booking.expires_at || done) return;
    const expStr = booking.expires_at.endsWith("Z") ? booking.expires_at : booking.expires_at + "Z";
    const exp = new Date(expStr).getTime();

    const tick = () => {
      const remaining = Math.max(0, exp - Date.now());
      setTimeLeft(remaining);
      if (remaining === 0 && redirectLeft === null) {
        setRedirectLeft(5);
      }
    };

    tick();
    const iv = setInterval(tick, 1000);
    return () => clearInterval(iv);
  }, [booking, done, redirectLeft]);

  // Redirect effect
  useEffect(() => {
    if (redirectLeft === null) return;
    if (redirectLeft === 0) {
      navigate("/");
      return;
    }
    const iv = setTimeout(() => setRedirectLeft((r) => r! - 1), 1000);
    return () => clearTimeout(iv);
  }, [redirectLeft, navigate]);

  const bookingTotal = booking ? parseFloat(booking.total_price) : 0;
  // max pts you can use is bounded by user's balance and the total cost of room
  const maxPts = Math.min(balance, Math.floor(bookingTotal * RATE));
  const discount = pts / RATE;
  const finalTotal = Math.max(0, bookingTotal - discount);
  const estimatedEarnedPts = Math.max(0, Math.floor(finalTotal * 10));
  const isExpired = timeLeft !== null && timeLeft === 0;

  useEffect(() => {
    if (!done || earnedPts <= 0) {
      setAnimatedEarnedPts(0);
      return;
    }

    let cur = 0;
    const increment = Math.max(1, Math.ceil(earnedPts / 45));
    const timer = setInterval(() => {
      cur = Math.min(cur + increment, earnedPts);
      setAnimatedEarnedPts(cur);
      if (cur >= earnedPts) clearInterval(timer);
    }, 24);

    return () => clearInterval(timer);
  }, [done, earnedPts]);

  // Handle dollar amount input
  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/[^0-9.]/g, "");
    setInputVal(raw);
    if (!raw) {
      setPts(0);
      return;
    }
    const dollars = parseFloat(raw);
    if (!isNaN(dollars)) {
      const pointsWanted = Math.floor(dollars * RATE);
      setPts(Math.min(pointsWanted, maxPts));
    } else {
      setPts(0);
    }
  };

  const handleBlur = () => {
    if (pts > 0) {
      setInputVal((pts / RATE).toFixed(2));
    } else {
      setInputVal("");
    }
  };

  const useMaxPoints = () => {
    setPts(maxPts);
    setInputVal((maxPts / RATE).toFixed(2));
  };

  const handleConfirm = async () => {
    if (!booking) return;
    if (isExpired) return;
    if (!selectedCard) {
      setError("Please add or select a payment method to continue.");
      return;
    }

    setConfirming(true);
    setError("");
    const h = { "Content-Type": "application/json", ...auth.authHeader() };

    try {
      if (pts > 0) {
        const r = await fetch("/rewards/redeem", {
          method: "POST",
          headers: h,
          body: JSON.stringify({ booking_id: booking.id, points: pts }),
        });
        const d = await r.json();
        if (!r.ok) { setError(d.error || "Redemption failed."); return; }
      }

      const r2 = await fetch(`/reservations/${booking.id}/confirm`, { method: "POST", headers: h });
      const d2 = await r2.json();
      if (!r2.ok) { setError(d2.error || "Confirmation failed."); return; }

      setEarnedPts(d2.points_earned ?? 0);
      setDone(true);
      setTimeLeft(null); // stop timer visually
    } catch {
      setError("Network error — please try again.");
    } finally {
      setConfirming(false);
    }
  };

  if (loading) return <div className="checkout-loading">Loading checkout…</div>;
  if (error && !booking && !isExpired) return <div className="checkout-error alert alert-error">{error}</div>;

  if (redirectLeft !== null) {
    return (
      <div className="checkout-page">
        <div className="checkout-error card" style={{ textAlign: "center", padding: "60px 40px", maxWidth: "480px", margin: "40px auto" }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>⏱️</div>
          <h2 style={{ fontSize: "24px", fontWeight: 900, marginBottom: "12px", color: "var(--c-text)" }}>Session Expired</h2>
          <p style={{ color: "var(--c-text-muted)", fontSize: "15px", marginBottom: "24px", lineHeight: 1.5 }}>
            You did not complete checkout within the 5-minute reservation window. Please start a new search.
          </p>
          <div style={{ background: "var(--c-surface-2)", border: "1px solid var(--c-border)", borderRadius: "var(--radius-md)", padding: "12px", fontSize: "14px", color: "var(--c-text-muted)" }}>
            Redirecting to homepage in <strong style={{ color: "var(--c-text)", fontSize: "16px" }}>{redirectLeft}</strong>...
          </div>
        </div>
      </div>
    );
  }

  if (done && booking) {
    return (
      <div className="checkout-page">
        <div className="checkout-success card">
          <div className="success-icon">✓</div>
          <h2>Booking Confirmed!</h2>
          <p className="success-ref">{booking.booking_number}</p>
          {earnedPts > 0 && (
            <div className="success-points-highlight" aria-live="polite">
              <p className="points-highlight-label">Points Earned</p>
              <p className="points-highlight-value">+{animatedEarnedPts.toLocaleString()} pts</p>
              <p className="points-highlight-subtext">Nice! Your rewards balance has been updated.</p>
            </div>
          )}
          <div className="success-details">
            {[
              ["Hotel", booking.hotel_name ?? "—"],
              ["Dates", `${booking.start_date} → ${booking.end_date}`],
              ["Total charged", `$${finalTotal.toFixed(2)}`],
              ...(selectedCard ? [[
                "Payment",
                `${selectedCard.brand === "visa" ? "Visa" : selectedCard.brand === "mastercard" ? "Mastercard" : selectedCard.brand === "amex" ? "Amex" : "Card"} ••••${selectedCard.last4}`
              ]] : []),
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
        
        <div className="checkout-header-row">
          <h1 className="checkout-title">Checkout</h1>
          {timeLeft !== null && !done && (
            <div className={`checkout-timer ${timeLeft < 300000 ? "timer-danger" : ""}`}>
              ⏳ Time left to complete: <strong>{formatTime(timeLeft)}</strong>
            </div>
          )}
        </div>

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
          <div className="checkout-section card rewards-section-new">
            <div className="rewards-header">
              <h2>Use Rewards</h2>
              <span className="rewards-balance-chip">{balance.toLocaleString()} pts available</span>
            </div>
            
            <p className="rewards-info">Enter the <strong>dollar amount</strong> of rewards you'd like to apply to this booking (100 pts = $1).</p>
            
            <div className="rewards-controls">
              <div className="rewards-input-wrapper">
                <span className="currency-symbol">$</span>
                <input
                  className="form-input pts-input-new"
                  type="text"
                  placeholder="0.00"
                  value={inputVal}
                  onChange={handleInput}
                  onBlur={handleBlur}
                  disabled={isExpired}
                />
              </div>
              <button className="btn btn-primary" style={{ fontWeight: 800, padding: "8px 16px", boxShadow: "var(--shadow-sm)" }} onClick={useMaxPoints} disabled={isExpired || maxPts === 0}>
                Apply max (${(maxPts / RATE).toFixed(2)})
              </button>
            </div>

            {pts > 0 && (
              <div className="rewards-applied-text">
                Redeeming <strong>{pts.toLocaleString()} pts</strong> for a <strong>${(pts / RATE).toFixed(2)}</strong> discount.
              </div>
            )}
          </div>
        )}

        {/* Credit card payment */}
        {booking && (
          <div className="checkout-section card">
            <div className="payment-header">
              <h2>Payment Method</h2>
              {selectedCard && (
                <span className="payment-selected-chip">
                  ✓ {selectedCard.brand !== "generic" ? selectedCard.brand.charAt(0).toUpperCase() + selectedCard.brand.slice(1) : "Card"} ••••{selectedCard.last4}
                </span>
              )}
            </div>
            <CreditCardForm
              onCardSelected={(card) => setSelectedCard(card)}
              onCardCleared={() => setSelectedCard(null)}
            />
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
            <div className="points-preview">
              You will earn approximately <strong>+{estimatedEarnedPts.toLocaleString()} pts</strong> from this booking.
            </div>

            {!selectedCard && !isExpired && (
              <div className="alert alert-info" style={{ marginBottom: 12 }}>
                💳 Please add a payment method above to continue.
              </div>
            )}

            {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}

            <button
              className="btn btn-primary btn-lg"
              onClick={handleConfirm}
              disabled={confirming || !selectedCard || isExpired}
              style={{ width: "100%" }}
            >
              {isExpired ? "Session Expired" : confirming ? "Confirming…" : selectedCard ? `Pay $${finalTotal.toFixed(2)}` : "Add a payment method"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
