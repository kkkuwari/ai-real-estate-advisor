"use client";

import { useMemo, useState } from "react";

const BACKEND_URL = "http://127.0.0.1:8000";

const propertyTemplate = {
  postcode: "",
  property_type: "Flat",
  bedrooms: 2,
  purchase_price: 250000,
  monthly_rent: 1200,
};

const initialProperties = [
  { ...propertyTemplate, postcode: "M1 4BT" },
  { ...propertyTemplate, postcode: "E14 5AB", purchase_price: 420000, monthly_rent: 1900 },
];

export default function ComparePage() {
  const [properties, setProperties] = useState(initialProperties);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [validationError, setValidationError] = useState("");

  const propertyCount = properties.length;

  const canAddThird = propertyCount < 3;
  const canRemoveThird = propertyCount > 2;

  const comparisonSummary = useMemo(() => {
    if (!results.length) {
      return null;
    }
    const avgScore =
      results.reduce((sum, item) => sum + item.investment_score, 0) / results.length;
    const top = results[0];
    return { avgScore: avgScore.toFixed(2), top };
  }, [results]);

  function updateProperty(index, field, value) {
    const numericFields = ["bedrooms", "purchase_price", "monthly_rent"];
    setProperties((prev) =>
      prev.map((item, idx) =>
        idx === index
          ? {
              ...item,
              [field]: numericFields.includes(field) ? Number(value) : value,
            }
          : item
      )
    );
  }

  function addThirdProperty() {
    if (!canAddThird) {
      return;
    }
    setProperties((prev) => [
      ...prev,
      { ...propertyTemplate, postcode: "SW1A 1AA", purchase_price: 560000, monthly_rent: 2400 },
    ]);
  }

  function removeThirdProperty() {
    if (!canRemoveThird) {
      return;
    }
    setProperties((prev) => prev.slice(0, 2));
  }

  async function handleCompare(event) {
    event.preventDefault();
    setValidationError("");
    setLoading(true);
    setError("");
    setResults([]);

    const hasInvalid = properties.some(
      (item) =>
        !item.postcode.trim()
        || item.bedrooms < 1
        || item.bedrooms > 10
        || item.purchase_price <= 0
        || item.monthly_rent <= 0
    );
    if (hasInvalid) {
      setLoading(false);
      setValidationError("Please check all properties. Use valid postcode and positive numeric values.");
      return;
    }

    try {
      const responses = await Promise.all(
        properties.map(async (property, idx) => {
          const response = await fetch(`${BACKEND_URL}/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(property),
          });
          if (!response.ok) {
            throw new Error(`Prediction request failed for Property ${idx + 1}.`);
          }
          const prediction = await response.json();
          return {
            ...property,
            ...prediction,
          };
        })
      );

      const ranked = [...responses]
        .sort((a, b) => b.investment_score - a.investment_score)
        .map((item, idx) => ({ ...item, rank: idx + 1 }));
      setResults(ranked);
    } catch (err) {
      setError("Comparison failed. Please review inputs and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="card">
        <h2 className="section-title">Compare Properties</h2>
        <p className="section-subtitle">
          Compare 2 or 3 property scenarios and rank them by investment score.
        </p>

        <form onSubmit={handleCompare}>
          <div className="compare-grid">
            {properties.map((property, idx) => (
              <article className="compare-form-card" key={`property-${idx}`}>
                <h3>Property {idx + 1}</h3>
                <div className="field">
                  <label>Postcode</label>
                  <small>Example: M1 4BT</small>
                  <input
                    type="text"
                    value={property.postcode}
                    onChange={(e) => updateProperty(idx, "postcode", e.target.value)}
                    required
                  />
                </div>

                <div className="field">
                  <label>Property Type</label>
                  <small>Dwelling category.</small>
                  <select
                    value={property.property_type}
                    onChange={(e) => updateProperty(idx, "property_type", e.target.value)}
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
                  <small>Total bedrooms.</small>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={property.bedrooms}
                    onChange={(e) => updateProperty(idx, "bedrooms", e.target.value)}
                    required
                  />
                </div>

                <div className="field">
                  <label>Purchase Price (GBP)</label>
                  <small>Estimated acquisition cost.</small>
                  <input
                    type="number"
                    min="1"
                    value={property.purchase_price}
                    onChange={(e) => updateProperty(idx, "purchase_price", e.target.value)}
                    required
                  />
                </div>

                <div className="field">
                  <label>Monthly Rent (GBP)</label>
                  <small>Expected monthly rent.</small>
                  <input
                    type="number"
                    min="1"
                    value={property.monthly_rent}
                    onChange={(e) => updateProperty(idx, "monthly_rent", e.target.value)}
                    required
                  />
                </div>
              </article>
            ))}
          </div>

          <div className="action-row">
            <button className="button-primary" type="submit" disabled={loading}>
              {loading ? "Comparing..." : "Compare Scenarios"}
            </button>
            {canAddThird && (
              <button className="button-secondary" type="button" onClick={addThirdProperty}>
                Add 3rd Property
              </button>
            )}
            {canRemoveThird && (
              <button className="button-secondary" type="button" onClick={removeThirdProperty}>
                Use 2 Properties
              </button>
            )}
          </div>
        </form>

        {validationError && <p className="field-error">{validationError}</p>}
        {error && <div className="alert">{error}</div>}
        {loading && <div className="loading-state">Running predictions for selected properties...</div>}
      </section>

      {comparisonSummary && (
        <section className="summary-grid">
          <article className="summary-card">
            <h3>Compared Properties</h3>
            <p>{results.length}</p>
          </article>
          <article className="summary-card">
            <h3>Average Score</h3>
            <p>{comparisonSummary.avgScore}</p>
          </article>
          <article className="summary-card">
            <h3>Top Recommendation</h3>
            <p>{comparisonSummary.top.recommendation}</p>
          </article>
        </section>
      )}

      {results.length > 0 && (
        <section className="card">
          <h3 className="section-title">Ranked Results</h3>
          <p className="section-subtitle">
            Rankings are based on the current prototype investment score.
          </p>

          <div className="chart-duo">
            <article className="chart-card">
              <h4>Investment Score Comparison</h4>
              <div className="bar-chart-list">
                {results.map((item) => (
                  <div className="bar-chart-row" key={`score-${item.rank}-${item.postcode}`}>
                    <div className="bar-chart-label">
                      <span>#{item.rank}</span>
                      <small>{item.postcode}</small>
                    </div>
                    <div className="bar-chart-track">
                      <div
                        className="bar-chart-fill"
                        style={{ width: `${Math.max(0, Math.min(100, item.investment_score))}%` }}
                      />
                    </div>
                    <strong>{item.investment_score.toFixed(1)}</strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="chart-card">
              <h4>Predicted Yield Comparison</h4>
              <div className="bar-chart-list">
                {results.map((item) => (
                  <div className="bar-chart-row" key={`yield-${item.rank}-${item.postcode}`}>
                    <div className="bar-chart-label">
                      <span>#{item.rank}</span>
                      <small>{item.postcode}</small>
                    </div>
                    <div className="bar-chart-track">
                      <div
                        className="bar-chart-fill bar-chart-fill-yield"
                        style={{ width: `${Math.max(0, Math.min(100, (item.predicted_yield / 10) * 100))}%` }}
                      />
                    </div>
                    <strong>{item.predicted_yield.toFixed(2)}%</strong>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="ranked-grid">
            {results.map((item) => (
              <article
                key={`${item.postcode}-${item.rank}`}
                className={`ranked-card ${item.rank === 1 ? "ranked-card-best" : ""}`}
              >
                <div className="rank-row">
                  <span className="rank-pill">Rank #{item.rank}</span>
                  {item.rank === 1 && <span className="badge badge-strong">Best Option</span>}
                </div>

                <h4>
                  {item.postcode} - {item.region}
                </h4>
                <p className="muted" style={{ marginTop: 0 }}>
                  {item.property_type}, {item.bedrooms} bedrooms
                </p>

                <div className="result-metrics">
                  <article className="metric-card">
                    <h4>Predicted Yield</h4>
                    <p className="metric-value">{item.predicted_yield}%</p>
                  </article>
                  <article className="metric-card">
                    <h4>Investment Score</h4>
                    <p className="metric-value">{item.investment_score}</p>
                  </article>
                </div>

                <div style={{ marginTop: 10 }}>
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
                </div>

                <div className="compare-bars">
                  <div className="compare-bar-row">
                    <span>Score</span>
                    <span>{item.investment_score}</span>
                  </div>
                  <div className="progress-track">
                    <div
                      className="progress-fill"
                      style={{ width: `${Math.max(0, Math.min(100, item.investment_score))}%` }}
                    />
                  </div>

                  <div className="compare-bar-row">
                    <span>Yield</span>
                    <span>{item.predicted_yield}%</span>
                  </div>
                  <div className="progress-track">
                    <div
                      className="progress-fill progress-fill-yield"
                      style={{ width: `${Math.max(0, Math.min(100, (item.predicted_yield / 10) * 100))}%` }}
                    />
                  </div>
                </div>

                <div className="compare-details">
                  <p>
                    <strong>Purchase Price:</strong> GBP {item.purchase_price}
                  </p>
                  <p>
                    <strong>Monthly Rent:</strong> GBP {item.monthly_rent}
                  </p>
                  <p>
                    <strong>Crime Rate:</strong> {item.crime_rate}
                  </p>
                  <p>
                    <strong>Amenity Score:</strong> {item.amenity_score}
                  </p>
                  <p>
                    <strong>HPI Growth:</strong> {item.hpi_growth}%
                  </p>
                  <p>
                    <strong>Distance to Station:</strong> {item.distance_to_station} km
                  </p>
                  <p>
                    <strong>Data Sources:</strong> {(item.data_sources_used || []).join(", ")}
                  </p>
                </div>
              </article>
            ))}
          </div>
          <p className="helper-note">
            This comparison is decision-support only. Enriched neighbourhood values may use fallback
            estimates when live APIs are not available.
          </p>
        </section>
      )}
    </>
  );
}
