"use client";

/**
 * HowItWorksSection — replaces fake testimonials with a concrete 3-step process.
 */

import "./TestimonialsSection.css";

const STEPS = [
  {
    step: "01",
    title: "Browse the Marketplace",
    description:
      "Use natural-language semantic search to find templates that match your business type, industry, or visual style. No endless category filtering.",
  },
  {
    step: "02",
    title: "Preview With Your Brand",
    description:
      "Open any template in the live canvas. Paste your logo, pick brand colors, and run Instant Fill to generate realistic copy tailored to your business.",
  },
  {
    step: "03",
    title: "Download and Deploy",
    description:
      "Export clean source code as a ZIP, or push directly to Vercel, Netlify, or GitHub Pages. Your site is live in minutes, not weeks.",
  },
];

export default function HowItWorksSection() {
  return (
    <section className="section how-it-works-section">
      <div className="container-xl">
        <div className="section-header">
          <h2 className="section-title">
            How Site Studio works
          </h2>
          <p className="section-subtitle">
            Three straightforward steps from discovery to a live website.
          </p>
        </div>

        <div className="how-it-works-grid">
          {STEPS.map((s) => (
            <div key={s.step} className="how-step-card">
              <div className="how-step-number">{s.step}</div>
              <h3 className="how-step-title">{s.title}</h3>
              <p className="how-step-desc">{s.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
