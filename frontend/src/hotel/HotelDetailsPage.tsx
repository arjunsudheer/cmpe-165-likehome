import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import HotelDetails from "./HotelDetails";
import type { Hotel } from "../types/Hotel";

type HotelDetailsResponse = {
  id: number;
  name: string;
  city: string;
  address: string;
  price_per_night: number;
  rating: number;
  review_count: number;
  amenities: string[];
  photos: Array<{
    url: string;
    alt_text: string;
  }>;
};

const HotelDetailsPage: React.FC = () => {
  const { hotelId } = useParams();
  const [hotel, setHotel] = useState<Hotel | null>(null);
  const [status, setStatus] = useState("Loading hotel...");

  useEffect(() => {
    if (!hotelId) {
      setStatus("Missing hotel id.");
      return;
    }

    let cancelled = false;

    async function loadHotel() {
      try {
        const res = await fetch(`/hotels/${hotelId}`);
        const data = (await res.json()) as HotelDetailsResponse | { error?: string };

        if (!res.ok) {
          if (!cancelled) {
            setHotel(null);
            setStatus(data && "error" in data ? data.error || "Failed to load hotel." : "Failed to load hotel.");
          }
          return;
        }

        const hotelData = data as HotelDetailsResponse;
        if (!cancelled) {
          setHotel({
            id: hotelData.id,
            name: hotelData.name,
            location: hotelData.city,
            address: hotelData.address,
            rating: hotelData.rating,
            description: `${hotelData.review_count} review${hotelData.review_count === 1 ? "" : "s"} for ${hotelData.name}.`,
            pricePerNight: hotelData.price_per_night,
            amenities: hotelData.amenities,
            photos: hotelData.photos.map((photo) => photo.url),
            reviewCount: hotelData.review_count,
          });
          setStatus("");
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : String(err);
          setHotel(null);
          setStatus(`Network error: ${message}`);
        }
      }
    }

    void loadHotel();
    return () => {
      cancelled = true;
    };
  }, [hotelId]);

  return (
    <div>
      {status && <p>{status}</p>}
      <HotelDetails hotel={hotel} />
    </div>
  );
};

export default HotelDetailsPage;
