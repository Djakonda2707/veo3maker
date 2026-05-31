import { Background } from './components/Background'
import { Hero } from './components/Hero'
import { PainPoints } from './components/PainPoints'
import { Outcomes } from './components/Outcomes'
import { Program } from './components/Program'
import { Bonuses } from './components/Bonuses'
import { FormatTiming } from './components/FormatTiming'
import { Pricing } from './components/Pricing'
import { Faq } from './components/Faq'
import { FinalCta } from './components/FinalCta'
import { Footer } from './components/Footer'
import { StickyCta } from './components/StickyCta'

export default function App() {
  return (
    <>
      <Background />
      <main>
        <Hero />
        <PainPoints />
        <Outcomes />
        <Program />
        <Bonuses />
        <FormatTiming />
        <Pricing />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
      <StickyCta />
    </>
  )
}
