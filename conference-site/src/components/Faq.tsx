import { Section } from './Section'
import { faq } from '../data/content'

export function Faq() {
  return (
    <Section id="faq">
      <h2 className="section-title">{faq.title}</h2>
      <div className="faq-list">
        {faq.items.map((item) => (
          <details className="faq-item" key={item.q}>
            <summary className="faq-q">
              {item.q}
              <span className="faq-icon" aria-hidden="true">
                +
              </span>
            </summary>
            <div className="faq-a">{item.a}</div>
          </details>
        ))}
      </div>
    </Section>
  )
}
