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

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Dashboard</h1>
        <p className="mt-2 text-zinc-600">
          Welcome back, {user?.username}! Monitor your brand mentions in real-time.
        </p>
      </div>

      {/* Brand Cards Grid */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-zinc-900">Your Brands</h2>
          {brands.length > 0 && (
            <button
              onClick={() => router.push('/dashboard/brands')}
              className="text-sm font-medium text-zinc-900 hover:text-zinc-700"
            >
              Manage All →
            </button>
          )}
        </div>

        {brandsError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-sm text-red-600">Failed to load brands</p>
          </div>
        )}

        {!brandsError && brands.length === 0 && (
          <div className="rounded-lg border border-zinc-200 bg-white p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold text-zinc-900 mb-2">Welcome to BrandPulse</h3>
              <p className="text-zinc-600 mb-6 max-w-md mx-auto">
                Start monitoring your brand's online presence. Track mentions, analyze sentiment, and gain valuable insights.
              </p>
            </div>

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
                <p className="font-medium text-zinc-900 mb-1">Track Mentions</p>
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

            <div className="mt-8 text-center">
              <button
                onClick={() => router.push('/dashboard/brands')}
                className="inline-flex items-center gap-2 rounded-md bg-zinc-900 px-6 py-3 text-sm font-medium text-white hover:bg-zinc-800 transition-colors"
              >
                Add Your First Brand
                <span>→</span>
              </button>
            </div>
          </div>
        )}

        {brands.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {brands.map((brand: Brand) => {
              const mentionCount = brand.mention_count || 0

              return (
                <div
                  key={brand.id}
                  onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                  className="cursor-pointer rounded-lg border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-lg"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-zinc-900">{brand.name}</h3>
                      <p className="mt-1 text-xs text-zinc-500">
                        Added {new Date(brand.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-3xl">
                      🎯
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between py-2 border-t border-zinc-100">
                      <span className="text-sm text-zinc-600">Total Mentions</span>
                      <span className="text-lg font-bold text-zinc-900">{mentionCount}</span>
                    </div>

                    <div className="pt-2 border-t border-zinc-100">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-zinc-600">View Details</span>
                        <span className="text-zinc-900 font-medium">→</span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {brands.length > 0 && (
          <div className="mt-8 rounded-lg border border-zinc-200 bg-zinc-50 p-6">
            <div className="flex items-start gap-4">
              <div className="text-3xl">💡</div>
              <div className="flex-1">
                <h3 className="font-semibold text-zinc-900 mb-1">Pro Tip</h3>
                <p className="text-sm text-zinc-600">
                  Click on any brand card to view detailed analytics, sentiment trends, AI-powered insights, and search through mentions.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
