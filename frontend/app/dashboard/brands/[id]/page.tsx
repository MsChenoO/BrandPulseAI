'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { api } from '@/lib/api'
import type { Brand, MentionList } from '@/lib/types'

interface PageProps {
  params: Promise<{ id: string }>
}

export default function BrandDetailPage({ params }: PageProps) {
  const { id } = use(params)
  const router = useRouter()
  const brandId = parseInt(id)

  // Fetch brand data
  const { data: brand, error: brandError } = useSWR(
    `/brands/${brandId}`,
    () => api.getBrand(brandId)
  )

  // Fetch brand mentions
  const { data: mentions, error: mentionsError } = useSWR(
    `/brands/${brandId}/mentions`,
    () => api.getMentions(brandId, { limit: 50 })
  )

  // Fetch sentiment trend
  const { data: sentimentTrend, error: trendError } = useSWR(
    `/brands/${brandId}/sentiment-trend`,
    () => api.getSentimentTrend(brandId, 30)
  )

  // Loading state
  if (!brand && !brandError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-zinc-500">Loading brand...</div>
      </div>
    )
  }

  // Error state
  if (brandError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="text-red-600 mb-4">Failed to load brand</div>
        <button
          onClick={() => router.push('/dashboard')}
          className="text-sm text-zinc-600 hover:text-zinc-900"
        >
          ← Back to Dashboard
        </button>
      </div>
    )
  }

  // Calculate metrics from mentions
  const totalMentions = mentions?.total || 0
  const mentionsList = mentions?.mentions || []

  const positiveCount = mentionsList.filter(
    (m) => m.sentiment_label?.toLowerCase() === 'positive'
  ).length
  const neutralCount = mentionsList.filter(
    (m) => m.sentiment_label?.toLowerCase() === 'neutral'
  ).length
  const negativeCount = mentionsList.filter(
    (m) => m.sentiment_label?.toLowerCase() === 'negative'
  ).length

  const positivePercent = totalMentions > 0 ? ((positiveCount / totalMentions) * 100).toFixed(0) : 0
  const neutralPercent = totalMentions > 0 ? ((neutralCount / totalMentions) * 100).toFixed(0) : 0
  const negativePercent = totalMentions > 0 ? ((negativeCount / totalMentions) * 100).toFixed(0) : 0

  // Calculate brand health (simple version for now)
  const brandHealth = totalMentions > 0
    ? Math.round(40 + (positiveCount / totalMentions) * 60) // 40-100 scale
    : 0

  const healthLabel = brandHealth >= 80 ? 'Excellent' : brandHealth >= 60 ? 'Good' : brandHealth >= 40 ? 'Fair' : 'Poor'
  const healthColor = brandHealth >= 80 ? 'text-green-600' : brandHealth >= 60 ? 'text-blue-600' : brandHealth >= 40 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-zinc-600 hover:text-zinc-900 transition-colors"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-3xl font-bold text-zinc-900">{brand?.name}</h1>
            <p className="text-sm text-zinc-500 mt-1">
              Added {brand?.created_at ? new Date(brand.created_at).toLocaleDateString() : ''}
            </p>
          </div>
        </div>
      </div>

      {/* Brand Health Score */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-zinc-600">Brand Health</p>
            <div className="mt-2 flex items-baseline gap-2">
              <span className={`text-4xl font-bold ${healthColor}`}>
                {brandHealth}
              </span>
              <span className="text-lg text-zinc-500">/ 100</span>
            </div>
            <p className={`mt-1 text-sm font-medium ${healthColor}`}>
              {healthLabel}
            </p>
          </div>
          <div className="text-6xl">
            {brandHealth >= 80 ? '🎉' : brandHealth >= 60 ? '😊' : brandHealth >= 40 ? '😐' : '😞'}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Total Mentions</p>
            <span className="text-2xl">📊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-900">{totalMentions}</p>
          <p className="mt-1 text-xs text-zinc-500">Last 30 days</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Positive</p>
            <span className="text-2xl">😊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{positiveCount}</p>
          <p className="mt-1 text-xs text-zinc-500">{positivePercent}% of total</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Neutral</p>
            <span className="text-2xl">😐</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-600">{neutralCount}</p>
          <p className="mt-1 text-xs text-zinc-500">{neutralPercent}% of total</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Negative</p>
            <span className="text-2xl">😞</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{negativeCount}</p>
          <p className="mt-1 text-xs text-zinc-500">{negativePercent}% of total</p>
        </div>
      </div>

      {/* Sentiment Trend (Placeholder) */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">Sentiment Trend</h2>
        {sentimentTrend && sentimentTrend.data_points.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-zinc-600">
              Average Sentiment: {sentimentTrend.overall_average.toFixed(2)}
            </p>
            <p className="text-xs text-zinc-500">
              {sentimentTrend.data_points.length} data points from{' '}
              {new Date(sentimentTrend.start_date).toLocaleDateString()} to{' '}
              {new Date(sentimentTrend.end_date).toLocaleDateString()}
            </p>
            {/* TODO: Add chart component here */}
            <div className="mt-4 p-8 bg-zinc-50 rounded-lg text-center text-sm text-zinc-500">
              📈 Chart visualization coming soon
            </div>
          </div>
        ) : (
          <p className="text-sm text-zinc-500">No sentiment data available yet</p>
        )}
      </div>

      {/* Key Insights (Placeholder) */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">🔍 Key Insights</h2>
        <div className="space-y-3">
          {totalMentions > 0 ? (
            <>
              <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                <span className="text-lg">📈</span>
                <div>
                  <p className="text-sm font-medium text-zinc-900">
                    {positivePercent}% positive sentiment
                  </p>
                  <p className="text-xs text-zinc-600">
                    Your brand is performing well with {positiveCount} positive mentions
                  </p>
                </div>
              </div>
              {negativeCount > 0 && (
                <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                  <span className="text-lg">⚠️</span>
                  <div>
                    <p className="text-sm font-medium text-zinc-900">
                      {negativeCount} negative mentions detected
                    </p>
                    <p className="text-xs text-zinc-600">
                      Monitor these mentions closely for potential issues
                    </p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-zinc-500">No insights available yet. Add mentions to see AI-powered insights.</p>
          )}
        </div>
      </div>

      {/* Latest Mentions */}
      <div className="rounded-lg border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 p-6">
          <h2 className="text-lg font-semibold text-zinc-900">Latest Mentions</h2>
          <p className="text-sm text-zinc-500 mt-1">
            Real-time mentions for {brand?.name}
          </p>
        </div>
        <div className="divide-y divide-zinc-200">
          {mentionsError && (
            <div className="p-6 text-center text-red-600">
              Failed to load mentions
            </div>
          )}
          {!mentionsError && mentionsList.length === 0 && (
            <div className="p-6 text-center text-zinc-500">
              No mentions found yet. Mentions will appear here as they are discovered.
            </div>
          )}
          {mentionsList.map((mention) => (
            <div key={mention.id} className="p-6 hover:bg-zinc-50 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h3 className="font-medium text-zinc-900">{mention.title}</h3>
                  {mention.content && (
                    <p className="mt-1 text-sm text-zinc-600 line-clamp-2">
                      {mention.content}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-4 text-xs text-zinc-500">
                    <span className="capitalize">{mention.source.replace('_', ' ')}</span>
                    {mention.sentiment_label && (
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
                          mention.sentiment_label === 'Positive'
                            ? 'bg-green-100 text-green-800'
                            : mention.sentiment_label === 'Negative'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-zinc-100 text-zinc-800'
                        }`}
                      >
                        {mention.sentiment_label}
                      </span>
                    )}
                    {mention.published_date && (
                      <span>{new Date(mention.published_date).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
                <a
                  href={mention.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-zinc-900 hover:text-zinc-700"
                >
                  View →
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
