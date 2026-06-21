import { ComposableMap, Geographies, Geography, Line, Marker } from 'react-simple-maps'
import { Card, CardHeader } from './Card'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json'

const CITY_COORDS: Record<string, [number, number]> = {
  'Chicago, IL': [-87.6298, 41.8781],
  'Detroit, MI': [-83.0458, 42.3314],
  'Dallas, TX': [-96.7970, 32.7767],
  'Houston, TX': [-95.3698, 29.7604],
  'Los Angeles, CA': [-118.2437, 34.0522],
  'Phoenix, AZ': [-112.0740, 33.4484],
  'Atlanta, GA': [-84.3880, 33.7490],
  'Nashville, TN': [-86.7816, 36.1627],
  'Miami, FL': [-80.1918, 25.7617],
  'Jacksonville, FL': [-81.6557, 30.3322],
  'Seattle, WA': [-122.3321, 47.6062],
  'Portland, OR': [-122.6765, 45.5152],
  'Denver, CO': [-104.9903, 39.7392],
  'Kansas City, MO': [-94.5786, 39.0997],
  'New York, NY': [-74.0060, 40.7128],
  'Philadelphia, PA': [-75.1652, 39.9526],
  'Minneapolis, MN': [-93.2650, 44.9778],
  'Milwaukee, WI': [-87.9065, 43.0389],
  'San Antonio, TX': [-98.4936, 29.4241],
  'El Paso, TX': [-106.4850, 31.7619],
  'Columbus, OH': [-82.9988, 39.9612],
  'Indianapolis, IN': [-86.1581, 39.7684],
  'Memphis, TN': [-90.0490, 35.1495],
  'Little Rock, AR': [-92.2896, 34.7465],
  'Charlotte, NC': [-80.8431, 35.2271],
  'Richmond, VA': [-77.4360, 37.5407],
  'Sacramento, CA': [-121.4944, 38.5816],
  'Reno, NV': [-119.8138, 39.5296],
  'St. Louis, MO': [-90.1994, 38.6270],
}

interface Props {
  data: Array<{ origin: string; destination: string; count: number }>
}

export function BookedRoutesMap({ data }: Props) {
  const maxCount = Math.max(...data.map((r) => r.count), 1)

  const activeCities = new Set<string>()
  data.forEach((r) => {
    activeCities.add(r.origin)
    activeCities.add(r.destination)
  })

  return (
    <Card delay={0.45} className="overflow-hidden w-full">
      <CardHeader title="Booked Routes" subtitle="Origin-destination pairs for booked loads — thicker lines indicate more bookings on that lane" />
      <div className="map-body">
        <ComposableMap
          projection="geoAlbersUsa"
          projectionConfig={{ scale: 900 }}
          width={800}
          height={480}
          style={{ width: '100%', height: 'auto' }}
        >
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.properties?.name || geo.id}
                  geography={geo}
                  fill="#f1f3f7"
                  stroke="#d1d5de"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: 'none' },
                    hover: { outline: 'none', fill: '#e5e8ee' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>

          {data.map((route, i) => {
            const from = CITY_COORDS[route.origin]
            const to = CITY_COORDS[route.destination]
            if (!from || !to) return null
            const opacity = 0.2 + (route.count / maxCount) * 0.6
            const strokeWidth = 1 + (route.count / maxCount) * 2.5
            return (
              <Line
                key={`${route.origin}-${route.destination}-${i}`}
                from={from}
                to={to}
                stroke="#6366f1"
                strokeWidth={strokeWidth}
                strokeOpacity={opacity}
                strokeLinecap="round"
              />
            )
          })}

          {Array.from(activeCities).map((city) => {
            const coords = CITY_COORDS[city]
            if (!coords) return null
            return (
              <Marker key={city} coordinates={coords}>
                <circle r={3.5} fill="#4f46e5" stroke="#fff" strokeWidth={1.5} />
                <text
                  textAnchor="middle"
                  y={-8}
                  style={{
                    fontFamily: 'IBM Plex Mono, monospace',
                    fontSize: 8,
                    fill: '#4b5563',
                    fontWeight: 500,
                  }}
                >
                  {city.split(',')[0]}
                </text>
              </Marker>
            )
          })}
        </ComposableMap>
      </div>
    </Card>
  )
}