import { BrowserRouter, Routes, Route } from "react-router-dom";
import Register from "./Register";
import RewardsPage from "./RewardsPage";
import CheckoutPage from "./CheckoutPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Register />} />
        <Route path="/rewards" element={<RewardsPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
      </Routes>
    </BrowserRouter>
  );
}
