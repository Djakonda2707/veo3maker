import { Section } from './Section'
import { outcomes } from '../data/content'

export function Outcomes() {
  return (
    <Section id="outcomes">
      <h2 className="section-title">{outcomes.title}</h2>
      <div className="outcomes-grid">
        {outcomes.items.map((item, i) => (
          <div className="outcome-card" key={item.title}>
            <div className="outcome-num">{String(i + 1).padStart(2, '0')}</div>
            <div className="outcome-card-title">{item.title}</div>
            <div className="outcome-card-text">{item.text}</div>
          </div>
        ))}
      </div>
    </Section>
  )
}
