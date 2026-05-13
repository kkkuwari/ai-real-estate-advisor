"use client";

import { useEffect, useState } from "react";

const BACKEND_URL = "http://127.0.0.1:8000";

export default function SavedAnalysesPage() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAnalyses() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${BACKEND_URL}/analyses`);
        if (!response.ok) {
          throw new Error("Could not load analyses.");
        }
        const data = await response.json();
        setAnalyses(data);
      } catch (err) {
        setError(err.message || "Failed to fetch analyses.");
      } finally {
        setLoading(false);
      }
    }

    loadAnalyses();
  }, []);

  const chronologicalAnalyses = [...analyses].reverse();
  const trendPoints = chronologicalAnalyses.map((item, index) => {
    const x = chronologicalAnalyses.length > 1
      ? (index / (chronologicalAnalyses.length - 1)) * 100
      : 50;
    const y = Math.max(0, Math.min(100, 100 - (item.predicted_yield / 10) * 100));
    return { x, y, value: item.predicted_yield };
  });
  const trendPolyline = trendPoints.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <>
      <section className="card">
        <h2 className="section-title">Saved Investment Analyses</h2>
        <p className="section-subtitle">
          Stored model outputs from previous property evaluations.
        </p>

        {loading && <div className="loading-state">Loading saved analyses...</div>}
        {error && <div className="alert">Could not load saved analyses. Please refresh and try again.</div>}

        {!loading && !error && analyses.length > 0 && (
          <div className="summary-grid summary-grid-dashboard" style={{ marginTop: 12 }}>
            <article className="summary-card">
              <h3>Total Analyses</h3>
              <p>{analyses.length}</p>
            </article>
            <article className="summary-card">
              <h3>Avg Predicted Yield</h3>
              <p>
                {(
                  analyses.reduce((sum, item) => sum + item.predicted_yield, 0) / analyses.length
                ).toFixed(2)}
                %
              </p>
            </article>
            <article className="summary-card">
              <h3>Strong Buy Count</h3>
              <p>{analyses.filter((item) => item.recommendation === "Strong Buy").length}</p>
            </article>
            <article className="summary-card">
              <h3>Last Updated</h3>
              <p>{new Date(analyses[0].created_at).toLocaleDateString()}</p>
            </article>
          </div>
        )}

        {!loading && !error && analyses.length > 1 && (
          <section className="chart-card" style={{ marginTop: 12 }}>
            <h4>Predicted Yield Trend</h4>
            <p className="muted">Oldest to newest saved analysis</p>
            <div className="trend-chart-wrap">
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="trend-chart">
                <polyline points={trendPolyline} className="trend-line" />
                {trendPoints.map((point, idx) => (
                  <circle key={`trend-${idx}`} cx={point.x} cy={point.y} r="1.6" className="trend-dot" />
                ))}
              </svg>
            </div>
          </section>
        )}
      </section>

      <section className="card">
        {!loading && !error && analyses.length === 0 && (
          <div className="empty-state">
            <h3>No saved analyses yet</h3>
            <p className="muted">
              Run an analysis on the Analyse page, then use Save Analysis to store it here.
            </p>
          </div>
        )}

        {!loading && !error && analyses.length > 0 && (
          <>
            <div className="table-header">
              <h3>History</h3>
              <p className="muted">Recent saved outputs from the analysis workflow.</p>
            </div>
            <div className="table-wrap table-wrap-dashboard">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Postcode</th>
                    <th>Region</th>
                    <th>Type</th>
                    <th>Bedrooms</th>
                    <th>Predicted Yield (%)</th>
                    <th>Investment Score</th>
                    <th>Recommendation</th>
                    <th>Created At</th>
                  </tr>
                </thead>
                <tbody>
                  {analyses.map((item) => (
                    <tr key={item.id}>
                      <td>{item.id}</td>
                      <td>{item.postcode}</td>
                      <td>{item.region}</td>
                      <td>{item.property_type}</td>
                      <td>{item.bedrooms}</td>
                      <td>{item.predicted_yield}</td>
                      <td>{item.investment_score}</td>
                      <td>
                        <span
                          className={`badge ${
                            item.recommendation === "Strong Buy"
                              ? "badge-strong"
                              : item.recommendation === "Moderate"
                                ? "badge-moderate"
                                : "badge-weak"
                          }`}
                        >
                          {item.recommendation}
                        </span>
                      </td>
                      <td>{new Date(item.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>
    </>
  );
}
