import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { Card, CardHeader } from './Card'
import { ChartTooltip } from '../utils'

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

export function OutcomeChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }))
  const total = chartData.reduce((sum, d) => sum + d.value, 0)

  return (
    <Card delay={0.4}>
      <CardHeader title="Call Summary" subtitle="Distribution across all calls" />
      <div className="outcome-body">
        <div className="outcome-pie-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={52}
                outerRadius={78}
                paddingAngle={3}
                dataKey="value"
                strokeWidth={0}
              >
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={OUTCOME_COLORS[entry.name] || '#9ca3b4'} />
                ))}
              </Pie>
              <Tooltip
                content={
                  <ChartTooltip
                    labelFormatter={(name) => OUTCOME_LABELS[name] || name}
                    valueSuffix="calls"
                  />
                }
              />
              <text
                x="50%"
                y="48%"
                textAnchor="middle"
                className="fill-surface-900 font-display"
                style={{ fontSize: '24px', fontWeight: 700 }}
              >
                {total}
              </text>
              <text
                x="50%"
                y="60%"
                textAnchor="middle"
                className="fill-surface-400 font-mono"
                style={{ fontSize: '10px' }}
              >
                TOTAL
              </text>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="outcome-legend">
          {chartData.map((entry) => (
            <div key={entry.name} className="outcome-legend-row">
              <div className="outcome-legend-left">
                <div
                  className="outcome-dot"
                  style={{ backgroundColor: OUTCOME_COLORS[entry.name] || '#9ca3b4' }}
                />
                <span className="outcome-label">
                  {OUTCOME_LABELS[entry.name] || entry.name}
                </span>
              </div>
              <div className="outcome-legend-right">
                <span className="outcome-count">{entry.value}</span>
                <span className="outcome-pct">
                  {total > 0 ? Math.round((entry.value / total) * 100) : 0}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}