"use client";

import { motion } from "framer-motion";
import { Check, Zap } from "lucide-react";
import Link from "@/components/Link";
import "./PricingSection.css";

const PLANS = [
  {
    name: "Community Edition",
    price: 0,
    description: "Everything you need to analyze, customize, and export website templates.",
    features: [
      "Browse professional frontend templates",
      "Unlimited ZIP uploads & automated code analysis",
      "Dynamic interactive live browser previews",
      "One-click direct source ZIP downloads",
      "Derive brand CSS templates & color schemes",
      "Lighthouse SEO and accessibility scanning",
      "100% free and open-source utility",
    ],
    cta: "Explore the Marketplace",
    href: "/marketplace",
    popular: true,
  },
];

export default function PricingSection() {
  return (
    <section id="pricing" className="section pricing-section-wrap">
      <div className="container-xl">
        {/* Header */}
        <div className="section-header">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="section-badge"
          >
            <Zap className="section-badge-icon" />
            100% Free Platform
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45, delay: 0.08 }}
            className="section-title"
          >
            No Fees. No Signups required to browse. <span className="gradient-text">Just Build.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45, delay: 0.16 }}
            className="section-subtitle"
          >
            Site Studio is a free utility platform for frontend developers to analyze, live preview, and download templates.
          </motion.p>
        </div>

        {/* Plans */}
        <div className="pricing-grid-solo">
          {PLANS.map((plan) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="pricing-card popular pricing-card-solo"
            >
              <div className="pricing-header">
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
              </div>

              <div className="pricing-price-wrapper">
                <span className="pricing-price" style={{ color: "var(--emerald-500)" }}>
                  $0
                </span>
                <span className="pricing-period">/ forever</span>
              </div>

              <ul className="pricing-features-grid">
                {plan.features.map((feature) => (
                  <li key={feature} className="pricing-feature-item">
                    <Check className="pricing-check-icon" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className="pricing-cta popular"
              >
                {plan.cta}
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
