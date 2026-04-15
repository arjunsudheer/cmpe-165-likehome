import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./MyBookingsPage.css";

interface BookingRow {
  id: number;
  booking_number: string;
  title: string;
  hotel_id: number | null;
  hotel_name: string | null;
  hotel_city: string | null;
  room_type: string | null;
  start_date: string;
  end_date: string;
  total_price: string;
  status: "INPROGRESS" | "CONFIRMED" | "COMPLETED" | "CANCELLED";
}

interface CancellationPreview {
  booking_id: number;
  booking_number: string;
  status: "INPROGRESS" | "CONFIRMED" | "COMPLETED" | "CANCELLED";
  policy_hours: number;
  check_in_date: string;
  cutoff_at: string;
  fee_amount: string;
  refund_amount: string;
  points_to_restore: number;
}

const STATUS_LABEL = { INPROGRESS: "Pending", CONFIRMED: "Confirmed", COMPLETED: "Completed", CANCELLED: "Cancelled" };
const STATUS_BADGE = { INPROGRESS: "badge-pending", CONFIRMED: "badge-confirmed", COMPLETED: "badge-completed", CANCELLED: "badge-cancelled" };

function nights(start: string, end: string) {
  return Math.round((new Date(end).getTime() - new Date(start).getTime()) / 86400000);
}

export default function MyBookingsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [bookings, setBookings] = useState<BookingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancelling, setCancelling] = useState<number | null>(null);
  const [confirmCancelId, setConfirmCancelId] = useState<number | null>(null);
  const [cancelPreview, setCancelPreview] = useState<CancellationPreview | null>(null);
  const [cancelPreviewLoading, setCancelPreviewLoading] = useState(false);
  const [cancelPreviewError, setCancelPreviewError] = useState("");

  useEffect(() => {
    if (!auth.isAuthenticated) { navigate("/login"); return; }
    fetch("/reservations/", { headers: auth.authHeader() })
      .then((r) => {
        if (!r.ok) throw new Error(`Bookings fetch failed: ${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((d) => {
        if (Array.isArray(d)) setBookings(d);
        else setError(d.error || "Failed to load bookings.");
      })
      .catch((err) => {
        console.error("Bookings fetch error:", err);
        setError(err instanceof Error ? err.message : "Network error.");
      })
      .finally(() => setLoading(false));
  }, [auth, navigate]);

  const handleCancelClick = (id: number) => {
    setCancelPreview(null);
    setCancelPreviewError("");
    setConfirmCancelId(id);
  };

  useEffect(() => {
    if (confirmCancelId === null) return;
    setCancelPreviewLoading(true);
    setCancelPreviewError("");

    fetch(`/reservations/${confirmCancelId}/cancellation-preview`, {
      headers: auth.authHeader(),
    })
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || "Failed to load cancellation details.");
        setCancelPreview(d.cancellation ?? null);
      })
      .catch((err) => {
        setCancelPreview(null);
        setCancelPreviewError(
          err instanceof Error ? err.message : "Failed to load cancellation details.",
        );
      })
      .finally(() => setCancelPreviewLoading(false));
  }, [auth, confirmCancelId]);

  const confirmCancel = async () => {
    if (confirmCancelId === null) return;
    const id = confirmCancelId;
    setCancelling(id);
    setCancelPreviewError("");
    try {
      const r = await fetch(`/reservations/${id}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json", ...auth.authHeader() },
        body: JSON.stringify({ confirmed: true }),
      });
      const d = await r.json();
      if (!r.ok) {
        setCancelPreviewError(d.error || "Cancel failed.");
        return;
      }
      setBookings((prev) => prev.map((b) => b.id === id ? { ...b, status: "CANCELLED" } : b));
      setConfirmCancelId(null);
      setCancelPreview(null);
    } catch {
      setCancelPreviewError("Network error.");
    } finally {
      setCancelling(null);
    }
  };

  const upcoming = bookings.filter((b) => b.status === "CONFIRMED" || b.status === "INPROGRESS");
  const past = bookings.filter((b) => b.status === "COMPLETED" || b.status === "CANCELLED");
  const bookingToCancel = bookings.find((b) => b.id === confirmCancelId) ?? null;
  const cancellationFee = bookingToCancel
    ? (parseFloat(bookingToCancel.total_price) * 0.10).toFixed(2)
    : null;
  const refundAmount = bookingToCancel
    ? (parseFloat(bookingToCancel.total_price) * 0.90).toFixed(2)
    : null;

  return (
    <div className="my-bookings-page">
      <div className="my-bookings-container">
        <h1>My Bookings</h1>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="bookings-skeletons">
            {[1, 2, 3].map((i) => <div key={i} className="booking-skeleton" />)}
          </div>
        ) : bookings.length === 0 ? (
          <div className="bookings-empty">
            <div className="bookings-empty-icon">🏨</div>
            <h2>No bookings yet</h2>
            <p>Find your next stay and book in minutes.</p>
            <Link to="/" className="btn btn-primary">Browse Hotels</Link>
          </div>
        ) : (
          <>
            {upcoming.length > 0 && (
              <section className="bookings-group">
                <h2 className="group-label">Upcoming</h2>
                {upcoming.map((b) => <BookingCard key={b.id} b={b} onCancel={handleCancelClick} cancelling={cancelling === b.id} />)}
              </section>
            )}
            {past.length > 0 && (
              <section className="bookings-group">
                <h2 className="group-label">Past</h2>
                {past.map((b) => <BookingCard key={b.id} b={b} onCancel={handleCancelClick} cancelling={cancelling === b.id} />)}
              </section>
            )}
          </>
        )}
      </div>

      {confirmCancelId !== null && (
        <div className="cancel-overlay" onClick={() => setConfirmCancelId(null)}>
          <div className="cancel-dialog card" onClick={(e) => e.stopPropagation()}>
            <div className="cancel-icon">⚠️</div>
            <h2 className="cancel-title">Cancel Booking?</h2>
            <p className="cancel-sub">
              Review the cancellation details below before confirming.
            </p>
            {cancelPreviewLoading && (
              <p className="cancel-sub">Loading refund details…</p>
            )}
            {!cancelPreviewLoading && cancelPreviewError && (
              <div className="alert alert-error">{cancelPreviewError}</div>
            )}
            {!cancelPreviewLoading && !cancelPreviewError && cancelPreview && (
              <div className="booking-details-grid" style={{ marginBottom: 20 }}>
                {[
                  ["Check-in", cancelPreview.check_in_date],
                  ["Cancel by", new Date(cancelPreview.cutoff_at).toLocaleString()],
                  ["Cancellation fee", `$${cancellationFee ?? Number(cancelPreview.fee_amount).toFixed(2)}`],
                  ["Refund", `$${refundAmount ?? Number(cancelPreview.refund_amount).toFixed(2)}`],
                  ["Points restored", cancelPreview.points_to_restore.toLocaleString()],
                ].map(([k, v]) => (
                  <div key={k} className="booking-detail">
                    <span className="detail-label">{k}</span>
                    <span className="detail-value">{v}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="cancel-actions">
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setConfirmCancelId(null);
                  setCancelPreview(null);
                  setCancelPreviewError("");
                }}
              >
                Go Back
              </button>
              <button
                className="btn btn-danger"
                onClick={confirmCancel}
                disabled={cancelPreviewLoading || !!cancelPreviewError || !cancelPreview || cancelling === confirmCancelId}
              >
                {cancelling === confirmCancelId ? "Cancelling…" : "Confirm Cancellation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BookingCard({ b, onCancel, cancelling }: { b: BookingRow; onCancel: (id: number) => void; cancelling: boolean }) {
  const n = nights(b.start_date, b.end_date);
  const canCancel = b.status === "CONFIRMED" || b.status === "INPROGRESS";
  const canReschedule = b.status !== "CANCELLED";

  return (
    <div className={`booking-card card${b.status === "CANCELLED" ? " booking-card-cancelled" : ""}`}>
      <div className="booking-card-header">
        <div>
          {b.hotel_id
            ? <a href={`/hotel/${b.hotel_id}`} target="_blank" rel="noopener noreferrer" className="booking-hotel-name">{b.hotel_name ?? "Unknown hotel"}</a>
            : <span className="booking-hotel-name">{b.hotel_name ?? "Unknown hotel"}</span>
          }
          {b.hotel_city && <span className="booking-city">{b.hotel_city}</span>}
        </div>
        <span className={`badge ${STATUS_BADGE[b.status]}`}>{STATUS_LABEL[b.status]}</span>
      </div>

      <div className="booking-details-grid">
        {[
          ["Trip", b.title],
          ["Check-in", b.start_date],
          ["Check-out", b.end_date],
          ["Nights", String(n)],
          ["Room", b.room_type ? b.room_type.charAt(0) + b.room_type.slice(1).toLowerCase() : "—"],
          ["Total", `$${parseFloat(b.total_price).toFixed(2)}`],
        ].map(([k, v]) => (
          <div key={k} className="booking-detail">
            <span className="detail-label">{k}</span>
            <span className="detail-value">{v}</span>
          </div>
        ))}
      </div>

      <div className="booking-card-footer">
        <span className="booking-ref">{b.booking_number}</span>
        <div className="booking-actions-row">
          {canReschedule && (
            b.hotel_id ? (
              <Link className="btn btn-secondary booking-reschedule-btn" to={`/booking/${b.hotel_id}?rescheduleBookingId=${b.id}`}>
                Reschedule
              </Link>
            ) : (
              <button className="btn btn-secondary booking-reschedule-btn" disabled>
                Reschedule
              </button>
            )
          )}
          {canCancel && (
            <button className="btn btn-secondary booking-cancel-btn" onClick={() => onCancel(b.id)} disabled={cancelling}>
              {cancelling ? "Cancelling…" : "Cancel"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}