import Link from "next/link";
import ReadAloudList from "@/components/ReadAloudList";

export default function ReadAloudPage() {
  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>Read Aloud Practice</h1>
        <Link className="view-btn" href="/">← Home</Link>
      </div>
      <ReadAloudList />
    </div>
  );
}
