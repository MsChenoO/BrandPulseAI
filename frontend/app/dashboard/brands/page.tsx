'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { api } from '@/lib/api'
import type { Brand } from '@/lib/types'

// Helper function to format relative time
function getRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return 'just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`
  if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)}mo ago`
  return `${Math.floor(diffInSeconds / 31536000)}y ago`
}

// Helper function to check if ingestion is likely in progress
function isIngestionInProgress(brand: Brand): boolean {
  const created = new Date(brand.created_at)
  const now = new Date()
  const diffInMinutes = (now.getTime() - created.getTime()) / 1000 / 60
  return diffInMinutes < 5 && (brand.mention_count === 0 || !brand.mention_count)
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
    'from-indigo-500 to-indigo-600',
  ]
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

export default function BrandsPage() {
  const router = useRouter()
  const [newBrandName, setNewBrandName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [fetchingBrandId, setFetchingBrandId] = useState<number | null>(null)
  const [sortBy, setSortBy] = useState('updated_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const { data, error: fetchError, mutate } = useSWR(
    `/brands?sort_by=${sortBy}&sort_order=${sortOrder}`,
    () => api.getBrands(sortBy, sortOrder),
    {
      refreshInterval: (latestData) => {
        if (latestData?.brands?.some(isIngestionInProgress)) {
          return 5000
        }
        return 0
      },
    }
  )

  const handleCreateBrand = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.createBrand(newBrandName)
      setNewBrandName('')
      setSuccessMessage(`🎉 ${newBrandName} has been added successfully!`)
      setTimeout(() => setSuccessMessage(''), 3000)
      mutate()
    } catch (err: any) {
      setError(err.error || err.detail || 'Failed to create brand')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteBrand = async (id: number, brandName: string) => {
    if (!confirm(`Are you sure you want to delete ${brandName}?`)) return

    try {
      await api.deleteBrand(id)
      setError('')
      setSuccessMessage(`✓ ${brandName} has been deleted`)
      setTimeout(() => setSuccessMessage(''), 3000)
      mutate()
    } catch (err: any) {
      setSuccessMessage('')
      alert(err.error || err.detail || 'Failed to delete brand')
    }
  }

  const handleFetchMentions = async (id: number, brandName: string) => {
    setFetchingBrandId(id)
    setError('')

    try {
      await api.fetchMentions(id, 10)
      setSuccessMessage(`🔄 Fetching mentions for ${brandName}...`)
      setTimeout(() => {
        setSuccessMessage('')
        mutate()
      }, 5000)
    } catch (err: any) {
      setError(err.error || err.detail || 'Failed to fetch mentions')
      setTimeout(() => setError(''), 3000)
    } finally {
      setFetchingBrandId(null)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Hero Header with Gradient */}
      <div className="gradient-primary text-white p-8 md:p-12 rounded-2xl mb-8 animate-fade-in">
        <h1 className="text-4xl md:text-5xl font-bold mb-3">
          Brand Monitor
        </h1>
        <p className="text-lg md:text-xl opacity-90">
          Track sentiment across the web in real-time
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="card-modern mb-8 p-4 border-success bg-success/5 animate-fade-in">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
            <p className="text-sm font-medium text-success">{successMessage}</p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="card-modern mb-8 p-4 border-danger bg-danger/5 animate-fade-in">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-medium text-danger">{error}</p>
          </div>
        </div>
      )}

      {/* Add New Brand Card */}
      <div className="card-modern p-8 mb-8 animate-slide-in">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-foreground">Add New Brand</h2>
        </div>

        <form onSubmit={handleCreateBrand} className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            value={newBrandName}
            onChange={(e) => setNewBrandName(e.target.value)}
            placeholder="Enter brand name..."
            required
            className="input-modern flex-1"
          />
          <button
            type="submit"
            disabled={loading}
            className="btn-primary whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Adding...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Brand
              </span>
            )}
          </button>
        </form>
      </div>

      {/* Brands Section */}
      <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
        {/* Header with Sorting */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <h2 className="text-2xl font-bold text-foreground">
            Your Brands
            {data?.brands && (
              <span className="ml-3 text-lg font-normal text-muted-foreground">
                ({data.brands.length})
              </span>
            )}
          </h2>

          {/* Sorting Controls */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-muted-foreground">Sort:</label>
            <select
              value={sortBy}
              onChange={(e) => {
                const newSortBy = e.target.value
                setSortBy(newSortBy)
                if (newSortBy === 'name') {
                  setSortOrder('asc')
                } else {
                  setSortOrder('desc')
                }
              }}
              className="input-modern text-sm py-2 px-3 w-auto"
            >
              <option value="updated_at">Recently Updated</option>
              <option value="created_at">Recently Created</option>
              <option value="name">Name (A-Z)</option>
              <option value="mention_count">Most Mentions</option>
            </select>

            <button
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              className="p-2 rounded-lg border-2 border-border hover:border-primary hover:bg-primary/5 transition-all"
              title={sortOrder === 'desc' ? 'Descending' : 'Ascending'}
            >
              {sortOrder === 'desc' ? (
                <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Loading State */}
        {!data && !fetchError && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="spinner mb-4"></div>
            <p className="text-muted-foreground">Loading your brands...</p>
          </div>
        )}

        {/* Error State */}
        {fetchError && (
          <div className="card-modern p-12 text-center">
            <svg className="w-16 h-16 text-danger mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-lg font-medium text-foreground mb-2">Failed to load brands</p>
            <p className="text-muted-foreground">Please try refreshing the page</p>
          </div>
        )}

        {/* Empty State */}
        {data && data.brands.length === 0 && (
          <div className="card-modern p-16 text-center">
            <div className="inline-flex h-24 w-24 mx-auto mb-6 rounded-2xl gradient-primary items-center justify-center shadow-2xl">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold gradient-text mb-3">No brands yet</h3>
            <p className="text-lg text-muted-foreground max-w-md mx-auto">Add your first brand above to start monitoring sentiment and tracking mentions</p>
          </div>
        )}

        {/* Brands Grid */}
        {data && data.brands.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.brands.map((brand: Brand, index: number) => (
              <div
                key={brand.id}
                className="card-modern card-hover p-6 relative overflow-hidden animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {/* Decorative gradient corner */}
                <div className="absolute top-0 right-0 w-32 h-32 gradient-primary opacity-10 rounded-bl-full"></div>

                {/* Brand Header */}
                <div className="relative z-10 mb-6">
                  <div className="flex items-start gap-4 mb-4">
                    {/* Logo */}
                    <div className={`flex-shrink-0 w-16 h-16 rounded-xl bg-gradient-to-br ${getBrandColor(brand.name)} flex items-center justify-center shadow-lg`}>
                      <span className="text-2xl font-bold text-white">
                        {brand.name.charAt(0).toUpperCase()}
                      </span>
                    </div>

                    {/* Brand Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xl font-bold text-foreground mb-2 truncate">
                        {brand.name}
                      </h3>
                      {isIngestionInProgress(brand) ? (
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
                          <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                          <span className="text-sm font-medium text-primary">Fetching mentions...</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-muted/50">
                          <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                          <span className="text-sm font-bold text-foreground">{brand.mention_count || 0}</span>
                          <span className="text-sm text-muted-foreground">mentions</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Updated {getRelativeTime(brand.updated_at)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-3 relative z-10">
                  <button
                    onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                    className="btn-primary w-full text-sm py-2.5"
                  >
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      View Details
                    </span>
                  </button>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleFetchMentions(brand.id, brand.name)}
                      disabled={fetchingBrandId === brand.id}
                      className="flex-1 px-4 py-2.5 text-sm font-semibold rounded-lg border-2 border-primary/20 text-primary hover:bg-primary/5 hover:border-primary transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {fetchingBrandId === brand.id ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="w-3.5 h-3.5 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                          Fetching
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Refresh
                        </span>
                      )}
                    </button>
                    <button
                      onClick={() => handleDeleteBrand(brand.id, brand.name)}
                      className="px-4 py-2.5 text-sm font-semibold rounded-lg border-2 border-danger/20 text-danger hover:bg-danger/5 hover:border-danger transition-all"
                      title="Delete brand"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
