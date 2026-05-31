import { Section } from './Section'
import { painPoints } from '../data/content'

export function PainPoints() {
  return (
    <Section id="pain" className="section--pain">
      <h2 className="section-title">{painPoints.title}</h2>
      <p className="section-lead">{painPoints.subtitle}</p>

      <ul className="pain-list">
        {painPoints.pains.map((p) => (
          <li className="pain-item" key={p}>
            <span className="pain-x" aria-hidden="true">
              ✕
            </span>
            {p}
          </li>
        ))}
      </ul>

      <h3 className="subsection-title">{painPoints.forWhomTitle}</h3>
      <div className="forwhom-grid">
        {painPoints.forWhom.map((f) => (
          <div className="forwhom-card" key={f.title}>
            <div className="forwhom-card-title">{f.title}</div>
            <div className="forwhom-card-text">{f.text}</div>
          </div>
        ))}
      </div>
    </Section>
  )
}
