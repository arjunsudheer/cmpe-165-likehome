import "./BookingConflictWarning.css";

export interface BookingInfo {
  hotelName: string;
  checkIn: string;
  checkOut: string;
}

interface Props {
  newBooking: BookingInfo;
  existingBooking: BookingInfo;
  onGoBack: () => void;
  onBookAnyway: () => void;
}

export default function BookingConflictWarning({
  newBooking,
  existingBooking,
  onGoBack,
  onBookAnyway,
}: Props) {
  return (
    <div className="conflict-overlay" onClick={onGoBack}>
      <div className="conflict-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="conflict-icon">⚠️</div>

        <h2 className="conflict-title">Scheduling Conflict</h2>
        <p className="conflict-sub">
          These bookings overlap. This and other overlapping bookings will become nonrefundable and no rewards will be earned on this purchase.
        </p>

        <div className="conflict-bookings">
          <div className="conflict-booking conflict-booking--new">
            <span className="conflict-tag conflict-tag--new">New booking</span>
            <p className="conflict-hotel">{newBooking.hotelName}</p>
            <p className="conflict-dates">{newBooking.checkIn} — {newBooking.checkOut}</p>
          </div>

          <div className="conflict-vs">vs</div>

          <div className="conflict-booking conflict-booking--existing">
            <span className="conflict-tag conflict-tag--existing">Existing booking</span>
            <p className="conflict-hotel">{existingBooking.hotelName}</p>
            <p className="conflict-dates">{existingBooking.checkIn} — {existingBooking.checkOut}</p>
          </div>
        </div>

        <div className="conflict-actions">
          <button className="btn btn-secondary" onClick={onGoBack}>
            Change dates
          </button>
          <button className="btn btn-danger" onClick={onBookAnyway}>
            Book anyway
          </button>
        </div>
      </div>
    </div>
  );
}
