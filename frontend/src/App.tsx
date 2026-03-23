import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./shared/Navbar";
import Footer from "./shared/Footer";
import HomePage from "./home/HomePage";
import Login from "./auth/Login";
import Register from "./auth/Register";
import HotelDetailsPage from "./hotel/HotelDetailsPage";
import Booking from "./reservation/Booking";
import CheckoutPage from "./payment/CheckoutPage";
import RewardsPage from "./rewards/RewardsPage";
import MyBookingsPage from "./mybooking/MyBookingsPage";
import "./index.css";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <main className="page-body">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/hotel/:id" element={<HotelDetailsPage />} />
            <Route path="/booking/:hotelId" element={<Booking />} />
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/rewards" element={<RewardsPage />} />
            <Route path="/my-bookings" element={<MyBookingsPage />} />
          </Routes>
        </main>
        <Footer />
      </BrowserRouter>
    </AuthProvider>
  );
}
