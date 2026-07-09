"use client";

/**
 * Marketplace Page — split layout: sidebar filters + template grid + toolbar (React JSX).
 */

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { navigate } from "@/components/Link";
const useRouter = () => ({
  push: (to) => navigate(to),
  replace: (to) => navigate(to),
});
const useSearchParams = () => new URLSearchParams(window.location.search);
import { useAppAuth } from "@/lib/auth";
import {
  LayoutGrid, LayoutList, Search, ChevronDown, X,
} from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import SidebarFilters from "@/components/marketplace/SidebarFilters";
import TemplateGrid from "@/components/marketplace/TemplateGrid";
import { useTemplates, useToggleFavorite, useToggleWishlist } from "@/hooks/useTemplates";
import { useFilterStore } from "@/store";
import { cn, debounce } from "@/lib/utils";
import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import "./Page.css";

const SORT_OPTIONS = [
  { value: "newest", label: "Newest" },
  { value: "best_sellers", label: "Best Sellers" },
  { value: "best_rated", label: "Best Rated" },
  { value: "trending", label: "Trending" },
  { value: "lowest_price", label: "Lowest Price" },
  { value: "highest_price", label: "Highest Price" },
  { value: "most_downloaded", label: "Most Downloaded" },
];

function Marketplace() {
  const { getToken } = useAppAuth();
  const { filters, setFilter, setFilters, resetFilters } = useFilterStore();
  const [view, setView] = useState("grid");
  const [searchInput, setSearchInput] = useState(filters.q ?? "");
  const searchParams = useSearchParams();

  // Sync URL params → store on mount
  useEffect(() => {
    const params = {};
    searchParams.forEach((v, k) => { params[k] = v; });
    if (Object.keys(params).length > 0) {
      setFilters({
        category: params.category,
        q: params.q,
        sort: params.sort ?? "newest",
        page: params.page ? Number(params.page) : 1,
        min_price: params.min_price ? Number(params.min_price) : undefined,
        max_price: params.max_price ? Number(params.max_price) : undefined,
        sales: params.sales,
        compatibility: params.compatibility,
        language: params.language,
        date_added: params.date_added,
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get("/categories"),
    staleTime: 1000 * 60 * 10,
  });

  // Fetch templates
  const [token, setToken] = useState(null);
  useEffect(() => {
    getToken().then(setToken);
  }, [getToken]);

  const { data, isLoading } = useTemplates(filters, token);

  const favoriteMutation = useToggleFavorite(token ?? "");
  const wishlistMutation = useToggleWishlist(token ?? "");

  // Debounced search
  const debouncedSearch = debounce((value) => {
    setFilter("q", value || undefined);
  }, 350);

  const handleSearch = (value) => {
    setSearchInput(value);
    debouncedSearch(value);
  };

  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;

  return (
    <>
      <Navbar />
      <div className="marketplace-page">
        <div className="marketplace-container">
          <div className="marketplace-layout">
            {/* ── Sidebar ──────────────────────────────────────────────── */}
            <div className="marketplace-sidebar">
              <div className="sticky-sidebar">
                <SidebarFilters categories={categories} />
              </div>
            </div>

            {/* ── Main Content ─────────────────────────────────────────── */}
            <div className="marketplace-main">
              {/* Toolbar */}
              <div className="marketplace-toolbar">
                {/* Search Bar */}
                <div className="marketplace-search">
                  <Search className="marketplace-search-icon" />
                  <input
                    type="text"
                    placeholder="Search templates..."
                    value={searchInput}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="marketplace-search-input"
                  />
                  {searchInput && (
                    <button
                      onClick={() => handleSearch("")}
                      className="search-clear-btn"
                    >
                      <X className="search-clear-icon" />
                    </button>
                  )}
                </div>

                {/* Sort Toggle */}
                <div className="marketplace-sort-bar">
                  {SORT_OPTIONS.slice(0, 4).map((o) => (
                    <button
                      key={o.value}
                      onClick={() => setFilter("sort", o.value)}
                      className={cn(
                        "sort-btn",
                        (filters.sort || "newest") === o.value && "active"
                      )}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>

                {/* View Toggle */}
                <div className="view-toggle">
                  {(["grid", "list"]).map((v) => (
                    <button
                      key={v}
                      onClick={() => setView(v)}
                      className={cn(
                        "view-btn",
                        view === v && "active"
                      )}
                    >
                      {v === "grid" ? (
                        <LayoutGrid className="view-toggle-icon" />
                      ) : (
                        <LayoutList className="view-toggle-icon" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Result count */}
              <div className="result-count-bar">
                <p className="result-count-text">
                  {isLoading ? "Loading..." : `${total.toLocaleString()} templates found`}
                </p>
              </div>

              {/* Grid */}
              <TemplateGrid
                templates={data?.items ?? []}
                isLoading={isLoading}
                view={view}
                onFavorite={(id) => token && favoriteMutation.mutate(id)}
                onWishlist={(id) => token && wishlistMutation.mutate(id)}
              />

              {/* Pagination */}
              {!isLoading && totalPages > 1 && (
                <div className="pagination-container">
                  <button
                    onClick={() => setFilter("page", Math.max(1, (filters.page ?? 1) - 1))}
                    disabled={(filters.page ?? 1) <= 1}
                    className="page-nav-btn"
                  >
                    Previous
                  </button>
                  {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                    const page = i + 1;
                    return (
                      <button
                        key={page}
                        onClick={() => setFilter("page", page)}
                        className={cn(
                          "page-num-btn",
                          (filters.page ?? 1) === page && "active"
                        )}
                      >
                        {page}
                      </button>
                    );
                  })}
                  <button
                    onClick={() => setFilter("page", Math.min(totalPages, (filters.page ?? 1) + 1))}
                    disabled={(filters.page ?? 1) >= totalPages}
                    className="page-nav-btn"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default Marketplace;
