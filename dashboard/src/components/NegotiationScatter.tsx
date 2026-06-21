import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { Card, CardHeader } from './Card'
import { formatCurrency } from '../utils'

interface Props {
  data: Array<{ loadboard_rate: number; agreed_price: number }>
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: any[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  const savings = d.loadboard_rate - d.agreed_price
  const pct = ((savings / d.loadboard_rate) * 100).toFixed(1)
  return (
    <div className="scatter-tooltip">
      <div className="scatter-tooltip-row">
        <span className="scatter-tooltip-label">Loadboard</span>
        <span className="scatter-tooltip-val">
          {formatCurrency(d.loadboard_rate)}
        </span>
      </div>
      <div className="scatter-tooltip-row">
        <span className="scatter-tooltip-label">Agreed</span>
        <span className="scatter-tooltip-val--green">
          {formatCurrency(d.agreed_price)}
        </span>
      </div>
      <div className="scatter-tooltip-divider">
        <span className="scatter-tooltip-label">Saved</span>
        <span className="scatter-tooltip-saved">
          {formatCurrency(savings)} ({pct}%)
        </span>
      </div>
    </div>
  )
}

export function NegotiationScatter({ data }: Props) {
  const allValues = data.flatMap((d) => [d.loadboard_rate, d.agreed_price])
  const min = Math.floor(Math.min(...allValues) * 0.9)
  const max = Math.ceil(Math.max(...allValues) * 1.05)

  return (
    <Card delay={0.35}>
      <CardHeader
        title="Negotiation Performance"
        subtitle="Agreed price vs. loadboard rate — below diagonal = savings"
      />
      <div className="card-body-chart">
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="loadboard_rate"
              name="Loadboard Rate"
              domain={[min, max]}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              label={{
                value: 'Loadboard Rate',
                position: 'insideBottom',
                offset: -2,
                style: { fontSize: 10, fontFamily: 'IBM Plex Mono', fill: '#9ca3b4' },
              }}
            />
            <YAxis
              type="number"
              dataKey="agreed_price"
              name="Agreed Price"
              domain={[min, max]}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              label={{
                value: 'Agreed Price',
                angle: -90,
                position: 'insideLeft',
                offset: 20,
                style: { fontSize: 10, fontFamily: 'IBM Plex Mono', fill: '#9ca3b4' },
              }}
            />
            <ReferenceLine
              segment={[
                { x: min, y: min },
                { x: max, y: max },
              ]}
              stroke="#d1d5de"
              strokeDasharray="6 4"
              strokeWidth={1.5}
              label={{
                value: '1:1',
                position: 'insideTopLeft',
                style: { fontSize: 10, fontFamily: 'IBM Plex Mono', fill: '#9ca3b4' },
              }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter
              data={data}
              fill="#10b981"
              fillOpacity={0.7}
              strokeWidth={1.5}
              stroke="#059669"
              r={5}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}