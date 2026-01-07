'use client'

import { use, useState } from 'react'
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

// Generate consistent color for brand based on name
function getBrandColor(name: string) {
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

export default function BrandDetailPage({ params }: PageProps) {
  const { id } = use(params)
  const router = useRouter()
  const brandId = parseInt(id)
  const [activeTab, setActiveTab] = useState<'overview' | 'mentions' | 'insights'>('overview')

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
      <div className="space-y-6 animate-pulse">
        <div className="card-modern p-8">
          <div className="flex items-center gap-6">
            <div className="h-20 w-20 bg-muted rounded-2xl"></div>
            <div className="flex-1">
              <div className="h-8 w-48 bg-muted rounded mb-3"></div>
              <div className="h-4 w-32 bg-muted/50 rounded"></div>
            </div>
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card-modern p-6">
              <div className="h-4 w-24 bg-muted rounded mb-4"></div>
              <div className="h-10 w-16 bg-muted rounded mb-2"></div>
              <div className="h-3 w-20 bg-muted/50 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (brandError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="card-modern p-12 text-center max-w-md">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-danger/10 mb-6">
            <svg className="w-8 h-8 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-foreground mb-2">Brand Not Found</h3>
          <p className="text-muted-foreground mb-6">This brand may have been deleted or you don't have access to it.</p>
          <button
            onClick={() => router.push('/dashboard/brands')}
            className="btn-primary"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Brands
          </button>
        </div>
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

  // Calculate brand health score
  const brandHealth = totalMentions > 0
    ? Math.round(40 + (positiveCount / totalMentions) * 60)
    : 0

  const healthLabel = brandHealth >= 80 ? 'Excellent' : brandHealth >= 60 ? 'Good' : brandHealth >= 40 ? 'Fair' : 'Poor'

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="card-modern p-8 relative overflow-hidden animate-fade-in">
        <div className="absolute top-0 right-0 w-96 h-96 gradient-primary opacity-5 rounded-full blur-3xl" />

        <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-center gap-6">
            {/* Brand Avatar */}
            <div className={`flex-shrink-0 h-20 w-20 rounded-2xl bg-gradient-to-br ${getBrandColor(brand?.name || '')} flex items-center justify-center shadow-xl`}>
              <span className="text-3xl font-bold text-white">
                {brand?.name.charAt(0).toUpperCase()}
              </span>
            </div>

            {/* Brand Info */}
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-2">{brand?.name}</h1>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Added {brand?.created_at ? new Date(brand.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''}</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span className="font-semibold text-foreground">{totalMentions}</span> total mentions
                </div>
              </div>
            </div>
          </div>

          {/* Back Button */}
          <button
            onClick={() => router.push('/dashboard/brands')}
            className="px-6 py-3 rounded-lg border-2 border-border text-foreground hover:border-primary hover:bg-primary/5 transition-all font-medium"
          >
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Brands
            </span>
          </button>
        </div>
      </div>

      {/* Health Score & Key Metrics */}
      <div className="grid gap-6 md:grid-cols-5 animate-fade-in" style={{ animationDelay: '0.1s' }}>
        {/* Brand Health Score */}
        <div className="card-modern p-6 md:col-span-2 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 gradient-success opacity-10 rounded-full blur-3xl" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-success/10">
                <svg className="w-4 h-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Brand Health</h3>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-baseline gap-2">
                  <span className={`text-5xl font-bold ${brandHealth >= 80 ? 'text-success' : brandHealth >= 60 ? 'text-primary' : brandHealth >= 40 ? 'text-warning' : 'text-danger'}`}>
                    {brandHealth}
                  </span>
                  <span className="text-xl text-muted-foreground font-medium">/ 100</span>
                </div>
                <p className={`mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-bold ${
                  brandHealth >= 80 ? 'bg-success/10 text-success' :
                  brandHealth >= 60 ? 'bg-primary/10 text-primary' :
                  brandHealth >= 40 ? 'bg-warning/10 text-warning' :
                  'bg-danger/10 text-danger'
                }`}>
                  {healthLabel}
                </p>
              </div>

              {/* Health Icon */}
              <div className="flex-shrink-0">
                {brandHealth >= 80 ? (
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-success/10">
                    <svg className="w-10 h-10 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                ) : brandHealth >= 60 ? (
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                    <svg className="w-10 h-10 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                    </svg>
                  </div>
                ) : brandHealth >= 40 ? (
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-warning/10">
                    <svg className="w-10 h-10 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                ) : (
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-danger/10">
                    <svg className="w-10 h-10 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                )}
              </div>
            </div>

            {/* Health Description */}
            <p className="mt-4 text-sm text-muted-foreground">
              {brandHealth >= 80 ? 'Your brand has excellent sentiment!' :
               brandHealth >= 60 ? 'Your brand is performing well.' :
               brandHealth >= 40 ? 'Consider improving brand perception.' :
               'Your brand needs attention.'}
            </p>
          </div>
        </div>

        {/* Sentiment Metrics */}
        <div className="card-modern p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 gradient-success opacity-10 rounded-full blur-2xl" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-success/10">
                <svg className="w-4 h-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Positive</h3>
            </div>
            <p className="text-3xl font-bold text-success mb-1">{positiveCount}</p>
            <p className="text-sm text-muted-foreground">{positivePercent}% of total</p>
          </div>
        </div>

        <div className="card-modern p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-muted/20 rounded-full blur-2xl" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Neutral</h3>
            </div>
            <p className="text-3xl font-bold text-foreground mb-1">{neutralCount}</p>
            <p className="text-sm text-muted-foreground">{neutralPercent}% of total</p>
          </div>
        </div>

        <div className="card-modern p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-danger/10 rounded-full blur-2xl" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-danger/10">
                <svg className="w-4 h-4 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Negative</h3>
            </div>
            <p className="text-3xl font-bold text-danger mb-1">{negativeCount}</p>
            <p className="text-sm text-muted-foreground">{negativePercent}% of total</p>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="card-modern p-2 animate-fade-in" style={{ animationDelay: '0.2s' }}>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'overview'
                ? 'gradient-primary text-white shadow-lg'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
          >
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Overview
            </span>
          </button>
          <button
            onClick={() => setActiveTab('mentions')}
            className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'mentions'
                ? 'gradient-primary text-white shadow-lg'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
          >
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Mentions ({totalMentions})
            </span>
          </button>
          <button
            onClick={() => setActiveTab('insights')}
            className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'insights'
                ? 'gradient-primary text-white shadow-lg'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
          >
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              AI Insights
            </span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Sentiment Trend Chart */}
            <div className="card-modern p-8">
              <div className="flex items-center gap-2 mb-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-foreground">Sentiment Trend</h2>
              </div>

              {sentimentTrend && sentimentTrend.data_points.length > 0 ? (
                <div className="space-y-6">
                  <div className="flex flex-wrap items-center gap-6 text-sm">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/50">
                      <span className="text-muted-foreground">Average:</span>
                      <span className="font-bold text-foreground text-base">
                        {(sentimentTrend.overall_average * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/50">
                      <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-muted-foreground">Period:</span>
                      <span className="font-semibold text-foreground">
                        {new Date(sentimentTrend.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} -{' '}
                        {new Date(sentimentTrend.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/50">
                      <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      <span className="font-semibold text-foreground">{sentimentTrend.data_points.length}</span>
                      <span className="text-muted-foreground">data points</span>
                    </div>
                  </div>
                  <SentimentTrendChart data={sentimentTrend.data_points} />
                </div>
              ) : (
                <div className="p-12 bg-muted/30 rounded-xl text-center">
                  <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-4">
                    <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <p className="text-muted-foreground">
                    No trend data available yet. Sentiment trends will appear as mentions are collected over time.
                  </p>
                </div>
              )}
            </div>

            {/* Search Section */}
            <div className="card-modern p-8">
              <div className="flex items-center gap-2 mb-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
                  <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-foreground">Search Mentions</h2>
              </div>
              <BrandSearch brandId={brandId} brandName={brand?.name || ''} />
            </div>
          </div>
        )}

        {/* Mentions Tab */}
        {activeTab === 'mentions' && (
          <div className="card-modern">
            <div className="border-b border-border p-8">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Latest Mentions</h2>
                  <p className="text-muted-foreground">
                    Real-time mentions for {brand?.name}
                  </p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 border border-primary/20">
                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span className="font-bold text-primary">{totalMentions}</span>
                  <span className="text-sm text-primary">mentions</span>
                </div>
              </div>
            </div>

            <div className="divide-y divide-border">
              {mentionsError && (
                <div className="p-12 text-center">
                  <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-danger/10 mb-4">
                    <svg className="w-8 h-8 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-danger font-medium">Failed to load mentions</p>
                </div>
              )}

              {!mentionsError && mentionsList.length === 0 && (
                <div className="p-16 text-center">
                  <div className="inline-flex h-20 w-20 items-center justify-center rounded-2xl gradient-primary mb-6">
                    <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-foreground mb-2">No mentions yet</h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    Mentions will appear here as they are discovered from Google News and HackerNews.
                  </p>
                </div>
              )}

              {mentionsList.map((mention, index) => (
                <div
                  key={mention.id}
                  className="p-6 hover:bg-muted/30 transition-all group"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                        {mention.title}
                      </h3>
                      {mention.content && (
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                          {mention.content}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-3 text-xs">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/50 text-foreground font-medium">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                          {mention.source.replace('_', ' ')}
                        </span>
                        {mention.sentiment_label && (
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md font-semibold ${
                              mention.sentiment_label === 'Positive'
                                ? 'bg-success/10 text-success'
                                : mention.sentiment_label === 'Negative'
                                ? 'bg-danger/10 text-danger'
                                : 'bg-muted text-muted-foreground'
                            }`}
                          >
                            {mention.sentiment_label === 'Positive' && (
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            )}
                            {mention.sentiment_label === 'Negative' && (
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            )}
                            {mention.sentiment_label}
                          </span>
                        )}
                        {mention.published_date && (
                          <span className="flex items-center gap-1.5 text-muted-foreground">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {new Date(mention.published_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </span>
                        )}
                      </div>
                    </div>
                    <a
                      href={mention.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-shrink-0 px-4 py-2 rounded-lg border-2 border-primary/20 text-primary hover:bg-primary hover:text-white hover:border-primary transition-all font-semibold text-sm"
                    >
                      <span className="flex items-center gap-2">
                        View
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </span>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Insights Tab */}
        {activeTab === 'insights' && (
          <div className="card-modern p-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg gradient-primary">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-foreground">AI-Powered Insights</h2>
            </div>
            <BrandInsights mentions={mentionsList} brandName={brand?.name || ''} />
          </div>
        )}
      </div>
    </div>
  )
}
