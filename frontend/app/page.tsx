import Link from "next/link";

const workstreams = [
  {
    number: "01",
    title: "Housing indicators",
    text: "Rental definitions, reference periods, coverage and data-quality context will remain visible alongside future source-approved series.",
    tag: "Publication pending",
  },
  {
    number: "02",
    title: "Income indicators",
    text: "Economic-family and private-household measures must stay independently identified. They cannot be silently combined with rents.",
    tag: "Comparability gated",
  },
  {
    number: "03",
    title: "Regional explorer",
    text: "Interactive CMA mapping and comparisons are planned once the geographic crosswalk and source licences have been reviewed.",
    tag: "Future milestone",
  },
] as const;

export default function HomePage() {
  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Link className="brand" href="/" aria-label="UrbanGauge home">
            <span className="brand-symbol" aria-hidden="true"><span /><span /><span /></span>
            <span>Urban<span className="brand-highlight">Gauge</span></span>
          </Link>
          <div className="header-caption">Independent Canadian data research</div>
          <a className="source-link" href="https://github.com/DevIsola/UrbanGauge" target="_blank" rel="noopener noreferrer">
            View repository <span aria-hidden="true">↗</span>
          </a>
        </div>
      </header>

      <main id="main">
        <section className="hero" aria-labelledby="hero-heading">
          <div className="container hero-grid">
            <div className="hero-copy">
              <span className="eyebrow"><span className="eyebrow-dot" /> URBANGAUGE / RESEARCH PREVIEW</span>
              <h1 id="hero-heading">A clearer lens on <em>where we live.</em></h1>
              <p className="hero-lede">
                Housing, income and opportunity data can tell useful stories—when we respect what the sources actually measure.
                UrbanGauge is building an evidence-first foundation for Canadian metropolitan research.
              </p>
              <div className="hero-actions">
                <a className="primary-link" href="#scope">Explore the approach <span aria-hidden="true">↓</span></a>
                <span className="quiet-note">No public datasets available yet</span>
              </div>
            </div>
            <div className="research-panel" aria-label="Project research status">
              <div className="panel-top"><span className="panel-kicker">RESEARCH STATUS</span><span className="status-indicator">Foundation</span></div>
              <div className="panel-graphic" aria-hidden="true">
                <div className="graphic-grid"><span/><span/><span/><span/><span/></div>
                <div className="graphic-line line-one" /><div className="graphic-line line-two" />
                <div className="graphic-orb" />
              </div>
              <div className="panel-bottom"><span>Design direction accepted</span><strong>M00 / ACCEPTED</strong></div>
              <p className="panel-disclaimer">Illustrative artwork only. No quantitative indicators are displayed.</p>
            </div>
          </div>
        </section>

        <section className="scope-section" id="scope" aria-labelledby="scope-heading">
          <div className="container">
            <div className="section-heading">
              <div><p className="section-kicker">THE RESEARCH FOUNDATION</p><h2 id="scope-heading">Questions before conclusions.</h2></div>
              <p>Three areas under development. Publishing depends on reviewed definitions, provenance and reuse permissions.</p>
            </div>
            <div className="card-grid">
              {workstreams.map((item) => (
                <article className="scope-card" key={item.number}>
                  <span className="card-number">{item.number} / RESEARCH TRACK</span>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                  <span className="card-tag">{item.tag}</span>
                </article>
              ))}
            </div>
            <div className="principle"><span className="principle-icon" aria-hidden="true">i</span><p><strong>Methodology before metrics.</strong> An affordability ratio, a combined cross-source comparison, and any public source-derived export remain explicitly unapproved.</p></div>
          </div>
        </section>
      </main>

      <footer className="site-footer"><div className="container footer-inner"><span>© UrbanGauge · Independent research repository</span><span>Engineering foundation preview · Not a published data product</span></div></footer>
    </div>
  );
}
