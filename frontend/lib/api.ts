// API Client for BrandPulse Backend

import config from './config'
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  Brand,
  BrandList,
  MentionList,
  SearchRequest,
  SearchResponse,
  SemanticSearchRequest,
  SemanticSearchResponse,
  HybridSearchRequest,
  HybridSearchResponse,
  SentimentTrendResponse,
  APIError,
} from './types'

// ============================================================================
// Token Management
// ============================================================================

const TOKEN_KEY = 'brandpulse_token'

export const tokenManager = {
  get: (): string | null => {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEY)
  },

  set: (token: string): void => {
    if (typeof window === 'undefined') return
    localStorage.setItem(TOKEN_KEY, token)
  },

  remove: (): void => {
    if (typeof window === 'undefined') return
    localStorage.removeItem(TOKEN_KEY)
  },
}

// ============================================================================
// API Client Class
// ============================================================================

class APIClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  /**
   * Build headers with authentication if token exists
   */
  private getHeaders(customHeaders?: HeadersInit): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }

    const token = tokenManager.get()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return headers
  }

  /**
   * Generic request handler with error handling
   */
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`

    const response = await fetch(url, {
      ...options,
      headers: this.getHeaders(options?.headers),
    })

    if (!response.ok) {
      // Try to parse error response
      let error: APIError
      try {
        error = await response.json()
      } catch {
        error = {
          error: response.statusText,
          status_code: response.status,
        }
      }
      throw error
    }

    return response.json()
  }

  // ==========================================================================
  // Authentication Endpoints
  // ==========================================================================

  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })

    // Store token
    tokenManager.set(response.access_token)

    return response
  }

  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    })

    // Store token
    tokenManager.set(response.access_token)

    return response
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me')
  }

  /**
   * Logout user (remove token)
   */
  logout(): void {
    tokenManager.remove()
  }

  // ==========================================================================
  // Brand Endpoints
  // ==========================================================================

  /**
   * Get all brands
   */
  async getBrands(): Promise<BrandList> {
    const brands = await this.request<Brand[]>('/brands')
    return {
      brands,
      total: brands.length
    }
  }

  /**
   * Get single brand by ID
   */
  async getBrand(id: number): Promise<Brand> {
    return this.request<Brand>(`/brands/${id}`)
  }

  /**
   * Create a new brand
   */
  async createBrand(name: string): Promise<Brand> {
    return this.request<Brand>('/brands', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
  }

  /**
   * Delete a brand
   */
  async deleteBrand(id: number): Promise<void> {
    await this.request(`/brands/${id}`, {
      method: 'DELETE',
    })
  }

  // ==========================================================================
  // Mention Endpoints
  // ==========================================================================

  /**
   * Get mentions for a brand
   */
  async getMentions(
    brandId: number,
    params?: {
      source?: string
      sentiment?: string
      limit?: number
      offset?: number
    }
  ): Promise<MentionList> {
    const queryParams = new URLSearchParams()
    if (params?.source) queryParams.set('source', params.source)
    if (params?.sentiment) queryParams.set('sentiment', params.sentiment)
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.offset) queryParams.set('offset', params.offset.toString())

    const query = queryParams.toString()
    const endpoint = `/brands/${brandId}/mentions${query ? `?${query}` : ''}`

    return this.request<MentionList>(endpoint)
  }

  /**
   * Get sentiment trend for a brand
   */
  async getSentimentTrend(
    brandId: number,
    days: number = 30
  ): Promise<SentimentTrendResponse> {
    return this.request<SentimentTrendResponse>(
      `/brands/${brandId}/sentiment-trend?days=${days}`
    )
  }

  /**
   * Get recent mentions for a brand (from /mentions endpoint)
   * Phase 5: For loading initial data on dashboard
   */
  async getRecentMentions(
    brandId?: number,
    limit: number = 50
  ): Promise<MentionList> {
    const queryParams = new URLSearchParams()
    if (brandId) queryParams.set('brand_id', brandId.toString())
    queryParams.set('limit', limit.toString())

    const query = queryParams.toString()
    return this.request<MentionList>(`/mentions${query ? `?${query}` : ''}`)
  }

  /**
   * Get recent mentions for a specific brand
   */
  async getBrandRecentMentions(
    brandId: number,
    limit: number = 20
  ): Promise<MentionList> {
    return this.request<MentionList>(
      `/mentions/brand/${brandId}/recent?limit=${limit}`
    )
  }

  /**
   * Get sentiment statistics
   */
  async getSentimentStats(
    brandId?: number,
    days: number = 30
  ): Promise<{
    total_mentions: number
    positive_count: number
    neutral_count: number
    negative_count: number
    positive_percentage: number
    neutral_percentage: number
    negative_percentage: number
    average_score: number
  }> {
    const queryParams = new URLSearchParams()
    if (brandId) queryParams.set('brand_id', brandId.toString())
    queryParams.set('days', days.toString())

    const query = queryParams.toString()
    return this.request(`/mentions/stats/sentiment${query ? `?${query}` : ''}`)
  }

  // ==========================================================================
  // Search Endpoints
  // ==========================================================================

  /**
   * Full-text search
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Semantic search
   */
  async semanticSearch(
    request: SemanticSearchRequest
  ): Promise<SemanticSearchResponse> {
    return this.request<SemanticSearchResponse>('/search/semantic', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Hybrid search (keyword + semantic)
   */
  async hybridSearch(
    request: HybridSearchRequest
  ): Promise<HybridSearchResponse> {
    return this.request<HybridSearchResponse>('/search/hybrid', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // ==========================================================================
  // Health Check
  // ==========================================================================

  /**
   * Check API health
   */
  async health(): Promise<{ status: string; service: string; version: string }> {
    return this.request('/health')
  }
}

// ============================================================================
// Export singleton instance
// ============================================================================

export const api = new APIClient(config.apiUrl)

export default api
