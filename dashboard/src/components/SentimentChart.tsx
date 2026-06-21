import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Card, CardHeader } from './Card'

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#10b981',
  neutral: '#f59e0b',
  negative: '#f43f5e',
}

const OUTCOME_LABELS: Record<string, string> = {
  booked: 'Booked',
  rejected: 'Rejected',
  no_match: 'No Match',
  no_agreement: 'No Agree.',
  not_authorized: 'Not Auth.',
}

interface Props {
  data: Record<string, Record<string, number>>
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string }) {
  if (!active || !payload?.length) return null
  const total = payload.reduce((s: number, e: any) => s + (e.value || 0), 0)
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-label">
        {OUTCOME_LABELS[label || ''] || label}
      </p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="chart-tooltip-row">
          <div className="flex items-center gap-2">
            <div className="chart-tooltip-dot" style={{ backgroundColor: entry.color }} />
            <span className="chart-tooltip-name capitalize">{entry.dataKey}</span>
          </div>
          <span className="chart-tooltip-val">{entry.value}</span>
        </div>
      ))}
      <div className="chart-tooltip-divider">
        <span className="chart-tooltip-total">Total: {total}</span>
      </div>
    </div>
  )
}

export function SentimentChart({ data }: Props) {
  const chartData = Object.entries(data).map(([outcome, sentiments]) => ({
    outcome,
    positive: sentiments.positive || 0,
    neutral: sentiments.neutral || 0,
    negative: sentiments.negative || 0,
  }))

  chartData.sort(
    (a, b) =>
      b.positive + b.neutral + b.negative - (a.positive + a.neutral + a.negative)
  )

  return (
    <Card delay={0.5}>
      <CardHeader title="Sentiment Summary" subtitle="Carrier tone breakdown per call result" />
      <div className="card-body-chart">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="outcome"
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => OUTCOME_LABELS[v] || v}
              dy={8}
            />
            <YAxis axisLine={false} tickLine={false} dx={-8} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f1f3f7' }} />
            <Legend
              verticalAlign="top"
              height={30}
              formatter={(value: string) => (
                <span className="legend-label capitalize">{value}</span>
              )}
            />
            <Bar dataKey="positive" stackId="a" fill={SENTIMENT_COLORS.positive} radius={[0, 0, 0, 0]} />
            <Bar dataKey="neutral" stackId="a" fill={SENTIMENT_COLORS.neutral} radius={[0, 0, 0, 0]} />
            <Bar dataKey="negative" stackId="a" fill={SENTIMENT_COLORS.negative} radius={[4, 4, 0, 0]} barSize={32} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
