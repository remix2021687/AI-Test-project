# Reliable Investor Database

An evidence-first investor research dashboard with a Python SEC EDGAR collection
pipeline and a React/TypeScript frontend.

## Data scope and limitations

The initial collector is deliberately scoped to **configured CIKs** and the
filings exposed by the SEC EDGAR company submissions API. It is not a global
investor discovery service: EDGAR does not provide a complete directory of
venture capital firms, private equity firms, or family offices. A recent
Form 13F-HR is a signal of recent filing activity, not proof that a firm is
currently investing or that it is a VC/PE/family office.
Only records with a Form 13F-HR filed within the configured 12–24 month
window are exported. Stale or unverifiable filing histories are excluded.

EDGAR company submissions also do not establish total AUM, investment check
sizes, or target sectors. Those fields remain unknown unless separately
verified from a source and are never inferred from a 13F filing. In particular,
13F holdings value is not represented as total AUM. The dashboard shows
coverage and source-backed verification separately; it does not claim an
accuracy score until there are audited verification samples. The requested
95%+ accuracy is a quality target, not a seeded or guaranteed result.

## Project layout

```text
backend/                 SEC collection, parsing, validation, metrics, API
data/processed/          investor export and optional audited sample
data/seeds/              configured CIK list and input documentation
frontend/                Vite + React + TypeScript dashboard
backend/tests/           backend collector, API, and metrics tests
```

The dashboard uses Tailwind CSS utility classes and is split by responsibility
under `frontend/src/components/`:
`layout/` contains the shell/navigation pieces, `dashboard/` contains the metric
panels, `investors/` contains the search/filter/table UI, and `ui/` contains
shared feedback states. Data loading lives in `hooks/`, API types in
`investors.ts`, and formatting/filtering helpers in `utils/`.

## Requirements

- Python 3.11+
- Node.js 20+
- A descriptive SEC `User-Agent` containing an organization and contact email.
  Set it in `SEC_USER_AGENT`; do not use a made-up contact address.

The SEC APIs are public and do not require an API key. Respect SEC fair-access
limits and retain source filing URLs when using collected data.

## Local development

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
# Set SEC_USER_AGENT to your organization's name and real contact email.
python -m backend.pipeline
uvicorn backend.app:app --reload
```

Add CIKs to the seed file described in `data/seeds/README.md` before running a
collection. With no configured CIKs the pipeline writes a header-only CSV,
which is preferable to a fabricated demo dataset.
The activity window defaults to 24 months and can be set to 12–24 months with
`ACTIVE_MONTHS`.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The Vite development server proxies `/api` requests to `http://localhost:8000`.
For a separately hosted frontend, configure `VITE_API_BASE_URL` to the backend
origin at build time and allow that origin in the backend CORS configuration.

### Tests and checks

```bash
python -m pytest
cd frontend && npm test && npm run build
```

## API and dashboard

- `GET /api/investors` — collected investor records and their filing evidence.
- `GET /api/metrics` — record counts, completeness, and sample-backed accuracy
  (null when there is no verified sample).
- `GET /api/scaling` — a scenario estimate driven by explicit assumptions; it
  is not a quote or a measured cost. Set `SCALING_TARGET_RECORDS` and
  `COST_PER_RECORD_USD` to supply the scenario inputs; without a unit cost,
  cost values are explicitly unconfigured rather than shown as `$0`.

The dashboard supports sector and check-size filters when sourced values are
available. Missing fields are presented as unknown and are not silently
treated as zero.

To measure accuracy, add one row per manually reviewed field to
`data/processed/verification_sample.csv` with the CIK, field name, independently
verified value, HTTPS source URL, and verification date. The API compares those
values with the current dataset; it reports the percentage of matching field
checks and the number of distinct reviewed CIKs. An empty sample reports
accuracy as unmeasured, and checks for CIKs no longer in the active dataset are
ignored with a warning. See `data/processed/README.md` for the audit-file schema
and normalization rules.

## Data workflow and AI use

1. Curate CIK seeds; profile enrichment beyond EDGAR is not currently supported.
2. Collect filing metadata from SEC EDGAR with an identifying User-Agent.
3. Parse submissions and validate CIK format, filing recency, and provenance.
4. Export accepted records to `data/processed/sample_investors.csv`.
5. Review a sample against its original primary sources and record each checked
   value in `data/processed/verification_sample.csv`.
6. Use the dashboard to inspect the data and adjust the separate scaling
   assumptions for a planning scenario.

AI assistance may be used to implement and review the pipeline and interface.
It must not be treated as evidence for investor attributes or as a substitute
for inspecting SEC filings. Verify all material claims against the linked
primary source. No investor rows or accuracy results are generated just to
populate the UI.

## Deployment

The frontend is a static Vite application suitable for Vercel. Deploy the
backend as a Python ASGI service (for example, Render) with `uvicorn` as its
start command, set `SEC_USER_AGENT`, and configure the frontend's
`VITE_API_BASE_URL` to the deployed API origin. Set `CORS_ORIGINS` to the
deployed frontend origin when frontend and backend use different origins.
Never commit environment secrets or private research data.

For local containerized deployment, set `SEC_USER_AGENT` in the environment
and run `docker compose up --build`; the dashboard is available at
`http://localhost:8080`. The compose configuration mounts `./data` into the API
container so collected CSV output persists on the host.
