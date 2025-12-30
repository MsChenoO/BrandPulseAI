'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { api } from '@/lib/api'
import type { Brand, MentionList } from '@/lib/types'
import { SentimentTrendChart } from '@/components/sentiment-trend-chart'
import { BrandInsights } from '@/components/brand-insights'
import { BrandSearch } from '@/components/brand-search'

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

  // Loading state with skeleton
  if (!brand && !brandError) {
    return (
      <div className="space-y-6 animate-pulse">
        {/* Header Skeleton */}
        <div className="flex items-center gap-4">
          <div className="h-8 w-16 bg-zinc-200 rounded"></div>
          <div>
            <div className="h-8 w-48 bg-zinc-200 rounded"></div>
            <div className="h-4 w-32 bg-zinc-100 rounded mt-2"></div>
          </div>
        </div>

        {/* Health Score Skeleton */}
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="h-6 w-32 bg-zinc-200 rounded mb-4"></div>
          <div className="h-12 w-24 bg-zinc-200 rounded"></div>
        </div>

        {/* Metrics Skeleton */}
        <div className="grid gap-6 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-lg border border-zinc-200 bg-white p-6">
              <div className="h-4 w-24 bg-zinc-200 rounded mb-3"></div>
              <div className="h-8 w-16 bg-zinc-200 rounded"></div>
            </div>
          ))}
        </div>

        {/* Chart Skeleton */}
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="h-6 w-40 bg-zinc-200 rounded mb-4"></div>
          <div className="h-64 bg-zinc-100 rounded"></div>
        </div>
      </div>
    )
  }

  // Error state
  if (brandError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="text-red-600 mb-4">Failed to load brand</div>
        <button
          onClick={() => router.push('/dashboard/brands')}
          className="text-sm text-zinc-600 hover:text-zinc-900"
        >
          ← Back to Brands
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
            onClick={() => router.push('/dashboard/brands')}
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

      {/* Sentiment Trend Chart */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">📈 Sentiment Trend</h2>
        {sentimentTrend && sentimentTrend.data_points.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center gap-6 text-sm">
              <div>
                <span className="text-zinc-600">Average Sentiment:</span>
                <span className="ml-2 font-semibold text-zinc-900">
                  {(sentimentTrend.overall_average * 100).toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-zinc-600">Period:</span>
                <span className="ml-2 font-medium text-zinc-700">
                  {new Date(sentimentTrend.start_date).toLocaleDateString()} -{' '}
                  {new Date(sentimentTrend.end_date).toLocaleDateString()}
                </span>
              </div>
              <div>
                <span className="text-zinc-600">Data Points:</span>
                <span className="ml-2 font-medium text-zinc-700">
                  {sentimentTrend.data_points.length}
                </span>
              </div>
            </div>
            <SentimentTrendChart data={sentimentTrend.data_points} />
          </div>
        ) : (
          <div className="p-8 bg-zinc-50 rounded-lg text-center">
            <p className="text-sm text-zinc-500">
              No sentiment data available yet. Data will appear as mentions are collected.
            </p>
          </div>
        )}
      </div>

      {/* AI-Powered Key Insights */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">🔍 Key Insights</h2>
        <BrandInsights mentions={mentionsList} brandName={brand?.name || ''} />
      </div>

      {/* Scoped Search */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">🔎 Search Mentions</h2>
        <BrandSearch brandId={brandId} brandName={brand?.name || ''} />
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
