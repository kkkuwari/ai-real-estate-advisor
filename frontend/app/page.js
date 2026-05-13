export default function HomePage() {
  return (
    <>
      <section className="card hero">
        <h2>AI-Driven Real Estate Investment Insights</h2>
        <p>
          A final-year academic prototype that predicts rental yield, combines local risk and
          growth indicators, and supports transparent property investment decisions for UK-inspired
          market scenarios.
        </p>
        <div className="hero-actions">
          <a href="/analyse">
            <button className="button-primary" type="button">
              Analyse Property
            </button>
          </a>
          <a href="/analyses">
            <button className="button-secondary" type="button">
              View Saved Analyses
            </button>
          </a>
        </div>
      </section>

      <section className="feature-grid">
        <article className="card feature-card">
          <h3>ML Yield Prediction</h3>
          <p>
            Forecast expected rental yield from key property and location inputs using a trained
            machine-learning model.
          </p>
        </article>

        <article className="card feature-card">
          <h3>Neighbourhood Risk Indicators</h3>
          <p>
            Include amenity quality, crime rate, and local house-price growth to enrich investment
            interpretation beyond price and rent alone.
          </p>
        </article>

        <article className="card feature-card">
          <h3>Saved Investment Analyses</h3>
          <p>
            Persist analyses in SQLite and review recommendations over time in a simple dashboard
            view for reporting.
          </p>
        </article>
      </section>
    </>
  );
}
