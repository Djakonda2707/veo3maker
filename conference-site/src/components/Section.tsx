import type { ReactNode } from 'react'
import { useReveal } from '../hooks/useReveal'

type Props = {
  id?: string
  className?: string
  children: ReactNode
}

/** Секция-обёртка с плавным появлением при скролле. */
export function Section({ id, className, children }: Props) {
  const { ref, visible } = useReveal<HTMLElement>()
  return (
    <section
      id={id}
      ref={ref}
      className={`section reveal${visible ? ' is-visible' : ''}${className ? ` ${className}` : ''}`}
    >
      <div className="container">{children}</div>
    </section>
  )
}
