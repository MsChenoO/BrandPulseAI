'use client'

import { useAuth } from '@/contexts/auth-context'
import { useWebSocketContext } from '@/contexts/websocket-context'
import { MentionFeed } from '@/components/mention-feed'

export default function DashboardPage() {
  const { user } = useAuth()
  const { dashboardStats, realtimeMentions } = useWebSocketContext()

  // Calculate real-time stats from mentions if no stats from server
  const totalMentions = dashboardStats?.total_mentions ?? realtimeMentions.length
  const positiveCount =
    dashboardStats?.positive_count ??
    realtimeMentions.filter((m) => m.sentiment_label.toLowerCase() === 'positive').length
  const neutralCount =
    dashboardStats?.neutral_count ??
    realtimeMentions.filter((m) => m.sentiment_label.toLowerCase() === 'neutral').length
  const negativeCount =
    dashboardStats?.negative_count ??
    realtimeMentions.filter((m) => m.sentiment_label.toLowerCase() === 'negative').length

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Dashboard</h1>
        <p className="mt-2 text-zinc-600">
          Welcome back, {user?.username}! Monitor your brand mentions in real-time.
        </p>
      </div>

      {/* Real-time Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:shadow-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Total Mentions</p>
            <span className="text-2xl">📊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-900">{totalMentions}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {dashboardStats ? 'Live data' : 'Real-time count'}
          </p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:shadow-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Positive</p>
            <span className="text-2xl">😊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{positiveCount}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {totalMentions > 0 ? `${((positiveCount / totalMentions) * 100).toFixed(0)}%` : '0%'}
          </p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:shadow-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Neutral</p>
            <span className="text-2xl">😐</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-600">{neutralCount}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {totalMentions > 0 ? `${((neutralCount / totalMentions) * 100).toFixed(0)}%` : '0%'}
          </p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:shadow-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Negative</p>
            <span className="text-2xl">😞</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{negativeCount}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {totalMentions > 0 ? `${((negativeCount / totalMentions) * 100).toFixed(0)}%` : '0%'}
          </p>
        </div>
      </div>

      {/* Live Mention Feed */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <MentionFeed maxItems={10} />
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h2 className="text-xl font-semibold text-zinc-900">Getting Started</h2>
        <div className="mt-4 space-y-3">
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-100 text-xs font-medium text-zinc-600">
              1
            </div>
            <div>
              <p className="font-medium text-zinc-900">Add your first brand</p>
              <p className="text-sm text-zinc-600">
                Go to the Brands page to start tracking mentions for your brand
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-100 text-xs font-medium text-zinc-600">
              2
            </div>
            <div>
              <p className="font-medium text-zinc-900">Search mentions</p>
              <p className="text-sm text-zinc-600">
                Use the Search page to find specific mentions using keywords or semantic search
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-100 text-xs font-medium text-zinc-600">
              3
            </div>
            <div>
              <p className="font-medium text-zinc-900">Monitor in real-time</p>
              <p className="text-sm text-zinc-600">
                Watch as new mentions come in and analyze sentiment trends over time
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
