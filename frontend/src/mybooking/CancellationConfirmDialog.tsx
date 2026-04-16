import { useId, useState } from "react";

export interface CancellationPreview {
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

function formatUsd(amountStr: string) {
  const n = Number(amountStr);
  if (Number.isNaN(n)) return "—";
  return `$${n.toFixed(2)}`;
}

export interface CancellationConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  preview: CancellationPreview | null;
  loading: boolean;
  loadError: string;
  /** When set, preview may still be shown but cancellation is not allowed (e.g. past policy window). */
  policyBlockedMessage: string | null;
  hotelName: string | null;
  tripTitle: string | null;
  onConfirm: () => void;
  confirming: boolean;
}

export default function CancellationConfirmDialog({
  open,
  onClose,
  preview,
  loading,
  loadError,
  policyBlockedMessage,
  hotelName,
  tripTitle,
  onConfirm,
  confirming,
}: CancellationConfirmDialogProps) {
  const [feeAcknowledged, setFeeAcknowledged] = useState(false);
  const ackId = useId();

  if (!open) return null;

  const blocked = !!policyBlockedMessage;
  const canConfirm =
    !loading &&
    !loadError &&
    !!preview &&
    !blocked &&
    feeAcknowledged;

  const fee = preview ? formatUsd(preview.fee_amount) : "—";
  const refund = preview ? formatUsd(preview.refund_amount) : "—";
  const feeNum = preview ? Number(preview.fee_amount) : 0;

  return (
    <div
      className="cancel-overlay"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="cancel-dialog card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cancel-dialog-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="cancel-icon" aria-hidden>⚠️</div>
        <h2 id="cancel-dialog-title" className="cancel-title">
          {blocked ? "Cannot cancel this booking" : "Cancel this booking?"}
        </h2>

        {(hotelName || tripTitle) && (
          <p className="cancel-booking-context">
            {hotelName && <span className="cancel-context-hotel">{hotelName}</span>}
            {tripTitle && <span className="cancel-context-trip">{tripTitle}</span>}
          </p>
        )}

        {!blocked && (
          <p className="cancel-sub">
            Review the fee and refund below. This action cannot be undone.
          </p>
        )}

        {loading && (
          <p className="cancel-loading">Loading cancellation details…</p>
        )}

        {!loading && loadError && (
          <div className="alert alert-error cancel-dialog-alert">{loadError}</div>
        )}

        {!loading && !loadError && preview && (
          <>
            {blocked && policyBlockedMessage && (
              <div className="alert alert-error cancel-dialog-alert">{policyBlockedMessage}</div>
            )}

            <div className="cancel-fee-highlight">
              <span className="cancel-fee-label">Cancellation fee</span>
              <span className="cancel-fee-value">{fee}</span>
              <span className="cancel-fee-note">
                {feeNum <= 0
                  ? "No fee for this cancellation."
                  : "This amount is kept per our cancellation policy."}
              </span>
            </div>

            <div className="booking-details-grid cancel-detail-grid">
              {[
                ["Check-in", preview.check_in_date],
                [
                  `Cancel by (${preview.policy_hours}h policy)`,
                  new Date(preview.cutoff_at).toLocaleString(undefined, {
                    dateStyle: "medium",
                    timeStyle: "short",
                  }),
                ],
                ["Refund to your card", refund],
                ["Rewards points restored", preview.points_to_restore.toLocaleString()],
                ["Booking reference", preview.booking_number],
              ].map(([k, v]) => (
                <div key={k} className="booking-detail">
                  <span className="detail-label">{k}</span>
                  <span className="detail-value">{v}</span>
                </div>
              ))}
            </div>

            {!blocked && (
              <label className="cancel-ack" htmlFor={ackId}>
                <input
                  id={ackId}
                  type="checkbox"
                  className="cancel-ack-input"
                  checked={feeAcknowledged}
                  onChange={(e) => setFeeAcknowledged(e.target.checked)}
                />
                <span>
                  I understand the <strong>{fee}</strong> cancellation fee and that I will receive
                  a <strong>{refund}</strong> refund
                  {preview.points_to_restore > 0
                    ? `, plus ${preview.points_to_restore.toLocaleString()} rewards points restored`
                    : ""}
                  .
                </span>
              </label>
            )}
          </>
        )}

        <div className="cancel-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
            disabled={confirming}
          >
            {blocked ? "Close" : "Go back"}
          </button>
          {!blocked && (
            <button
              type="button"
              className="btn btn-danger"
              onClick={onConfirm}
              disabled={!canConfirm || confirming}
            >
              {confirming ? "Cancelling…" : "Confirm cancellation"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
