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
        localStorage.setItem("auth_token", token)
        localStorage.setItem("user", JSON.stringify(user))
        set({ user, token })
      },
      logout: () => {
        localStorage.removeItem("auth_token")
        localStorage.removeItem("user")
        set({ user: null, token: null })
      },
    }),
    {
      name: "auth-storage",
    },
  ),
)
