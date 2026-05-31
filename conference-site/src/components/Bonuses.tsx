import { Section } from './Section'
import { bonuses } from '../data/content'

export function Bonuses() {
  return (
    <Section id="bonuses" className="section--bonuses">
      <h2 className="section-title">{bonuses.title}</h2>
      <div className="bonuses-grid">
        {bonuses.items.map((item) => (
          <div className="bonus-card" key={item.title}>
            <div className="bonus-gift" aria-hidden="true">
              ★
            </div>
            <div className="bonus-card-title">{item.title}</div>
            <div className="bonus-card-text">{item.text}</div>
          </div>
        ))}
      </div>
    </Section>
  )
}
