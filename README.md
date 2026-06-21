# HappyRobot Logistics — Inbound Carrier Sales

End-to-end build for the HappyRobot FDE challenge: an inbound voice
agent that verifies a carrier's FMCSA authority, searches and books
loads against a legacy TMS, negotiates rate within a hidden ceiling,
and surfaces every call on an operational dashboard.

```
happyrobot-carrier-sales/
├── README.md                 
├── GIT_SETUP.md
├── middleware/                 AWS Lambda + API Gateway (SAM)
│   ├── README.md              detailed backend docs (architecture, design decisions)
│   ├── TESTING.md             4-layer test guide, no HappyRobot agent needed
│   ├── template.yaml           SAM template: API Gateway + Lambdas, no external database
│   ├── src/
│   │   ├── common/             TMS wire protocol codec/client, FMCSA client (+ mock), negotiation logic, config, HTTP helpers
│   │   ├── verify_carrier/     POST /carrier/verify
│   │   ├── search_loads/       POST /loads/search
│   │   ├── get_load/           GET  /loads/{load_id}
│   │   ├── book_load/          POST /loads/{load_id}/book
│   │   ├── negotiate/          POST /negotiate
│   │   └── metrics/            GET  /metrics — reads & aggregates Twin's calls_log
│   ├── scripts/                 standalone test scripts (no AWS, no Docker)
│   ├── tests/                   pytest unit tests (codec + negotiation logic)
│   └── events/                  sample API Gateway events for `sam local invoke`
└── dashboard/                  Standalone Docker dashboard (React + Vite + nginx)
    ├── README.md
    ├── Dockerfile
    ├── docker-compose.yml
    ├── nginx.conf
    ├── .env.example
    └── src/
```

## What this covers

- **FMCSA verification** (`POST /carrier/verify`) — confirmed working
  against the real QCMobile API from AWS infrastructure (the API
  blocked requests from a home/residential IP during local testing,
  not from AWS — see `middleware/README.md` for the investigation).
- **TMS integration** (`search_loads`, `get_load`, `book_load`) against
  a legacy line-oriented TCP protocol, with explicit handling for all 4
  documented fault categories (timeout, partial response, malformed
  response, delayed termination) and bounded retries on idempotent
  reads only. `book_load` deliberately does NOT auto-retry, to avoid
  double-booking risk on transient TMS faults — see the comment block
  in `src/book_load/app.py`, including how `ALREADY_BOOKED` is treated
  as a success signal on a follow-up attempt.
- **Negotiation** (`POST /negotiate`) — the rate ceiling (`max_rate`)
  never leaves the Lambda; the agent only ever receives accept /
  counter / reject, capped at 3 rounds. Confirmed in live voice
  testing, including under direct adversarial pressure to disclose the
  ceiling.

## Data layer and operational UI

Call activity is captured using HappyRobot's native **Twin** database
(a per-org Postgres instance with a REST gateway) — there is no
DynamoDB or other external database anywhere in this project:

- Normal call outcomes (`outcome`, `carrier_sentiment`,
  `negotiation_rounds`, `agreed_price`, origin/destination, etc.) are
  written to Twin's `calls_log` table via a native "Write to Twin"
  workflow node, immediately after the call's `Extract` step — no
  custom Lambda involved in writing this data.
- A `carrier_roster` table (also in Twin) maps `mc_number` to
  `registered_phone_number`, intended to be read via a native "Read
  from Twin" node for the OTP step (see "Still to do" below — the OTP
  flow itself could not be fully tested end-to-end in this engagement
  due to missing SMS-sending credentials).

**Two operational UIs exist for this project:**

1. **A native HappyRobot App** ("Carrier Ops Console"), built with
   the platform's Apps + Twin integration, fully functional at its
   HappyRobot-managed public URL.
2. **The `dashboard/` in this repo** — a standalone, Dockerized
   React dashboard, reading from the middleware's `GET /metrics`
   endpoint (which itself reads and aggregates Twin's `calls_log`
   server-side). This exists specifically to satisfy the engagement's
   literal requirement that the solution be "containerized and
   deployable with a single command to a cloud environment of the
   customer's choice" — HappyRobot's App login flow is designed to
   validate against the App's own registered public domain, not an
   arbitrary self-hosted origin (confirmed through direct testing; see
   `dashboard/README.md` for the full reasoning).

Both read the same underlying Twin data; they are complementary, not
redundant — the native App best satisfies the "prefer native tooling"
guidance, while `dashboard/` best satisfies the literal Docker/
single-command/any-cloud deployment requirement.

## Deploying the middleware (AWS SAM)

Requires the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
and configured AWS credentials.

```bash
cd middleware
sam build
sam deploy --guided
```

You'll be prompted for 7 parameters: `TmsHost`, `TmsPort`,
`TmsAuthToken`, `FmcsaApiKey`, `FmcsaMode` (`live` or `mock`),
`TwinGatewayUrl`, and `TwinOrgId` (the last two from Settings → Twin
Database in the HappyRobot platform). All secrets use CloudFormation
`NoEcho`, never hardcoded in source.

On success, `sam deploy` prints the `ApiUrl` and `ApiKeyId` outputs.
Get the actual API key value with:

```bash
aws apigateway get-api-key --api-key <ApiKeyId> --include-value
```

Configure that base URL + API key (header `x-api-key`) as the
tool/webhook target for each action node in the HappyRobot workflow
(verify, search, get, book, negotiate), and as the `VITE_API_URL` /
`VITE_API_KEY` values for `dashboard/`.

See `middleware/TESTING.md` for a 4-layer test progression (raw
credentials → protocol codec unit tests → SAM local → deployed AWS)
that doesn't require the HappyRobot agent at all.

## Running the dashboard (Docker)

```bash
cd dashboard
cp .env.example .env
# edit .env: paste the real ApiUrl + API key from the sam deploy output
docker compose up --build
```

Open `http://localhost:8080`. See `dashboard/README.md` for details.

## Security notes

- No credentials are hardcoded anywhere in this repo; `.env` files are
  gitignored.
- TMS and FMCSA tokens are CloudFormation `NoEcho` parameters and
  Lambda environment variables only.
- Every middleware endpoint requires `x-api-key` (API Gateway usage
  plan), including `dashboard`'s read access via `/metrics`.
- The rate ceiling (`max_rate`/`MAX_BUY`) is stripped server-side
  before any response leaves the Lambdas — the agent (and therefore the
  carrier) never sees it directly or indirectly. Confirmed resistant
  to direct adversarial pressure in live voice testing.
- A custom real-time classifier (`security_pressure`) flags carrier
  attempts to extract the rate ceiling or bypass OTP verification,
  for ops review.


## Next steps

- **Live transfer to a senior representative.** The handoff after a
  successful booking is currently simulated by the agent verbally —
  next step is wiring this to an actual live transfer, replacing the
  simulated handoff entirely.
- **Populate `carrier_roster` with real phone numbers at scale.**
  FMCSA's QCMobile API (used for authority verification) does not
  return a phone number field — confirmed by inspecting every field in
  its response and reviewing all 9 documented QCMobile endpoints, none
  of which expose carrier contact information. The OTP step therefore
  depends on the brokerage's own carrier roster as the source of
  truth for registered phone numbers (the brokerage already manages a
  network of known carriers, per the engagement brief). Before
  production rollout, this table needs to be populated from the
  brokerage's real carrier database — likely a bulk import keyed by
  MC number — rather than the handful of test entries currently
  seeded for this proof of concept.

