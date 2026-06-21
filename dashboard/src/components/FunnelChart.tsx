import { motion } from 'motion/react'
import { Card, CardHeader } from './Card'

interface FunnelStage {
  stage: string
  count: number
}

interface Props {
  data: FunnelStage[]
}

const STAGE_COLORS = [
  { bg: 'bg-indigo-100', fill: 'bg-brand-600', text: 'text-brand-600' },
  { bg: 'bg-indigo-100', fill: 'bg-indigo-500', text: 'text-indigo-500' },
  { bg: 'bg-indigo-100', fill: 'bg-indigo-400', text: 'text-indigo-400' },
  { bg: 'bg-emerald-100', fill: 'bg-emerald-500', text: 'text-emerald-500' },
]

export function FunnelChart({ data }: Props) {
  if (!data.length) return null
  const maxCount = data[0].count || 1

  return (
    <Card delay={0.3}>
      <CardHeader title="Conversion Funnel" subtitle="Carrier call pipeline from intake to booking" />
      <div className="funnel-body">
        {data.map((stage, i) => {
          const pct = Math.round((stage.count / maxCount) * 100)
          const colors = STAGE_COLORS[i] || STAGE_COLORS[0]
          const conversionFromPrev =
            i > 0 && data[i - 1].count > 0
              ? Math.round((stage.count / data[i - 1].count) * 100)
              : null

          return (
            <div key={stage.stage}>
              {conversionFromPrev !== null && (
                <div className="funnel-conversion">
                  <svg width="12" height="12" viewBox="0 0 12 12" className="text-surface-400">
                    <path d="M6 2v8M3 7l3 3 3-3" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span className="funnel-conversion-text">
                    {conversionFromPrev}% conversion
                  </span>
                </div>
              )}
              <div className="funnel-row">
                <div className="funnel-label">
                  <p className="funnel-label-text">{stage.stage}</p>
                </div>
                <div className={`funnel-bar-bg ${colors.bg}`}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.8, delay: 0.3 + i * 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
                    className={`funnel-bar-fill ${colors.fill}`}
                  />
                </div>
                <div className="funnel-count">
                  <span className={`funnel-count-text ${colors.text}`}>
                    {stage.count}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}