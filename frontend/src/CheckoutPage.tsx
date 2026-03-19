import { useState, useEffect } from "react";
import "./CheckoutPage.css";

// mock data - replace with api call later
const MOCK_BALANCE = 420;
const POINTS_TO_DOLLAR = 100;
const MOCK_BOOKING_TOTAL = 289.0;

export default function CheckoutPage() {
  const [balance, setBalance] = useState(0);
  const [pointsToRedeem, setPointsToRedeem] = useState(0);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setBalance(MOCK_BALANCE);
      setLoading(false);
    }, 400);
  }, []);

  const maxPoints = Math.min(balance, Math.floor(MOCK_BOOKING_TOTAL * POINTS_TO_DOLLAR));
  const discount = pointsToRedeem / POINTS_TO_DOLLAR;
  const pct = maxPoints > 0 ? (pointsToRedeem / maxPoints) * 100 : 0;

  const handleSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Math.min(parseInt(e.target.value, 10), maxPoints);
    setPointsToRedeem(val);
    setInputValue(val > 0 ? val.toString() : "");
  };

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/[^0-9]/g, "");
    setInputValue(raw);

    if (raw === "") {
      setPointsToRedeem(0);
      return;
    }

    const val = Math.min(parseInt(raw, 10), maxPoints);
    setPointsToRedeem(val);
  };

  // when they click out of the input, snap to valid value
  const handleBlur = () => {
    if (inputValue === "") {
      setPointsToRedeem(0);
      return;
    }
    const val = Math.min(parseInt(inputValue, 10) || 0, maxPoints);
    setPointsToRedeem(val);
    setInputValue(val > 0 ? val.toString() : "");
  };

  if (loading || balance <= 0) return null;

  return (
    <div className="checkout-container">
      <div className="rewards-card">
        <div className="rewards-header">
          <p className="rewards-title">Use Rewards</p>
          <p style={{ fontSize: 13, color: "#6b7280", margin: 0 }}>
            <span style={{ fontWeight: 600, color: "#111827" }}>{balance.toLocaleString()}</span> pts available
          </p>
        </div>
        <input
          type="range"
          className="slider"
          min={0}
          max={maxPoints}
          step={10}
          value={pointsToRedeem}
          onChange={handleSlider}
          style={{
            background: `linear-gradient(to right, #667eea 0%, #667eea ${pct}%, #edf0f3 ${pct}%, #edf0f3 100%)`,
          }}
        />
        <div className="slider-labels">
          <span>0</span>
          {pointsToRedeem > 0 && (
            <span style={{ color: "#667eea", fontWeight: 600, fontSize: 13 }}>
              {pointsToRedeem.toLocaleString()} pts → -${discount.toFixed(2)}
            </span>
          )}
          <span>{maxPoints.toLocaleString()}</span>
        </div>

        {/* text input so user can type exact amount */}
        <div className="points-input-row">
          <label className="points-input-label">Or enter points:</label>
          <input
            type="text"
            className="points-input"
            placeholder="0"
            value={inputValue}
            onChange={handleInput}
            onBlur={handleBlur}
          />
        </div>
      </div>
    </div>
  );
}
