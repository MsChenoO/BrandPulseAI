'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import type { User, LoginRequest, RegisterRequest } from '@/lib/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check if user is already logged in
    const initAuth = async () => {
      try {
        const currentUser = await api.getCurrentUser()
        setUser(currentUser)
      } catch (error) {
        // Not authenticated or token expired
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (data: LoginRequest) => {
    const response = await api.login(data)
    setUser(response.user)
    router.push('/dashboard')
  }

  const register = async (data: RegisterRequest) => {
    const response = await api.register(data)
    setUser(response.user)
    router.push('/dashboard')
  }

  const logout = () => {
    api.logout()
    setUser(null)
    router.push('/login')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
