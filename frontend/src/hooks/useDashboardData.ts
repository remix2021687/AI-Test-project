import { useEffect, useState } from 'react'
import {
  fetchInvestors,
  fetchMetrics,
  fetchScaling,
  type Investor,
  type Metrics,
  type Scaling,
} from '../investors'
import type { AsyncState } from '../types/dashboard'

const initialState = <T,>(): AsyncState<T> => ({ data: null, loading: true, error: null })

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}

export function useDashboardData() {
  const [investors, setInvestors] = useState<AsyncState<Investor[]>>(initialState)
  const [metrics, setMetrics] = useState<AsyncState<Metrics>>(initialState)
  const [scaling, setScaling] = useState<AsyncState<Scaling>>(initialState)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setInvestors((current) => ({ ...current, loading: true, error: null }))
    setMetrics((current) => ({ ...current, loading: true, error: null }))
    setScaling((current) => ({ ...current, loading: true, error: null }))

    void fetchInvestors(controller.signal)
      .then((data) => setInvestors({ data, loading: false, error: null }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setInvestors((current) => ({
            ...current,
            loading: false,
            error: errorMessage(error, 'Could not load investor records.'),
          }))
        }
      })
    void fetchMetrics(controller.signal)
      .then((data) => setMetrics({ data, loading: false, error: null }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setMetrics((current) => ({
            ...current,
            loading: false,
            error: errorMessage(error, 'Could not load metrics.'),
          }))
        }
      })
    void fetchScaling(controller.signal)
      .then((data) => setScaling({ data, loading: false, error: null }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setScaling((current) => ({
            ...current,
            loading: false,
            error: errorMessage(error, 'Could not load scaling estimate.'),
          }))
        }
      })

    return () => controller.abort()
  }, [refreshKey])

  return {
    investors,
    metrics,
    scaling,
    retry: () => setRefreshKey((key) => key + 1),
  }
}
