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
  const [validationError, setValidationError] = useState("");

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
    setValidationError("");
    setLoading(true);
    setError("");
    setSaveMessage("");
    setPrediction(null);

    if (!formData.postcode.trim()) {
      setLoading(false);
      setValidationError("Please enter a valid UK postcode.");
      return;
    }
    if (formData.bedrooms < 1 || formData.bedrooms > 10) {
      setLoading(false);
      setValidationError("Bedrooms must be between 1 and 10.");
      return;
    }
    if (formData.purchase_price <= 0 || formData.monthly_rent <= 0) {
      setLoading(false);
      setValidationError("Price and rent must be positive values.");
      return;
    }

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
      setError("Prediction failed. Please check your values and try again.");
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
      setError("Could not save analysis. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="dashboard-grid">
        <section className="card">
          <div className="no-print">
          <h2 className="section-title">Analyse Property</h2>
          <p className="section-subtitle">
            Enter core property details and use postcode enrichment to generate an investment signal.
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
          {validationError && <p className="field-error">{validationError}</p>}
          {error && <div className="alert">{error}</div>}
          {saveMessage && <div className="success-note">{saveMessage}</div>}
          </div>
        </section>

        <section className="card">
          <h3 className="section-title">Prediction Dashboard</h3>
          <p className="section-subtitle">
            Outputs appear here after running the model prediction.
          </p>

          {loading && <div className="loading-state">Running prediction and enrichment...</div>}

          {!prediction && (
            <div className="empty-state">
              <p className="muted">No prediction yet. Submit the form to view investment metrics.</p>
            </div>
          )}

          {prediction && (
            <>
              <div className="action-row no-print" style={{ marginTop: 0 }}>
                <button className="button-secondary" type="button" onClick={() => window.print()}>
                  Print Analysis
                </button>
              </div>

              <section className="summary-banner">
                <div>
                  <h4>Investment Summary</h4>
                  <p className="summary-banner-value">{prediction.recommendation}</p>
                  <small>{prediction.postcode} - {prediction.region}</small>
                </div>
                <div className="summary-badge-wrap">
                  <span
                    className={`badge ${
                      prediction.recommendation === "Strong Buy"
                        ? "badge-strong"
                        : prediction.recommendation === "Moderate"
                          ? "badge-moderate"
                          : "badge-weak"
                    }`}
                  >
                    Decision Signal
                  </span>
                </div>
              </section>

              <div className="result-metrics result-metrics-strong">
                <article className="metric-card metric-card-strong">
                  <h4>Predicted Yield</h4>
                  <p className="metric-value">{prediction.predicted_yield}%</p>
                </article>

                <article className="metric-card metric-card-strong">
                  <h4>Investment Score</h4>
                  <p className="metric-value">{prediction.investment_score}</p>
                </article>

                <article className="metric-card">
                  <h4>Mapped Region</h4>
                  <p className="metric-value" style={{ fontSize: "1.08rem" }}>
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

              <div className="mini-visual-grid">
                <article className="mini-visual-card">
                  <h4>Score Gauge</h4>
                  <div
                    className="score-gauge"
                    style={{
                      background: `conic-gradient(#19906d ${Math.max(0, Math.min(100, prediction.investment_score))}%, #dfe7f3 0)`,
                    }}
                  >
                    <div className="score-gauge-inner">
                      <strong>{Math.round(prediction.investment_score)}</strong>
                      <small>/100</small>
                    </div>
                  </div>
                </article>

                <article className="mini-visual-card">
                  <h4>Yield Position</h4>
                  <div className="compare-bar-row">
                    <span>Model Yield</span>
                    <span>{prediction.predicted_yield}%</span>
                  </div>
                  <div className="progress-track">
                    <div
                      className="progress-fill progress-fill-yield"
                      style={{ width: `${Math.max(0, Math.min(100, (prediction.predicted_yield / 10) * 100))}%` }}
                    />
                  </div>
                  <div className="compare-bar-row" style={{ marginTop: 8 }}>
                    <span>Benchmark</span>
                    <span>5.0%</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: "50%" }} />
                  </div>
                </article>
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
              <p className="helper-note">
                Recommendations are prototype decision-support outputs. Some neighbourhood values
                may use fallback estimates when external APIs are unavailable.
              </p>
            </>
          )}
        </section>
      </div>

      {prediction && (
        <section className="print-only print-report">
          <h2>AI Real Estate Investment Advisor - Analysis Summary</h2>

          <h3>Property Input</h3>
          <p><strong>Postcode:</strong> {formData.postcode}</p>
          <p><strong>Property Type:</strong> {formData.property_type}</p>
          <p><strong>Bedrooms:</strong> {formData.bedrooms}</p>
          <p><strong>Purchase Price:</strong> GBP {formData.purchase_price}</p>
          <p><strong>Monthly Rent:</strong> GBP {formData.monthly_rent}</p>

          <h3>Prediction Output</h3>
          <p><strong>Predicted Yield:</strong> {prediction.predicted_yield}%</p>
          <p><strong>Investment Score:</strong> {prediction.investment_score}</p>
          <p><strong>Recommendation:</strong> {prediction.recommendation}</p>
          <p><strong>Mapped Region:</strong> {prediction.region}</p>

          <h3>Neighbourhood Metrics</h3>
          <p><strong>Crime Rate:</strong> {prediction.crime_rate}</p>
          <p><strong>Amenity Score:</strong> {prediction.amenity_score}</p>
          <p><strong>HPI Growth:</strong> {prediction.hpi_growth}%</p>
          <p><strong>Distance to Station:</strong> {prediction.distance_to_station} km</p>
          <p><strong>Data Sources:</strong> {(prediction.data_sources_used || []).join(", ")}</p>

          <p className="print-disclaimer">
            Disclaimer: this is a prototype decision-support output for academic use and not
            financial advice.
          </p>
        </section>
      )}
    </>
  );
}
