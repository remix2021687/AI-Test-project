import { useMemo, useState } from 'react'
import { DataQualityPanel } from './components/dashboard/DataQualityPanel'
import { ScalingPanel } from './components/dashboard/ScalingPanel'
import { SummaryStats } from './components/dashboard/SummaryStats'
import { InvestorsPanel } from './components/investors/InvestorsPanel'
import { PageHeading } from './components/layout/PageHeading'
import { PageFooter } from './components/layout/PageFooter'
import { Sidebar } from './components/layout/Sidebar'
import { TopBar } from './components/layout/TopBar'
import { ErrorMessage } from './components/ui/ErrorMessage'
import { useDashboardData } from './hooks/useDashboardData'
import { filterInvestors } from './utils/investorFilters'
import type { CheckSizeFilter, InvestorFilterActions } from './types/dashboard'

export default function App() {
  const { investors: investorState, metrics: metricsState, scaling: scalingState, retry } = useDashboardData()
  const [query, setQuery] = useState('')
  const [sector, setSector] = useState('all')
  const [checkSize, setCheckSize] = useState<CheckSizeFilter>('any')

  const investors = investorState.data
  const filteredInvestors = useMemo(
    () => filterInvestors(investors ?? [], query, sector, checkSize),
    [investors, query, sector, checkSize],
  )
  const filterActions: InvestorFilterActions = {
    onQueryChange: setQuery,
    onSectorChange: setSector,
    onCheckSizeChange: setCheckSize,
    onClear: () => {
      setQuery('')
      setSector('all')
      setCheckSize('any')
    },
  }
  const hasConnectionIssue = Boolean(investorState.error || metricsState.error || scalingState.error)
  const isLoading = investorState.loading || metricsState.loading || scalingState.loading

  return (
    <div className="min-h-screen">
      <Sidebar hasConnectionIssue={hasConnectionIssue} isConnecting={isLoading} />

      <main className="ml-[236px] min-h-screen max-[850px]:ml-[66px]" id="overview">
        <TopBar asOf={metricsState.data?.as_of ?? null} loading={isLoading} onRefresh={retry} />

        <div className="mx-auto max-w-[1500px] px-[42px] pt-[37px] pb-6 max-[850px]:px-[22px] max-[850px]:pt-7 max-[850px]:pb-5 max-[620px]:px-[14px] max-[620px]:pt-[25px] max-[620px]:pb-[18px]">
          <PageHeading asOf={metricsState.data?.as_of ?? null} />

          {metricsState.error && (
            <div className="mb-[10px]"><ErrorMessage message={`Metrics unavailable: ${metricsState.error}`} onRetry={retry} /></div>
          )}

          <SummaryStats metrics={metricsState.data} loading={metricsState.loading} />

          <div className="mb-[17px] grid grid-cols-2 gap-[15px] max-[850px]:grid-cols-1 max-[620px]:mb-3 max-[620px]:gap-[11px]">
            <DataQualityPanel metrics={metricsState.data} loading={metricsState.loading} />
            <ScalingPanel
              scaling={scalingState.data}
              loading={scalingState.loading}
              error={scalingState.error}
              onRetry={retry}
            />
          </div>

          <InvestorsPanel
            investors={investors}
            filteredInvestors={filteredInvestors}
            filters={{ query, sector, checkSize }}
            filterActions={filterActions}
            loading={investorState.loading}
            error={investorState.error}
            onRetry={retry}
          />

          <PageFooter />
        </div>
      </main>
    </div>
  )
}
