/**
 * TanStack Query hooks for all template-related API calls (React JS version).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Query Keys ────────────────────────────────────────────────────────────

export const templateKeys = {
  all: ["templates"],
  lists: () => [...templateKeys.all, "list"],
  list: (filters) => [...templateKeys.lists(), filters],
  details: () => [...templateKeys.all, "detail"],
  detail: (slug) => [...templateKeys.details(), slug],
  featured: () => [...templateKeys.all, "featured"],
};

// ── Hooks ─────────────────────────────────────────────────────────────────

/**
 * Paginated marketplace template list with filters.
 */
export function useTemplates(filters, token) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      params.set(k, String(v));
    }
  });

  return useQuery({
    queryKey: templateKeys.list(filters),
    queryFn: () =>
      api.get(`/templates?${params.toString()}`, token),
    placeholderData: (prev) => prev,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Single template detail by slug.
 */
export function useTemplate(slug, token) {
  return useQuery({
    queryKey: templateKeys.detail(slug),
    queryFn: () => api.get(`/templates/${slug}`, token),
    staleTime: 1000 * 60 * 5,
    enabled: !!slug,
  });
}

/**
 * Featured templates for landing page.
 */
export function useFeaturedTemplates(limit = 8) {
  return useQuery({
    queryKey: [...templateKeys.featured(), limit],
    queryFn: () =>
      api.get(`/templates/featured?limit=${limit}`),
    staleTime: 1000 * 60 * 10,
  });
}

/**
 * Search templates (keyword or semantic).
 */
export function useSearch(query, semantic = false, token) {
  return useQuery({
    queryKey: ["search", query, semantic],
    queryFn: () =>
      api.get(
        `/search?q=${encodeURIComponent(query)}&semantic=${semantic}`,
        token,
      ),
    enabled: query.length > 0,
    staleTime: 1000 * 30,
  });
}

/**
 * Toggle favorite mutation.
 */
export function useToggleFavorite(token) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (templateId) =>
      api.post(`/favorites/${templateId}`, {}, token),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: templateKeys.all });
      qc.invalidateQueries({ queryKey: ["favorites"] });
    },
  });
}

/**
 * Toggle wishlist mutation.
 */
export function useToggleWishlist(token) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (templateId) =>
      api.post(`/wishlist/${templateId}`, {}, token),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: templateKeys.all });
      qc.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });
}
