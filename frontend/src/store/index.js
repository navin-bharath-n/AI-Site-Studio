/**
 * Zustand store for marketplace filter state (React JS version).
 */

import { create } from "zustand";
import { useAuthStore } from "./authStore";

const defaultFilters = {
  sort: "newest",
  page: 1,
  page_size: 20,
};

export const useFilterStore = create((set, get) => ({
  filters: defaultFilters,

  setFilter: (key, value) =>
    set((state) => ({
      filters: {
        ...state.filters,
        [key]: value,
        // Reset to page 1 when any filter changes (except page itself)
        ...(key !== "page" ? { page: 1 } : {}),
      },
    })),

  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),

  resetFilters: () => set({ filters: defaultFilters }),

  isFilterActive: () => {
    const { filters } = get();
    const active = Object.entries(filters).some(([k, v]) => {
      if (k === "sort" && v === "newest") return false;
      if (k === "page" && v === 1) return false;
      if (k === "page_size" && v === 20) return false;
      return v !== undefined && v !== null && v !== "";
    });
    return active;
  },
}));

// ── Cart Store ────────────────────────────────────────────────────────────

export const useCartStore = create((set, get) => ({
  items: [],

  addItem: (item) => {
    const userId = useAuthStore.getState().user?.id || "guest";
    const currentItems = get().items;
    if (currentItems.some((i) => i.templateId === item.templateId)) return;
    const newItems = [...currentItems, item];
    localStorage.setItem(`cart_items_${userId}`, JSON.stringify(newItems));
    set({ items: newItems });
  },

  removeItem: (templateId) => {
    const userId = useAuthStore.getState().user?.id || "guest";
    const newItems = get().items.filter((i) => i.templateId !== templateId);
    localStorage.setItem(`cart_items_${userId}`, JSON.stringify(newItems));
    set({ items: newItems });
  },

  clearCart: () => {
    const userId = useAuthStore.getState().user?.id || "guest";
    localStorage.setItem(`cart_items_${userId}`, JSON.stringify([]));
    set({ items: [] });
  },

  total: () => get().items.reduce((sum, item) => sum + item.price, 0),

  isInCart: (templateId) => get().items.some((i) => i.templateId === templateId),
}));

// Subscribe to auth changes to dynamically swap carts on login/logout
if (typeof window !== "undefined") {
  // Set initial items based on current auth state
  const initialUserId = useAuthStore.getState().user?.id || "guest";
  const stored = localStorage.getItem(`cart_items_${initialUserId}`);
  if (stored) {
    useCartStore.setState({ items: JSON.parse(stored) });
  }

  useAuthStore.subscribe((state) => {
    const userId = state.user?.id || "guest";
    const storedCart = localStorage.getItem(`cart_items_${userId}`);
    useCartStore.setState({
      items: storedCart ? JSON.parse(storedCart) : [],
    });
  });
}
