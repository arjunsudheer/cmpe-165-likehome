import { BrowserRouter, Routes, Route } from "react-router-dom";
import Register from "./Register";
import BookingConflictPage from "./BookingConflictWarning";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Register />} />
        <Route path="/conflict" element={<BookingConflictPage />} />
      </Routes>
    </BrowserRouter>
  );
}