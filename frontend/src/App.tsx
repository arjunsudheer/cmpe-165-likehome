import { BrowserRouter, Route, Routes } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
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

// VITE_GOOGLE_CLIENT_ID is optional — Google button is hidden when absent
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

export default function App() {
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
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
    </GoogleOAuthProvider>
  );
}
