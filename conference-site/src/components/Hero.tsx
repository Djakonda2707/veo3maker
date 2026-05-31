import { config, hero } from '../data/content'
import { Countdown } from './Countdown'

export function Hero() {
  return (
    <header className="hero">
      <div className="container hero-inner">
        <div className="hero-badge">{hero.badge}</div>

        <h1 className="hero-title">
          {hero.title}
          <span className="hero-title-accent"> {hero.titleAccent}</span>
        </h1>

        <p className="hero-subtitle">{hero.subtitle}</p>

        <ul className="hero-bullets">
          {hero.bullets.map((b) => (
            <li key={b}>
              <span className="hero-bullet-mark" aria-hidden="true">
                ▸
              </span>
              {b}
            </li>
          ))}
        </ul>

        <div className="hero-meta">
          <div className="hero-meta-item">
            <span className="hero-meta-label">Когда</span>
            <span className="hero-meta-value">{config.datesShort}</span>
          </div>
          <div className="hero-meta-item">
            <span className="hero-meta-label">Формат</span>
            <span className="hero-meta-value">{config.format}</span>
          </div>
          <div className="hero-meta-item">
            <span className="hero-meta-label">Длительность</span>
            <span className="hero-meta-value">{config.duration}</span>
          </div>
        </div>

        <div className="hero-cta">
          <a className="btn btn--primary btn--lg" href={config.paymentUrl} target="_blank" rel="noopener noreferrer">
            {hero.ctaPrimary} — {config.priceEarly}
          </a>
          <a className="btn btn--ghost btn--lg" href="#program">
            {hero.ctaSecondary}
          </a>
        </div>

        <div className="hero-timer">
          <span className="hero-timer-text">
            Цена вырастет до {config.priceFull}. До повышения осталось:
          </span>
          <Countdown targetIso={config.priceRaiseAt} expiredLabel={`Сейчас цена ${config.priceFull}`} />
        </div>
      </div>
    </header>
  )
}
