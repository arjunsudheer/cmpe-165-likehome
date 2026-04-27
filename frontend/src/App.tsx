import { BrowserRouter, Route, Routes } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./shared/Navbar";
import Footer from "./shared/Footer";
import HomePage from "./home/HomePage";
import Login from "./auth/Login";
import Register from "./auth/Register";
import GoogleLoginPage from "./auth/GoogleLoginPage";
import ForgotPassword from "./auth/ForgotPassword";
import ResetPasswordSent from "./auth/ResetPasswordSent";
import ResetPassword from "./auth/ResetPassword";
import HotelDetailsPage from "./hotel/HotelDetailsPage";
import Booking from "./reservation/Booking";
import CheckoutPage from "./payment/CheckoutPage";
import RewardsPage from "./rewards/RewardsPage";
import MyBookingsPage from "./mybooking/MyBookingsPage";
import SettingsPage from "./settings/SettingsPage";
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
              {/* Dedicated page for teammates and users who want a direct Google sign-in entry point. */}
              <Route path="/google-login" element={<GoogleLoginPage />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/forgot-password/sent" element={<ResetPasswordSent />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/hotel/:id" element={<HotelDetailsPage />} />
              <Route path="/booking/:hotelId" element={<Booking />} />
              <Route path="/checkout" element={<CheckoutPage />} />
              <Route path="/rewards" element={<RewardsPage />} />
              <Route path="/my-bookings" element={<MyBookingsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
          <Footer />
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}
