import { formatDate } from '../../utils/formatters'

interface PageHeadingProps {
  asOf: string | null
}

export function PageHeading({ asOf }: PageHeadingProps) {
  return (
    <section className="mb-[25px] flex items-end justify-between max-[620px]:mb-[18px] max-[620px]:items-start max-[620px]:gap-[10px]">
      <div>
        <p className="mb-[9px] text-[9px] font-bold tracking-[1.25px] text-[#99a2ae]">INVESTOR INTELLIGENCE</p>
        <h1 className="mb-[7px] font-display text-[27px] leading-[1.2] font-bold tracking-[-1.15px] text-[#1d2939] max-[620px]:text-2xl">Your investor overview<span className="text-[#4f70eb]">.</span></h1>
        <p className="mb-0 text-[11px] text-[#7f8a99] max-[620px]:max-w-[280px] max-[620px]:text-[10px] max-[620px]:leading-[1.55]">A clear view of your investor universe and data coverage.</p>
      </div>
      <div className="flex items-center gap-[9px] pb-[3px] text-[10px] text-[#7a8797] max-[620px]:shrink-0 max-[620px]:pt-[5px] max-[620px]:pb-0 max-[620px]:text-[8px]">
        <span className="size-[6px] shrink-0 rounded-full bg-[#2cad76] shadow-[0_0_0_3px_#2cad761a]" />
        <span>{asOf ? `Updated ${formatDate(asOf)}` : 'Live workspace'}</span>
      </div>
    </section>
  )
}
