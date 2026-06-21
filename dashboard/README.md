# Carrier Sales Dashboard

Standalone, Dockerized operations dashboard (React + Vite + TypeScript)
reading from the `GET /metrics` endpoint of the middleware, which
itself reads and aggregates `calls_log` from Twin (HappyRobot's
native data layer) server-side.

## Why an external dashboard

A native HappyRobot App ("Carrier Ops Console") was also built for
this project, using the platform's Apps + Twin + OAuth login flow
end-to-end. It works correctly when accessed at its HappyRobot-managed
public URL. However, the engagement also requires the solution to be
"containerized (Docker) and deployable with a single command to a
cloud environment of the customer's choice" — and HappyRobot's App
login flow is designed to validate against the App's own registered
public domain, not an arbitrary self-hosted origin (confirmed through
direct testing: no redirect-URL allowlist setting was found in the
available App configuration, and the platform's own "How an app
works" documentation doesn't describe one as a core concept).

This standalone dashboard exists to unambiguously satisfy the literal
Docker/single-command/any-cloud requirement, using the same simple
`x-api-key` authentication pattern already used by every other
middleware endpoint — no platform-specific login dependency. The
native App remains available as a secondary, fully-functional
HappyRobot-native artifact.

## What it shows

- KPI cards (total calls, bookings, booking rate, avg. negotiation
  rounds)
- Call funnel (incoming → authorized → matched → booked)
- Call volume over time, broken down by outcome
- Outcome distribution (booked / rejected / no_match / no_agreement)
- Carrier sentiment, cross-tabulated by outcome
- Top booked lanes
- Booked routes (origin → destination)
- Recent bookings table

Note: `total_savings`, `avg_discount_pct`, and `cost_over_time` are
always 0/empty — the `calls_log` Twin table in this project does not
track `loadboard_rate` per call (descoped during development; see
`middleware/README.md`), so there's no source data for these specific
fields. Everything else reflects real data.

## Configuration

```bash
cp .env.example .env
```

Edit `.env` with your real middleware API URL and key:

```
VITE_API_URL=https://<your-api-id>.execute-api.<region>.amazonaws.com/prod
VITE_API_KEY=<your real x-api-key value>
```

## Running (single command)

```bash
docker compose up --build
```

Open `http://localhost:8080`.

Build is a two-stage Docker image: Node builds the static Vite bundle
(with `VITE_API_URL`/`VITE_API_KEY` baked in at build time, since
Vite env vars are embedded into the client bundle, not read at
runtime), then nginx serves the static files. `nginx.conf` includes
the standard SPA fallback (`try_files ... /index.html`) so client-side
routing doesn't 404 on refresh.

## Structure

```
dashboard/
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── .env.example
├── package.json
└── src/
    ├── App.tsx              # fetches GET /metrics, renders tabs
    ├── types.ts             # MetricsResponse shape
    └── components/          # KpiCards, charts, tables, map
```
