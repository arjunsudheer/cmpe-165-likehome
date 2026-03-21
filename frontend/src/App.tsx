import { BrowserRouter, Routes, Route } from "react-router-dom";
import Register from "./auth/Register";
import RewardsPage from "./rewards/RewardsPage";
import CheckoutPage from "./payment/CheckoutPage";
import BookingConflictPage from "./mybooking/BookingConflictWarning";
import HotelDetailsPage from "./hotel/HotelDetailsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Register />} />
        <Route path="/rewards" element={<RewardsPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/conflict" element={<BookingConflictPage />} />
        <Route path="/hotel" element={<HotelDetailsPage />} />
      </Routes>
    </BrowserRouter>
  );
}