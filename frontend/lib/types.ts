// API Types - Matching backend schemas

// ============================================================================
// Authentication Types
// ============================================================================

export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// ============================================================================
// Brand Types
// ============================================================================

export interface Brand {
  id: number
  name: string
  created_at: string
  mention_count?: number
}

export interface BrandList {
  brands: Brand[]
  total: number
}

// ============================================================================
// Mention Types
// ============================================================================

export type SentimentLabel = 'Positive' | 'Neutral' | 'Negative'
export type Source = 'google_news' | 'hackernews'

export interface Mention {
  id: number
  brand_id: number
  brand_name?: string
  source: Source
  title: string
  url: string
  content?: string
  sentiment_score?: number
  sentiment_label?: SentimentLabel
  published_date?: string
  ingested_date: string
  processed_date?: string
  author?: string
  points?: number
}

export interface MentionList {
  mentions: Mention[]
  total: number
  page: number
  page_size: number
}

// ============================================================================
// Search Types
// ============================================================================

export interface SearchRequest {
  query: string
  brand_id?: number
  source?: Source
  sentiment?: SentimentLabel
  limit?: number
}

export interface SearchResponse {
  results: Mention[]
  total: number
  took_ms: number
  query: string
}

export interface SemanticSearchRequest {
  query: string
  brand_id?: number
  source?: Source
  sentiment?: SentimentLabel
  limit?: number
  similarity_threshold?: number
}

export interface SemanticMention extends Mention {
  similarity_score: number
}

export interface SemanticSearchResponse {
  results: SemanticMention[]
  total: number
  query: string
  took_ms: number
}

export interface HybridSearchRequest {
  query: string
  brand_id?: number
  source?: Source
  sentiment?: SentimentLabel
  limit?: number
  semantic_weight?: number
  similarity_threshold?: number
}

export interface HybridMention extends Mention {
  hybrid_score: number
  keyword_score?: number
  semantic_score?: number
}

export interface HybridSearchResponse {
  results: HybridMention[]
  total: number
  query: string
  took_ms: number
  semantic_weight: number
}

// ============================================================================
// Sentiment Trend Types
// ============================================================================

export interface SentimentTrendPoint {
  date: string
  average_score: number
  mention_count: number
  positive_count: number
  neutral_count: number
  negative_count: number
}

export interface SentimentTrendResponse {
  brand_id: number
  brand_name: string
  start_date: string
  end_date: string
  data_points: SentimentTrendPoint[]
  overall_average: number
}

// ============================================================================
// Error Types
// ============================================================================

export interface APIError {
  error: string
  detail?: string
  status_code: number
}

// ============================================================================
// Generic Response Types
// ============================================================================

export interface MessageResponse {
  message: string
  detail?: string
}
