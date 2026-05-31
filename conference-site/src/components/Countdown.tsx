import { useCountdown } from '../hooks/useCountdown'

const pad = (n: number) => String(n).padStart(2, '0')

type Props = {
  targetIso: string
  /** Текст, когда время вышло (цена уже повышена). */
  expiredLabel?: string
}

/** Компактный таймер обратного отсчёта до повышения цены. */
export function Countdown({ targetIso, expiredLabel = 'Цена повышена' }: Props) {
  const t = useCountdown(targetIso)

  if (t.expired) {
    return <div className="countdown countdown--expired">{expiredLabel}</div>
  }

  const cells: Array<[number, string]> = [
    [t.days, 'дн'],
    [t.hours, 'час'],
    [t.minutes, 'мин'],
    [t.seconds, 'сек'],
  ]

  return (
    <div className="countdown" role="timer" aria-live="off">
      {cells.map(([value, label], i) => (
        <div className="countdown-cell" key={label}>
          <span className="countdown-num">{i === 0 ? value : pad(value)}</span>
          <span className="countdown-label">{label}</span>
        </div>
      ))}
    </div>
  )
}
