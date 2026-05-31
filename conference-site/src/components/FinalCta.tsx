import { Section } from './Section'
import { config, finalCta } from '../data/content'

export function FinalCta() {
  return (
    <Section id="join" className="section--final">
      <div className="final-card">
        <h2 className="final-title">{finalCta.title}</h2>
        <p className="final-subtitle">{finalCta.subtitle}</p>
        <a className="btn btn--primary btn--lg" href={config.paymentUrl} target="_blank" rel="noopener noreferrer">
          {finalCta.cta} — {config.priceEarly}
        </a>
      </div>
    </Section>
  )
}
