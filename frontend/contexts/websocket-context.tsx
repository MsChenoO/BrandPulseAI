'use client'

import { createContext, useContext, useState, ReactNode } from 'react'
import { useWebSocket, ConnectionStatus } from '@/hooks/useWebSocket'

interface Mention {
  id: number
  brand_id: number
  brand_name: string
  title: string
  content?: string
  url: string
  source: string
  sentiment_label: string
  sentiment_score?: number
  published_date?: string
  ingested_date: string
}

interface DashboardStats {
  total_mentions: number
  positive_count: number
  neutral_count: number
  negative_count: number
}

interface WebSocketContextType {
  realtimeMentions: Mention[]
  dashboardStats: DashboardStats | null
  isConnected: boolean
  status: ConnectionStatus
  subscribeToBrand: (brandId: number) => void
  unsubscribeFromBrand: (brandId: number) => void
}

const WebSocketContext = createContext<WebSocketContextType>({
  realtimeMentions: [],
  dashboardStats: null,
  isConnected: false,
  status: ConnectionStatus.DISCONNECTED,
  subscribeToBrand: () => {},
  unsubscribeFromBrand: () => {},
})

export function useWebSocketContext() {
  return useContext(WebSocketContext)
}

interface WebSocketProviderProps {
  children: ReactNode
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [realtimeMentions, setRealtimeMentions] = useState<Mention[]>([])
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)

  // Use real WebSocket hook
  const { status, isConnected, subscribeToBrand, unsubscribeFromBrand } = useWebSocket({
    autoConnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    onMessage: (message) => {
      console.log('WebSocket message received:', message.type)

      // Handle different message types
      switch (message.type) {
        case 'new_mention':
          // Add new mention to the top of the list
          if (message.data) {
            setRealtimeMentions((prev) => [message.data, ...prev].slice(0, 100))
            console.log('New mention added:', message.data.title)
          }
          break

        case 'stats_update':
          // Update dashboard stats
          if (message.data) {
            setDashboardStats(message.data)
            console.log('Stats updated:', message.data)
          }
          break

        case 'sentiment_update':
          // Handle sentiment updates if needed
          console.log('Sentiment update:', message.data)
          break

        default:
          console.log('Unhandled message type:', message.type)
      }
    },
    onConnect: () => {
      console.log('✅ WebSocket connected successfully')
    },
    onDisconnect: () => {
      console.log('❌ WebSocket disconnected')
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
    },
  })

  return (
    <WebSocketContext.Provider
      value={{
        realtimeMentions,
        dashboardStats,
        isConnected,
        status,
        subscribeToBrand,
        unsubscribeFromBrand,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  )
}
