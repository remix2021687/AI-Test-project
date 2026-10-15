import type { Investor } from '../investors'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export type CheckSizeFilter = 'any' | 'under-25k' | '25k-100k' | 'over-100k' | 'unknown'

export interface InvestorFilters {
  query: string
  sector: string
  checkSize: CheckSizeFilter
}

export interface InvestorFilterActions {
  onQueryChange: (value: string) => void
  onSectorChange: (value: string) => void
  onCheckSizeChange: (value: CheckSizeFilter) => void
  onClear: () => void
}

export type { Investor }
