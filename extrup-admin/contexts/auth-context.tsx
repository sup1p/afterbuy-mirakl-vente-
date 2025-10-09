"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { apiClient } from "@/lib/api-client"
import type { User } from "@/lib/types"

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadUser = async () => {
      if (apiClient.isAuthenticated()) {
        try {
          const userData = await apiClient.request<User>("/auth/me")
          setUser(userData)
        } catch (error) {
          console.error("Failed to load user:", error)
          apiClient.logout()
        }
      }
      setLoading(false)
    }

    loadUser()
  }, [])

  const login = async (username: string, password: string) => {
    await apiClient.login(username, password)
    const userData = await apiClient.request<User>("/auth/me")
    setUser(userData)
  }

  const logout = () => {
    apiClient.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
        isAdmin: user?.is_admin || false,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
