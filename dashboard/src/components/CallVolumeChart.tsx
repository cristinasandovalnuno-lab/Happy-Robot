import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Card, CardHeader } from './Card'
import { formatDate } from '../utils'

interface Props {
  data: Array<{ date: string; count: number; [key: string]: string | number }>
  outcomes: string[]
}

const OUTCOME_COLORS: Record<string, string> = {
  booked: '#10b981',
  rejected: '#f43f5e',
  no_match: '#f59e0b',
  no_agreement: '#6366f1',
  not_authorized: '#9ca3b4',
}

const OUTCOME_LABELS: Record<string, string> = {
  booked: 'Booked',
  rejected: 'Rejected',
  no_match: 'No Match',
  no_agreement: 'No Agreement',
  not_authorized: 'Not Authorized',
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string }) {
  if (!active || !payload?.length) return null
  const displayLabel = label ? formatDate(label) : ''
  return (
    <div className="chart-tooltip">
      {displayLabel && (
        <p className="chart-tooltip-label">{displayLabel}</p>
      )}
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="chart-tooltip-row">
          <div className="flex items-center gap-2">
            <div className="chart-tooltip-dot" style={{ backgroundColor: entry.color }} />
            <span className="chart-tooltip-name">
              {OUTCOME_LABELS[entry.dataKey] || entry.dataKey}
            </span>
          </div>
          <span className="chart-tooltip-val">{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

export function CallVolumeChart({ data, outcomes }: Props) {
  const orderedOutcomes = ['not_authorized', 'no_match', 'no_agreement', 'rejected', 'booked']
    .filter((o) => outcomes.includes(o))

  return (
    <Card delay={0.35} className="overflow-hidden">
      <CardHeader title="Call Volume" subtitle="Inbound carrier calls by outcome over time" />
      <div className="card-body-chart">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              {orderedOutcomes.map((outcome) => (
                <linearGradient key={outcome} id={`grad-${outcome}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={OUTCOME_COLORS[outcome]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={OUTCOME_COLORS[outcome]} stopOpacity={0.05} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              axisLine={false}
              tickLine={false}
              dy={8}
            />
            <YAxis axisLine={false} tickLine={false} dx={-8} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              height={30}
              formatter={(value: string) => (
                <span className="legend-label">
                  {OUTCOME_LABELS[value] || value}
                </span>
              )}
            />
            {orderedOutcomes.map((outcome) => (
              <Area
                key={outcome}
                type="monotone"
                dataKey={outcome}
                stackId="1"
                stroke={OUTCOME_COLORS[outcome]}
                strokeWidth={1.5}
                fill={`url(#grad-${outcome})`}
                dot={false}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}