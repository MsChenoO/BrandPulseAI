'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface SentimentDataPoint {
  date: string
  average_score: number
  mention_count: number
  positive_count: number
  neutral_count: number
  negative_count: number
}

interface SentimentTrendChartProps {
  data: SentimentDataPoint[]
}

export function SentimentTrendChart({ data }: SentimentTrendChartProps) {
  // Transform data for chart
  const chartData = data.map((point) => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    sentiment: parseFloat((point.average_score * 100).toFixed(1)), // Convert -1 to 1 → -100 to 100
    mentions: point.mention_count,
    positive: point.positive_count,
    neutral: point.neutral_count,
    negative: point.negative_count,
  }))

  return (
    <div className="space-y-4">
      {/* Sentiment Score Over Time */}
      <div>
        <h3 className="text-sm font-medium text-zinc-700 mb-3">Sentiment Score Over Time</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
            <XAxis
              dataKey="date"
              stroke="#71717a"
              fontSize={12}
            />
            <YAxis
              stroke="#71717a"
              fontSize={12}
              domain={[-100, 100]}
              ticks={[-100, -50, 0, 50, 100]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e4e4e7',
                borderRadius: '8px',
                fontSize: '12px'
              }}
              formatter={(value: number) => [`${value.toFixed(1)}`, 'Sentiment']}
            />
            <Line
              type="monotone"
              dataKey="sentiment"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Mention Volume Over Time */}
      <div>
        <h3 className="text-sm font-medium text-zinc-700 mb-3">Mention Volume</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
            <XAxis
              dataKey="date"
              stroke="#71717a"
              fontSize={12}
            />
            <YAxis
              stroke="#71717a"
              fontSize={12}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e4e4e7',
                borderRadius: '8px',
                fontSize: '12px'
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Line
              type="monotone"
              dataKey="positive"
              stroke="#16a34a"
              strokeWidth={2}
              name="Positive"
            />
            <Line
              type="monotone"
              dataKey="neutral"
              stroke="#71717a"
              strokeWidth={2}
              name="Neutral"
            />
            <Line
              type="monotone"
              dataKey="negative"
              stroke="#dc2626"
              strokeWidth={2}
              name="Negative"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
