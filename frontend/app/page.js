export default function HomePage() {
  return (
    <>
      <section className="card hero hero-dashboard">
        <div>
          <h2>AI-Driven Real Estate Investment Insights</h2>
          <p>
            A practical dashboard for estimating rental yield, checking neighbourhood risk signals,
            and comparing UK-style property scenarios.
          </p>
          <div className="hero-actions">
            <a href="/analyse" className="button-primary">
              Analyse Property
            </a>
            <a href="/compare" className="button-secondary">
              Compare Scenarios
            </a>
          </div>
        </div>

        <div className="hero-stat-grid">
          <article className="hero-stat-card">
            <h3>Prediction Inputs</h3>
            <p>5 Core Fields</p>
            <small>Postcode + property details</small>
          </article>
          <article className="hero-stat-card">
            <h3>Model Stack</h3>
            <p>Random Forest</p>
            <small>Linear baseline included</small>
          </article>
          <article className="hero-stat-card">
            <h3>Data Sources</h3>
            <p>Postcodes + Police</p>
            <small>Fallback defaults supported</small>
          </article>
        </div>
      </section>

      <section className="feature-grid">
        <article className="card feature-card feature-kpi">
          <span className="feature-icon">RUN</span>
          <h3>8</h3>
          <p>Sample analysis runs for demo outputs.</p>
        </article>

        <article className="card feature-card feature-kpi">
          <span className="feature-icon">AVG</span>
          <h3>5.39%</h3>
          <p>Average predicted yield from saved records.</p>
        </article>

        <article className="card feature-card feature-kpi">
          <span className="feature-icon">TOP</span>
          <h3>Strong Buy</h3>
          <p>Highest recommendation level in current workflow.</p>
        </article>

        <article className="card feature-card feature-kpi">
          <span className="feature-icon">DATA</span>
          <h3>Hybrid</h3>
          <p>Model + postcode enrichment with fallbacks.</p>
        </article>
      </section>

      <section className="feature-grid">
        <article className="card feature-card">
          <span className="feature-icon">ML</span>
          <h3>ML Yield Prediction</h3>
          <p>
            Forecast expected rental yield from key property and location inputs using a trained
            machine-learning model.
          </p>
        </article>

        <article className="card feature-card">
          <span className="feature-icon">RISK</span>
          <h3>Neighbourhood Risk Indicators</h3>
          <p>
            Include amenity quality, crime rate, and local house-price growth to enrich investment
            interpretation beyond price and rent alone.
          </p>
        </article>

        <article className="card feature-card">
          <span className="feature-icon">SAVE</span>
          <h3>Saved Investment Analyses</h3>
          <p>
            Persist analyses in SQLite and review recommendations over time in a simple dashboard
            view for reporting.
          </p>
        </article>
      </section>

      <section className="card">
        <h3 className="section-title">Workflow</h3>
        <div className="workflow-grid">
          <article className="workflow-step">
            <span>1</span>
            <p>Enter postcode and property details.</p>
          </article>
          <article className="workflow-step">
            <span>2</span>
            <p>Run prediction with neighbourhood enrichment.</p>
          </article>
          <article className="workflow-step">
            <span>3</span>
            <p>Save or compare scenarios by investment score.</p>
          </article>
        </div>
      </section>
    </>
  );
}
