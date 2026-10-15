import type { Metrics } from '../../investors'
import { formatNumber } from '../../utils/formatters'
import { LoadingBlock } from '../ui/LoadingBlock'
import { StatCard } from './StatCard'

interface SummaryStatsProps {
  metrics: Metrics | null
  loading: boolean
}

export function SummaryStats({ metrics, loading }: SummaryStatsProps) {
  return (
    <section className="mb-[17px] grid grid-cols-4 gap-[14px] max-[620px]:mb-3 max-[620px]:grid-cols-2 max-[620px]:gap-[9px]" aria-label="Investor summary">
      {metrics ? (
        <>
          <StatCard label="Total records" value={formatNumber(metrics.total_records)} caption="Investor universe" icon="◎" accent="blue" />
          <StatCard label="Recent 13F filers" value={formatNumber(metrics.active_records)} caption="Within activity window" icon="↗" accent="green" />
          <StatCard label="Records sampled" value={formatNumber(metrics.verified_records)} caption="Independent field review" icon="✓" accent="violet" />
          <StatCard
            label="Data accuracy"
            value={metrics.accuracy_percent === null ? 'Not measured' : `${metrics.accuracy_percent.toFixed(1)}%`}
            caption={metrics.accuracy_sample_size > 0 ? `${formatNumber(metrics.accuracy_sample_size)} sampled` : 'No sample yet'}
            icon="◌"
            accent="amber"
          />
        </>
      ) : loading ? (
        <div className="col-span-full flex min-h-[89px] items-center rounded-[9px] border border-[#edf0f3] bg-white px-[18px] py-[18px] text-[11px] text-[#8490a0] shadow-[0_2px_8px_#23324804]"><LoadingBlock label="Loading investor metrics" /></div>
      ) : (
        <div className="col-span-full flex min-h-[89px] items-center rounded-[9px] border border-[#f1e8dc] bg-[#fffdf9] px-[18px] py-[18px] text-[11px] text-[#8490a0] shadow-[0_2px_8px_#23324804]">Summary metrics aren't available yet. Investor records are shown below when available.</div>
      )}
    </section>
  )
}
