// Phase 5: WebSocket Context Provider
// Provides WebSocket connection state and real-time data throughout the app

'use client'

import React, { createContext, useContext, useCallback, useState, useEffect } from 'react'
import { useWebSocket, ConnectionStatus, WebSocketMessage } from '@/hooks/useWebSocket'

interface Mention {
  id: number
  title: string
  content: string
  url: string
  source: string
  sentiment_label: string
  sentiment_score: number
  brand_id: number
  published_at: string
  created_at: string
}

interface DashboardStats {
  total_mentions: number
  positive_count: number
  neutral_count: number
  negative_count: number
  new_today: number
}

interface WebSocketContextType {
  // Connection state
  status: ConnectionStatus
  isConnected: boolean

  // Real-time data
  realtimeMentions: Mention[]
  dashboardStats: DashboardStats | null
  lastUpdate: string | null

  // Control functions
  subscribeToBrand: (brandId: number) => void
  unsubscribeFromBrand: (brandId: number) => void
  clearMentions: () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

interface WebSocketProviderProps {
  children: React.ReactNode
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  // Real-time data state
  const [realtimeMentions, setRealtimeMentions] = useState<Mention[]>([])
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((message: WebSocketMessage) => {
    console.log('WebSocket message received:', message)

    switch (message.type) {
      case 'new_mention':
        // Add new mention to the list (at the beginning)
        if (message.data) {
          setRealtimeMentions((prev) => [message.data, ...prev].slice(0, 50)) // Keep last 50
          setLastUpdate(new Date().toISOString())
        }
        break

      case 'sentiment_update':
        // Update sentiment data
        if (message.data) {
          console.log('Sentiment update:', message.data)
          setLastUpdate(new Date().toISOString())
        }
        break

      case 'stats_update':
        // Update dashboard statistics
        if (message.data) {
          setDashboardStats(message.data)
          setLastUpdate(new Date().toISOString())
        }
        break

      case 'notification':
        // Handle notifications
        if (message.data) {
          console.log('Notification:', message.data)
          // You could integrate with a toast notification system here
        }
        break

      case 'error':
        console.error('WebSocket error:', message.message)
        break

      default:
        console.log('Unknown message type:', message.type)
    }
  }, [])

  // Initialize WebSocket connection
  const {
    status,
    isConnected,
    subscribeToBrand,
    unsubscribeFromBrand,
  } = useWebSocket({
    autoConnect: true,
    onMessage: handleMessage,
    onConnect: () => {
      console.log('WebSocket connected!')
    },
    onDisconnect: () => {
      console.log('WebSocket disconnected')
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
    },
  })

  // Clear mentions
  const clearMentions = useCallback(() => {
    setRealtimeMentions([])
  }, [])

  const value: WebSocketContextType = {
    status,
    isConnected,
    realtimeMentions,
    dashboardStats,
    lastUpdate,
    subscribeToBrand,
    unsubscribeFromBrand,
    clearMentions,
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

/**
 * Hook to access WebSocket context.
 *
 * Must be used within a WebSocketProvider.
 *
 * @example
 * ```tsx
 * function Dashboard() {
 *   const { isConnected, realtimeMentions, subscribeToBrand } = useWebSocketContext()
 *
 *   useEffect(() => {
 *     subscribeToBrand(123)
 *   }, [])
 *
 *   return (
 *     <div>
 *       <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
 *       <p>Mentions: {realtimeMentions.length}</p>
 *     </div>
 *   )
 * }
 * ```
 */
export function useWebSocketContext() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  }
  return context
}
