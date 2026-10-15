import { describe, expect, it } from 'vitest'
import type { Investor } from '../investors'
import { filterInvestors } from './investorFilters'

const investors: Investor[] = [
  {
    cik: '0000000001',
    name: 'North Capital',
    latest_filing_date: null,
    latest_filing_form: null,
    is_active: null,
    source_url: null,
    aum_usd: null,
    check_size_min_usd: null,
    check_size_max_usd: null,
    target_sectors: ['Climate'],
  },
  {
    cik: '0000000002',
    name: 'Harbor Partners',
    latest_filing_date: null,
    latest_filing_form: null,
    is_active: null,
    source_url: null,
    aum_usd: null,
    check_size_min_usd: 25_000,
    check_size_max_usd: 100_000,
    target_sectors: ['Health'],
  },
]

describe('investor filtering', () => {
  it('filters by search query and sector', () => {
    expect(filterInvestors(investors, 'north', 'Climate', 'any').map(({ cik }) => cik))
      .toEqual(['0000000001'])
    expect(filterInvestors(investors, '', 'Health', 'any').map(({ cik }) => cik))
      .toEqual(['0000000002'])
  })

  it('filters by check-size ranges and unknown values', () => {
    expect(filterInvestors(investors, '', 'all', '25k-100k').map(({ cik }) => cik))
      .toEqual(['0000000002'])
    expect(filterInvestors(investors, '', 'all', 'unknown').map(({ cik }) => cik))
      .toEqual(['0000000001'])
  })
})
