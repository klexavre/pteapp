import Link from "next/link";
import WordDrillList from "@/components/WordDrillList";

export default function WordsPage() {
  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>Single-Word Drills</h1>
        <Link className="view-btn" href="/">← Home</Link>
      </div>
      <WordDrillList />
    </div>
  );
}
