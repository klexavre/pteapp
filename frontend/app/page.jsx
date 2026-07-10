import Link from "next/link";
import SyncDataPanel from "@/components/SyncDataPanel";

export default function HomePage() {
  return (
    <div className="app-shell" suppressHydrationWarning>
      <div className="home-hero" suppressHydrationWarning>
        <h1>PTE Practice Platform</h1>
        <p>A professional local testing environment for PTE speaking practice.</p>
        <SyncDataPanel />
      </div>

      <div className="home-cards home-cards-3" suppressHydrationWarning>
        <Link href="/sentences" className="home-card" suppressHydrationWarning>
          <div className="icon">🗣️</div>
          <h2>Repeat Sentence</h2>
          <p>
            Listen to a sentence, then repeat it back. Auto-play, timed
            countdown, and beep-cued recording - just like the real exam.
          </p>
        </Link>
        
        <Link href="/read-aloud" className="home-card">
          <div className="icon">📖</div>
          <h2>Read Aloud</h2>
          <p>
            Read a passage aloud after a timed prep countdown. Great for
            building fluency and pronunciation on longer text.
          </p>
        </Link>

        <Link href="/words" className="home-card" suppressHydrationWarning>
          <div className="icon">🔤</div>
          <h2>Word Drills</h2>
          <p>
            Practice pronunciation one word at a time. Great for building up
            clarity before attempting full sentences.
          </p>
        </Link>
      </div>
    </div>
  );
}
