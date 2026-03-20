import { useState } from "react";
import "./BookingConflictWarning.css";

interface BookingInfo {
  hotelName: string;
  checkIn: string;
  checkOut: string;
}

interface BookingConflictWarningProps {
  newBooking: BookingInfo;
  existingBooking: BookingInfo;
  onGoBack: () => void;
  onBookAnyway: () => void;
}

// mock data - will come from backend conflict check later
const MOCK_NEW_BOOKING = {
  hotelName: "Celadon City Inn",
  checkIn: "Mar 22, 2026",
  checkOut: "Mar 25, 2026",
};

const MOCK_CONFLICT = {
  hotelName: "Goldenrod Grand Hotel",
  checkIn: "Mar 23, 2026",
  checkOut: "Mar 26, 2026",
};

function BookingConflictWarning({ newBooking, existingBooking, onGoBack, onBookAnyway }: BookingConflictWarningProps) {
  return (
    <div className="conflict-overlay" onClick={onGoBack}>
      <div className="conflict-dialog" onClick={(e) => e.stopPropagation()}>

        <div className="conflict-header">
          <h2>Scheduling Conflict</h2>
          <p>These bookings have overlapping dates. You can only stay at one hotel at a time.</p>
        </div>

        <div className="conflict-bookings">
          <div className="conflict-booking">
            <span className="conflict-tag conflict-tag--new">New</span>
            <p className="conflict-hotel">{newBooking.hotelName}</p>
            <p className="conflict-dates">{newBooking.checkIn} — {newBooking.checkOut}</p>
          </div>

          <div className="conflict-vs">vs</div>

          <div className="conflict-booking conflict-booking--existing">
            <span className="conflict-tag conflict-tag--existing">Existing</span>
            <p className="conflict-hotel">{existingBooking.hotelName}</p>
            <p className="conflict-dates">{existingBooking.checkIn} — {existingBooking.checkOut}</p>
          </div>
        </div>

        <div className="conflict-actions">
          <button className="conflict-btn conflict-btn--secondary" onClick={onGoBack}>
            Change dates
          </button>
          <button className="conflict-btn conflict-btn--danger" onClick={onBookAnyway}>
            Book anyway
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BookingConflictPage() {
  const [showWarning, setShowWarning] = useState(true);

  return (
    <div className="conflict-page">
      {!showWarning && (
        <button className="conflict-trigger" onClick={() => setShowWarning(true)}>
          Show conflict warning
        </button>
      )}

      {showWarning && (
        <BookingConflictWarning
          newBooking={MOCK_NEW_BOOKING}
          existingBooking={MOCK_CONFLICT}
          onGoBack={() => setShowWarning(false)}
          onBookAnyway={() => setShowWarning(false)}
        />
      )}
    </div>
  );
}
