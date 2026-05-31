/** Фон: blueprint-сетка + неоновые градиентные «блобы». Чисто декоративный. */
export function Background() {
  return (
    <div className="bg" aria-hidden="true">
      <div className="bg-grid" />
      <div className="bg-blob bg-blob--cyan" />
      <div className="bg-blob bg-blob--violet" />
      <div className="bg-blob bg-blob--lime" />
      <div className="bg-vignette" />
    </div>
  )
}
