import type { Metrics } from '../../investors'
import { formatNumber } from '../../utils/formatters'
import { LoadingBlock } from '../ui/LoadingBlock'

interface DataQualityPanelProps {
  metrics: Metrics | null
  loading: boolean
}

export function DataQualityPanel({ metrics, loading }: DataQualityPanelProps) {
  const completeness = metrics
    ? Math.max(0, Math.min(100, metrics.completeness_percent))
    : 0

  return (
    <section className="min-w-0 rounded-[9px] border border-[#edf0f3] bg-white p-[19px_20px_17px] shadow-[0_2px_8px_#23324804] max-[850px]:min-h-0 max-[620px]:px-[15px] max-[620px]:py-4" id="data-quality">
      <div className="mb-[21px] flex items-start justify-between">
        <div>
          <p className="mb-[6px] text-[9px] font-bold tracking-[1.25px] text-[#99a2ae]">DATA HEALTH</p>
          <h2 className="mb-0 font-display text-sm leading-[1.3] font-semibold tracking-[-0.25px] text-[#263448]">Coverage &amp; quality</h2>
        </div>
        <span className="grid size-[29px] place-items-center rounded-lg bg-[#eef2ff] text-[15px] text-[#5373e9]" aria-hidden="true">◈</span>
      </div>
      {metrics ? (
        <>
          <div className="mb-[11px] flex items-end justify-between">
            <div className="grid gap-[5px]"><span className="text-[10px] text-[#798697]">Record completeness</span><span className="font-display text-[23px] leading-none font-bold tracking-[-0.6px] text-[#233249]">{metrics.completeness_percent.toFixed(1)}<small className="ml-0.5 text-[15px]">%</small></span></div>
            <span className="pb-0.5 text-[9px] text-[#a0a9b4]">Across investor profiles</span>
          </div>
          <div
            className="h-[7px] w-full overflow-hidden rounded-[10px] bg-[#edf0f5]"
            role="progressbar"
            aria-label="Record completeness"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={completeness}
          >
            <span className="block h-full rounded-[inherit] bg-gradient-to-r from-[#4968e8] to-[#8296f0] transition-[width] duration-300 motion-reduce:transition-none" style={{ width: `${completeness}%` }} />
          </div>
          <div className="mt-[15px] flex items-center justify-between text-[9px] text-[#758194]">
            <span className="flex items-center gap-[6px]"><i className="size-[6px] rounded-full bg-[#36b27c]" />Accuracy</span>
            <strong className="text-[10px] font-semibold text-[#344258]">{metrics.accuracy_percent === null ? 'Not measured' : `${metrics.accuracy_percent.toFixed(1)}%`}</strong>
          </div>
          <p className="mt-[11px] mb-0 text-[9px] text-[#a1a9b4]">
            {metrics.accuracy_sample_size > 0
              ? `Accuracy is based on a sample of ${formatNumber(metrics.accuracy_sample_size)} records.`
              : 'Accuracy has not been measured on a sample yet.'}
          </p>
        </>
      ) : loading ? <LoadingBlock label="Loading data quality" /> : <p className="empty-note">Quality metrics are unavailable.</p>}
    </section>
  )
}
