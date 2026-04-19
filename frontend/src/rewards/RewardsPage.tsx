import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./RewardsPage.css";

interface Tx {
  id: number;
  booking_id: number | null;
  points: number;
  recorded_at: string | null;
}

export default function RewardsPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [balance, setBalance] = useState(0);
  const [dollarValue, setDollarValue] = useState(0);
  const [history, setHistory] = useState<Tx[]>([]);
  const [displayCount, setDisplayCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!auth.isAuthenticated) { navigate("/login"); return; }

    const h = auth.authHeader();
    Promise.all([
      fetch("/rewards/balance", { headers: h }).then((r) => {
        if (!r.ok) throw new Error(`Balance fetch failed: ${r.status}`);
        return r.json();
      }),
      fetch("/rewards/history", { headers: h }).then((r) => {
        if (!r.ok) throw new Error(`History fetch failed: ${r.status}`);
        return r.json();
      }),
    ])
      .then(([bal, hist]) => {
        setBalance(bal.total_points ?? 0);
        setDollarValue(bal.dollar_value ?? 0);
        setHistory(Array.isArray(hist) ? hist : []);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load rewards data.");
      })
      .finally(() => setLoading(false));
  }, [auth, navigate]);

  // Count-up animation — setState is only ever called inside the interval
  // callback, never synchronously in the effect body, avoiding cascading renders.
  useEffect(() => {
    if (loading) return;

    // Always drive display through the timer so setState is never called
    // synchronously; for balance === 0 the interval fires once and stops.
    let cur = 0;
    const target = balance;
    const inc = target > 0 ? target / 40 : 0;

    const t = setInterval(() => {
      cur += inc;
      if (cur >= target || target === 0) {
        setDisplayCount(target);
        clearInterval(t);
      } else {
        setDisplayCount(Math.floor(cur));
      }
    }, 24);

    return () => clearInterval(t);
  }, [loading, balance]);

  return (
    <div className="rewards-page">
      <div className="rewards-container">
        <h1 className="rewards-page-title">Rewards Points</h1>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="rewards-balance-card card rewards-shimmer" />
        ) : !error ? (
          <div className="rewards-balance-card card">
            <p className="balance-label">Your Balance</p>
            <div className="balance-row">
              <span className="balance-number">{displayCount.toLocaleString()}</span>
              <span className="balance-unit">pts</span>
            </div>
            <p className="balance-value">
              Worth <strong>${Number(dollarValue).toFixed(2)}</strong>
              <span className="balance-rate"> · 100 pts = $1.00</span>
            </p>
          </div>
        ) : null}

        <div className="rewards-history card">
          <h2 className="history-title">Points History</h2>
          {loading ? (
            <div className="history-loading">Loading transactions…</div>
          ) : history.length === 0 ? (
            <p className="history-empty">
              No transactions yet. Book a stay to start earning!
            </p>
          ) : (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Booking</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {history.map((tx) => (
                  <tr key={tx.id}>
                    <td>
                      {tx.recorded_at
                        ? new Date(tx.recorded_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td>{tx.booking_id ? `#${tx.booking_id}` : "—"}</td>
                    <td className={tx.points >= 0 ? "pts-earn" : "pts-spend"}>
                      {tx.points >= 0 ? "+" : ""}
                      {tx.points.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
