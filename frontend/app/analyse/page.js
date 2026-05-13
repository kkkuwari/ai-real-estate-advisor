"use client";

import { useState } from "react";

const BACKEND_URL = "http://127.0.0.1:8000";

const initialForm = {
  postcode: "M1 4BT",
  property_type: "Flat",
  bedrooms: 2,
  purchase_price: 260000,
  monthly_rent: 1250,
};

export default function AnalysePage() {
  const [formData, setFormData] = useState(initialForm);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  function updateField(name, value) {
    const numericFields = [
      "bedrooms",
      "purchase_price",
      "monthly_rent",
    ];
    setFormData((prev) => ({
      ...prev,
      [name]: numericFields.includes(name) ? Number(value) : value,
    }));
  }

  async function handlePredict(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setSaveMessage("");
    setPrediction(null);

    try {
      const response = await fetch(`${BACKEND_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!response.ok) {
        throw new Error("Prediction request failed.");
      }
      const result = await response.json();
      setPrediction(result);
    } catch (err) {
      setError(err.message || "Could not fetch prediction.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError("");
    setSaveMessage("");

    try {
      const response = await fetch(`${BACKEND_URL}/save-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!response.ok) {
        throw new Error("Save request failed.");
      }
      const saved = await response.json();
      setSaveMessage(`Saved analysis #${saved.id} successfully.`);
    } catch (err) {
      setError(err.message || "Could not save analysis.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="dashboard-grid">
        <section className="card">
          <h2>Analyse Property</h2>
          <p className="muted">
            Enter core property and neighbourhood indicators to generate an investment signal.
          </p>
          <form onSubmit={handlePredict}>
            <div className="input-grid">
              <div className="field">
                <label>Postcode</label>
                <small>Enter a UK postcode (for example M1 4BT).</small>
                <input
                  type="text"
                  value={formData.postcode}
                  onChange={(e) => updateField("postcode", e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label>Property Type</label>
                <small>Dwelling category used by the trained model.</small>
                <select
                  value={formData.property_type}
                  onChange={(e) => updateField("property_type", e.target.value)}
                  required
                >
                  <option>Flat</option>
                  <option>Terraced</option>
                  <option>Semi-Detached</option>
                  <option>Detached</option>
                </select>
              </div>

              <div className="field">
                <label>Bedrooms</label>
                <small>Total number of bedrooms.</small>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.bedrooms}
                  onChange={(e) => updateField("bedrooms", e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label>Purchase Price (GBP)</label>
                <small>Estimated acquisition cost.</small>
                <input
                  type="number"
                  min="1"
                  value={formData.purchase_price}
                  onChange={(e) => updateField("purchase_price", e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label>Monthly Rent (GBP)</label>
                <small>Expected gross monthly rent.</small>
                <input
                  type="number"
                  min="1"
                  value={formData.monthly_rent}
                  onChange={(e) => updateField("monthly_rent", e.target.value)}
                  required
                />
              </div>

            </div>

            <div className="action-row">
              <button className="button-primary" type="submit" disabled={loading}>
                {loading ? "Predicting..." : "Run Prediction"}
              </button>
              {prediction && (
                <button className="button-secondary" type="button" onClick={handleSave} disabled={saving}>
                  {saving ? "Saving..." : "Save Analysis"}
                </button>
              )}
            </div>
          </form>
          {error && <div className="alert">{error}</div>}
          {saveMessage && <div className="success-note">{saveMessage}</div>}
        </section>

        <section className="card">
          <h3>Prediction Dashboard</h3>
          <p className="muted">
            Outputs appear here after running the model prediction.
          </p>

          {!prediction && (
            <div className="empty-state">
              <p className="muted">No prediction yet. Submit the form to view investment metrics.</p>
            </div>
          )}

          {prediction && (
            <>
              <div className="result-metrics">
                <article className="metric-card">
                  <h4>Predicted Yield</h4>
                  <p className="metric-value">{prediction.predicted_yield}%</p>
                </article>

                <article className="metric-card">
                  <h4>Investment Score</h4>
                  <p className="metric-value">{prediction.investment_score}</p>
                </article>

                <article className="metric-card">
                  <h4>Mapped Region</h4>
                  <p className="metric-value" style={{ fontSize: "1.1rem" }}>
                    {prediction.region}
                  </p>
                </article>
              </div>

              <div style={{ marginTop: 12 }}>
                <span
                  className={`badge ${
                    prediction.recommendation === "Strong Buy"
                      ? "badge-strong"
                      : prediction.recommendation === "Moderate"
                        ? "badge-moderate"
                        : "badge-weak"
                  }`}
                >
                  Recommendation: {prediction.recommendation}
                </span>
              </div>

              <div className="progress-wrap">
                <p className="progress-label">Investment score strength</p>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{ width: `${Math.max(0, Math.min(100, prediction.investment_score))}%` }}
                  />
                </div>
              </div>

              <div className="yield-comparison">
                <div className="yield-row">
                  <span>Yield comparison</span>
                  <span>Benchmark: 5.0%</span>
                </div>
                <div className="yield-bars">
                  <div className="yield-bar yield-bar-model">
                    <span style={{ width: `${Math.max(0, Math.min(100, (prediction.predicted_yield / 10) * 100))}%` }} />
                  </div>
                  <div className="yield-bar yield-bar-benchmark">
                    <span style={{ width: "50%" }} />
                  </div>
                </div>
              </div>

              <div className="yield-comparison" style={{ marginTop: 14 }}>
                <div className="yield-row">
                  <span>Neighbourhood data automatically enriched from postcode</span>
                  <span>{prediction.postcode}</span>
                </div>
                <div className="yield-bars" style={{ gap: 10, marginTop: 10 }}>
                  <div className="summary-grid">
                    <article className="summary-card">
                      <h3>Crime Rate</h3>
                      <p>{prediction.crime_rate}</p>
                    </article>
                    <article className="summary-card">
                      <h3>Amenity Score</h3>
                      <p>{prediction.amenity_score}</p>
                    </article>
                    <article className="summary-card">
                      <h3>HPI Growth</h3>
                      <p>{prediction.hpi_growth}%</p>
                    </article>
                    <article className="summary-card">
                      <h3>Distance To Station</h3>
                      <p>{prediction.distance_to_station} km</p>
                    </article>
                  </div>
                  <p className="muted">
                    Data sources used: {(prediction.data_sources_used || []).join(", ")}
                  </p>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </>
  );
}
