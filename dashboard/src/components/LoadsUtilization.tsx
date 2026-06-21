import { motion } from 'motion/react'
import { Card } from './Card'

interface Props {
  data: { total_loads: number; booked: number }
}

export function LoadsUtilization({ data }: Props) {
  const pct = data.total_loads > 0 ? Math.round((data.booked / data.total_loads) * 100) : 0
  const available = data.total_loads - data.booked

  return (
    <Card delay={0.45}>
      <div className="utilization-body">
        <div className="utilization-header">
          <div>
            <h3 className="card-title">Loads Utilization</h3>
            <p className="card-subtitle">
              {data.booked} of {data.total_loads} loads booked
            </p>
          </div>
          <div className="utilization-legend">
            <div className="utilization-legend-item">
              <div className="utilization-dot--booked" />
              <span className="utilization-legend-text">Booked ({data.booked})</span>
            </div>
            <div className="utilization-legend-item">
              <div className="utilization-dot--available" />
              <span className="utilization-legend-text">Available ({available})</span>
            </div>
          </div>
        </div>
        <div className="utilization-bar-bg">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 1, delay: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="utilization-bar-fill"
          />
        </div>
        <div className="utilization-footer">
          <span className="utilization-bound">0%</span>
          <span className="utilization-pct">{pct}% utilized</span>
          <span className="utilization-bound">100%</span>
        </div>
      </div>
    </Card>
  )
}