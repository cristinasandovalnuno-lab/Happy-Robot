import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardHeader } from './Card'
import { ChartTooltip } from '../utils'

function shortenLane(lane: string) {
  return lane
    .replace(/ -> /g, ' > ')
    .replace(/, [A-Z]{2}/g, '')
}

export function TopLanes({ data }: { data: Array<{ lane: string; count: number }> }) {
  const chartData = data.slice(0, 10).map((d) => ({
    ...d,
    short: shortenLane(d.lane),
  }))

  return (
    <Card delay={0.5} className="w-full flex flex-col">
      <CardHeader title="Top Lanes" subtitle="Most requested origin-destination pairs" />
      <div className="card-body-chart flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 10, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="short"
              width={140}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fontFamily: 'Outfit' }}
            />
            <Tooltip
              content={
                <ChartTooltip
                  labelFormatter={(_label, payload) =>
                    payload?.[0]?.payload?.lane ?? _label
                  }
                  valueSuffix="calls"
                />
              }
              cursor={{ fill: '#f1f3f7' }}
            />
            <Bar
              dataKey="count"
              fill="#6366f1"
              radius={[0, 6, 6, 0]}
              barSize={24}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}