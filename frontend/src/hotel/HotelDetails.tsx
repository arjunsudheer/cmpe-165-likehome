import React from "react";
import "./HotelDetails.css";

export interface Hotel {
  name: string;
  location: string;
  rating: number;
  description: string;
  photos?: string[];
}

interface HotelDetailsProps {
  hotel: Hotel | null;
}

const HotelDetails: React.FC<HotelDetailsProps> = ({ hotel }) => {
  if (!hotel) return <p>No hotel selected.</p>;

  return (
    <div className="hotel-details">
      <h2 className="hotel-name">{hotel.name}</h2>
      <p className="hotel-location">{hotel.location}</p>
      <p className="hotel-rating">Rating: {hotel.rating} / 5</p>
      <p className="hotel-description">{hotel.description}</p>

      {hotel.photos && hotel.photos.length > 0 && (
        <div className="hotel-gallery">
          {hotel.photos.map((photo, idx) => (
            <img
              key={idx}
              src={photo}
              alt={`${hotel.name} photo ${idx + 1}`}
              className="hotel-photo"
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default HotelDetails;