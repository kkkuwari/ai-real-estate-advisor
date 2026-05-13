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

  return (
    <>
      <section className="card">
        <h2>Saved Investment Analyses</h2>
        <p className="muted">
          Stored model outputs from previous property evaluations.
        </p>

        {loading && <p className="muted">Loading analyses...</p>}
        {error && <div className="alert">{error}</div>}

        {!loading && !error && analyses.length > 0 && (
          <div className="summary-grid" style={{ marginTop: 12 }}>
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
          </div>
        )}
      </section>

      <section className="card">
        {!loading && !error && analyses.length === 0 && (
          <div className="empty-state">
            <h3>No analyses saved yet</h3>
            <p className="muted">
              Run a property prediction on the Analyse page and save it to build your dashboard history.
            </p>
          </div>
        )}

        {!loading && !error && analyses.length > 0 && (
          <div className="table-wrap">
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
        )}
      </section>
    </>
  );
}
