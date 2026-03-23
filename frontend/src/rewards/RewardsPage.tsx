import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./RewardsPage.css";

interface Tx { id: number; booking_id: number | null; points: number; recorded_at: string | null; }

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
        if (!r.ok) throw new Error(`Balance fetch failed: ${r.status} ${r.statusText}`);
        return r.json();
      }),
      fetch("/rewards/history", { headers: h }).then((r) => {
        if (!r.ok) throw new Error(`History fetch failed: ${r.status} ${r.statusText}`);
        return r.json();
      }),
    ])
      .then(([bal, hist]) => {
        setBalance(bal.total_points ?? 0);
        setDollarValue(bal.dollar_value ?? 0);
        setHistory(Array.isArray(hist) ? hist : []);
      })
      .catch((err) => {
        console.error("Rewards data fetch error:", err);
        setError(err instanceof Error ? err.message : "Failed to load rewards data.");
      })
      .finally(() => setLoading(false));
  }, [auth.isAuthenticated, navigate]);

  // Animated count-up on load
  useEffect(() => {
    if (loading || balance === 0) { setDisplayCount(balance); return; }
    let cur = 0;
    const inc = balance / 40;
    const t = setInterval(() => {
      cur += inc;
      if (cur >= balance) { setDisplayCount(balance); clearInterval(t); }
      else setDisplayCount(Math.floor(cur));
    }, 24);
    return () => clearInterval(t);
  }, [loading, balance]);

  return (
    <div className="rewards-page">
      <div className="rewards-container">
        <h1 className="rewards-page-title">Rewards Points</h1>

        {error && (
          <div className="alert alert-error">
            {error}
            {error.includes("status") && (
              <div className="error-details" style={{ fontSize: "0.85em", marginTop: "0.5em", opacity: 0.9 }}>
                Check browser console and backend logs for details.
              </div>
            )}
          </div>
        )}

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

        {/* Points history */}
        <div className="rewards-history card">
          <h2 className="history-title">Points History</h2>
          {loading ? (
            <div className="history-loading">Loading transactions…</div>
          ) : history.length === 0 ? (
            <p className="history-empty">No transactions yet. Book a stay to start earning!</p>
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
                    <td>{tx.recorded_at ? new Date(tx.recorded_at).toLocaleDateString() : "—"}</td>
                    <td>{tx.booking_id ? `#${tx.booking_id}` : "—"}</td>
                    <td className={tx.points >= 0 ? "pts-earn" : "pts-spend"}>
                      {tx.points >= 0 ? "+" : ""}{tx.points.toLocaleString()}
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
