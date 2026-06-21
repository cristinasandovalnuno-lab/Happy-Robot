export function formatDate(dateStr: string) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatTimestamp(ts: string) {
  const d = new Date(ts)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatTime(ts: string) {
  const d = new Date(ts)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

export function formatCurrency(value: number) {
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`
  return `$${value.toLocaleString()}`
}

export function ChartTooltip({
  active,
  payload,
  label,
  labelFormatter,
  valueFormatter,
  valueSuffix,
}: {
  active?: boolean
  payload?: any[]
  label?: string
  labelFormatter?: (label: string, payload?: any[]) => string
  valueFormatter?: (value: number) => string
  valueSuffix?: string
}) {
  if (!active || !payload?.length) return null
  const rawLabel = label ?? payload[0].name ?? ''
  const displayLabel = labelFormatter ? labelFormatter(rawLabel, payload) : rawLabel
  const value = payload[0].value
  const displayValue = valueFormatter ? valueFormatter(value) : value
  return (
    <div className="chart-tooltip">
      {displayLabel && (
        <p className="chart-tooltip-label mb-1">{displayLabel}</p>
      )}
      <p className="text-lg font-display font-bold text-surface-900">
        {displayValue}{' '}
        {valueSuffix && (
          <span className="text-xs font-normal text-surface-400">{valueSuffix}</span>
        )}
      </p>
    </div>
  )
}
