import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import BookingConflictWarning, { type BookingInfo } from "../mybooking/BookingConflictWarning";
import { ROOM_LABELS, ROOM_MULTIPLIERS } from "../constants";
import "./Booking.css";

type Step = 1 | 2 | 3;

interface HotelMeta { id: number; name: string; city: string; price_per_night: number; }

interface AvailRoom { id: number; room: number; room_type: string; }

interface RoomOption {
  type: string;
  label: string;
  count: number;
  price: number;
  rooms: AvailRoom[];
}

interface ConflictRow { booking_id: number; hotel_name: string | null; start_date: string; end_date: string; }

function calcNights(ci: string, co: string) {
  if (!ci || !co) return 0;
  const n = Math.floor((new Date(co).getTime() - new Date(ci).getTime()) / 86400000);
  return n > 0 ? n : 0;
}

function fmtDate(iso: string) {
  return new Date(iso + "T00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export default function Booking() {
  const { hotelId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const auth = useAuth();
  const rescheduleBookingId = searchParams.get("rescheduleBookingId");
  const isReschedule = !!rescheduleBookingId;
  const [hotel, setHotel] = useState<HotelMeta | null>(null);
  const [step, setStep] = useState<Step>(1);
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(1);
  const [title, setTitle] = useState("");
  const [roomOptions, setRoomOptions] = useState<RoomOption[]>([]);
  const [selectedType, setSelectedType] = useState("");
  const [stepLoading, setStepLoading] = useState(false);
  const [stepError, setStepError] = useState("");
  const [conflict, setConflict] = useState<{ newB: BookingInfo; existingB: BookingInfo } | null>(null);
  const [creating, setCreating] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [originalCheckIn, setOriginalCheckIn] = useState("");
  const [originalCheckOut, setOriginalCheckOut] = useState("");

  const today = new Date().toISOString().split("T")[0];
  const nights = useMemo(() => calcNights(checkIn, checkOut), [checkIn, checkOut]);
  const canAdvance1 = title.trim() && checkIn && checkOut && nights > 0 && guests >= 1 && guests <= 8;
  const selectedOpt = roomOptions.find((o) => o.type === selectedType) ?? null;
  const total = selectedOpt ? selectedOpt.price * nights : 0;

  useEffect(() => {
    if (!auth.isAuthenticated) { navigate("/login"); return; }
    if (!hotelId) return;
    fetch(`/hotels/${hotelId}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.error) { navigate("/"); return; }
        setHotel({ id: d.id, name: d.name, city: d.city, price_per_night: d.price_per_night });
      });
  }, [hotelId, auth.isAuthenticated, navigate]);

  useEffect(() => {
    if (!isReschedule || !rescheduleBookingId || !auth.isAuthenticated) return;
    fetch(`/reservations/${rescheduleBookingId}`, { headers: auth.authHeader() })
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) {
          setLoadError(d.error || `Could not load booking (${r.status}).`);
          return;
        }
        setTitle(d.title || "");
        setOriginalCheckIn(d.start_date || "");
        setOriginalCheckOut(d.end_date || "");
        setCheckIn(d.start_date || "");
        setCheckOut(d.end_date || "");
      })
      .catch(() => setLoadError("Network error — is the backend running?"));
  }, [auth, isReschedule, rescheduleBookingId]);

  // Step 1 → 2: check user conflicts, then load available rooms
  const goToStep2 = async (force = false) => {
    setStepError("");
    setStepLoading(true);

    try {
      if (!force) {
        const cp = new URLSearchParams({ start_date: checkIn, end_date: checkOut });
        const cr = await fetch(`/reservations/check-conflicts?${cp}`, { headers: auth.authHeader() });
        const cd = await cr.json();
        const conflicts: ConflictRow[] = (cd.conflicts ?? []).filter(
          (row: ConflictRow) => !isReschedule || row.booking_id !== Number(rescheduleBookingId),
        );
        if (conflicts.length > 0) {
          const first: ConflictRow = conflicts[0];
          setConflict({
            newB: { hotelName: hotel!.name, checkIn: fmtDate(checkIn), checkOut: fmtDate(checkOut) },
            existingB: { hotelName: first.hotel_name ?? "Another hotel", checkIn: fmtDate(first.start_date), checkOut: fmtDate(first.end_date) },
          });
          setStepLoading(false);
          return;
        }
      }

      const ap = new URLSearchParams({ hotel_id: String(hotelId), start_date: checkIn, end_date: checkOut });
      const ar = await fetch(`/reservations/availability?${ap}`);
      const ad: AvailRoom[] | { error?: string } = await ar.json();

      if (!ar.ok || "error" in ad) {
        setStepError((ad as { error?: string }).error || "Failed to check availability.");
        return;
      }

      const grouped: Record<string, RoomOption> = {};
      for (const r of ad as AvailRoom[]) {
        if (!grouped[r.room_type]) {
          grouped[r.room_type] = {
            type: r.room_type,
            label: ROOM_LABELS[r.room_type] ?? r.room_type,
            count: 0,
            price: hotel!.price_per_night * (ROOM_MULTIPLIERS[r.room_type] ?? 1),
            rooms: [],
          };
        }
        grouped[r.room_type].count++;
        grouped[r.room_type].rooms.push(r);
      }

      const opts = Object.values(grouped).sort((a, b) => a.price - b.price);
      if (opts.length === 0) {
        setStepError("No rooms available for these dates.");
        return;
      }

      setRoomOptions(opts);
      setStep(2);
    } catch {
      setStepError("Network error — please try again.");
    } finally {
      setStepLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!selectedOpt || !hotel) return;
    setCreating(true);
    setStepError("");
    try {
      const body = JSON.stringify({ title, room: selectedOpt.rooms[0].id, start_date: checkIn, end_date: checkOut });
      const res = await fetch(isReschedule ? `/reservations/${rescheduleBookingId}` : "/reservations/", {
        method: isReschedule ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json", ...auth.authHeader() },
        body,
      });
      const data = await res.json();
      if (!res.ok) { setStepError(data.error || "Booking failed."); return; }
      if (isReschedule) {
        navigate("/my-bookings");
        return;
      }
      navigate(`/checkout?booking_id=${data.booking.id}`);
    } catch {
      setStepError("Network error — please try again.");
    } finally {
      setCreating(false);
    }
  };

  if (!hotel) return <div className="booking-loading">Loading…</div>;

  return (
    <div className="booking-page">
      {conflict && (
        <BookingConflictWarning
          newBooking={conflict.newB}
          existingBooking={conflict.existingB}
          onGoBack={() => { setConflict(null); setStepLoading(false); }}
          onBookAnyway={() => { setConflict(null); goToStep2(true); }}
        />
      )}

      <div className="booking-container">
        <div className="booking-breadcrumb">
          <Link to={`/hotel/${hotel.id}`}>← {hotel.name}</Link>
        </div>

        {/* Step indicators */}
        <div className="booking-steps">
          {(["Dates", "Room", "Confirm"] as const).map((label, i) => (
            <div key={label} className={`booking-step${step === i + 1 ? " active" : ""}${step > i + 1 ? " done" : ""}`}>
              <div className="step-num">{step > i + 1 ? "✓" : i + 1}</div>
              <span>{label}</span>
            </div>
          ))}
        </div>

        <div className="booking-card card">
          {/* ── Step 1 ─────────────────── */}
          {step === 1 && (
            <>
              <h2>Select dates</h2>

              <div className="booking-grid">
                <div className="form-group" style={{ gridColumn: "1/-1" }}>
                  <label className="form-label">Trip name</label>
                  <input className="form-input" type="text" placeholder='e.g. "Family vacation"' value={title} onChange={(e) => setTitle(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Check-in</label>
                  <input className="form-input" type="date" min={today} value={checkIn} onChange={(e) => setCheckIn(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Check-out</label>
                  <input className="form-input" type="date" min={checkIn || today} value={checkOut} onChange={(e) => setCheckOut(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Guests</label>
                  <input className="form-input" type="number" min={1} max={8} value={guests} onChange={(e) => setGuests(Number(e.target.value))} />
                </div>
              </div>

              {nights > 0 && hotel && (
                <p className="booking-hint">
                  {nights} night{nights !== 1 ? "s" : ""} · from ${(hotel.price_per_night * 0.85 * nights).toFixed(0)} estimated
                </p>
              )}

              {stepError && <div className="alert alert-error">{stepError}</div>}

              <div className="booking-actions">
                <button className="btn btn-primary" onClick={() => goToStep2(false)} disabled={!canAdvance1 || stepLoading}>
                  {stepLoading ? "Checking…" : "Check Availability"}
                </button>
              </div>
            </>
          )}

          {/* ── Step 2 ─────────────────── */}
          {step === 2 && (
            <>
              <h2>Choose a room</h2>
              <div className="room-grid">
                {roomOptions.map((opt) => (
                  <button
                    key={opt.type}
                    className={`room-card${opt.type === selectedType ? " active" : ""}`}
                    onClick={() => setSelectedType(opt.type)}
                  >
                    <div className="room-card-top">
                      <span className="room-name">{opt.label}</span>
                      <span className="room-price">${opt.price.toFixed(0)}/night</span>
                    </div>
                    <span className="room-avail">{opt.count} available</span>
                  </button>
                ))}
              </div>

              {selectedOpt && (
                <div className="booking-summary">
                  {selectedOpt.label} × {nights} night{nights !== 1 ? "s" : ""} =&nbsp;
                  <strong>${total.toFixed(2)}</strong>
                </div>
              )}

              <div className="booking-actions">
                <button className="btn btn-secondary" onClick={() => { setStep(1); setStepError(""); }}>Back</button>
                <button className="btn btn-primary" onClick={() => { if (selectedOpt) { setStep(3); setStepError(""); } }} disabled={!selectedOpt}>Next</button>
              </div>
            </>
          )}

          {/* ── Step 3 ─────────────────── */}
          {step === 3 && selectedOpt && (
            <>
              <h2>Confirm booking</h2>
              <div className="confirm-block">
                {isReschedule && originalCheckIn && originalCheckOut && (
                  <div className="confirm-grid" style={{ marginBottom: 12 }}>
                    <div className="confirm-row">
                      <span className="confirm-key">New Check-In dates</span>
                      <strong className="confirm-val">{originalCheckIn} → {originalCheckOut}</strong>
                    </div>
                    <div className="confirm-row">
                      <span className="confirm-key">New Check-Out dates</span>
                      <strong className="confirm-val">{checkIn} → {checkOut}</strong>
                    </div>
                  </div>
                )}
                <div className="confirm-grid">
                  {[
                    ["Hotel", hotel.name],
                    ["Trip", title],
                    ...(!isReschedule ? [["Check-in", checkIn], ["Check-out", checkOut]] : []),
                    ["Guests", String(guests)],
                    ["Room", selectedOpt.label],
                  ].map(([k, v]) => (
                    <div key={k} className="confirm-row">
                      <span className="confirm-key">{k}</span>
                      <strong className="confirm-val">{v}</strong>
                    </div>
                  ))}
                </div>
                <div className="confirm-total">
                  <span>Total</span>
                  <strong>${total.toFixed(2)}</strong>
                </div>
                <p className="confirm-hint">You can apply rewards points on the next screen.</p>
              </div>

              {stepError && <div className="alert alert-error">{stepError}</div>}

              <div className="booking-actions">
                <button className="btn btn-secondary" onClick={() => { setStep(2); setStepError(""); }}>Back</button>
                <button className="btn btn-primary" onClick={handleConfirm} disabled={creating}>
                  {creating ? (isReschedule ? "Saving…" : "Creating…") : (isReschedule ? "Save Changes" : "Proceed to Checkout")}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
