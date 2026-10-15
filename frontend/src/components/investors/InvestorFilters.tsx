import type { CheckSizeFilter, InvestorFilterActions, InvestorFilters as FilterValues } from '../../types/dashboard'

interface InvestorFiltersProps {
  sectors: string[]
  filters: FilterValues
  actions: InvestorFilterActions
}

export function InvestorFilters({ sectors, filters, actions }: InvestorFiltersProps) {
  const handleCheckSizeChange = (value: string) => {
    const validFilters: CheckSizeFilter[] = ['any', 'under-25k', '25k-100k', 'over-100k', 'unknown']
    if (validFilters.includes(value as CheckSizeFilter)) {
      actions.onCheckSizeChange(value as CheckSizeFilter)
    }
  }

  return (
    <div className="flex items-center gap-[9px] px-5 pb-[15px] max-[620px]:flex-wrap max-[620px]:items-stretch max-[620px]:gap-[7px] max-[620px]:px-[14px] max-[620px]:pb-3" role="search">
      <label className="flex min-h-[34px] w-[min(315px,45%)] items-center gap-2 rounded-md border border-[#e7ebf0] px-[10px] focus-within:border-[#8da2f4] focus-within:shadow-[0_0_0_3px_#4164e512] max-[620px]:w-full">
        <span className="rotate-[-20deg] text-[19px] leading-none text-[#909baa]" aria-hidden="true">⌕</span>
        <span className="sr-only">Search investors</span>
        <input
          type="search"
          placeholder="Search by name, CIK, or sector"
          value={filters.query}
          className="w-full min-w-0 border-0 bg-transparent p-0 text-[10px] text-[#344257] outline-none placeholder:text-[#a3acb7] focus-visible:outline-none"
          onChange={(event) => actions.onQueryChange(event.target.value)}
        />
        {filters.query && <button className="cursor-pointer border-0 bg-transparent px-0.5 text-[17px] leading-none text-[#8792a0]" aria-label="Clear search" onClick={() => actions.onQueryChange('')}>×</button>}
      </label>
      <label className="relative max-[620px]:flex-1">
        <span className="sr-only">Filter by sector</span>
        <span className="pointer-events-none absolute top-1/2 right-[10px] -translate-y-[55%] text-[13px] text-[#8994a2]">⌄</span>
        <select className="h-[34px] min-w-[120px] cursor-pointer appearance-none rounded-md border border-[#e7ebf0] bg-white py-0 pr-7 pl-[10px] text-[10px] text-[#667386] hover:border-[#cbd2dc] max-[620px]:w-full" value={filters.sector} onChange={(event) => actions.onSectorChange(event.target.value)}>
          <option value="all">All sectors</option>
          {sectors.map((item) => <option value={item} key={item}>{item}</option>)}
        </select>
      </label>
      <label className="relative max-[620px]:flex-1">
        <span className="sr-only">Filter by check size</span>
        <span className="pointer-events-none absolute top-1/2 right-[10px] -translate-y-[55%] text-[13px] text-[#8994a2]">⌄</span>
        <select className="h-[34px] min-w-[136px] cursor-pointer appearance-none rounded-md border border-[#e7ebf0] bg-white py-0 pr-7 pl-[10px] text-[10px] text-[#667386] hover:border-[#cbd2dc] max-[620px]:w-full" value={filters.checkSize} onChange={(event) => handleCheckSizeChange(event.target.value)}>
          <option value="any">Any check size</option>
          <option value="under-25k">Up to $25k</option>
          <option value="25k-100k">$25k – $100k</option>
          <option value="over-100k">$100k+</option>
          <option value="unknown">Not reported</option>
        </select>
      </label>
    </div>
  )
}
