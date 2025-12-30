'use client'

interface Mention {
  sentiment_score?: number
  sentiment_label?: string
  published_date?: string
  source: string
}

interface BrandInsightsProps {
  mentions: Mention[]
  brandName: string
}

export function BrandInsights({ mentions, brandName }: BrandInsightsProps) {
  if (mentions.length === 0) {
    return (
      <div className="text-sm text-zinc-500">
        No insights available yet. Add mentions to see AI-powered insights.
      </div>
    )
  }

  // Calculate metrics
  const total = mentions.length
  const positive = mentions.filter(m => m.sentiment_label?.toLowerCase() === 'positive').length
  const neutral = mentions.filter(m => m.sentiment_label?.toLowerCase() === 'neutral').length
  const negative = mentions.filter(m => m.sentiment_label?.toLowerCase() === 'negative').length

  const positivePercent = ((positive / total) * 100).toFixed(0)
  const negativePercent = ((negative / total) * 100).toFixed(0)

  // Calculate average sentiment
  const avgSentiment = mentions
    .filter(m => m.sentiment_score !== undefined)
    .reduce((sum, m) => sum + (m.sentiment_score || 0), 0) / mentions.filter(m => m.sentiment_score !== undefined).length

  // Detect trends (last 7 days vs previous 7 days)
  const now = new Date()
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
  const fourteenDaysAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000)

  const recentMentions = mentions.filter(m => m.published_date && new Date(m.published_date) >= sevenDaysAgo)
  const previousMentions = mentions.filter(m => m.published_date && new Date(m.published_date) >= fourteenDaysAgo && new Date(m.published_date) < sevenDaysAgo)

  const recentAvg = recentMentions.length > 0
    ? recentMentions.reduce((sum, m) => sum + (m.sentiment_score || 0), 0) / recentMentions.length
    : 0

  const previousAvg = previousMentions.length > 0
    ? previousMentions.reduce((sum, m) => sum + (m.sentiment_score || 0), 0) / previousMentions.length
    : 0

  const sentimentChange = recentAvg - previousAvg
  const volumeChange = recentMentions.length - previousMentions.length

  // Source breakdown
  const sources = mentions.reduce((acc, m) => {
    acc[m.source] = (acc[m.source] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const topSource = Object.entries(sources).sort((a, b) => b[1] - a[1])[0]

  // Detect spikes (any day with 2x average mentions)
  const mentionsByDay = mentions.reduce((acc, m) => {
    if (m.published_date) {
      const date = new Date(m.published_date).toDateString()
      acc[date] = (acc[date] || 0) + 1
    }
    return acc
  }, {} as Record<string, number>)

  const avgDaily = Object.values(mentionsByDay).reduce((a, b) => a + b, 0) / Object.keys(mentionsByDay).length
  const spikeDays = Object.entries(mentionsByDay).filter(([_, count]) => count > avgDaily * 2)

  const insights = []

  // Sentiment performance insight
  if (positive > negative * 2) {
    insights.push({
      type: 'positive',
      icon: '🎉',
      title: `Strong positive sentiment`,
      description: `${positivePercent}% of mentions are positive. ${brandName} is performing excellently in public perception.`
    })
  } else if (positive > neutral && positive > negative) {
    insights.push({
      type: 'positive',
      icon: '😊',
      title: `Positive sentiment majority`,
      description: `${positivePercent}% positive mentions. ${brandName} maintains a favorable reputation.`
    })
  } else if (negative > positive) {
    insights.push({
      type: 'warning',
      icon: '⚠️',
      title: `Negative sentiment detected`,
      description: `${negativePercent}% of mentions are negative. Consider addressing concerns proactively.`
    })
  }

  // Trend insight
  if (Math.abs(sentimentChange) > 0.1 && recentMentions.length >= 5 && previousMentions.length >= 5) {
    const direction = sentimentChange > 0 ? 'improved' : 'declined'
    const percentage = Math.abs(sentimentChange * 100).toFixed(0)
    insights.push({
      type: sentimentChange > 0 ? 'positive' : 'warning',
      icon: sentimentChange > 0 ? '📈' : '📉',
      title: `Sentiment ${direction} ${percentage}% this week`,
      description: `Compared to last week, sentiment has ${direction} from ${(previousAvg * 100).toFixed(0)} to ${(recentAvg * 100).toFixed(0)}.`
    })
  }

  // Volume spike insight
  if (spikeDays.length > 0) {
    const [spikeDate, spikeCount] = spikeDays[0]
    const multiplier = (spikeCount / avgDaily).toFixed(1)
    insights.push({
      type: 'info',
      icon: '🔥',
      title: `Volume spike detected`,
      description: `${multiplier}x normal activity on ${new Date(spikeDate).toLocaleDateString()}. ${spikeCount} mentions recorded.`
    })
  }

  // Volume trend
  if (volumeChange > 0 && recentMentions.length >= 5) {
    insights.push({
      type: 'info',
      icon: '📊',
      title: `Mention volume increased`,
      description: `${volumeChange} more mentions this week compared to last week. Your brand visibility is growing.`
    })
  } else if (volumeChange < -5) {
    insights.push({
      type: 'info',
      icon: '📉',
      title: `Mention volume decreased`,
      description: `${Math.abs(volumeChange)} fewer mentions this week. Consider increasing marketing efforts.`
    })
  }

  // Source insight
  if (topSource) {
    const sourceName = topSource[0].replace('_', ' ')
    const sourcePercent = ((topSource[1] / total) * 100).toFixed(0)
    insights.push({
      type: 'info',
      icon: '📰',
      title: `Most active on ${sourceName}`,
      description: `${sourcePercent}% of mentions come from ${sourceName}. Focus engagement efforts here.`
    })
  }

  // Recent negative alert
  const recentNegative = recentMentions.filter(m => m.sentiment_label?.toLowerCase() === 'negative')
  if (recentNegative.length >= 3) {
    insights.push({
      type: 'alert',
      icon: '🚨',
      title: `${recentNegative.length} negative mentions this week`,
      description: `Monitor these closely for potential PR issues. Early response can prevent escalation.`
    })
  }

  const getCardStyle = (type: string) => {
    switch (type) {
      case 'positive':
        return 'bg-green-50 border-green-100'
      case 'warning':
        return 'bg-yellow-50 border-yellow-100'
      case 'alert':
        return 'bg-red-50 border-red-100'
      default:
        return 'bg-blue-50 border-blue-100'
    }
  }

  return (
    <div className="space-y-3">
      {insights.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Not enough data for insights yet. Check back after more mentions are collected.
        </p>
      ) : (
        insights.map((insight, index) => (
          <div
            key={index}
            className={`flex items-start gap-3 p-4 rounded-lg border ${getCardStyle(insight.type)}`}
          >
            <span className="text-xl flex-shrink-0">{insight.icon}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-zinc-900">{insight.title}</p>
              <p className="text-xs text-zinc-600 mt-1">{insight.description}</p>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
