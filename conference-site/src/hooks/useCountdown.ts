import { useEffect, useState } from 'react'

export type TimeLeft = {
  days: number
  hours: number
  minutes: number
  seconds: number
  expired: boolean
}

function diff(target: number): TimeLeft {
  const ms = target - Date.now()
  if (ms <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, expired: true }
  }
  const totalSeconds = Math.floor(ms / 1000)
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
    expired: false,
  }
}

/** Тикающий обратный отсчёт до момента `targetIso` (ISO-строка с таймзоной). */
export function useCountdown(targetIso: string): TimeLeft {
  const target = new Date(targetIso).getTime()
  const [time, setTime] = useState<TimeLeft>(() => diff(target))

  useEffect(() => {
    const id = setInterval(() => setTime(diff(target)), 1000)
    return () => clearInterval(id)
  }, [target])

  return time
}
