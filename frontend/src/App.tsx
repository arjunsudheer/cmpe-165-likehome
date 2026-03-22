import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./HomePage";
import Register from "./auth/Register";
import RewardsPage from "./rewards/RewardsPage";
import CheckoutPage from "./payment/CheckoutPage";
import BookingConflictPage from "./mybooking/BookingConflictWarning";
import HotelDetailsPage from "./hotel/HotelDetailsPage";
import Booking from "./Booking"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/register" element={<Register />} />
        <Route path="/rewards" element={<RewardsPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/conflict" element={<BookingConflictPage />} />
        <Route path="/hotel" element={<HotelDetailsPage />} />
        <Route path="/booking" element={<Booking />} />
      </Routes>
    </BrowserRouter>
  );
}