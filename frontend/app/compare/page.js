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
    setLoading(true);
    setError("");
    setResults([]);

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
      setError(err.message || "Could not compare properties.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="card">
        <h2>Compare Properties</h2>
        <p className="muted">
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

        {error && <div className="alert">{error}</div>}
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
          <h3>Ranked Results</h3>
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
        </section>
      )}
    </>
  );
}
