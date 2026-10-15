import type { Investor } from '../../investors'
import type { InvestorFilterActions, InvestorFilters as FilterValues } from '../../types/dashboard'
import { formatNumber } from '../../utils/formatters'
import { ErrorMessage } from '../ui/ErrorMessage'
import { LoadingBlock } from '../ui/LoadingBlock'
import { InvestorFilters } from './InvestorFilters'
import { InvestorTable } from './InvestorTable'

interface InvestorsPanelProps {
  investors: Investor[] | null
  filteredInvestors: Investor[]
  filters: FilterValues
  filterActions: InvestorFilterActions
  loading: boolean
  error: string | null
  onRetry: () => void
}

export function InvestorsPanel({
  investors,
  filteredInvestors,
  filters,
  filterActions,
  loading,
  error,
  onRetry,
}: InvestorsPanelProps) {
  const sectors = [...new Set((investors ?? []).flatMap((investor) => investor.target_sectors))]
    .sort((left, right) => left.localeCompare(right))

  return (
    <section className="min-w-0 overflow-hidden rounded-[9px] border border-[#edf0f3] bg-white shadow-[0_2px_8px_#23324804]" id="investors">
      <div className="flex items-start justify-between px-5 pt-[19px] pb-[17px] max-[620px]:px-[14px] max-[620px]:pt-4 max-[620px]:pb-[13px]">
        <div>
          <p className="mb-[7px] text-[9px] font-bold tracking-[1.25px] text-[#99a2ae]">YOUR UNIVERSE</p>
          <div className="flex items-center gap-[9px]">
            <h2 className="mb-0 font-display text-sm leading-[1.3] font-semibold tracking-[-0.25px] text-[#263448]">Investor records</h2>
            {investors && <span className="inline-flex h-5 min-w-[22px] items-center justify-center rounded-[10px] bg-[#eff2ff] px-1.5 text-[9px] font-semibold text-[#526de1]">{formatNumber(investors.length)}</span>}
          </div>
          <p className="mt-1 mb-0 text-[10px] text-[#8d98a6]">Configured CIKs with recent 13F filings; filing activity does not prove current investing.</p>
        </div>
        <span className="mt-[5px] flex items-center gap-[7px] text-[9px] text-[#8995a3] max-[620px]:text-[0px]"><span className="size-[6px] shrink-0 rounded-full bg-[#2cad76] shadow-[0_0_0_3px_#2cad761a]" />Synced from API</span>
      </div>

      <InvestorFilters sectors={sectors} filters={filters} actions={filterActions} />

      {error && (
        <div className="table-error"><ErrorMessage message={`Investor records unavailable: ${error}`} onRetry={onRetry} /></div>
      )}
      {loading && !investors && <LoadingBlock label="Loading investor records" />}
      {!loading && !investors && error && (
        <div className="grid justify-items-center px-5 py-[31px] pb-[34px] text-center">
          <span className="grid size-[34px] place-items-center rounded-[9px] bg-[#eff2ff] text-xl text-[#5e75e1]" aria-hidden="true">⌁</span>
          <h3 className="mt-[9px] mb-[5px] font-display text-[13px] font-semibold text-[#364459]">We couldn’t load your investors</h3>
          <p className="mb-[14px] max-w-[340px] text-[10px] leading-[1.6] text-[#8b96a4]">Check that the investor service is available, then try again.</p>
          <button className="inline-flex min-h-[33px] cursor-pointer items-center justify-center rounded-md border border-[#4565df] bg-[#4565df] px-3 text-[10px] font-semibold text-white transition-colors hover:bg-[#3555d0]" onClick={onRetry}>Retry connection</button>
        </div>
      )}
      {investors && investors.length === 0 && !loading && (
        <div className="grid justify-items-center px-5 py-[31px] pb-[34px] text-center">
          <span className="grid size-[34px] place-items-center rounded-[9px] bg-[#eff2ff] text-xl text-[#5e75e1]" aria-hidden="true">◎</span>
          <h3 className="mt-[9px] mb-[5px] font-display text-[13px] font-semibold text-[#364459]">No investor records yet</h3>
          <p className="mb-[14px] max-w-[340px] text-[10px] leading-[1.6] text-[#8b96a4]">When records are available, they’ll appear here. No sample data is shown.</p>
        </div>
      )}
      {investors && investors.length > 0 && filteredInvestors.length === 0 && (
        <div className="grid justify-items-center px-5 py-[31px] pb-[34px] text-center">
          <h3 className="mt-[9px] mb-[5px] font-display text-[13px] font-semibold text-[#364459]">No matching investors</h3>
          <p className="mb-[14px] max-w-[340px] text-[10px] leading-[1.6] text-[#8b96a4]">Try a different search or clear your filters.</p>
          <button className="cursor-pointer border-0 bg-transparent p-0 text-[9px] font-semibold text-[#4968d4] underline-offset-2 hover:underline" onClick={filterActions.onClear}>Clear all filters</button>
        </div>
      )}
      {filteredInvestors.length > 0 && (
        <>
          <InvestorTable investors={filteredInvestors} />
          <div className="flex min-h-10 items-center justify-between border-t border-[#eff1f4] bg-white px-5 text-[9px] text-[#929dab] max-[620px]:px-[14px]">
            <span>Showing <strong className="font-semibold text-[#657287]">{formatNumber(filteredInvestors.length)}</strong> of <strong className="font-semibold text-[#657287]">{formatNumber(investors?.length ?? 0)}</strong> records</span>
            {loading && <span className="flex items-center gap-[6px]"><span className="size-[11px] animate-spin rounded-full border-[1.5px] border-[#e4e9f0] border-t-[#5875e8] motion-reduce:animate-none" />Refreshing…</span>}
          </div>
        </>
      )}
    </section>
  )
}
