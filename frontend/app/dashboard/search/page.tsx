'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import type { SearchResponse, SemanticSearchResponse, HybridSearchResponse } from '@/lib/types'

type SearchMode = 'keyword' | 'semantic' | 'hybrid'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState<SearchMode>('keyword')
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setResults(null)

    try {
      let data
      if (searchMode === 'keyword') {
        data = await api.search({ query, limit: 20 })
      } else if (searchMode === 'semantic') {
        data = await api.semanticSearch({ query, limit: 20 })
      } else {
        data = await api.hybridSearch({ query, limit: 20 })
      }
      setResults(data)
    } catch (err: any) {
      setError(err.error || err.detail || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Search</h1>
        <p className="mt-2 text-zinc-600">
          Search mentions using keyword, semantic, or hybrid search
        </p>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">
              Search Mode
            </label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setSearchMode('keyword')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
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
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
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
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  searchMode === 'hybrid'
                    ? 'bg-zinc-900 text-white'
                    : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
                }`}
              >
                Hybrid
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="query" className="block text-sm font-medium text-zinc-700 mb-2">
              Search Query
            </label>
            <div className="flex gap-3">
              <input
                id="query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query..."
                required
                className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-zinc-500"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-md bg-zinc-900 px-6 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
        </form>
      </div>

      {results && (
        <div className="rounded-lg border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 p-6">
            <h2 className="text-lg font-semibold text-zinc-900">
              Results ({results.total})
            </h2>
            <p className="text-sm text-zinc-500">
              Found in {results.took_ms}ms
            </p>
          </div>
          <div className="divide-y divide-zinc-200">
            {results.results.length === 0 ? (
              <div className="p-6 text-center text-zinc-500">
                No results found
              </div>
            ) : (
              results.results.map((mention: any) => (
                <div key={mention.id} className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h3 className="font-medium text-zinc-900">
                        {mention.title}
                      </h3>
                      {mention.content && (
                        <p className="mt-1 text-sm text-zinc-600 line-clamp-2">
                          {mention.content}
                        </p>
                      )}
                      <div className="mt-2 flex items-center gap-4 text-xs text-zinc-500">
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
                          <span>Similarity: {(mention.similarity_score * 100).toFixed(1)}%</span>
                        )}
                        {mention.hybrid_score && (
                          <span>Score: {mention.hybrid_score.toFixed(2)}</span>
                        )}
                      </div>
                    </div>
                    <a
                      href={mention.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-zinc-900 hover:text-zinc-700"
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
