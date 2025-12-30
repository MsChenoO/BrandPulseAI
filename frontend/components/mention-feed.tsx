// Phase 5: Live Mention Feed Component
// Displays real-time mentions as they arrive via WebSocket

'use client'

import { useWebSocketContext } from '@/contexts/websocket-context'
import { useEffect } from 'react'

interface MentionFeedProps {
  brandId?: number
  maxItems?: number
}

/**
 * Live feed of real-time mentions.
 *
 * Displays mentions as they arrive via WebSocket in real-time.
 * Optionally filter by brand ID.
 *
 * @example
 * ```tsx
 * <MentionFeed brandId={123} maxItems={10} />
 * ```
 */
export function MentionFeed({ brandId, maxItems = 20 }: MentionFeedProps) {
  const { realtimeMentions, subscribeToBrand, unsubscribeFromBrand, lastUpdate } =
    useWebSocketContext()

  // Subscribe to brand updates
  useEffect(() => {
    if (brandId) {
      subscribeToBrand(brandId)
      return () => {
        unsubscribeFromBrand(brandId)
      }
    }
  }, [brandId, subscribeToBrand, unsubscribeFromBrand])

  // Filter mentions by brand if specified
  const filteredMentions = brandId
    ? realtimeMentions.filter((mention) => mention.brand_id === brandId)
    : realtimeMentions

  // Limit number of displayed mentions
  const displayedMentions = filteredMentions.slice(0, maxItems)

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'negative':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'neutral':
        return 'bg-zinc-100 text-zinc-800 border-zinc-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getSentimentEmoji = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return '😊'
      case 'negative':
        return '😞'
      case 'neutral':
        return '😐'
      default:
        return '📰'
    }
  }

  const getSourceBadgeColor = (source: string) => {
    if (source.includes('google')) return 'bg-blue-100 text-blue-800'
    if (source.includes('hacker')) return 'bg-orange-100 text-orange-800'
    if (source.includes('reddit')) return 'bg-red-100 text-red-800'
    if (source.includes('twitter')) return 'bg-sky-100 text-sky-800'
    return 'bg-purple-100 text-purple-800'
  }

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return 'Just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  if (displayedMentions.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-8 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-zinc-100">
          <span className="text-3xl">📡</span>
        </div>
        <h3 className="mt-4 text-lg font-medium text-zinc-900">Waiting for mentions...</h3>
        <p className="mt-2 text-sm text-zinc-600">
          New mentions will appear here in real-time as they are discovered.
        </p>
        {lastUpdate && (
          <p className="mt-2 text-xs text-zinc-500">
            Last update: {new Date(lastUpdate).toLocaleTimeString()}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-zinc-900">
          Live Mentions ({displayedMentions.length})
        </h3>
        {lastUpdate && (
          <span className="text-xs text-zinc-500">
            Last update: {new Date(lastUpdate).toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {displayedMentions.map((mention) => (
          <div
            key={mention.id}
            className="group relative rounded-lg border border-zinc-200 bg-white p-4 transition-all hover:border-zinc-300 hover:shadow-md"
          >
            {/* New badge for recent mentions */}
            {new Date(mention.created_at).getTime() >
              Date.now() - 60000 && (
              <div className="absolute -top-2 -right-2">
                <span className="flex h-6 w-6">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-6 w-6 bg-blue-500 items-center justify-center text-xs text-white font-bold">
                    NEW
                  </span>
                </span>
              </div>
            )}

            {/* Header: Source and Time */}
            <div className="flex items-center justify-between mb-2">
              <span
                className={`text-xs font-medium px-2 py-1 rounded ${getSourceBadgeColor(
                  mention.source
                )}`}
              >
                {mention.source}
              </span>
              <span className="text-xs text-zinc-500">
                {formatTimeAgo(mention.created_at)}
              </span>
            </div>

            {/* Title */}
            <h4 className="font-medium text-zinc-900 mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
              {mention.title}
            </h4>

            {/* Content preview */}
            <p className="text-sm text-zinc-600 line-clamp-2 mb-3">
              {mention.content}
            </p>

            {/* Footer: Sentiment and Link */}
            <div className="flex items-center justify-between">
              <div
                className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded border ${getSentimentColor(
                  mention.sentiment_label
                )}`}
              >
                <span>{getSentimentEmoji(mention.sentiment_label)}</span>
                <span className="capitalize">{mention.sentiment_label}</span>
                <span className="ml-1 opacity-75">
                  ({(mention.sentiment_score * 100).toFixed(0)}%)
                </span>
              </div>

              {mention.url && (
                <a
                  href={mention.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
                >
                  View source →
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredMentions.length > maxItems && (
        <p className="text-center text-sm text-zinc-500">
          Showing {maxItems} of {filteredMentions.length} mentions
        </p>
      )}
    </div>
  )
}
