import React, { useState } from "react";
import type { Hotel } from "../types/Hotel";

interface Props {
  hotels: Hotel[];
  onFilter: (filteredHotels: Hotel[]) => void;
}

const allAmenities = [
  "wifi",
  "pool",
  "parking",
  "gym",
  "spa",
  "restaurant",
  "pet-friendly",
];

const HotelFilter: React.FC<Props> = ({ hotels, onFilter }) => {
  const [maxPrice, setMaxPrice] = useState<number>(500);
  const [minRating, setMinRating] = useState<number>(0);
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);

  const toggleAmenity = (amenity: string) => {
    setSelectedAmenities((prev) =>
      prev.includes(amenity)
        ? prev.filter((a) => a !== amenity)
        : [...prev, amenity]
    );
  };

  const applyFilters = () => {
    const filtered = hotels.filter((hotel) => {
      const priceMatch = hotel.pricePerNight <= maxPrice;
      const ratingMatch = hotel.rating >= minRating;

      const amenitiesMatch =
        selectedAmenities.length === 0 ||
        selectedAmenities.every((a) => hotel.amenities.includes(a));

      return priceMatch && ratingMatch && amenitiesMatch;
    });

    onFilter(filtered);
  };

  return (
    <div className="filter-container">
      <h3>Filter Hotels</h3>

      <div>
        <label>Max Price: ${maxPrice}</label>
        <input
          type="range"
          min="50"
          max="1000"
          step="10"
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
        />
      </div>

      <div>
        <label>Minimum Rating</label>
        <select
          value={minRating}
          onChange={(e) => setMinRating(Number(e.target.value))}
        >
          <option value={0}>All</option>
          <option value={3}>3+ Stars</option>
          <option value={4}>4+ Stars</option>
          <option value={5}>5 Stars</option>
        </select>
      </div>

      <div>
        <label>Amenities</label>
        {allAmenities.map((amenity) => (
          <div key={amenity}>
            <input
              type="checkbox"
              checked={selectedAmenities.includes(amenity)}
              onChange={() => toggleAmenity(amenity)}
            />
            <label>{amenity}</label>
          </div>
        ))}
      </div>

      <button onClick={applyFilters}>Apply Filters</button>
    </div>
  );
};

export default HotelFilter;