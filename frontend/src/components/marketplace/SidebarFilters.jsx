"use client";

/**
 * SidebarFilters — collapsible filter cards for marketplace (React JSX).
 */

import { useState } from "react";
import { ChevronDown, ChevronUp, X, SlidersHorizontal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useFilterStore } from "@/store";
import "./SidebarFilters.css";

function FilterSection({ title, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="filter-section">
      <button
        onClick={() => setOpen(!open)}
        className="filter-toggle-btn"
      >
        {title}
        {open ? <ChevronUp className="filter-toggle-icon" /> : <ChevronDown className="filter-toggle-icon" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="filter-collapsible-wrapper"
          >
            <div className="filter-collapsible-content">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function CheckboxOption({ label, count, checked, onChange }) {
  return (
    <label className="checkbox-option">
      <div className="checkbox-content-wrapper">
        <div
          className={cn(
            "checkbox-indicator",
            checked && "checked"
          )}
          onClick={() => onChange(!checked)}
        >
          {checked && (
            <svg className="check-svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>
        <span className="checkbox-label">
          {label}
        </span>
      </div>
      {count !== undefined && (
        <span className="text-xs text-muted-foreground">{count}</span>
      )}
    </label>
  );
}

const COMPATIBILITIES = ["Elementor", "Bootstrap", "Gatsby", "Figma", "Tailwind CSS"];
const LANGUAGES = ["HTML", "React", "Next.js", "Vue", "Angular", "Svelte"];
const SALES_TIERS = [
  { label: "No sales", value: "no-sales" },
  { label: "Low", value: "low" },
  { label: "Medium", value: "medium" },
  { label: "High", value: "high" },
  { label: "Top seller", value: "top-seller" },
];
const DATE_RANGES = [
  { label: "Last 24 Hours", value: "last-24h" },
  { label: "Last Week", value: "last-week" },
  { label: "Last Month", value: "last-month" },
  { label: "Last Year", value: "last-year" },
];

export default function SidebarFilters({ categories }) {
  const { filters, setFilter, resetFilters, isFilterActive } = useFilterStore();
  const active = isFilterActive();

  return (
    <aside className="sidebar-filters-aside">
      {/* Header */}
      <div className="filters-header">
        <div className="filters-header-title">
          <SlidersHorizontal className="filters-sliders-icon" />
          <span className="filters-header-text">Filters</span>
          {active && (
            <span className="filters-active-badge">
              !
            </span>
          )}
        </div>
        {active && (
          <button
            onClick={resetFilters}
            className="filters-clear-btn"
          >
            <X className="filters-clear-icon" /> Clear all
          </button>
        )}
      </div>

      <div className="filters-sections-container">
        {/* Category */}
        <FilterSection title="Category">
          <div className="filters-options-container">
            {categories.map((cat) => (
              <CheckboxOption
                key={cat.id}
                label={cat.name}
                count={cat.template_count}
                checked={filters.category === cat.slug}
                onChange={(v) => setFilter("category", v ? cat.slug : undefined)}
              />
            ))}
          </div>
        </FilterSection>

        {/* Price */}
        <FilterSection title="Price">
          <div className="price-range-inputs">
            <div className="price-input-wrapper">
              <span className="price-currency-symbol">$</span>
              <input
                type="number"
                placeholder="Min"
                min="0"
                value={filters.min_price ?? ""}
                onChange={(e) => {
                  const val = e.target.value;
                  setFilter("min_price", val !== "" ? Number(val) : undefined);
                }}
                className="price-num-input"
              />
            </div>
            <span className="price-range-separator">to</span>
            <div className="price-input-wrapper">
              <span className="price-currency-symbol">$</span>
              <input
                type="number"
                placeholder="Max"
                min="0"
                value={filters.max_price ?? ""}
                onChange={(e) => {
                  const val = e.target.value;
                  setFilter("max_price", val !== "" ? Number(val) : undefined);
                }}
                className="price-num-input"
              />
            </div>
          </div>
        </FilterSection>

        {/* On Sale & Sales */}
        <FilterSection title="On Sale & Sales">
          <div className="filters-options-container">
            <CheckboxOption
              label="On Sale"
              checked={!!filters.is_on_sale}
              onChange={(v) => setFilter("is_on_sale", v || undefined)}
            />
            <div className="sales-separator-line" />
            {SALES_TIERS.map((tier) => (
              <CheckboxOption
                key={tier.value}
                label={tier.label}
                checked={filters.sales === tier.value}
                onChange={(v) => setFilter("sales", v ? tier.value : undefined)}
              />
            ))}
          </div>
        </FilterSection>

        {/* Rating */}
        <FilterSection title="Rating">
          <div className="filters-options-container">
            {[5, 4, 3].map((r) => (
              <CheckboxOption
                key={r}
                label={`${r}+ Stars`}
                checked={filters.rating === r}
                onChange={(v) => setFilter("rating", v ? r : undefined)}
              />
            ))}
          </div>
        </FilterSection>

        {/* Date Added */}
        <FilterSection title="Date Added">
          <div className="filters-options-container">
            {DATE_RANGES.map((range) => (
              <CheckboxOption
                key={range.value}
                label={range.label}
                checked={filters.date_added === range.value}
                onChange={(v) => setFilter("date_added", v ? range.value : undefined)}
              />
            ))}
          </div>
        </FilterSection>

        {/* Language & Compatible with */}
        <FilterSection title="Language & Compatibility" defaultOpen={false}>
          <div className="filters-options-container">
            <div className="subsection-label">Languages</div>
            {LANGUAGES.map((lang) => (
              <CheckboxOption
                key={lang}
                label={lang}
                checked={filters.language === lang.toLowerCase()}
                onChange={(v) => setFilter("language", v ? lang.toLowerCase() : undefined)}
              />
            ))}
            <div className="sales-separator-line" />
            <div className="subsection-label">Compatibility</div>
            {COMPATIBILITIES.map((comp) => (
              <CheckboxOption
                key={comp}
                label={comp}
                checked={filters.compatibility === comp}
                onChange={(v) => setFilter("compatibility", v ? comp : undefined)}
              />
            ))}
          </div>
        </FilterSection>
      </div>
    </aside>
  );
}
