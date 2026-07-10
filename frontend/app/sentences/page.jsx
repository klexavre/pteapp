import Link from "next/link";
import QuestionList from "@/components/QuestionList";

export default function SentencesPage() {
  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>Repeat Sentence Practice</h1>
        <Link className="view-btn" href="/">← Home</Link>
      </div>
      <QuestionList />
    </div>
  );
}
