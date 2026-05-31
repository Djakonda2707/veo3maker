import { Section } from './Section'
import { program } from '../data/content'

export function Program() {
  return (
    <Section id="program">
      <h2 className="section-title">{program.title}</h2>
      <p className="section-lead">{program.subtitle}</p>

      <div className="program-grid">
        {program.days.map((day) => (
          <article className="program-day" key={day.label}>
            <div className="program-day-head">
              <span className="program-day-label">{day.label}</span>
              <h3 className="program-day-title">{day.title}</h3>
            </div>
            <p className="program-day-lead">{day.lead}</p>

            <ol className="program-blocks">
              {day.blocks.map((block) => (
                <li className="program-block" key={block.title}>
                  <div className="program-block-title">{block.title}</div>
                  <div className="program-block-text">{block.text}</div>
                </li>
              ))}
            </ol>
          </article>
        ))}
      </div>
    </Section>
  )
}
