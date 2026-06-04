/**
 * Zustand auth store.
 * Persists tokens to localStorage.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setTokens: ({ access_token, refresh_token }) => {
        set({ accessToken: access_token, refreshToken: refresh_token });
      },

      setUser: (user) => set({ user }),

      login: ({ user, access_token, refresh_token }) => {
        set({ user, accessToken: access_token, refreshToken: refresh_token });
      },

      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null });
      },

      isAuthenticated: () => !!get().accessToken,
    }),
    {
      name: 'dms-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
