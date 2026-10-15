import type { Scaling } from '../../investors'
import { formatConfiguredCurrency, formatNumber, getAssumptionText } from '../../utils/formatters'
import { ErrorMessage } from '../ui/ErrorMessage'
import { LoadingBlock } from '../ui/LoadingBlock'

interface ScalingPanelProps {
  scaling: Scaling | null
  loading: boolean
  error: string | null
  onRetry: () => void
}

export function ScalingPanel({ scaling, loading, error, onRetry }: ScalingPanelProps) {
  const progress = scaling && scaling.target_records > 0
    ? Math.max(0, Math.min(100, (scaling.current_records / scaling.target_records) * 100))
    : 0

  return (
    <section className="min-w-0 rounded-[9px] border border-[#edf0f3] bg-white p-[19px_20px_17px] shadow-[0_2px_8px_#23324804] max-[850px]:min-h-0 max-[620px]:px-[15px] max-[620px]:py-4" id="scaling">
      <div className="mb-[21px] flex items-start justify-between">
        <div>
          <p className="mb-[6px] text-[9px] font-bold tracking-[1.25px] text-[#99a2ae]">GROWTH PLAN</p>
          <h2 className="mb-0 font-display text-sm leading-[1.3] font-semibold tracking-[-0.25px] text-[#263448]">Scaling estimate</h2>
        </div>
        <span className="grid size-[29px] place-items-center rounded-lg bg-[#eaf7f1] text-[15px] text-[#20996c]" aria-hidden="true">↗</span>
      </div>
      {scaling ? (
        <>
          <div className="mb-[15px] mt-px flex items-center gap-[14px]">
            <div className="grid gap-1"><strong className="font-display text-[19px] leading-[1.2] font-bold tracking-[-0.5px] text-[#25344a]">{formatNumber(scaling.current_records)}</strong><span className="text-[9px] text-[#8b96a4]">Current records</span></div>
            <span className="-mt-[13px] text-sm text-[#b5bdc7]" aria-hidden="true">→</span>
            <div className="grid gap-1"><strong className="font-display text-[19px] leading-[1.2] font-bold tracking-[-0.5px] text-[#25344a]">{formatNumber(scaling.target_records)}</strong><span className="text-[9px] text-[#8b96a4]">Target records</span></div>
          </div>
          <div
            className="h-1.5 w-full overflow-hidden rounded-[10px] bg-[#edf0f5]"
            role="progressbar"
            aria-label="Progress toward target records"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
          >
            <span className="block h-full rounded-[inherit] bg-gradient-to-r from-[#32aa79] to-[#83cf9b] transition-[width] duration-300 motion-reduce:transition-none" style={{ width: `${progress}%` }} />
          </div>
          <div className="mt-[14px] flex gap-[38px]">
            <div className="grid gap-1"><span className="text-[9px] text-[#8d98a6]">Cost per record</span><strong className="text-[11px] font-semibold text-[#354357]">{formatConfiguredCurrency(scaling.cost_per_record_usd)}</strong></div>
            <div className="grid gap-1"><span className="text-[9px] text-[#8d98a6]">Estimated total</span><strong className="text-[11px] font-semibold text-[#354357]">{formatConfiguredCurrency(scaling.estimated_total_cost_usd, true)}</strong></div>
          </div>
          <div className="mt-[14px] border-t border-[#eff1f4] pt-[10px]">
            <span className="mb-[5px] block text-[8px] font-bold tracking-[1.25px] text-[#99a2ae]">ASSUMPTIONS</span>
            <p className="mb-0 text-[9px] leading-[1.5] text-[#8994a2] [overflow-wrap:anywhere]">{getAssumptionText(scaling.assumptions)}</p>
          </div>
        </>
      ) : loading ? <LoadingBlock label="Loading scale estimate" /> : (
        <div>
          <p className="mb-3 text-[10px] text-[#8d98a6]">Scale estimate is unavailable.</p>
          {error && <ErrorMessage message={error} onRetry={onRetry} />}
        </div>
      )}
    </section>
  )
}
