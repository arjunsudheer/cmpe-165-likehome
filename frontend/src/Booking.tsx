import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import "./Booking.css";

type Step = 1 | 2 | 3;

type Room = {
  id: string;
  name: string;
  capacity: number;
  pricePerNight: number;
  features: string[];
};

const rooms: Room[] = [
  {
    id: "studio",
    name: "Studio Suite",
    capacity: 2,
    pricePerNight: 89,
    features: ["Free Wi-Fi", "City view", "Queen bed"],
  },
  {
    id: "family",
    name: "Family Room",
    capacity: 4,
    pricePerNight: 129,
    features: ["2 bedrooms", "Kitchenette", "Family friendly"],
  },
  {
    id: "penthouse",
    name: "Penthouse",
    capacity: 6,
    pricePerNight: 199,
    features: ["Terrace", "Living area", "Premium amenities"],
  },
];

function toLocalDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const d = new Date(`${dateStr}T00:00:00`);
  if (Number.isNaN(d.getTime())) return null;
  return d;
}

function calcNights(checkIn: string, checkOut: string): number {
  const start = toLocalDate(checkIn);
  const end = toLocalDate(checkOut);
  if (!start || !end) return 0;
  const diffMs = end.getTime() - start.getTime();
  const nights = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  return nights > 0 ? nights : 0;
}

function formatMoney(amount: number): string {
  // Simple formatting to keep it dependency-free.
  return `$${amount.toFixed(2)}`;
}

export default function Booking() {
  const [step, setStep] = useState<Step>(1);
  const [checkIn, setCheckIn] = useState<string>("");
  const [checkOut, setCheckOut] = useState<string>("");
  const [guests, setGuests] = useState<number>(2);
  const [selectedRoomId, setSelectedRoomId] = useState<string>("");
  const [status, setStatus] = useState<string>("");

  const selectedRoom = useMemo(
    () => rooms.find((r) => r.id === selectedRoomId) ?? null,
    [selectedRoomId],
  );

  const nights = useMemo(() => calcNights(checkIn, checkOut), [checkIn, checkOut]);
  const totalPrice = useMemo(() => {
    if (!selectedRoom) return 0;
    return nights * selectedRoom.pricePerNight;
  }, [nights, selectedRoom]);

  const canGoStep2 = useMemo(() => {
    return nights > 0 && guests >= 1 && guests <= 8;
  }, [nights, guests]);

  const canGoStep3 = Boolean(selectedRoom);

  const goNext = () => {
    setStatus("");
    if (step === 1) {
      if (!canGoStep2) {
        setStatus("Please select valid dates and number of guests.");
        return;
      }
      setStep(2);
      return;
    }

    if (step === 2) {
      if (!canGoStep3) {
        setStatus("Please select a room type.");
        return;
      }
      setStep(3);
      return;
    }
  };

  const goBack = () => {
    setStatus("");
    if (step === 1) return;
    if (step === 2) setStep(1);
    if (step === 3) setStep(2);
  };

  const confirm = () => {
    setStatus("");
    if (!selectedRoom) {
      setStatus("Room is required.");
      setStep(2);
      return;
    }
    if (!nights) {
      setStatus("Invalid dates.");
      setStep(1);
      return;
    }
    setStatus(
      `Confirmed! ${selectedRoom.name} for ${guests} guest(s), ${nights} night(s), total ${formatMoney(
        totalPrice,
      )}.`,
    );
  };

  return (
    <div className="booking-page">
      <header className="booking-header">
        <div className="booking-title">
          <h1>LikeHome</h1>
          <p>Booking flow UI: pick dates, choose room, confirm.</p>
        </div>

        <nav className="booking-nav">
          <Link to="/" className="booking-link">
            Register
          </Link>
          <Link to="/booking" className="booking-link">
            Booking
          </Link>
        </nav>
      </header>

      <main className="booking-main">
        <div className="booking-steps" aria-label="Booking steps">
          <div className={`booking-step ${step === 1 ? "active" : ""} ${step > 1 ? "done" : ""}`}>
            <div className="booking-step-index">1</div>
            <div className="booking-step-label">Dates</div>
          </div>
          <div className={`booking-step ${step === 2 ? "active" : ""} ${step > 2 ? "done" : ""}`}>
            <div className="booking-step-index">2</div>
            <div className="booking-step-label">Room</div>
          </div>
          <div className={`booking-step ${step === 3 ? "active" : ""}`}>
            <div className="booking-step-index">3</div>
            <div className="booking-step-label">Confirm</div>
          </div>
        </div>

        <section className="booking-card" aria-live="polite">
          {step === 1 && (
            <>
              <h2 className="booking-card-title">Select your dates</h2>
              <div className="booking-grid">
                <label className="booking-field">
                  <span>Check-in</span>
                  <input
                    type="date"
                    value={checkIn}
                    onChange={(e) => setCheckIn(e.target.value)}
                    required
                  />
                </label>

                <label className="booking-field">
                  <span>Check-out</span>
                  <input
                    type="date"
                    value={checkOut}
                    onChange={(e) => setCheckOut(e.target.value)}
                    min={checkIn || undefined}
                    required
                  />
                </label>

                <label className="booking-field">
                  <span>Guests</span>
                  <input
                    type="number"
                    min={1}
                    max={8}
                    value={guests}
                    onChange={(e) => setGuests(Number(e.target.value))}
                    required
                  />
                </label>
              </div>

              {nights > 0 ? (
                <p className="booking-hint">You selected {nights} night(s).</p>
              ) : (
                <p className="booking-hint">Choose a valid check-in and check-out.</p>
              )}

              <div className="booking-actions">
                <button type="button" className="booking-btn" onClick={goNext} disabled={!canGoStep2}>
                  Next
                </button>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <h2 className="booking-card-title">Choose a room</h2>

              <div className="room-grid" role="list">
                {rooms.map((room) => {
                  const active = room.id === selectedRoomId;
                  return (
                    <button
                      key={room.id}
                      type="button"
                      className={`room-card ${active ? "active" : ""}`}
                      onClick={() => setSelectedRoomId(room.id)}
                      aria-pressed={active}
                    >
                      <div className="room-card-head">
                        <div className="room-name">{room.name}</div>
                        <div className="room-price">{formatMoney(room.pricePerNight)}/night</div>
                      </div>
                      <div className="room-capacity">Capacity: up to {room.capacity} guests</div>
                      <ul className="room-features">
                        {room.features.map((f) => (
                          <li key={f}>{f}</li>
                        ))}
                      </ul>
                    </button>
                  );
                })}
              </div>

              {selectedRoom && nights > 0 ? (
                <div className="booking-summary-inline">
                  <div>
                    {selectedRoom.name} x {nights} night(s)
                  </div>
                  <div className="booking-summary-inline-price">Total: {formatMoney(totalPrice)}</div>
                </div>
              ) : (
                <p className="booking-hint">Select a room to continue.</p>
              )}

              <div className="booking-actions">
                <button type="button" className="booking-btn secondary" onClick={goBack}>
                  Back
                </button>
                <button type="button" className="booking-btn" onClick={goNext} disabled={!canGoStep3}>
                  Next
                </button>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <h2 className="booking-card-title">Confirm your booking</h2>

              {selectedRoom ? (
                <div className="confirm-grid">
                  <div className="confirm-block">
                    <div className="confirm-row">
                      <span>Check-in</span>
                      <strong>{checkIn || "-"}</strong>
                    </div>
                    <div className="confirm-row">
                      <span>Check-out</span>
                      <strong>{checkOut || "-"}</strong>
                    </div>
                    <div className="confirm-row">
                      <span>Guests</span>
                      <strong>{guests}</strong>
                    </div>
                    <div className="confirm-row">
                      <span>Room</span>
                      <strong>{selectedRoom.name}</strong>
                    </div>
                  </div>

                  <div className="confirm-price">
                    <div className="confirm-price-line">
                      {formatMoney(selectedRoom.pricePerNight)} x {nights} night(s)
                    </div>
                    <div className="confirm-price-total">Total: {formatMoney(totalPrice)}</div>
                    <button type="button" className="booking-btn" onClick={confirm}>
                      Confirm
                    </button>
                  </div>
                </div>
              ) : (
                <p className="booking-hint">Missing room selection.</p>
              )}

              <div className="booking-actions">
                <button type="button" className="booking-btn secondary" onClick={goBack}>
                  Back
                </button>
              </div>
            </>
          )}

          {status && <div className="booking-status">{status}</div>}
        </section>
      </main>
    </div>
  );
}

