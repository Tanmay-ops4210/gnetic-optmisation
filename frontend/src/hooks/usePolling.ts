import { useEffect, useRef } from 'react'

export function usePolling(fn: () => Promise<void>, interval: number, active: boolean) {
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    if (!active) return
    const id = setInterval(() => fnRef.current(), interval)
    return () => clearInterval(id)
  }, [active, interval])
}
