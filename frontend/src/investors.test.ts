import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchInvestors, fetchMetrics, fetchScaling } from './investors'

const fetchMock = vi.fn<typeof fetch>()

function respondWith(payload: unknown, status = 200): void {
  fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  }))
}

function signal(): AbortSignal {
  return new AbortController().signal
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
  fetchMock.mockReset()
})

describe('investor API parsing', () => {
  it('preserves nullable source values and requests the expected endpoint', async () => {
    respondWith({
      investors: [{
        cik: '0001234567',
        name: 'Example Capital',
        latest_filing_date: '2025-02-01',
        latest_filing_form: '13F-HR',
        is_active: true,
        source_url: null,
        aum_usd: null,
        check_size_min_usd: null,
        check_size_max_usd: null,
        target_sectors: [],
      }],
    })

    const result = await fetchInvestors(signal())

    expect(result).toHaveLength(1)
    expect(result[0].aum_usd).toBeNull()
    expect(result[0].target_sectors).toEqual([])
    expect(fetchMock.mock.calls[0][0]).toBe('/api/investors')
  })

  it('rejects records with an invalid CIK instead of silently dropping them', async () => {
    respondWith({ investors: [{ cik: '123', name: 'Malformed record' }] })

    await expect(fetchInvestors(signal())).rejects.toThrow('valid CIK or name')
  })

  it('rejects missing required metric values rather than presenting them as zero', async () => {
    respondWith({
      total_records: 1,
      active_records: 1,
      verified_records: 1,
      accuracy_percent: null,
      completeness_percent: 0,
      as_of: null,
    })

    await expect(fetchMetrics(signal())).rejects.toThrow('valid "accuracy_sample_size"')
  })

  it('loads an explicit scaling estimate', async () => {
    respondWith({
      current_records: 10,
      target_records: 100,
      cost_per_record_usd: 2,
      estimated_total_cost_usd: 200,
      assumptions: ['Illustrative unit-cost assumption'],
    })

    await expect(fetchScaling(signal())).resolves.toMatchObject({
      target_records: 100,
      estimated_total_cost_usd: 200,
    })
  })

  it('keeps an unconfigured scaling cost unknown', async () => {
    respondWith({
      current_records: 0,
      target_records: 10000,
      cost_per_record_usd: null,
      estimated_total_cost_usd: null,
      assumptions: ['No unit cost configured'],
    })

    await expect(fetchScaling(signal())).resolves.toMatchObject({
      cost_per_record_usd: null,
      estimated_total_cost_usd: null,
    })
  })
})
