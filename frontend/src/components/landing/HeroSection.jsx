"use client";

/**
 * HeroSection — clean, direct hero with no fake counters or AI-slop copy.
 */

import Link from "@/components/Link";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import "./HeroSection.css";

export default function HeroSection() {
  return (
    <section className="hero-section">
      {/* Subtle grid pattern */}
      <div className="hero-grid-pattern" />

      <div className="hero-container">
        <div className="hero-content-wrapper">
          {/* Category label */}
          <motion.p
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="hero-eyebrow"
          >
            Website Template Marketplace
          </motion.p>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="hero-title"
          >
            Find a professional template.{" "}
            <span className="gradient-text">Preview it with your brand.</span>{" "}
            Download and launch.
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="hero-subtitle"
          >
            Site Studio lets you search templates by describing your business,
            fill them with your real content using AI, and export clean source
            code — all from one tool, at no cost.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="hero-ctas"
          >
            <Link href="/marketplace" className="hero-cta-primary">
              Browse Templates
              <ArrowRight className="hero-cta-arrow" />
            </Link>
            <Link href="/#features" className="hero-cta-secondary-btn">
              See how it works
            </Link>
          </motion.div>

          {/* Factual feature callouts */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.45 }}
            className="hero-feature-row"
          >
            <span className="hero-feature-item">Semantic search</span>
            <span className="hero-feature-divider" />
            <span className="hero-feature-item">Live brand preview</span>
            <span className="hero-feature-divider" />
            <span className="hero-feature-item">AI content fill</span>
            <span className="hero-feature-divider" />
            <span className="hero-feature-item">Free to use</span>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
