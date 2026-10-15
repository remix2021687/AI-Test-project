interface StatCardProps {
  label: string
  value: string
  caption: string
  icon: string
  accent: 'blue' | 'green' | 'violet' | 'amber'
}

export function StatCard({ label, value, caption, icon, accent }: StatCardProps) {
  const accentClasses = {
    blue: 'bg-[#edf1ff] text-[#4164e5]',
    green: 'bg-[#e9f7f0] text-[#21966c]',
    violet: 'bg-[#f2edfb] text-[#8662d5]',
    amber: 'bg-[#fff5e6] text-[#d69331]',
  }[accent]

  return (
    <article className="min-h-[123px] rounded-[9px] border border-[#edf0f3] bg-white px-[17px] pt-[15px] pb-[14px] shadow-[0_2px_8px_#23324804] max-[850px]:min-h-[116px] max-[850px]:p-3 max-[620px]:min-h-[108px] max-[620px]:p-3">
      <div className="mb-[13px] flex items-center justify-between max-[620px]:mb-[9px]">
        <span className={`grid size-[27px] place-items-center rounded-[7px] text-[15px] font-semibold ${accentClasses}`} aria-hidden="true">{icon}</span>
        <span className="text-[9px] text-[#9ba5b1] max-[850px]:max-w-[78px] max-[850px]:text-right max-[620px]:max-w-[85px] max-[620px]:text-[8px]">{caption}</span>
      </div>
      <p className="mb-1 text-[10px] text-[#718093] max-[620px]:text-[9px]">{label}</p>
      <p className="mb-0 font-display text-[21px] leading-[1.25] font-bold tracking-[-0.6px] text-[#1c2a3d] max-[850px]:text-[17px] max-[620px]:text-lg">{value}</p>
    </article>
  )
}
