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
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`
  if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`
  return `${Math.floor(diffInSeconds / 31536000)} years ago`
}

export default function BrandsPage() {
  const router = useRouter()
  const [newBrandName, setNewBrandName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [fetchingBrandId, setFetchingBrandId] = useState<number | null>(null)

  const { data, error: fetchError, mutate } = useSWR('/brands', () => api.getBrands())

  const handleCreateBrand = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.createBrand(newBrandName)
      setNewBrandName('')
      mutate()
    } catch (err: any) {
      setError(err.error || err.detail || 'Failed to create brand')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteBrand = async (id: number, brandName: string) => {
    if (!confirm('Are you sure you want to delete this brand?')) return

    try {
      await api.deleteBrand(id)
      setError('')
      setSuccessMessage(`${brandName} has been deleted successfully`)
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
      setSuccessMessage(`Fetching mentions for ${brandName}... Check back in a moment!`)
      setTimeout(() => {
        setSuccessMessage('')
        mutate() // Refresh to show new mention counts
      }, 5000)
    } catch (err: any) {
      setError(err.error || err.detail || 'Failed to fetch mentions')
      setTimeout(() => setError(''), 3000)
    } finally {
      setFetchingBrandId(null)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Brands</h1>
        <p className="mt-2 text-zinc-600">
          Manage the brands you are tracking
        </p>
      </div>

      {successMessage && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <div className="flex items-center gap-2">
            <span className="text-green-600">✓</span>
            <p className="text-sm font-medium text-green-800">{successMessage}</p>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-zinc-900">Add New Brand</h2>
        <form onSubmit={handleCreateBrand} className="mt-4 flex gap-3">
          <input
            type="text"
            value={newBrandName}
            onChange={(e) => setNewBrandName(e.target.value)}
            placeholder="Brand name"
            required
            className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-zinc-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
          >
            {loading ? 'Adding...' : 'Add Brand'}
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">My Brands</h2>

        {!data && !fetchError && (
          <div className="text-center py-12 text-zinc-500">Loading...</div>
        )}

        {fetchError && (
          <div className="text-center py-12 text-red-600">
            Failed to load brands
          </div>
        )}

        {data && data.brands.length === 0 && (
          <div className="text-center py-12 text-zinc-500">
            No brands yet. Add your first brand above.
          </div>
        )}

        {data && data.brands.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.brands.map((brand: Brand) => (
              <div
                key={brand.id}
                className="group relative rounded-lg border border-zinc-200 bg-white p-6 hover:shadow-lg transition-shadow"
              >
                {/* Brand Header */}
                <div className="mb-4">
                  <div className="flex items-start gap-3 mb-3">
                    {/* Logo Placeholder */}
                    <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-zinc-100 to-zinc-200 border border-zinc-300 flex items-center justify-center">
                      <span className="text-xl font-bold text-zinc-600">
                        {brand.name.charAt(0).toUpperCase()}
                      </span>
                    </div>

                    {/* Brand Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xl font-semibold text-zinc-900 mb-1">
                        {brand.name}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-zinc-500">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                          </svg>
                          {brand.mention_count || 0} mentions
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-zinc-500">
                    Updated {getRelativeTime(brand.updated_at)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                    className="flex-1 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 transition-colors"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleFetchMentions(brand.id, brand.name)}
                    disabled={fetchingBrandId === brand.id}
                    className="rounded-md px-3 py-2 text-sm font-medium text-blue-600 border border-blue-200 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {fetchingBrandId === brand.id ? 'Fetching...' : 'Refresh'}
                  </button>
                  <button
                    onClick={() => handleDeleteBrand(brand.id, brand.name)}
                    className="rounded-md px-3 py-2 text-sm font-medium text-red-600 border border-red-200 hover:bg-red-50 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
