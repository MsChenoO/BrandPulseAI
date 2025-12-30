'use client'

import { useWebSocketContext } from '@/contexts/websocket-context'
import useSWR from 'swr'
import { api } from '@/lib/api'

interface MentionFeedProps {
  maxItems?: number
  brandId?: number
}

export function MentionFeed({ maxItems = 10, brandId }: MentionFeedProps) {
  const { realtimeMentions, isConnected } = useWebSocketContext()

  // Fetch recent mentions from API as fallback
  const { data: apiMentions } = useSWR(
    brandId ? `/brands/${brandId}/mentions` : '/mentions/recent',
    () => {
      if (brandId) {
        return api.getMentions(brandId, { limit: maxItems })
      }
      // For now, return empty - in a real implementation, you'd have a global mentions endpoint
      return Promise.resolve({ mentions: [], total: 0 })
    }
  )

  // Use real-time mentions if available, otherwise use API data
  const mentions = realtimeMentions.length > 0
    ? realtimeMentions.slice(0, maxItems)
    : (apiMentions?.mentions || []).slice(0, maxItems)

  // Filter by brand if specified
  const filteredMentions = brandId
    ? mentions.filter((m) => m.brand_id === brandId)
    : mentions

  if (filteredMentions.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-2">📭</div>
        <p className="text-sm text-zinc-500">
          No mentions yet. Add brands and start monitoring!
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-zinc-900">
          Latest Mentions
        </h2>
        <div className="flex items-center gap-2">
          {isConnected && (
            <span className="flex items-center gap-1.5 text-xs text-green-600">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              Live
            </span>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {filteredMentions.map((mention, index) => (
          <div
            key={`${mention.id}-${index}`}
            className="p-4 rounded-lg border border-zinc-200 bg-white hover:bg-zinc-50 transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {mention.brand_name && (
                    <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-700">
                      {mention.brand_name}
                    </span>
                  )}
                  <span className="text-xs text-zinc-500 capitalize">
                    {mention.source.replace('_', ' ')}
                  </span>
                </div>

                <h3 className="font-medium text-zinc-900 text-sm line-clamp-1">
                  {mention.title}
                </h3>

                {mention.content && (
                  <p className="mt-1 text-xs text-zinc-600 line-clamp-2">
                    {mention.content}
                  </p>
                )}

                <div className="mt-2 flex items-center gap-3 text-xs text-zinc-500">
                  {mention.sentiment_label && (
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
                        mention.sentiment_label.toLowerCase() === 'positive'
                          ? 'bg-green-100 text-green-800'
                          : mention.sentiment_label.toLowerCase() === 'negative'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-zinc-100 text-zinc-800'
                      }`}
                    >
                      {mention.sentiment_label}
                    </span>
                  )}
                  {mention.published_date && (
                    <span>
                      {new Date(mention.published_date).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>

              <a
                href={mention.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-medium text-zinc-900 hover:text-zinc-700 flex-shrink-0"
              >
                View →
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
