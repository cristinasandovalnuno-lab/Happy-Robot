import { motion } from 'motion/react'
import type { MetricsResponse } from '../types'
import { formatCurrency } from '../utils'

interface KpiItem {
  label: string
  value: string
  sub?: string
  color: string
  icon: keyof typeof ICONS
}

const ICONS: Record<string, string> = {
  check: 'M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3',
  package: 'M16.5 9.4l-9-5.19M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z',
  dollar: 'M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6',
  trend: 'M23 6l-9.5 9.5-5-5L1 18M17 6h6v6',
  repeat: 'M17 1l4 4-4 4M3 11V9a4 4 0 014-4h14M7 23l-4-4 4-4M21 13v2a4 4 0 01-4 4H3',
  phone: 'M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.362 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0122 16.92z',
}

function Icon({ name }: { name: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d={ICONS[name]} />
    </svg>
  )
}

export function KpiCards({ data }: { data: MetricsResponse }) {
  const kpis: KpiItem[] = [
    {
      label: 'Booking Rate',
      value: `${data.booking_rate}%`,
      sub: 'of all calls',
      color: 'bg-emerald-50 text-emerald-600',
      icon: 'check',
    },
    {
      label: 'Total Bookings',
      value: data.total_bookings.toLocaleString(),
      sub: 'loads booked',
      color: 'bg-indigo-50 text-indigo-600',
      icon: 'package',
    },
    {
      label: 'Total Savings',
      value: formatCurrency(data.total_savings),
      sub: 'vs. loadboard rates',
      color: 'bg-teal-50 text-teal-600',
      icon: 'dollar',
    },
    {
      label: 'Avg Discount',
      value: `${data.avg_discount_pct}%`,
      sub: 'from loadboard rate',
      color: 'bg-amber-50 text-amber-600',
      icon: 'trend',
    },
    {
      label: 'Avg Rounds',
      value: data.avg_negotiation_rounds.toFixed(1),
      sub: 'to close deal',
      color: 'bg-rose-50 text-rose-600',
      icon: 'repeat',
    },
    {
      label: 'Total Calls',
      value: data.total_calls.toLocaleString(),
      sub: 'inbound carrier calls',
      color: 'bg-sky-50 text-sky-600',
      icon: 'phone',
    },
  ]

  return (
    <div className="kpi-grid">
      {kpis.map((kpi, i) => (
        <motion.div
          key={kpi.label}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: i * 0.08, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="kpi-card group"
        >
          <div className="kpi-content">
            <div className="kpi-text">
              <p className="kpi-label">{kpi.label}</p>
              <div>
                <p className="kpi-value">{kpi.value}</p>
                {kpi.sub && <p className="kpi-sub">{kpi.sub}</p>}
              </div>
            </div>
            <div className={`kpi-icon ${kpi.color}`}>
              <Icon name={kpi.icon} />
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}