// Phase 5: WebSocket Connection Status Indicator
// Displays real-time connection status with visual feedback

'use client'

import { ConnectionStatus } from '@/hooks/useWebSocket'

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus
  className?: string
}

/**
 * Visual indicator for WebSocket connection status.
 *
 * Displays a colored dot and status text to show the current connection state.
 *
 * @example
 * ```tsx
 * const { status } = useWebSocket()
 * return <ConnectionStatusIndicator status={status} />
 * ```
 */
export function ConnectionStatusIndicator({
  status,
  className = '',
}: ConnectionStatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return {
          color: 'bg-green-500',
          pulseColor: 'bg-green-400',
          text: 'Connected',
          textColor: 'text-green-700',
          pulse: true,
        }
      case ConnectionStatus.CONNECTING:
        return {
          color: 'bg-yellow-500',
          pulseColor: 'bg-yellow-400',
          text: 'Connecting...',
          textColor: 'text-yellow-700',
          pulse: true,
        }
      case ConnectionStatus.RECONNECTING:
        return {
          color: 'bg-orange-500',
          pulseColor: 'bg-orange-400',
          text: 'Reconnecting...',
          textColor: 'text-orange-700',
          pulse: true,
        }
      case ConnectionStatus.DISCONNECTED:
        return {
          color: 'bg-gray-400',
          pulseColor: 'bg-gray-300',
          text: 'Disconnected',
          textColor: 'text-gray-600',
          pulse: false,
        }
      case ConnectionStatus.ERROR:
        return {
          color: 'bg-red-500',
          pulseColor: 'bg-red-400',
          text: 'Connection Error',
          textColor: 'text-red-700',
          pulse: false,
        }
      default:
        return {
          color: 'bg-gray-400',
          pulseColor: 'bg-gray-300',
          text: 'Unknown',
          textColor: 'text-gray-600',
          pulse: false,
        }
    }
  }

  const config = getStatusConfig()

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative flex h-3 w-3">
        {config.pulse && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.pulseColor} opacity-75`}
          />
        )}
        <span
          className={`relative inline-flex rounded-full h-3 w-3 ${config.color}`}
        />
      </div>
      <span className={`text-sm font-medium ${config.textColor}`}>
        {config.text}
      </span>
    </div>
  )
}

/**
 * Compact connection status indicator (dot only).
 *
 * Useful for displaying in limited space areas like navigation bars.
 */
export function ConnectionStatusDot({
  status,
  className = '',
}: ConnectionStatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return {
          color: 'bg-green-500',
          pulseColor: 'bg-green-400',
          title: 'Connected',
          pulse: true,
        }
      case ConnectionStatus.CONNECTING:
        return {
          color: 'bg-yellow-500',
          pulseColor: 'bg-yellow-400',
          title: 'Connecting...',
          pulse: true,
        }
      case ConnectionStatus.RECONNECTING:
        return {
          color: 'bg-orange-500',
          pulseColor: 'bg-orange-400',
          title: 'Reconnecting...',
          pulse: true,
        }
      case ConnectionStatus.DISCONNECTED:
        return {
          color: 'bg-gray-400',
          pulseColor: 'bg-gray-300',
          title: 'Disconnected',
          pulse: false,
        }
      case ConnectionStatus.ERROR:
        return {
          color: 'bg-red-500',
          pulseColor: 'bg-red-400',
          title: 'Connection Error',
          pulse: false,
        }
      default:
        return {
          color: 'bg-gray-400',
          pulseColor: 'bg-gray-300',
          title: 'Unknown',
          pulse: false,
        }
    }
  }

  const config = getStatusConfig()

  return (
    <div className={`relative flex h-3 w-3 ${className}`} title={config.title}>
      {config.pulse && (
        <span
          className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.pulseColor} opacity-75`}
        />
      )}
      <span
        className={`relative inline-flex rounded-full h-3 w-3 ${config.color}`}
      />
    </div>
  )
}
