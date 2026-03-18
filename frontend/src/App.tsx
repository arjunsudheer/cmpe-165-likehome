import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Register from "./Register";
import Booking from "./Booking";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Register />} />
        <Route path="/booking" element={<Booking />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}