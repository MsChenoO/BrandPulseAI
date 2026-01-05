'use client'

import { useState } from 'react'
import { api } from '@/lib/api'

type SearchMode = 'keyword' | 'semantic' | 'hybrid'

interface Mention {
  id: number
  title: string
  content?: string
  url: string
  source: string
  sentiment_label?: string
  published_date?: string
  similarity_score?: number
  hybrid_score?: number
}

interface BrandSearchProps {
  brandId: number
  brandName: string
}

export function BrandSearch({ brandId, brandName }: BrandSearchProps) {
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState<SearchMode>('keyword')
  const [results, setResults] = useState<Mention[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setError('')
    setLoading(true)
    setResults(null)

    try {
      let data
      // NOTE: Backend needs to be updated to accept brand_id parameter
      // For now, this will search globally and we'll filter client-side
      if (searchMode === 'keyword') {
        data = await api.search({ query, limit: 50 })
      } else if (searchMode === 'semantic') {
        data = await api.semanticSearch({ query, limit: 50 })
      } else {
        data = await api.hybridSearch({ query, limit: 50 })
      }

      // Filter results to only this brand
      const filteredResults = data.results.filter((m: any) => m.brand_id === brandId)
      setResults(filteredResults)
    } catch (err: any) {
      setError(err.error || err.detail || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearch} className="space-y-4">
        {/* Search Mode Tabs */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-zinc-700">Search within {brandName}:</span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setSearchMode('keyword')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                searchMode === 'keyword'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
              }`}
            >
              Keyword
            </button>
            <button
              type="button"
              onClick={() => setSearchMode('semantic')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                searchMode === 'semantic'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
              }`}
            >
              Semantic
            </button>
            <button
              type="button"
              onClick={() => setSearchMode('hybrid')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                searchMode === 'hybrid'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
              }`}
            >
              Hybrid
            </button>
          </div>
        </div>

        {/* Search Input */}
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${brandName} mentions...`}
            className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-zinc-500"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      {/* Search Results */}
      {results !== null && (
        <div className="rounded-lg border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 p-4">
            <h3 className="text-sm font-semibold text-zinc-900">
              {results.length} result{results.length !== 1 ? 's' : ''} found
            </h3>
          </div>
          <div className="divide-y divide-zinc-200">
            {results.length === 0 ? (
              <div className="p-6 text-center text-sm text-zinc-500">
                No results found. Try a different search query.
              </div>
            ) : (
              results.map((mention) => (
                <div key={mention.id} className="p-4 hover:bg-zinc-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-zinc-900 text-sm">{mention.title}</h4>
                      {mention.content && (
                        <p className="mt-1 text-xs text-zinc-600 line-clamp-2">
                          {mention.content}
                        </p>
                      )}
                      <div className="mt-2 flex items-center gap-3 text-xs text-zinc-500">
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
                        {mention.similarity_score && (
                          <span>Similarity: {(mention.similarity_score * 100).toFixed(0)}%</span>
                        )}
                        {mention.hybrid_score && (
                          <span>Score: {mention.hybrid_score.toFixed(2)}</span>
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
                      className="text-xs font-medium text-zinc-900 hover:text-zinc-700 flex-shrink-0"
                    >
                      View →
                    </a>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
