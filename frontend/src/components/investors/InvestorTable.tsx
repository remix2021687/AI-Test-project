import type { Investor } from '../../investors'
import { checkSizeLabel, formatCurrency, formatDate, statusClass, statusLabel } from '../../utils/formatters'

interface InvestorTableProps {
  investors: Investor[]
}

export function InvestorTable({ investors }: InvestorTableProps) {
  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[930px] border-collapse text-left">
        <thead className="bg-[#fafbfc]">
          <tr>
            <th className="h-[34px] w-[20%] border-y border-[#eff1f4] px-3 text-[8px] font-semibold tracking-[0.55px] whitespace-nowrap text-[#929dab] first:pl-5" scope="col">INVESTOR</th>
            <th className="h-[34px] w-[11%] border-y border-[#eff1f4] px-3 text-[8px] font-semibold tracking-[0.55px] whitespace-nowrap text-[#929dab]" scope="col">STATUS</th>
            <th className="h-[34px] w-[20%] border-y border-[#eff1f4] px-3 text-[8px] font-semibold tracking-[0.55px] whitespace-nowrap text-[#929dab]" scope="col">TARGET SECTORS</th>
            <th className="h-[34px] w-[12%] border-y border-[#eff1f4] px-3 text-[8px] font-semibold tracking-[0.55px] whitespace-nowrap text-[#929dab]" scope="col">AUM</th>
            <th className="h-[34px] w-[15%] border-y border-[#eff1f4] px-3 text-[8px] font-semibold tracking-[0.55px] whitespace-nowrap text-[#929dab]" scope="col">CHECK SIZE</th>
            <th className="h-[34px] border-y border-[#eff1f4] px-3 text-[8px] font-semibold tracking-[0.55px] whitespace-nowrap text-[#929dab]" scope="col">LATEST FILING</th>
            <th className="h-[34px] border-y border-[#eff1f4] px-3 text-[8px] font-semibold tracking-[0.55px] whitespace-nowrap text-[#929dab]" scope="col"><span className="sr-only">Source</span></th>
          </tr>
        </thead>
        <tbody>
          {investors.map((investor, index) => {
            const avatarClasses = index % 3 === 1
              ? 'bg-[#eaf4ef] text-[#45896e]'
              : index % 3 === 2
                ? 'bg-[#fbf0e4] text-[#b47a42]'
                : 'bg-[#edf0fa] text-[#5e73c8]'
            return (
              <tr className="hover:bg-[#fcfdff] [&:not(:last-child)>td]:border-b [&:not(:last-child)>td]:border-[#f0f2f5]" key={investor.cik}>
              <td className="h-[61px] px-3 py-2 align-middle text-[9px] text-[#435166] first:pl-5">
                <div className="flex items-center gap-[9px]">
                  <div className={`grid size-[29px] shrink-0 place-items-center rounded-full font-display text-[11px] font-semibold ${avatarClasses}`} aria-hidden="true">{investor.name.trim().charAt(0).toUpperCase() || '?'}</div>
                  <div className="grid gap-1">
                    <strong className="text-[10px] font-semibold text-[#344256]">{investor.name}</strong>
                    <span className="text-[8px] text-[#929dab]">CIK {investor.cik || 'Not reported'}</span>
                  </div>
                </div>
              </td>
              <td className="h-[61px] px-3 py-2 align-middle text-[9px] text-[#435166]"><span className={`inline-flex items-center gap-[5px] whitespace-nowrap rounded-xl px-[7px] py-1 text-[8px] font-medium ${statusClass(investor.is_active)}`}><i className="size-[5px] rounded-full" />{statusLabel(investor.is_active)}</span></td>
              <td className="h-[61px] px-3 py-2 align-middle text-[9px] text-[#435166]">
                {investor.target_sectors.length > 0
                  ? <div className="flex flex-wrap gap-1">{investor.target_sectors.map((item) => <span className="max-w-full overflow-hidden rounded bg-[#f3f5f8] px-1.5 py-1 text-[8px] text-ellipsis whitespace-nowrap text-[#68768a]" key={item}>{item}</span>)}</div>
                  : <span className="text-[9px] text-[#a0a9b4]">Not reported</span>}
              </td>
              <td className="h-[61px] px-3 py-2 align-middle text-[9px] font-medium whitespace-nowrap text-[#47566a]">{formatCurrency(investor.aum_usd, true)}</td>
              <td className="h-[61px] px-3 py-2 align-middle text-[9px] font-medium whitespace-nowrap text-[#47566a]">{checkSizeLabel(investor)}</td>
              <td className="h-[61px] px-3 py-2 align-middle text-[9px] text-[#435166]">
                <div className="grid gap-1">
                  <strong className="text-[10px] font-semibold text-[#344256]">{investor.latest_filing_form ?? 'Not reported'}</strong>
                  <span className="text-[8px] text-[#929dab]">{formatDate(investor.latest_filing_date)}</span>
                </div>
              </td>
              <td className="h-[61px] px-3 py-2 align-middle text-[9px] text-[#435166]">
                {investor.source_url ? (
                  <a className="grid size-[23px] place-items-center rounded-[5px] bg-[#f6f7f9] text-[13px] text-[#718198] no-underline transition-colors hover:bg-[#edf1ff] hover:text-[#365be7]" href={investor.source_url} target="_blank" rel="noreferrer" aria-label={`Open source for ${investor.name}`} title="Open source">
                    ↗
                  </a>
                ) : <span className="pl-[7px] text-[9px] text-[#a0a9b4]" aria-label="Source not reported">—</span>}
              </td>
            </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
