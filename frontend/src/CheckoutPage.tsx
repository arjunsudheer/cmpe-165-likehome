import { useState, useEffect } from "react";
import type { ChangeEvent } from "react";
import {
  MOCK_BALANCE,
  POINTS_TO_DOLLAR,
  MOCK_BOOKING_TOTAL,
} from "./constants";
import "./CheckoutPage.css";

export default function CheckoutPage() {
  const [balance, setBalance] = useState(0);
  const [pointsToRedeem, setPointsToRedeem] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setBalance(MOCK_BALANCE);
      setLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const maxPoints = Math.min(balance, MOCK_BOOKING_TOTAL * POINTS_TO_DOLLAR);
  const discount = pointsToRedeem / POINTS_TO_DOLLAR;
  const pct = maxPoints > 0 ? (pointsToRedeem / maxPoints) * 100 : 0;

  const handleSlider = (e: ChangeEvent<HTMLInputElement>) => {
    setPointsToRedeem(Number(e.target.value));
  };

  if (loading) {
    return (
      <div className="checkout-container">
        <div className="checkout-card">
          <p className="checkout-loading">Loading…</p>
        </div>
      </div>
    );
  }

  if (balance <= 0) {
    return (
      <div className="checkout-container">
        <div className="checkout-card">
          <div className="checkout-header">
            <p className="checkout-title">Use Rewards</p>
            <p className="checkout-empty">No rewards points available</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-container">
      <div className="checkout-card">
        <div className="checkout-header">
          <p className="checkout-title">Use Rewards</p>
          <p className="checkout-balance">
            {balance.toLocaleString()} pts (${(balance / POINTS_TO_DOLLAR).toFixed(2)})
          </p>
        </div>

        <div className="slider-section">
          <label htmlFor="points-slider" className="slider-label">
            Redeem points
          </label>
          <input
            id="points-slider"
            type="range"
            min={0}
            max={maxPoints}
            value={pointsToRedeem}
            onChange={handleSlider}
            className="points-slider"
          />
          <div className="slider-info">
            <span>{pointsToRedeem.toLocaleString()} pts</span>
            <span>{pct.toFixed(0)}%</span>
          </div>
        </div>

        <div className="checkout-summary">
          <div className="summary-row">
            <span>Booking total</span>
            <span>${MOCK_BOOKING_TOTAL.toFixed(2)}</span>
          </div>
          <div className="summary-row discount">
            <span>Points discount</span>
            <span>&minus;${discount.toFixed(2)}</span>
          </div>
          <div className="summary-row total">
            <span>You pay</span>
            <span>${(MOCK_BOOKING_TOTAL - discount).toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
