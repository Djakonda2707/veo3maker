import { useEffect, useState } from 'react'
import { config } from '../data/content'

/** Липкая нижняя кнопка покупки — появляется после прокрутки первого экрана. */
export function StickyCta() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > window.innerHeight * 0.8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className={`sticky-cta${show ? ' is-visible' : ''}`}>
      <div className="sticky-cta-info">
        <span className="sticky-cta-price">{config.priceEarly}</span>
        <span className="sticky-cta-sub">сейчас · потом {config.priceFull}</span>
      </div>
      <a className="btn btn--primary" href={config.paymentUrl} target="_blank" rel="noopener noreferrer">
        Забронировать
      </a>
    </div>
  )
}
