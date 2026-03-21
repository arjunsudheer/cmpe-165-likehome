import { BrowserRouter, Routes, Route } from "react-router-dom";
import Register from "./Register";
import RewardsPage from "./RewardsPage";
import CheckoutPage from "./CheckoutPage";
import BookingConflictPage from "./BookingConflictWarning";
import HotelDetailsPage from "./HotelDetailsPage";

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