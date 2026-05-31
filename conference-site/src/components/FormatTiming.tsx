import { Section } from './Section'
import { formatInfo, speaker } from '../data/content'

export function FormatTiming() {
  return (
    <Section id="format">
      <h2 className="section-title">{formatInfo.title}</h2>

      <div className="format-grid">
        {formatInfo.items.map((item) => (
          <div className="format-item" key={item.label}>
            <div className="format-item-label">{item.label}</div>
            <div className="format-item-value">{item.value}</div>
          </div>
        ))}
      </div>

      <div className="speaker">
        <h3 className="subsection-title">{speaker.title}</h3>
        <p className="speaker-text">{speaker.text}</p>
        <ul className="speaker-highlights">
          {speaker.highlights.map((h) => (
            <li key={h}>
              <span className="hero-bullet-mark" aria-hidden="true">
                ▸
              </span>
              {h}
            </li>
          ))}
        </ul>
      </div>
    </Section>
  )
}
