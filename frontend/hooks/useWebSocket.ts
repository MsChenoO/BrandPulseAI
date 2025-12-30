// Phase 5: WebSocket Hook for Real-Time Updates
// Manages WebSocket connection with automatic reconnection and JWT authentication

import { useEffect, useRef, useState, useCallback } from 'react'
import { config } from '@/lib/config'
import { tokenManager } from '@/lib/api'

// WebSocket connection states
export enum ConnectionStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  RECONNECTING = 'reconnecting',
}

// WebSocket message types
export interface WebSocketMessage {
  type: string
  data?: any
  message?: string
  timestamp?: string
  status?: string
  brand_id?: number
}

// Hook options
interface UseWebSocketOptions {
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

// Hook return type
interface UseWebSocketReturn {
  status: ConnectionStatus
  connect: () => void
  disconnect: () => void
  sendMessage: (message: any) => void
  subscribeToBrand: (brandId: number) => void
  unsubscribeFromBrand: (brandId: number) => void
  lastMessage: WebSocketMessage | null
  isConnected: boolean
}

/**
 * Custom hook for managing WebSocket connection.
 *
 * Features:
 * - Automatic connection with JWT authentication
 * - Automatic reconnection on disconnect
 * - Heartbeat/ping to keep connection alive
 * - Brand subscription management
 * - Type-safe message handling
 *
 * @param options - Hook configuration options
 * @returns WebSocket connection state and control functions
 *
 * @example
 * ```tsx
 * function Dashboard() {
 *   const { status, lastMessage, subscribeToBrand } = useWebSocket({
 *     onMessage: (msg) => {
 *       if (msg.type === 'new_mention') {
 *         console.log('New mention:', msg.data)
 *       }
 *     }
 *   })
 *
 *   useEffect(() => {
 *     subscribeToBrand(123)
 *   }, [])
 *
 *   return <div>Status: {status}</div>
 * }
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options

  // WebSocket instance
  const wsRef = useRef<WebSocket | null>(null)

  // Connection state
  const [status, setStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  // Reconnection state
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Heartbeat/ping interval
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)

  /**
   * Send a message to the WebSocket server
   */
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected. Cannot send message.')
    }
  }, [])

  /**
   * Subscribe to brand-specific updates
   */
  const subscribeToBrand = useCallback((brandId: number) => {
    sendMessage({
      type: 'subscribe',
      brand_id: brandId,
    })
  }, [sendMessage])

  /**
   * Unsubscribe from brand-specific updates
   */
  const unsubscribeFromBrand = useCallback((brandId: number) => {
    sendMessage({
      type: 'unsubscribe',
      brand_id: brandId,
    })
  }, [sendMessage])

  /**
   * Start heartbeat to keep connection alive
   */
  const startHeartbeat = useCallback(() => {
    // Clear existing interval
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
    }

    // Send ping every 30 seconds
    heartbeatIntervalRef.current = setInterval(() => {
      sendMessage({ type: 'ping' })
    }, 30000)
  }, [sendMessage])

  /**
   * Stop heartbeat
   */
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
  }, [])

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Get JWT token
    const token = tokenManager.get()
    if (!token) {
      console.error('No authentication token available')
      setStatus(ConnectionStatus.ERROR)
      return
    }

    // Prevent multiple connections
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket is already connected')
      return
    }

    try {
      setStatus(ConnectionStatus.CONNECTING)

      // Build WebSocket URL with token
      const wsUrl = `${config.wsUrl}/ws/connect?token=${token}`

      // Create WebSocket connection
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      // Connection opened
      ws.onopen = () => {
        console.log('WebSocket connected')
        setStatus(ConnectionStatus.CONNECTED)
        reconnectAttemptsRef.current = 0
        startHeartbeat()
        onConnect?.()
      }

      // Message received
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)

          // Handle specific message types
          if (message.type === 'connection' && message.status === 'connected') {
            console.log('WebSocket connection confirmed')
          } else if (message.type === 'pong') {
            // Heartbeat response
            console.debug('Received pong')
          } else {
            // Pass message to callback
            onMessage?.(message)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      // Connection closed
      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setStatus(ConnectionStatus.DISCONNECTED)
        stopHeartbeat()
        onDisconnect?.()

        // Attempt reconnection if not manually closed
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          setStatus(ConnectionStatus.RECONNECTING)
          reconnectAttemptsRef.current++

          console.log(
            `Reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          )

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('Max reconnection attempts reached')
          setStatus(ConnectionStatus.ERROR)
        }
      }

      // Connection error
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setStatus(ConnectionStatus.ERROR)
        onError?.(error)
      }
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
      setStatus(ConnectionStatus.ERROR)
    }
  }, [
    onConnect,
    onDisconnect,
    onError,
    onMessage,
    reconnectInterval,
    maxReconnectAttempts,
    startHeartbeat,
    stopHeartbeat,
  ])

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Stop heartbeat
    stopHeartbeat()

    // Close WebSocket connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect')
      wsRef.current = null
    }

    setStatus(ConnectionStatus.DISCONNECTED)
    reconnectAttemptsRef.current = 0
  }, [stopHeartbeat])

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    // Cleanup on unmount
    return () => {
      disconnect()
    }
  }, [autoConnect]) // Only run on mount/unmount

  return {
    status,
    connect,
    disconnect,
    sendMessage,
    subscribeToBrand,
    unsubscribeFromBrand,
    lastMessage,
    isConnected: status === ConnectionStatus.CONNECTED,
  }
}
