interface ErrorMessageProps {
  message: string
  onRetry: () => void
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="flex flex-wrap items-center gap-[7px] text-[9px] leading-[1.5] text-[#9b5b48]" role="alert">
      <span className="grid size-[17px] shrink-0 place-items-center rounded-full bg-[#fff0ec] text-[10px] font-bold" aria-hidden="true">!</span>
      <span>{message}</span>
      <button className="cursor-pointer border-0 bg-transparent p-0 text-[9px] font-semibold text-[#4968d4] underline-offset-2 hover:underline focus-visible:rounded-sm" onClick={onRetry}>Try again</button>
    </div>
  )
}
