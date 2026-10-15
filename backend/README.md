# SEC-seeded investor database

This backend only creates institution records for CIKs supplied in a seed CSV.
It uses the SEC company submissions endpoint to inspect the most recent
`13F-HR` or `13F-HR/A` in each company's recent filing arrays, checking SEC
referenced history chunks if no 13F appears in the recent window.
`is_active` means that filing date falls within the configured 12–24 month
window; it does not establish that an institution is currently investing.
The status is null if the filing history could not be completely inspected.
The SEC submissions API provides filing metadata, not total AUM, check size,
or target sectors. Those investor profile fields therefore remain `null` and
are never inferred from filing activity.

## Local commands

From the repository root:

```sh
python -m pip install -r backend/requirements.txt
python -m backend.pipeline
uvicorn backend.app:app --reload
python -m unittest discover -s backend/tests -v
```

The API reads `data/processed/sample_investors.csv`, produced by the pipeline.
With no seed file (or an empty seed CSV), the pipeline still creates this CSV
with its header row only. Create `data/seeds/seed_ciks.csv` with a `cik` header and
one SEC CIK per row, or configure another file using `SEED_CIK_CSV`. A CSV
without a header is also accepted when CIKs occupy its first column.
See [`data/seeds/README.md`](../data/seeds/README.md) for the exact seed schema,
an example, and provenance guidance. No seed records are shipped.

Before a request is made to SEC, set `SEC_USER_AGENT` to a truthful,
descriptive application identity and a real contact address. The project does
not invent or ship contact details. For example, provide your own value in
your shell environment:

```sh
export SEC_USER_AGENT="Example Research Database admin@example.org"
```

Collector configuration:

| Variable | Default | Meaning |
| --- | --- | --- |
| `SEED_CIK_CSV` | `data/seeds/seed_ciks.csv` | Seed CIK input CSV |
| `OUTPUT_CSV` | `data/processed/sample_investors.csv` | Generated dataset |
| `INVESTORS_CSV` | `data/processed/sample_investors.csv` | CSV served by the API |
| `ACTIVE_MONTHS` | `24` | Filing recency threshold (must be 12–24) |
| `SEC_USER_AGENT` | required for SEC requests | Identifies this client to SEC |
| `CORS_ORIGINS` | empty | Optional comma-separated browser origins allowed for GET API requests |

The same options can be passed to `python -m backend.pipeline` as `--seeds`,
`--output`, and `--active-months`.

## API contract

- `GET /api/investors` → `{"investors": [...]}`. Each Investor has `cik`,
  `name`, `latest_filing_date`, `latest_filing_form`, `is_active`, `source_url`,
  `aum_usd`, `check_size_min_usd`, `check_size_max_usd`, and `target_sectors`.
  The profile fields unsupported by the submissions endpoint are `null`.
- `GET /api/metrics` → record and active counts; verified records and accuracy
  are zero/`null` because there is no independent verification sample.
  Completeness is based on the presence of identity, filing, and source fields,
  capped at 95% until an independent sample is recorded. `as_of` is the
  reporting date, not a filing date.
- `GET /api/scaling` → a linear planning scenario, not a forecast or quote.
  `SCALING_TARGET_RECORDS` defaults to `10000`; `COST_PER_RECORD_USD` defaults
  to `0.0` because no costs are known. Supply a planning unit cost to calculate
  a nonzero scenario.

The exported CSV includes `accession_number` and `filing_url` in addition to
the public Investor fields, so the filing metadata is traceable. `source_url`
links to the SEC submissions JSON response for that seeded CIK.

## Tests

Tests use synthetic submissions payloads and do not make network requests.
The collector has bounded retries for transient SEC failures, validates
submissions JSON and CIKs, skips unusable individual seed records while
logging the failure, and writes the CSV atomically.
