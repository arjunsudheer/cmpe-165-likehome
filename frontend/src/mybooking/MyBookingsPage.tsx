import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import CancellationConfirmDialog from "./CancellationConfirmDialog";
import type { CancellationPreview } from "./CancellationConfirmDialog";
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

const STATUS_LABEL = {
  INPROGRESS: "Pending",
  CONFIRMED: "Confirmed",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
};
const STATUS_BADGE = {
  INPROGRESS: "badge-pending",
  CONFIRMED: "badge-confirmed",
  COMPLETED: "badge-completed",
  CANCELLED: "badge-cancelled",
};

function nights(start: string, end: string) {
  return Math.round(
    (new Date(end).getTime() - new Date(start).getTime()) / 86400000,
  );
}

// ── Receipt HTML generator ─────────────────────────────────────────────────────

function buildReceiptHTML(b: BookingRow): string {
  const n = nights(b.start_date, b.end_date);
  const fee = (parseFloat(b.total_price) * 0.1).toFixed(2);
  const rows: [string, string][] = [
    ["Booking Number", b.booking_number],
    ["Trip Title", b.title],
    ["Hotel", b.hotel_name ?? "—"],
    ["City", b.hotel_city ?? "—"],
    [
      "Room Type",
      b.room_type
        ? b.room_type.charAt(0) + b.room_type.slice(1).toLowerCase()
        : "—",
    ],
    ["Check-in", b.start_date],
    ["Check-out", b.end_date],
    ["Nights", String(n)],
    ["Status", STATUS_LABEL[b.status]],
    ["Total Price", `$${parseFloat(b.total_price).toFixed(2)}`],
    ["Cancellation Fee (10%)", `$${fee}`],
  ];

  const tableRows = rows
    .map(
      ([k, v]) => `
      <tr>
        <td class="label">${k}</td>
        <td class="value">${v}</td>
      </tr>`,
    )
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Booking Receipt – ${b.booking_number}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #1a1a2e;
      padding: 48px 40px;
      max-width: 640px;
      margin: 0 auto;
    }
    header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; }
    .brand { font-size: 22px; font-weight: 900; letter-spacing: -0.5px; color: var(--c-primary, #7c6fcd); }
    .receipt-label { font-size: 11px; font-weight: 700; text-transform: uppercase;
                     letter-spacing: 1px; color: #888; text-align: right; }
    .receipt-label strong { display: block; font-size: 18px; color: #1a1a2e;
                            text-transform: none; letter-spacing: 0; margin-top: 2px; }
    hr { border: none; border-top: 1.5px solid #e5e7eb; margin-bottom: 28px; }
    table { width: 100%; border-collapse: collapse; }
    tr:nth-child(even) td { background: #f9fafb; }
    td { padding: 10px 14px; font-size: 14px; }
    td.label { font-weight: 600; color: #6b7280; width: 46%; }
    td.value { color: #111827; }
    footer { margin-top: 40px; font-size: 12px; color: #9ca3af; text-align: center; }
    @media print {
      body { padding: 24px; }
      @page { margin: 1cm; }
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">Like<span>Home</span></div>
    <div class="receipt-label">
      Booking Receipt
      <strong>${b.booking_number}</strong>
    </div>
  </header>
  <hr />
  <table>
    <tbody>${tableRows}</tbody>
  </table>
  <footer>
    Issued on ${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
    &nbsp;·&nbsp; Thank you for staying with us.
  </footer>
</body>
</html>`;
}

function downloadReceipt(b: BookingRow) {
  const html = buildReceiptHTML(b);
  // Open in a hidden iframe, then print — the browser's "Save as PDF" option handles the rest
  const iframe = document.createElement("iframe");
  iframe.style.cssText = "position:fixed;width:0;height:0;border:0;opacity:0;";
  document.body.appendChild(iframe);

  const doc = iframe.contentWindow?.document;
  if (!doc) {
    document.body.removeChild(iframe);
    return;
  }
  doc.open();
  doc.write(html);
  doc.close();

  iframe.contentWindow?.focus();
  // Small delay to allow styles to render before printing
  setTimeout(() => {
    iframe.contentWindow?.print();
    setTimeout(() => document.body.removeChild(iframe), 1000);
  }, 300);
}

// ── MyBookingsPage ─────────────────────────────────────────────────────────────

export default function MyBookingsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [bookings, setBookings] = useState<BookingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancelling, setCancelling] = useState<number | null>(null);
  const [confirmCancelId, setConfirmCancelId] = useState<number | null>(null);
  const [cancelPreview, setCancelPreview] =
    useState<CancellationPreview | null>(null);
  const [cancelPreviewLoading, setCancelPreviewLoading] = useState(false);
  const [cancelPreviewError, setCancelPreviewError] = useState("");
  const [cancelPolicyBlocked, setCancelPolicyBlocked] = useState<string | null>(
    null,
  );

  // Per-booking email state: null = idle, "sending" = in-flight, "sent" = success, string = error message
  const [emailStatus, setEmailStatus] = useState<
    Record<number, "sending" | "sent" | string>
  >({});

  useEffect(() => {
    if (!auth.isAuthenticated) {
      navigate("/login");
      return;
    }
    fetch("/reservations/", { headers: auth.authHeader() })
      .then((r) => {
        if (!r.ok)
          throw new Error(`Bookings fetch failed: ${r.status} ${r.statusText}`);
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
    setCancelPolicyBlocked(null);
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
        if (r.ok) {
          setCancelPolicyBlocked(null);
          setCancelPreview(d.cancellation ?? null);
          return;
        }
        if (d.cancellation) {
          setCancelPreview(d.cancellation);
          setCancelPolicyBlocked(
            d.error || "This booking cannot be cancelled online.",
          );
          return;
        }
        throw new Error(d.error || "Failed to load cancellation details.");
      })
      .catch((err) => {
        setCancelPreview(null);
        setCancelPolicyBlocked(null);
        setCancelPreviewError(
          err instanceof Error
            ? err.message
            : "Failed to load cancellation details.",
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
      setBookings((prev) =>
        prev.map((b) => (b.id === id ? { ...b, status: "CANCELLED" } : b)),
      );
      setConfirmCancelId(null);
      setCancelPreview(null);
      setCancelPolicyBlocked(null);
    } catch {
      setCancelPreviewError("Network error.");
    } finally {
      setCancelling(null);
    }
  };

  const handleEmailReceipt = async (id: number) => {
    setEmailStatus((prev) => ({ ...prev, [id]: "sending" }));
    try {
      const r = await fetch(`/reservations/${id}/email-receipt`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...auth.authHeader() },
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || "Failed to send email.");
      setEmailStatus((prev) => ({ ...prev, [id]: "sent" }));
      setTimeout(
        () =>
          setEmailStatus((prev) => {
            const s = { ...prev };
            delete s[id];
            return s;
          }),
        4000,
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to send email.";
      setEmailStatus((prev) => ({ ...prev, [id]: msg }));
      setTimeout(
        () =>
          setEmailStatus((prev) => {
            const s = { ...prev };
            delete s[id];
            return s;
          }),
        4000,
      );
    }
  };

  const upcoming = bookings.filter(
    (b) => b.status === "CONFIRMED" || b.status === "INPROGRESS",
  );
  const past = bookings.filter(
    (b) => b.status === "COMPLETED" || b.status === "CANCELLED",
  );
  const bookingToCancel =
    bookings.find((b) => b.id === confirmCancelId) ?? null;

  return (
    <div className="my-bookings-page">
      <div className="my-bookings-container">
        <h1>My Bookings</h1>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="bookings-skeletons">
            {[1, 2, 3].map((i) => (
              <div key={i} className="booking-skeleton" />
            ))}
          </div>
        ) : bookings.length === 0 ? (
          <div className="bookings-empty">
            <div className="bookings-empty-icon">🏨</div>
            <h2>No bookings yet</h2>
            <p>Find your next stay and book in minutes.</p>
            <Link to="/" className="btn btn-primary">
              Browse Hotels
            </Link>
          </div>
        ) : (
          <>
            {upcoming.length > 0 && (
              <section className="bookings-group">
                <h2 className="group-label">Upcoming</h2>
                {upcoming.map((b) => (
                  <BookingCard
                    key={b.id}
                    b={b}
                    onCancel={handleCancelClick}
                    cancelling={cancelling === b.id}
                    onDownloadReceipt={downloadReceipt}
                    onEmailReceipt={handleEmailReceipt}
                    emailStatus={emailStatus[b.id] ?? null}
                  />
                ))}
              </section>
            )}
            {past.length > 0 && (
              <section className="bookings-group">
                <h2 className="group-label">Past</h2>
                {past.map((b) => (
                  <BookingCard
                    key={b.id}
                    b={b}
                    onCancel={handleCancelClick}
                    cancelling={cancelling === b.id}
                    onDownloadReceipt={downloadReceipt}
                    onEmailReceipt={handleEmailReceipt}
                    emailStatus={emailStatus[b.id] ?? null}
                  />
                ))}
              </section>
            )}
          </>
        )}
      </div>

      <CancellationConfirmDialog
        key={
          confirmCancelId !== null
            ? `${confirmCancelId}-${cancelPreview?.booking_id ?? "pending"}`
            : "closed"
        }
        open={confirmCancelId !== null}
        onClose={() => {
          if (cancelling !== null) return;
          setConfirmCancelId(null);
          setCancelPreview(null);
          setCancelPreviewError("");
          setCancelPolicyBlocked(null);
        }}
        preview={cancelPreview}
        loading={cancelPreviewLoading}
        loadError={cancelPreviewError}
        policyBlockedMessage={cancelPolicyBlocked}
        hotelName={bookingToCancel?.hotel_name ?? null}
        tripTitle={bookingToCancel?.title ?? null}
        onConfirm={confirmCancel}
        confirming={cancelling === confirmCancelId}
      />
    </div>
  );
}

// ── BookingCard ────────────────────────────────────────────────────────────────

function BookingCard({
  b,
  onCancel,
  cancelling,
  onDownloadReceipt,
  onEmailReceipt,
  emailStatus,
}: {
  b: BookingRow;
  onCancel: (id: number) => void;
  cancelling: boolean;
  onDownloadReceipt: (b: BookingRow) => void;
  onEmailReceipt: (id: number) => void;
  emailStatus: "sending" | "sent" | string | null;
}) {
  const n = nights(b.start_date, b.end_date);
  const canCancel = b.status === "CONFIRMED" || b.status === "INPROGRESS";
  const canReschedule = b.status !== "CANCELLED";

  const emailLabel =
    emailStatus === "sending"
      ? "Sending…"
      : emailStatus === "sent"
        ? "✓ Sent!"
        : emailStatus
          ? "⚠ Failed"
          : "Email Receipt";

  return (
    <div
      className={`booking-card card${b.status === "CANCELLED" ? " booking-card-cancelled" : ""}`}
    >
      <div className="booking-card-header">
        <div>
          {b.hotel_id ? (
            <a
              href={`/hotel/${b.hotel_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="booking-hotel-name"
            >
              {b.hotel_name ?? "Unknown hotel"}
            </a>
          ) : (
            <span className="booking-hotel-name">
              {b.hotel_name ?? "Unknown hotel"}
            </span>
          )}
          {b.hotel_city && <span className="booking-city">{b.hotel_city}</span>}
        </div>
        <span className={`badge ${STATUS_BADGE[b.status]}`}>
          {STATUS_LABEL[b.status]}
        </span>
      </div>

      <div className="booking-details-grid">
        {[
          ["Trip", b.title],
          ["Check-in", b.start_date],
          ["Check-out", b.end_date],
          ["Nights", String(n)],
          [
            "Room",
            b.room_type
              ? b.room_type.charAt(0) + b.room_type.slice(1).toLowerCase()
              : "—",
          ],
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
          {canReschedule &&
            (b.hotel_id ? (
              <Link
                className="btn btn-secondary booking-reschedule-btn"
                to={`/booking/${b.hotel_id}?rescheduleBookingId=${b.id}`}
              >
                Reschedule
              </Link>
            ) : (
              <button
                className="btn btn-secondary booking-reschedule-btn"
                disabled
              >
                Reschedule
              </button>
            ))}
          <button
            className="btn btn-secondary booking-reschedule-btn booking-receipt-btn"
            onClick={() => onDownloadReceipt(b)}
            title="Download PDF receipt"
          >
            Download Receipt
          </button>
          <button
            className={`btn btn-secondary booking-reschedule-btn booking-receipt-btn${emailStatus === "sent" ? " btn-success" : emailStatus && emailStatus !== "sending" ? " btn-error" : ""}`}
            onClick={() => onEmailReceipt(b.id)}
            disabled={emailStatus === "sending" || emailStatus === "sent"}
            title="Email receipt to your account address"
          >
            {emailLabel}
          </button>
          {canCancel && (
            <button
              className="btn btn-secondary booking-cancel-btn"
              onClick={() => onCancel(b.id)}
              disabled={cancelling}
            >
              {cancelling ? "Cancelling…" : "Cancel"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
