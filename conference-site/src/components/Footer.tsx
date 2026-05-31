import { config } from '../data/content'

export function Footer() {
  const year = new Date().getFullYear()
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div className="footer-brand">
          ИИ для дизайна интерьера и архитектуры · {config.datesShort}
        </div>
        <div className="footer-links">
          <a href={config.telegramUrl} target="_blank" rel="noopener noreferrer">
            Telegram
          </a>
          <a href={`mailto:${config.email}`}>{config.email}</a>
        </div>
        <div className="footer-copy">© {year}. Все права защищены.</div>
      </div>
    </footer>
  )
}
