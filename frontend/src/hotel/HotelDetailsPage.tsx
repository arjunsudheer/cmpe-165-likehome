import React from "react";
import HotelDetails from "./HotelDetails";
import type { Hotel } from "./HotelDetails";

const exampleHotel: Hotel = {
  name: "Seaside Resort",
  location: "Miami Beach, FL",
  rating: 4.5,
  description:
    "A luxurious resort right on the beach, with world-class amenities and stunning ocean views.",
  photos: [
    "https://images.unsplash.com/photo-1566073771259-6a8506099945",
    "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa",
    "https://images.unsplash.com/photo-1582719508461-905c673771fd",
    "https://images.unsplash.com/photo-1590490360182-c33d57733427",
    "https://images.unsplash.com/photo-1571896349842-33c89424de2d",
    "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb"
  ],
};

const HotelDetailsPage: React.FC = () => {
  return <HotelDetails hotel={exampleHotel} />;
};

export default HotelDetailsPage;