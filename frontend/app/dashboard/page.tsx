'use client'

import { useAuth } from '@/contexts/auth-context'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Dashboard</h1>
        <p className="mt-2 text-zinc-600">
          Welcome back, {user?.username}! Monitor your brand mentions in real-time.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Total Mentions</p>
            <span className="text-2xl">📊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-900">-</p>
          <p className="mt-1 text-xs text-zinc-500">Coming soon</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Positive</p>
            <span className="text-2xl">😊</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">-</p>
          <p className="mt-1 text-xs text-zinc-500">Coming soon</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Neutral</p>
            <span className="text-2xl">😐</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-zinc-600">-</p>
          <p className="mt-1 text-xs text-zinc-500">Coming soon</p>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-600">Negative</p>
            <span className="text-2xl">😞</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">-</p>
          <p className="mt-1 text-xs text-zinc-500">Coming soon</p>
        </div>
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
