interface LoadingBlockProps {
  label?: string
}

export function LoadingBlock({ label = 'Loading data' }: LoadingBlockProps) {
  return (
    <div className="flex min-h-[95px] items-center justify-center gap-[9px] text-[10px] text-[#8692a1]" role="status" aria-live="polite">
      <span className="size-[15px] animate-spin rounded-full border-2 border-[#e4e9f0] border-t-[#5875e8] motion-reduce:animate-none" aria-hidden="true" />
      <span>{label}…</span>
    </div>
  )
}
