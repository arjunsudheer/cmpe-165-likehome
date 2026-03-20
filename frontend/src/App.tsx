import { BrowserRouter, Routes, Route } from "react-router-dom";
import Register from "./auth/Register";
import RewardsPage from "./rewards/RewardsPage";
import CheckoutPage from "./payment/CheckoutPage";
import BookingConflictPage from "./mybooking/BookingConflictWarning";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Register />} />
        <Route path="/rewards" element={<RewardsPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/conflict" element={<BookingConflictPage />} />
      </Routes>
    </BrowserRouter>
  );
}