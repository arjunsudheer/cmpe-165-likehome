import { useState, useEffect } from "react";
import { MOCK_BALANCE, POINTS_TO_DOLLAR } from "./constants";
import "./RewardsPage.css";

export default function RewardsPage() {
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching balance from backend (GET /api/users/:id/points)
    const timer = setTimeout(() => {
      setBalance(MOCK_BALANCE);
      setLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="rewards-container">
        <div className="rewards-card">
          <p className="rewards-loading">Loading rewards…</p>
        </div>
      </div>
    );
  }

  const dollarValue = balance / POINTS_TO_DOLLAR;

  return (
    <div className="rewards-container">
      <div className="rewards-card">
        <div className="rewards-header">
          <p className="rewards-title">Your Rewards</p>
        </div>

        {balance <= 0 ? (
          <p className="rewards-empty">No rewards points available</p>
        ) : (
          <div className="rewards-balance">
            <p className="balance-points">
              {balance.toLocaleString()}{" "}
              <span className="balance-label">points</span>
            </p>
            <p className="balance-dollars">
              &asymp; ${dollarValue.toFixed(2)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
