interface SidebarProps {
  hasConnectionIssue: boolean
  isConnecting: boolean
}

export function Sidebar({ hasConnectionIssue, isConnecting }: SidebarProps) {
  return (
    <aside className="fixed inset-y-0 left-0 z-10 flex w-[236px] flex-col border-r border-[#edf0f3] bg-white px-4 pt-[27px] pb-[14px] max-[850px]:w-[66px] max-[850px]:items-center max-[850px]:px-[9px] max-[850px]:pt-5 max-[850px]:pb-3">
      <a className="mb-[49px] ml-[9px] mt-px flex items-center gap-[10px] font-display text-[21px] leading-none font-extrabold tracking-[-1.2px] text-[#1d2a3d] no-underline max-[850px]:my-[2px] max-[850px]:mx-0" href="#overview" aria-label="Northstar dashboard home">
        <span className="grid size-7 rotate-[-7deg] place-items-center rounded-[9px] bg-gradient-to-br from-[#5178ff] to-[#3151d5] shadow-[0_4px_9px_#365be731] max-[850px]:size-[31px]" aria-hidden="true"><span className="block size-3 rounded-[50%_50%_50%_2px] border-2 border-white" /></span>
        <span className="max-[850px]:hidden">northstar<span className="text-[#4f70eb]">.</span></span>
      </a>
      <div className="mb-[10px] px-3 text-[9px] font-bold tracking-[1.25px] text-[#99a2ae] max-[850px]:hidden">WORKSPACE</div>
      <nav className="grid gap-[5px] max-[850px]:w-full max-[850px]:justify-items-center max-[850px]:gap-2" aria-label="Main navigation">
        <a className="flex min-h-10 items-center gap-[11px] rounded-[7px] bg-[#edf1ff] px-3 text-xs font-semibold text-[#365be7] no-underline transition-colors hover:bg-[#f5f7fb] hover:text-[#35445a] max-[850px]:size-[42px] max-[850px]:min-h-[42px] max-[850px]:justify-center max-[850px]:p-0 max-[850px]:text-[0px]" href="#overview" aria-label="Overview"><span className="w-[17px] text-center text-base leading-none" aria-hidden="true">⌂</span><span className="max-[850px]:hidden">Overview</span></a>
        <a className="flex min-h-10 items-center gap-[11px] rounded-[7px] px-3 text-xs font-medium text-[#788495] no-underline transition-colors hover:bg-[#f5f7fb] hover:text-[#35445a] max-[850px]:size-[42px] max-[850px]:min-h-[42px] max-[850px]:justify-center max-[850px]:p-0 max-[850px]:text-[0px]" href="#investors" aria-label="Investor records"><span className="w-[17px] text-center text-base leading-none" aria-hidden="true">▤</span><span className="max-[850px]:hidden">Investor records</span></a>
        <a className="flex min-h-10 items-center gap-[11px] rounded-[7px] px-3 text-xs font-medium text-[#788495] no-underline transition-colors hover:bg-[#f5f7fb] hover:text-[#35445a] max-[850px]:size-[42px] max-[850px]:min-h-[42px] max-[850px]:justify-center max-[850px]:p-0 max-[850px]:text-[0px]" href="#data-quality" aria-label="Data quality"><span className="w-[17px] text-center text-base leading-none" aria-hidden="true">◈</span><span className="max-[850px]:hidden">Data quality</span></a>
        <a className="flex min-h-10 items-center gap-[11px] rounded-[7px] px-3 text-xs font-medium text-[#788495] no-underline transition-colors hover:bg-[#f5f7fb] hover:text-[#35445a] max-[850px]:size-[42px] max-[850px]:min-h-[42px] max-[850px]:justify-center max-[850px]:p-0 max-[850px]:text-[0px]" href="#scaling" aria-label="Scale estimate"><span className="w-[17px] text-center text-base leading-none" aria-hidden="true">↗</span><span className="max-[850px]:hidden">Scale estimate</span></a>
      </nav>
      <div className="mt-auto max-[850px]:w-full">
        <div className="mb-4 flex items-center gap-[9px] rounded-lg border border-[#edf0f3] px-[10px] py-3 max-[850px]:hidden">
          <span className={`size-[7px] shrink-0 rounded-full ${hasConnectionIssue ? 'bg-[#d99b40] shadow-[0_0_0_3px_#d99b401a]' : 'bg-[#2cad76] shadow-[0_0_0_3px_#2cad761a]'}`} />
          <div className="grid gap-[3px]">
            <strong className="text-[10px] font-semibold text-[#354256]">{hasConnectionIssue ? 'Connection issue' : isConnecting ? 'Connecting…' : 'API connected'}</strong>
            <span className="text-[9px] text-[#929cab]">{hasConnectionIssue ? 'Some data is unavailable' : 'Investor data source'}</span>
          </div>
        </div>
        <div className="flex items-center gap-[9px] border-t border-[#eef0f3] px-[5px] pt-[13px] pb-[2px] max-[850px]:w-full max-[850px]:justify-center max-[850px]:px-0">
          <div className="grid size-[30px] place-items-center rounded-full bg-[#e9edfb] text-[9px] font-bold text-[#5369bc] max-[850px]:size-[30px]" aria-hidden="true">NS</div>
          <div className="grid min-w-0 flex-1 gap-[3px] max-[850px]:hidden"><strong className="text-[10px] font-semibold text-[#354256]">Northstar team</strong><span className="text-[9px] text-[#929cab]">Investor research</span></div>
          <span className="text-xl tracking-[1px] text-[#9ca5b1] max-[850px]:hidden" aria-hidden="true">···</span>
        </div>
      </div>
    </aside>
  )
}
