import { useState, useEffect } from "react";
import "./RewardsPage.css";

// mock data for now, will hook up to backend later
const MOCK_BALANCE = 4820;
const POINTS_TO_DOLLAR = 100;

export default function RewardsPage() {
  const [loading, setLoading] = useState(true);
  const [count, setCount] = useState(0);
  const balance = MOCK_BALANCE;

  useEffect(() => {
    setTimeout(() => setLoading(false), 400);
  }, []);

  // count up animation for the balance number
  useEffect(() => {
    if (loading) return;
    let cur = 0;
    const inc = balance / 35;
    const timer = setInterval(() => {
      cur += inc;
      if (cur >= balance) { setCount(balance); clearInterval(timer); }
      else setCount(Math.floor(cur));
    }, 30);
    return () => clearInterval(timer);
  }, [loading, balance]);

  const dollarValue = balance / POINTS_TO_DOLLAR;

  if (loading) {
    return (
      <div className="rewards-container">
        <div className="balance-card loading">
          <div className="shimmer" />
        </div>
      </div>
    );
  }

  return (
    <div className="rewards-container">
      <div className="balance-card">
        <p className="balance-label">Rewards Balance</p>
        <div className="balance-row">
          <span className="balance-number">{count.toLocaleString()}</span>
          <span className="balance-points">points</span>
        </div>
        <p className="balance-info">
          <span style={{ color: "#667eea", fontWeight: 600 }}>${dollarValue.toFixed(2)}</span> value
        </p>
      </div>
    </div>
  );
}
