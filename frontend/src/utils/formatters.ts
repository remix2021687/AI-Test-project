import type { Investor } from '../investors'

export function formatCurrency(value: number | null, compact = false): string {
  if (value === null || !Number.isFinite(value)) return 'Not reported'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
    notation: compact && Math.abs(value) >= 1_000_000 ? 'compact' : 'standard',
  }).format(value)
}

export function formatConfiguredCurrency(value: number | null, compact = false): string {
  return value === null ? 'Not configured' : formatCurrency(value, compact)
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value)
}

export function formatDate(value: string | null): string {
  if (!value) return 'Not reported'
  const date = new Date(`${value.slice(0, 10)}T00:00:00`)
  if (Number.isNaN(date.getTime())) return 'Not reported'
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

export function checkSizeLabel(investor: Investor): string {
  const { check_size_min_usd: min, check_size_max_usd: max } = investor
  if (min === null && max === null) return 'Not reported'
  if (min === null) return `Up to ${formatCurrency(max)}`
  if (max === null) return `${formatCurrency(min)}+`
  if (min === max) return formatCurrency(min)
  return `${formatCurrency(min)} – ${formatCurrency(max)}`
}

export function statusLabel(value: boolean | null): string {
  return value === null ? 'Unknown' : value ? 'Active' : 'Inactive'
}

export function statusClass(value: boolean | null): string {
  return value === null
    ? 'bg-[#fff6e8] text-[#9a6b2f] [&_i]:bg-[#d49a45]'
    : value
      ? 'bg-[#eaf7f0] text-[#23855e] [&_i]:bg-[#31a976]'
      : 'bg-[#f1f3f5] text-[#778292] [&_i]:bg-[#9ba4af]'
}

export function getAssumptionText(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'No assumptions provided.'
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return value.map((item) => typeof item === 'string' ? item : JSON.stringify(item)).join(' · ')
  }
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
