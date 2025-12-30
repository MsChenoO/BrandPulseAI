'use client'

import { useAuth } from '@/contexts/auth-context'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { api } from '@/lib/api'

export default function DashboardPage() {
  const { user } = useAuth()
  const router = useRouter()

  // Fetch all brands
  const { data: brandsData } = useSWR('/brands', () => api.getBrands())
  const brands = brandsData?.brands || []

  // Calculate aggregated metrics
  const totalMentions = brands.reduce((sum, brand) => sum + (brand.mention_count || 0), 0)

  // Detect brands needing attention
  const brandsWithoutMentions = brands.filter(b => !b.mention_count || b.mention_count === 0)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900">Dashboard</h1>
          <p className="mt-2 text-zinc-600">
            Welcome back, {user?.username}! Here's your brand monitoring overview.
          </p>
        </div>
      </div>

      {/* Alerts */}
      {brandsWithoutMentions.length > 0 && brands.length > 0 && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-start gap-3">
            <span className="text-xl">💡</span>
            <div className="flex-1">
              <p className="font-medium text-blue-900">
                {brandsWithoutMentions.length} brand{brandsWithoutMentions.length !== 1 ? 's' : ''} need mention data
              </p>
              <p className="text-sm text-blue-700 mt-1">
                {brandsWithoutMentions.slice(0, 3).map(b => b.name).join(', ')}
                {brandsWithoutMentions.length > 3 && ` and ${brandsWithoutMentions.length - 3} more`} -
                Fetch mentions to start tracking
              </p>
              <button
                onClick={() => router.push('/dashboard/brands')}
                className="mt-2 text-sm font-medium text-blue-900 hover:text-blue-700"
              >
                Go to Brands →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Overall Metrics */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:shadow-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Total Brands</p>
            <span className="text-2xl">🎯</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-900">{brands.length}</p>
          <p className="mt-1 text-xs text-zinc-500">Being monitored</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:shadow-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Total Mentions</p>
            <span className="text-2xl">📊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-900">{totalMentions}</p>
          <p className="mt-1 text-xs text-zinc-500">Across all brands</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:shadow-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Active Tracking</p>
            <span className="text-2xl">✅</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">
            {brands.filter(b => b.mention_count && b.mention_count > 0).length}
          </p>
          <p className="mt-1 text-xs text-zinc-500">With data</p>
        </div>
      </div>

      {/* Quick Stats & Actions */}
      {brands.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Top Brands */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6">
            <h3 className="text-lg font-semibold text-zinc-900 mb-4">📈 Most Mentioned</h3>
            <div className="space-y-3">
              {brands
                .filter(b => b.mention_count && b.mention_count > 0)
                .sort((a, b) => (b.mention_count || 0) - (a.mention_count || 0))
                .slice(0, 5)
                .map((brand) => (
                  <div
                    key={brand.id}
                    onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-zinc-50 cursor-pointer transition-colors"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-zinc-900">{brand.name}</p>
                      <p className="text-xs text-zinc-500">
                        {brand.mention_count} mention{brand.mention_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <span className="text-zinc-400">→</span>
                  </div>
                ))}

              {brands.filter(b => b.mention_count && b.mention_count > 0).length === 0 && (
                <p className="text-sm text-zinc-500 text-center py-4">
                  No mentions yet. Fetch mentions to see data.
                </p>
              )}
            </div>
          </div>

          {/* Recent Brands */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6">
            <h3 className="text-lg font-semibold text-zinc-900 mb-4">🆕 Recently Added</h3>
            <div className="space-y-3">
              {brands
                .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                .slice(0, 5)
                .map((brand) => (
                  <div
                    key={brand.id}
                    onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-zinc-50 cursor-pointer transition-colors"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-zinc-900">{brand.name}</p>
                      <p className="text-xs text-zinc-500">
                        Added {new Date(brand.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="text-zinc-400">→</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      {brands.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2">
          <div
            onClick={() => router.push('/dashboard/brands')}
            className="cursor-pointer rounded-lg border border-zinc-200 bg-white p-6 hover:bg-zinc-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="text-3xl">🔧</div>
              <div>
                <p className="font-semibold text-zinc-900">Manage Brands</p>
                <p className="text-sm text-zinc-600">Add, delete, or fetch mentions</p>
              </div>
            </div>
          </div>

          <div
            onClick={() => router.push('/dashboard/search')}
            className="cursor-pointer rounded-lg border border-zinc-200 bg-white p-6 hover:bg-zinc-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="text-3xl">🔍</div>
              <div>
                <p className="font-semibold text-zinc-900">Search Mentions</p>
                <p className="text-sm text-zinc-600">Find specific mentions across brands</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {brands.length === 0 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-8">
          <div className="text-center">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-zinc-900 mb-2">Welcome to BrandPulse</h3>
            <p className="text-zinc-600 mb-6 max-w-md mx-auto">
              Start monitoring your brand's online presence. Track mentions, analyze sentiment, and gain valuable insights.
            </p>

            <div className="mt-8 grid gap-6 md:grid-cols-3 max-w-3xl mx-auto">
              <div className="text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-xl mx-auto mb-3">
                  1️⃣
                </div>
                <p className="font-medium text-zinc-900 mb-1">Add Your Brand</p>
                <p className="text-sm text-zinc-600">
                  Start by adding the brands you want to monitor
                </p>
              </div>

              <div className="text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-xl mx-auto mb-3">
                  2️⃣
                </div>
                <p className="font-medium text-zinc-900 mb-1">Fetch Mentions</p>
                <p className="text-sm text-zinc-600">
                  Collect mentions from news and social media
                </p>
              </div>

              <div className="text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-xl mx-auto mb-3">
                  3️⃣
                </div>
                <p className="font-medium text-zinc-900 mb-1">Analyze Insights</p>
                <p className="text-sm text-zinc-600">
                  View sentiment trends and AI-powered insights
                </p>
              </div>
            </div>

            <div className="mt-8">
              <button
                onClick={() => router.push('/dashboard/brands')}
                className="inline-flex items-center gap-2 rounded-md bg-zinc-900 px-6 py-3 text-sm font-medium text-white hover:bg-zinc-800 transition-colors"
              >
                Add Your First Brand
                <span>→</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
