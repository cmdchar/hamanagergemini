import { create } from "zustand"
import { persist } from "zustand/middleware"

interface User {
  id: string
  username: string
  email: string
}

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => {
        // Also save to separate key for apiClient interceptor
        if (typeof window !== 'undefined') {
          localStorage.setItem("auth_token", token)
        }
        set({ user, token })
      },
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem("auth_token")
        }
        set({ user: null, token: null })
      },
    }),
    {
      name: "auth-storage",
      // Sync token to localStorage on hydration
      onRehydrateStorage: () => (state) => {
        if (state?.token && typeof window !== 'undefined') {
          localStorage.setItem("auth_token", state.token)
        }
      },
    },
  ),
)
