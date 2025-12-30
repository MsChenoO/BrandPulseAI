'use client'

import { useAuth } from '@/contexts/auth-context'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { api } from '@/lib/api'
import type { Brand } from '@/lib/types'

export default function DashboardPage() {
  const { user } = useAuth()
  const router = useRouter()

  // Fetch all brands
  const { data: brandsData, error: brandsError } = useSWR(
    '/brands',
    () => api.getBrands()
  )

  const brands = brandsData?.brands || []

  // Fetch mentions for each brand to calculate metrics
  const brandMetrics = brands.map((brand: Brand) => {
    const { data: mentions } = useSWR(
      `/brands/${brand.id}/mentions`,
      () => api.getMentions(brand.id, { limit: 100 })
    )
    return { brand, mentions: mentions?.mentions || [] }
  })

  // Calculate overall statistics
  const totalMentions = brandMetrics.reduce(
    (sum, { mentions }) => sum + mentions.length,
    0
  )
  const totalPositive = brandMetrics.reduce(
    (sum, { mentions }) =>
      sum + mentions.filter((m) => m.sentiment_label === 'Positive').length,
    0
  )
  const totalNeutral = brandMetrics.reduce(
    (sum, { mentions }) =>
      sum + mentions.filter((m) => m.sentiment_label === 'Neutral').length,
    0
  )
  const totalNegative = brandMetrics.reduce(
    (sum, { mentions }) =>
      sum + mentions.filter((m) => m.sentiment_label === 'Negative').length,
    0
  )

  // Calculate health score for a brand
  const calculateHealth = (mentions: any[]) => {
    if (mentions.length === 0) return 0
    const positive = mentions.filter((m) => m.sentiment_label === 'Positive').length
    return Math.round(40 + (positive / mentions.length) * 60)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Dashboard</h1>
        <p className="mt-2 text-zinc-600">
          Welcome back, {user?.username}! Monitor your brand mentions in real-time.
        </p>
      </div>

      {/* Overall Statistics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Total Mentions</p>
            <span className="text-2xl">📊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-900">{totalMentions}</p>
          <p className="mt-1 text-xs text-zinc-500">Across all brands</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Positive</p>
            <span className="text-2xl">😊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{totalPositive}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {totalMentions > 0 ? `${((totalPositive / totalMentions) * 100).toFixed(0)}%` : '0%'} of total
          </p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Neutral</p>
            <span className="text-2xl">😐</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-600">{totalNeutral}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {totalMentions > 0 ? `${((totalNeutral / totalMentions) * 100).toFixed(0)}%` : '0%'} of total
          </p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Negative</p>
            <span className="text-2xl">😞</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{totalNegative}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {totalMentions > 0 ? `${((totalNegative / totalMentions) * 100).toFixed(0)}%` : '0%'} of total
          </p>
        </div>
      </div>

      {/* Brand Cards Grid */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-zinc-900">Your Brands</h2>
          <button
            onClick={() => router.push('/dashboard/brands')}
            className="text-sm font-medium text-zinc-900 hover:text-zinc-700"
          >
            View All →
          </button>
        </div>

        {brandsError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-sm text-red-600">Failed to load brands</p>
          </div>
        )}

        {!brandsError && brands.length === 0 && (
          <div className="rounded-lg border border-zinc-200 bg-white p-6">
            <h3 className="text-xl font-semibold text-zinc-900">Getting Started</h3>
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
                  <p className="font-medium text-zinc-900">Monitor sentiment</p>
                  <p className="text-sm text-zinc-600">
                    Track real-time sentiment analysis and brand health scores
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-100 text-xs font-medium text-zinc-600">
                  3
                </div>
                <div>
                  <p className="font-medium text-zinc-900">Analyze insights</p>
                  <p className="text-sm text-zinc-600">
                    View AI-powered insights, trends, and search through mentions
                  </p>
                </div>
              </div>
              <div className="mt-6">
                <button
                  onClick={() => router.push('/dashboard/brands')}
                  className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
                >
                  Add Your First Brand
                </button>
              </div>
            </div>
          </div>
        )}

        {brands.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {brandMetrics.map(({ brand, mentions }) => {
              const health = calculateHealth(mentions)
              const positive = mentions.filter((m) => m.sentiment_label === 'Positive').length
              const neutral = mentions.filter((m) => m.sentiment_label === 'Neutral').length
              const negative = mentions.filter((m) => m.sentiment_label === 'Negative').length

              const healthColor =
                health >= 80
                  ? 'text-green-600'
                  : health >= 60
                  ? 'text-blue-600'
                  : health >= 40
                  ? 'text-yellow-600'
                  : 'text-red-600'

              return (
                <div
                  key={brand.id}
                  onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                  className="cursor-pointer rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-md"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-zinc-900">{brand.name}</h3>
                      <p className="mt-1 text-xs text-zinc-500">
                        Added {new Date(brand.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    {health > 0 && (
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${healthColor}`}>{health}</div>
                        <p className="text-xs text-zinc-500">Health</p>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-3">
                    <div className="text-center">
                      <div className="text-xl font-bold text-green-600">{positive}</div>
                      <p className="text-xs text-zinc-500">Positive</p>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-zinc-600">{neutral}</div>
                      <p className="text-xs text-zinc-500">Neutral</p>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-red-600">{negative}</div>
                      <p className="text-xs text-zinc-500">Negative</p>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center justify-between border-t border-zinc-100 pt-4">
                    <p className="text-sm text-zinc-600">
                      {mentions.length} {mentions.length === 1 ? 'mention' : 'mentions'}
                    </p>
                    <span className="text-sm font-medium text-zinc-900">View Details →</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
