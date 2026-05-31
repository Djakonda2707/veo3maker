import { Section } from './Section'
import { config, pricing } from '../data/content'
import { Countdown } from './Countdown'

export function Pricing() {
  return (
    <Section id="pricing" className="section--pricing">
      <h2 className="section-title">{pricing.title}</h2>
      <p className="section-lead">{pricing.subtitle}</p>

      <div className="price-card">
        <div className="price-card-glow" aria-hidden="true" />

        <div className="price-card-head">
          <h3 className="price-plan-title">{pricing.planTitle}</h3>
          <div className="price-row">
            <div className="price-now">
              <span className="price-now-label">{pricing.earlyLabel}</span>
              <span className="price-now-value">{config.priceEarly}</span>
            </div>
            <div className="price-old">
              <span className="price-old-label">{pricing.fullLabel}</span>
              <span className="price-old-value">{config.priceFull}</span>
            </div>
          </div>
        </div>

        <ul className="price-features">
          {pricing.features.map((f) => (
            <li key={f}>
              <span className="price-check" aria-hidden="true">
                ✓
              </span>
              {f}
            </li>
          ))}
        </ul>

        <div className="price-timer">
          <span className="price-timer-text">До повышения цены осталось:</span>
          <Countdown targetIso={config.priceRaiseAt} expiredLabel={`Действует цена ${config.priceFull}`} />
        </div>

        <a className="btn btn--primary btn--lg btn--block" href={config.paymentUrl} target="_blank" rel="noopener noreferrer">
          {pricing.cta} {config.priceEarly}
        </a>

        <p className="price-note">{pricing.note}</p>
      </div>
    </Section>
  )
}
