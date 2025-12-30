'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { api } from '@/lib/api'
import type { Brand } from '@/lib/types'

export default function BrandsPage() {
  const router = useRouter()
  const [newBrandName, setNewBrandName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

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

  const handleDeleteBrand = async (id: number) => {
    if (!confirm('Are you sure you want to delete this brand?')) return

    try {
      await api.deleteBrand(id)
      mutate()
    } catch (err: any) {
      alert(err.error || err.detail || 'Failed to delete brand')
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

      <div className="rounded-lg border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 p-6">
          <h2 className="text-lg font-semibold text-zinc-900">Your Brands</h2>
        </div>
        <div className="divide-y divide-zinc-200">
          {!data && !fetchError && (
            <div className="p-6 text-center text-zinc-500">Loading...</div>
          )}
          {fetchError && (
            <div className="p-6 text-center text-red-600">
              Failed to load brands
            </div>
          )}
          {data && data.brands.length === 0 && (
            <div className="p-6 text-center text-zinc-500">
              No brands yet. Add your first brand above.
            </div>
          )}
          {data?.brands.map((brand: Brand) => (
            <div
              key={brand.id}
              className="flex items-center justify-between p-6"
            >
              <div>
                <h3 className="font-medium text-zinc-900">{brand.name}</h3>
                <p className="text-sm text-zinc-500">
                  {brand.mention_count || 0} mentions
                  {' · '}
                  Added {new Date(brand.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => router.push(`/dashboard/brands/${brand.id}`)}
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-zinc-900 hover:bg-zinc-100 transition-colors"
                >
                  View Details
                </button>
                <button
                  onClick={() => handleDeleteBrand(brand.id)}
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
