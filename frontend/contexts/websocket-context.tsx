'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

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
}

const WebSocketContext = createContext<WebSocketContextType>({
  realtimeMentions: [],
  dashboardStats: null,
  isConnected: false,
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
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // WebSocket connection would go here
    // For now, we'll use a mock implementation

    // Simulate connection
    setIsConnected(true)

    // In a real implementation, you would:
    // const ws = new WebSocket('ws://localhost:8000/ws')
    // ws.onopen = () => setIsConnected(true)
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data)
    //   if (data.type === 'mention') {
    //     setRealtimeMentions(prev => [data.mention, ...prev].slice(0, 100))
    //   } else if (data.type === 'stats') {
    //     setDashboardStats(data.stats)
    //   }
    // }
    // ws.onclose = () => setIsConnected(false)
    //
    // return () => ws.close()

    // Cleanup
    return () => {
      setIsConnected(false)
    }
  }, [])

  return (
    <WebSocketContext.Provider
      value={{
        realtimeMentions,
        dashboardStats,
        isConnected,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  )
}
