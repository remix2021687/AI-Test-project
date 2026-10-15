# Seed CIK input

The collector discovers institution records **only** from the CIKs explicitly
listed in this CSV. The default location is
`data/seeds/seed_ciks.csv` (override it with `SEED_CIK_CSV` or `--seeds`).
The seed list must be curated by the operator; the collector does not determine
whether a CIK is a VC, PE firm, family office, or another kind of filer.
Only seeded CIKs with a Form 13F-HR filed within the configured 12–24 month
window are exported. CIKs with stale or unverifiable activity are excluded.

## Exact schema

The supported header-based schema is one required column named `cik`, with one
SEC Central Index Key (1–10 digits) per subsequent row. CIKs are zero-padded to
10 digits by the collector. Do not add institution names or profile attributes
to this input; names are taken from the SEC submissions response.

```csv
cik
```

No sample seed CSV or sample investor rows are included in the repository.
The pipeline creates `data/processed/sample_investors.csv` with its header
only when this input is missing or has no usable CIKs.

Headerless files are also accepted if each row's first column is a CIK. Invalid
rows are logged and skipped; duplicate CIKs are deduplicated.

## Provenance and optional investor metadata

Each seeded CIK is looked up at the SEC company submissions endpoint. The
resulting record's `source_url` identifies that SEC JSON resource; the export
also keeps the latest 13F accession number and SEC Archives filing URL for
traceability. A 13F filing is evidence of a reported holdings filing, not
independent verification that the entity is an active investor.

The submissions API does **not** provide total AUM, check size, or target
sectors. Those output fields remain null. Do not populate or infer them from
the existence, size, or contents of a 13F filing. If a future enrichment
process supplies such metadata from another source, it must preserve that
source's URL, retrieval date, and verification method per field before the
values are presented as sourced or verified. Such enrichment is not currently
supported by this seed CSV.
