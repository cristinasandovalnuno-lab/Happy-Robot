import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import type { MetricsResponse } from './types'
import { KpiCards } from './components/KpiCards'
import { FunnelChart } from './components/FunnelChart'
import { NegotiationScatter } from './components/NegotiationScatter'
import { CallVolumeChart } from './components/CallVolumeChart'
import { SavingsChart } from './components/SavingsChart'
import { OutcomeChart } from './components/OutcomeChart'
import { SentimentChart } from './components/SentimentChart'
import { TopLanes } from './components/TopLanes'
import { BookedRoutesMap } from './components/BookedRoutesMap'
import { RecentBookingsTable } from './components/RecentBookingsTable'
import { LoadsUtilization } from './components/LoadsUtilization'

const API_BASE = import.meta.env.VITE_API_URL || ''
const API_KEY = import.meta.env.VITE_API_KEY || ''

type Tab = 'metrics' | 'loads'

const tabs: { key: Tab; label: string }[] = [
  { key: 'metrics', label: 'Metrics' },
  { key: 'loads', label: 'Loads' },
]

export default function App() {
  const [data, setData] = useState<MetricsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('metrics')

  useEffect(() => {
    fetch(`${API_BASE}/metrics`, {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {},
      })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(setData)
      .catch((err) => {
        setError(err.message || 'Failed to load metrics')
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="page-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="spinner"
        />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="page-center">
        <p className="error-text">{error || 'No data available'}</p>
      </div>
    )
  }

  const outcomeKeys = Object.keys(data.calls_by_outcome)

  return (
    <div className="page">
      {/* Header */}
      <header className="page-header">
        <div className="page-container">
          <div className="header-row">
            <div className="header-brand">
              <div className="header-logo">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <div>
                <h1 className="header-title">Acme Logistics</h1>
                <p className="header-subtitle">Command Center</p>
              </div>
            </div>
            <div className="header-actions">
              <span className="badge-live">
                <span className="badge-live-dot" />
                LIVE
              </span>
              <span className="header-date">
                {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div className="tab-bar">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`tab-btn ${activeTab === tab.key ? 'tab-btn--active' : 'tab-btn--inactive'}`}
              >
                {tab.label}
                {activeTab === tab.key && (
                  <motion.div layoutId="tab-indicator" className="tab-indicator" />
                )}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="page-main">
        <AnimatePresence mode="wait">
          {activeTab === 'metrics' && (
            <motion.div
              key="metrics"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <KpiCards data={data} />
              <div className="grid-2col">
                <FunnelChart data={data.call_funnel} />
                <NegotiationScatter data={data.negotiation_details} />
              </div>
              <div className="grid-2col">
                <CallVolumeChart data={data.call_volume_over_time} outcomes={outcomeKeys} />
                <SavingsChart data={data.savings_over_time} />
              </div>
              <div className="grid-2col">
                <OutcomeChart data={data.calls_by_outcome} />
                <SentimentChart data={data.sentiment_by_outcome} />
              </div>
            </motion.div>
          )}

          {activeTab === 'loads' && (
            <motion.div
              key="loads"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-stretch">
                <div className="lg:col-span-3 flex">
                  <BookedRoutesMap data={data.booked_routes} />
                </div>
                <div className="lg:col-span-2 flex">
                  <TopLanes data={data.top_lanes} />
                </div>
              </div>
              <LoadsUtilization data={data.loads_utilization} />
              <RecentBookingsTable data={data.recent_bookings} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}