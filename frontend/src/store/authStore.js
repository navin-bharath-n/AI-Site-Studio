/**
 * Auth store — persisted user session using Zustand + localStorage.
 * Integrates with FastAPI backend JWT.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

const SESSION_KEY = "aisitestudio_auth";
const API_BASE = "http://localhost:8000/api/v1";

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // ── State ──────────────────────────────────────────
      user: null,
      token: null,
      isSignedIn: false,
      isLoaded: false,          // true once hydrated
      pendingRedirect: null,    // set after OAuth redirect; consumed by App to navigate()

      // ── Actions ────────────────────────────────────────
      /** Called once on app mount to mark as hydrated */
      setLoaded: async () => {
        // Check URL for token after redirect
        const urlParams = new URLSearchParams(window.location.search);
        const urlToken = urlParams.get('token');
        const urlRedirect = urlParams.get('redirect');
        if (urlToken) {
          get().setToken(urlToken);
          await get().fetchProfile();
          // Store redirect path for the React app to handle (avoids hard page reload)
          if (urlRedirect) {
            set({ pendingRedirect: urlRedirect });
          }
          // Clean up URL
          window.history.replaceState({}, document.title, window.location.pathname);
          set({ isLoaded: true });
        } else if (get().token) {
          if (get().user && get().isSignedIn) {
            // Already hydrated from localStorage, render UI immediately
            set({ isLoaded: true });
            // Fetch in background to sync profile
            get().fetchProfile();
          } else {
            // No user in storage, fetch before rendering
            await get().fetchProfile();
            set({ isLoaded: true });
          }
        } else {
          set({ isLoaded: true });
        }
      },

      setToken: (token) => set({ token, isSignedIn: !!token }),

      clearPendingRedirect: () => set({ pendingRedirect: null }),

      fetchProfile: async () => {
        const { token } = get();
        if (!token) return;
        
        try {
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (res.ok) {
            const dbUser = await res.json();
            const mappedUser = {
              ...dbUser,
              firstName: dbUser.full_name ? dbUser.full_name.split(" ")[0] : "User",
              fullName: dbUser.full_name || "User",
              imageUrl: dbUser.avatar_url || "https://picsum.photos/seed/default/100/100",
              primaryEmailAddress: { emailAddress: dbUser.email }
            };
            set({ user: mappedUser, isSignedIn: true });
          } else {
            get().signOut();
          }
        } catch (err) {
          console.error("Failed to fetch profile", err);
          get().signOut();
        }
      },

      /** Redirect to backend OAuth (Google) */
      beginGoogleAuth: (role) => {
        window.location.href = `${API_BASE}/auth/google/login?role=${role || 'buyer'}`;
        return { success: true };
      },

      /** Email Login */
      signInWithEmail: async ({ email, password }) => {
        try {
          const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
          });
          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Invalid email or password");
          }
          const data = await res.json();
          set({ token: data.access_token, isSignedIn: true });
          await get().fetchProfile();
          return { success: true };
        } catch (err) {
          console.error("Login failed:", err);
          throw err;
        }
      },

      /** Email Register */
      registerWithEmail: async ({ email, password, role }) => {
        try {
          const res = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, role })
          });
          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Registration failed");
          }
          const data = await res.json();
          set({ token: data.access_token, isSignedIn: true });
          await get().fetchProfile();
          return { success: true };
        } catch (err) {
          console.error("Registration failed:", err);
          throw err;
        }
      },

      signOut: () =>
        set({
          user: null,
          token: null,
          isSignedIn: false,
        }),

      // Internal helper
      _pendingRole: "buyer",
      setPendingRole: (role) => set({ _pendingRole: role }),
    }),
    {
      name: SESSION_KEY,
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isSignedIn: state.isSignedIn,
      }),
    }
  )
);
