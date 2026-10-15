import type { Investor } from '../investors'
import type { CheckSizeFilter } from '../types/dashboard'

export function checkSizeMatches(investor: Investor, filter: CheckSizeFilter): boolean {
  const min = investor.check_size_min_usd
  const max = investor.check_size_max_usd
  if (filter === 'any') return true
  if (filter === 'unknown') return min === null && max === null
  if (min === null && max === null) return false
  const lower = min ?? 0
  const upper = max ?? Number.POSITIVE_INFINITY
  if (filter === 'under-25k') return lower <= 25_000
  if (filter === '25k-100k') return upper >= 25_000 && lower <= 100_000
  return upper >= 100_000
}

export function filterInvestors(
  investors: Investor[],
  query: string,
  sector: string,
  checkSize: CheckSizeFilter,
): Investor[] {
  const normalizedQuery = query.trim().toLowerCase()
  return investors.filter((investor) => {
    const searchable = `${investor.name} ${investor.cik} ${investor.latest_filing_form ?? ''} ${investor.target_sectors.join(' ')}`
      .toLowerCase()
    return (!normalizedQuery || searchable.includes(normalizedQuery))
      && (sector === 'all' || investor.target_sectors.includes(sector))
      && checkSizeMatches(investor, checkSize)
  })
}
