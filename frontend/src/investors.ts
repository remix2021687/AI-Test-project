export interface Investor {
  cik: string
  name: string
  latest_filing_date: string | null
  latest_filing_form: string | null
  is_active: boolean | null
  source_url: string | null
  aum_usd: number | null
  check_size_min_usd: number | null
  check_size_max_usd: number | null
  target_sectors: string[]
}

export interface Metrics {
  total_records: number
  active_records: number
  verified_records: number
  accuracy_percent: number | null
  accuracy_sample_size: number
  completeness_percent: number
  as_of: string | null
}

export interface Scaling {
  current_records: number
  target_records: number
  cost_per_record_usd: number | null
  estimated_total_cost_usd: number | null
  assumptions: unknown
}

type DataRecord = Record<string, unknown>

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

function asRecord(value: unknown): DataRecord | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? value as DataRecord
    : null
}

function finiteNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function optionalString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function nullableString(record: DataRecord, key: string): string | null {
  const value = record[key]
  if (value !== null && typeof value !== 'string') {
    throw new Error(`The response is missing a valid "${key}" value.`)
  }
  return optionalString(value)
}

function nullableNumber(record: DataRecord, key: string): number | null {
  const value = record[key]
  if (value === null) return null
  const parsed = finiteNumber(value)
  if (parsed === null) throw new Error(`The response is missing a valid "${key}" value.`)
  return parsed
}

function optionalHttpUrl(value: unknown): string | null {
  const text = optionalString(value)
  if (!text) return null
  try {
    const url = new URL(text)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null
  } catch {
    return null
  }
}

function parseInvestor(value: unknown): Investor | null {
  const row = asRecord(value)
  if (!row || typeof row.cik !== 'string' || !/^\d{10}$/.test(row.cik) || typeof row.name !== 'string' || !row.name.trim()) {
    return null
  }
  if (!Array.isArray(row.target_sectors) || row.target_sectors.some((sector) => typeof sector !== 'string')) {
    throw new Error('The investor response contains an invalid target_sectors list.')
  }
  const active = row.is_active
  if (active !== null && typeof active !== 'boolean') {
    throw new Error('The investor response contains an invalid is_active value.')
  }

  return {
    cik: row.cik,
    name: row.name.trim(),
    latest_filing_date: nullableString(row, 'latest_filing_date'),
    latest_filing_form: nullableString(row, 'latest_filing_form'),
    is_active: active,
    source_url: optionalHttpUrl(row.source_url),
    aum_usd: nullableNumber(row, 'aum_usd'),
    check_size_min_usd: nullableNumber(row, 'check_size_min_usd'),
    check_size_max_usd: nullableNumber(row, 'check_size_max_usd'),
    target_sectors: row.target_sectors.filter((sector): sector is string => typeof sector === 'string'),
  }
}

function requireNumber(record: DataRecord, key: string): number {
  const value = finiteNumber(record[key])
  if (value === null) throw new Error(`The response is missing a valid "${key}" value.`)
  return value
}

async function getJson(path: string, signal: AbortSignal): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
    signal,
  })
  if (!response.ok) throw new Error(`The server responded with ${response.status}.`)
  return response.json() as Promise<unknown>
}

export async function fetchInvestors(signal: AbortSignal): Promise<Investor[]> {
  const payload = asRecord(await getJson('/api/investors', signal))
  if (!payload || !Array.isArray(payload.investors)) {
    throw new Error('The response did not contain an investors list.')
  }
  const investors = payload.investors.map(parseInvestor)
  if (investors.some((investor) => investor === null)) {
    throw new Error('The investor response contains a record without a valid CIK or name.')
  }
  return investors.filter((investor): investor is Investor => investor !== null)
}

export async function fetchMetrics(signal: AbortSignal): Promise<Metrics> {
  const payload = asRecord(await getJson('/api/metrics', signal))
  if (!payload) throw new Error('The metrics response is not valid.')
  return {
    total_records: requireNumber(payload, 'total_records'),
    active_records: requireNumber(payload, 'active_records'),
    verified_records: requireNumber(payload, 'verified_records'),
    accuracy_percent: nullableNumber(payload, 'accuracy_percent'),
    accuracy_sample_size: requireNumber(payload, 'accuracy_sample_size'),
    completeness_percent: requireNumber(payload, 'completeness_percent'),
    as_of: nullableString(payload, 'as_of'),
  }
}

export async function fetchScaling(signal: AbortSignal): Promise<Scaling> {
  const payload = asRecord(await getJson('/api/scaling', signal))
  if (!payload) throw new Error('The scaling response is not valid.')
  const costPerRecord = nullableNumber(payload, 'cost_per_record_usd')
  const estimatedTotal = nullableNumber(payload, 'estimated_total_cost_usd')
  if ((costPerRecord === null) !== (estimatedTotal === null)) {
    throw new Error('The scaling response has an incomplete cost estimate.')
  }
  return {
    current_records: requireNumber(payload, 'current_records'),
    target_records: requireNumber(payload, 'target_records'),
    cost_per_record_usd: costPerRecord,
    estimated_total_cost_usd: estimatedTotal,
    assumptions: payload.assumptions,
  }
}
