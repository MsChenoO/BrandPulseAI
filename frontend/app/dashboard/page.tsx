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

  // Generate consistent color for brand based on name
  const getBrandColor = (name: string) => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-purple-500 to-purple-600',
      'from-pink-500 to-pink-600',
      'from-red-500 to-red-600',
      'from-orange-500 to-orange-600',
      'from-yellow-500 to-yellow-600',
      'from-green-500 to-green-600',
      'from-teal-500 to-teal-600',
      'from-cyan-500 to-cyan-600',
      'from-indigo-500 to-indigo-600',
    ]
    const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[hash % colors.length]
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold gradient-text">Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Welcome back, {user?.username}! Here's your brand monitoring overview.
          </p>
        </div>
      </div>

      {/* Alerts */}
      {brandsWithoutMentions.length > 0 && brands.length > 0 && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 animate-slide-in">
          <div className="flex items-start gap-3">
            <span className="text-xl">💡</span>
            <div className="flex-1">
              <p className="font-medium text-foreground">
                {brandsWithoutMentions.length} brand{brandsWithoutMentions.length !== 1 ? 's' : ''} need mention data
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {brandsWithoutMentions.slice(0, 3).map(b => b.name).join(', ')}
                {brandsWithoutMentions.length > 3 && ` and ${brandsWithoutMentions.length - 3} more`} -
                Fetch mentions to start tracking
              </p>
              <button
                onClick={() => router.push('/dashboard/brands')}
                className="mt-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                Go to Brands →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Overall Metrics */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="card-modern card-hover animate-fade-in relative overflow-hidden group p-6">
          <div className="absolute top-0 right-0 w-32 h-32 gradient-primary opacity-10 rounded-full blur-3xl group-hover:opacity-20 transition-opacity" />
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Total Brands</p>
              </div>
            </div>
            <p className="text-4xl font-bold text-foreground mb-1">{brands.length}</p>
            <p className="text-sm text-muted-foreground">Being monitored</p>
          </div>
        </div>

        <div className="card-modern card-hover animate-fade-in relative overflow-hidden group p-6" style={{ animationDelay: '0.1s' }}>
          <div className="absolute top-0 right-0 w-32 h-32 gradient-accent opacity-10 rounded-full blur-3xl group-hover:opacity-20 transition-opacity" />
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
                  <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Total Mentions</p>
              </div>
            </div>
            <p className="text-4xl font-bold text-foreground mb-1">{totalMentions}</p>
            <p className="text-sm text-muted-foreground">Across all brands</p>
          </div>
        </div>

        <div className="card-modern card-hover animate-fade-in relative overflow-hidden group p-6" style={{ animationDelay: '0.2s' }}>
          <div className="absolute top-0 right-0 w-32 h-32 gradient-success opacity-10 rounded-full blur-3xl group-hover:opacity-20 transition-opacity" />
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success/10">
                  <svg className="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Active Tracking</p>
              </div>
            </div>
            <p className="text-4xl font-bold text-success mb-1">
              {brands.filter(b => b.mention_count && b.mention_count > 0).length}
            </p>
            <p className="text-sm text-muted-foreground">With data</p>
          </div>
        </div>
      </div>

      {/* Quick Stats & Actions */}
      {brands.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Top Brands */}
          <div className="card-modern p-6 animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <div className="flex items-center gap-2 mb-5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-foreground">Most Mentioned</h3>
            </div>
            <div className="space-y-2">
              {brands
                .filter(b => b.mention_count && b.mention_count > 0)
                .sort((a, b) => (b.mention_count || 0) - (a.mention_count || 0))
                .slice(0, 5)
                .map((brand, index) => (
                  <div
                    key={brand.id}
                    onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                    className="group flex items-center gap-3 p-4 rounded-xl hover:bg-primary/5 cursor-pointer transition-all duration-200 border border-transparent hover:border-primary/20 hover:shadow-sm"
                  >
                    <div className="relative shrink-0">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${getBrandColor(brand.name)} shadow-md text-white text-lg font-bold`}>
                        {brand.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-gradient-primary text-white text-xs font-bold ring-2 ring-card">
                        {index + 1}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-foreground group-hover:text-primary transition-colors truncate">{brand.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {brand.mention_count} mention{brand.mention_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <svg className="w-5 h-5 text-primary opacity-0 group-hover:opacity-100 transition-opacity shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                ))}

              {brands.filter(b => b.mention_count && b.mention_count > 0).length === 0 && (
                <div className="text-center py-8">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-muted mb-3">
                    <svg className="w-6 h-6 text-muted-foreground opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    No mentions yet. Fetch mentions to see data.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Recent Brands */}
          <div className="card-modern p-6 animate-fade-in" style={{ animationDelay: '0.4s' }}>
            <div className="flex items-center gap-2 mb-5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
                <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-foreground">Recently Added</h3>
            </div>
            <div className="space-y-2">
              {brands
                .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                .slice(0, 5)
                .map((brand) => (
                  <div
                    key={brand.id}
                    onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                    className="group flex items-center gap-3 p-4 rounded-xl hover:bg-primary/5 cursor-pointer transition-all duration-200 border border-transparent hover:border-primary/20 hover:shadow-sm"
                  >
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${getBrandColor(brand.name)} shadow-md text-white text-lg font-bold shrink-0`}>
                      {brand.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-foreground group-hover:text-primary transition-colors truncate">{brand.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(brand.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </p>
                    </div>
                    <svg className="w-5 h-5 text-primary opacity-0 group-hover:opacity-100 transition-opacity shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
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
            className="cursor-pointer card-modern card-hover animate-fade-in group p-6 relative overflow-hidden"
            style={{ animationDelay: '0.5s' }}
          >
            <div className="absolute top-0 right-0 w-32 h-32 gradient-primary opacity-5 rounded-full blur-3xl group-hover:opacity-10 transition-opacity" />
            <div className="relative flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl gradient-primary shadow-lg shrink-0">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="font-bold text-foreground group-hover:text-primary transition-colors text-lg mb-1">Manage Brands</p>
                <p className="text-sm text-muted-foreground">Add, delete, or fetch mentions</p>
              </div>
              <svg className="w-6 h-6 text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          <div
            onClick={() => router.push('/dashboard/search')}
            className="cursor-pointer card-modern card-hover animate-fade-in group p-6 relative overflow-hidden"
            style={{ animationDelay: '0.6s' }}
          >
            <div className="absolute top-0 right-0 w-32 h-32 gradient-accent opacity-5 rounded-full blur-3xl group-hover:opacity-10 transition-opacity" />
            <div className="relative flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl gradient-accent shadow-lg shrink-0">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="font-bold text-foreground group-hover:text-primary transition-colors text-lg mb-1">Search Mentions</p>
                <p className="text-sm text-muted-foreground">Find specific mentions across brands</p>
              </div>
              <svg className="w-6 h-6 text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {brands.length === 0 && (
        <div className="card-modern p-8 md:p-16 animate-fade-in relative overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 gradient-primary opacity-5 rounded-full blur-3xl" />
          <div className="relative text-center">
            <div className="inline-flex h-20 w-20 items-center justify-center rounded-2xl gradient-primary shadow-2xl mb-6 animate-pulse-slow">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-3xl md:text-4xl font-bold gradient-text mb-4">Welcome to BrandPulse AI</h3>
            <p className="text-lg text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed">
              Start monitoring your brand's online presence. Track mentions, analyze sentiment, and gain valuable insights with AI-powered intelligence.
            </p>

            <div className="mt-12 grid gap-8 md:grid-cols-3 max-w-4xl mx-auto">
              <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-primary/5 to-transparent border border-primary/10 hover:border-primary/20 transition-all duration-300 hover:scale-105">
                <div className="flex h-16 w-16 items-center justify-center rounded-xl gradient-primary mx-auto mb-4 shadow-lg">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <p className="font-bold text-foreground mb-2 text-lg">Add Your Brand</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Start by adding the brands you want to monitor
                </p>
              </div>

              <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-accent/5 to-transparent border border-accent/10 hover:border-accent/20 transition-all duration-300 hover:scale-105">
                <div className="flex h-16 w-16 items-center justify-center rounded-xl gradient-accent mx-auto mb-4 shadow-lg">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <p className="font-bold text-foreground mb-2 text-lg">Fetch Mentions</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Collect mentions from news and social media
                </p>
              </div>

              <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-success/5 to-transparent border border-success/10 hover:border-success/20 transition-all duration-300 hover:scale-105">
                <div className="flex h-16 w-16 items-center justify-center rounded-xl gradient-success mx-auto mb-4 shadow-lg">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <p className="font-bold text-foreground mb-2 text-lg">Analyze Insights</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  View sentiment trends and AI-powered insights
                </p>
              </div>
            </div>

            <div className="mt-12">
              <button
                onClick={() => router.push('/dashboard/brands')}
                className="btn-primary inline-flex items-center gap-3 text-base px-8 py-4"
              >
                <span>Add Your First Brand</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
