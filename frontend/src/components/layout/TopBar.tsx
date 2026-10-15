import { formatDate } from '../../utils/formatters'

interface TopBarProps {
  asOf: string | null
  loading: boolean
  onRefresh: () => void
}

export function TopBar({ asOf, loading, onRefresh }: TopBarProps) {
  return (
    <header className="flex h-[65px] items-center justify-between border-b border-[#edf0f3] bg-white px-[42px] max-[850px]:px-[22px] max-[620px]:h-14 max-[620px]:px-4">
      <div className="flex items-center gap-[11px] text-[11px] text-[#98a1ad]"><span>Workspace</span><span className="text-[#c5cbd3]">/</span><strong className="font-semibold text-[#445166]">Overview</strong></div>
      <div className="flex items-center gap-[17px] max-[620px]:gap-0">
        <span className="text-[10px] text-[#97a1ae] max-[620px]:hidden">{asOf ? `Data as of ${formatDate(asOf)}` : 'Investor intelligence'}</span>
        <button className="inline-flex min-h-[33px] items-center justify-center gap-[7px] rounded-md border border-[#e4e8ed] bg-white px-3 text-[10px] font-semibold text-[#465368] transition-colors hover:border-[#d0d6df] hover:bg-[#f7f8fa] disabled:cursor-wait disabled:opacity-65" onClick={onRefresh} disabled={loading}>
          <span className="text-[15px] leading-none" aria-hidden="true">↻</span> Refresh
        </button>
      </div>
    </header>
  )
}
