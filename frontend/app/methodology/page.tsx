import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Methodology — UrbanGauge",
  description: "How UrbanGauge handles source evidence, statistical comparability, and publication review.",
};

export default function MethodologyPage() {
  return (
    <main className="scope-section" id="main">
      <div className="container">
        <p className="section-kicker">URBANGAUGE / RESEARCH METHODS</p>
        <h1>Methodology before metrics.</h1>
        <p className="hero-lede">
          UrbanGauge is currently an engineering and research preview. No public source-derived data
          products are available, and the illustration on the homepage is not a quantitative chart.
        </p>
        <div className="card-grid">
          <section className="scope-card">
            <span className="card-number">01 / SOURCE EVIDENCE</span>
            <h2>Traceable sources</h2>
            <p>Publisher identity, geography, period, population, units, revisions, and provenance require review before reuse.</p>
          </section>
          <section className="scope-card">
            <span className="card-number">02 / COMPARABILITY</span>
            <h2>Separate measures</h2>
            <p>Income and rent have unmatched populations and aggregations. No cross-publisher affordability ratio is approved.</p>
          </section>
          <section className="scope-card">
            <span className="card-number">03 / PUBLICATION</span>
            <h2>Explicit permission</h2>
            <p>Source redistribution, geographic crosswalks, and versioned browser exports remain closed pending independent review.</p>
          </section>
        </div>
        <p className="hero-actions">
          <Link className="primary-link" href="/">Back to UrbanGauge home</Link>
          <a className="source-link" href="https://github.com/DevIsola/UrbanGauge" target="_blank" rel="noopener noreferrer">Review research repository</a>
        </p>
      </div>
    </main>
  );
}
