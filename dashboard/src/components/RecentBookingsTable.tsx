import { Card, CardHeader } from './Card'
import { formatTimestamp, formatTime } from '../utils'

interface Booking {
  timestamp: string
  carrier_name: string
  load_id: string
  origin: string
  destination: string
  agreed_price: number
  negotiation_rounds: number
}

interface Props {
  data: Booking[]
}

export function RecentBookingsTable({ data }: Props) {
  return (
    <Card delay={0.5} className="overflow-hidden">
      <CardHeader title="Recent Bookings" subtitle="Latest loads booked by carriers" />
      <div className="px-6 pb-5 overflow-x-auto">
        <table className="table">
          <thead>
            <tr className="table-head-row">
              <th className="table-th">Date</th>
              <th className="table-th">Load</th>
              <th className="table-th">Carrier</th>
              <th className="table-th">Lane</th>
              <th className="table-th--right">Price</th>
              <th className="table-th--right-last">Rounds</th>
            </tr>
          </thead>
          <tbody>
            {data.map((b, i) => (
              <tr
                key={`${b.load_id}-${b.timestamp}-${i}`}
                className="table-row"
              >
                <td className="table-cell">
                  <p className="table-date">{formatTimestamp(b.timestamp)}</p>
                  <p className="table-time">{formatTime(b.timestamp)}</p>
                </td>
                <td className="table-cell">
                  <span className="table-load-id">{b.load_id}</span>
                </td>
                <td className="table-cell">
                  <span className="table-carrier">{b.carrier_name}</span>
                </td>
                <td className="table-cell">
                  <span className="table-lane">
                    {b.origin.split(',')[0]} → {b.destination.split(',')[0]}
                  </span>
                </td>
                <td className="table-cell--right">
                  <span className="table-price">
                    ${b.agreed_price?.toLocaleString('en-US', { minimumFractionDigits: 0 })}
                  </span>
                </td>
                <td className="table-cell--right-last">
                  <span className="table-rounds">{b.negotiation_rounds}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}