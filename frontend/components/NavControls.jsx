"use client";

import { useRouter } from "next/navigation";

/**
 * NavControls
 * -----------
 * Previous/Next buttons for moving between questions or words in sequence,
 * plus a "3 / 25" style position indicator. basePath is e.g. "/sentences"
 * or "/words".
 */
export default function NavControls({ basePath, prevId, nextId, position, total }) {
  const router = useRouter();

  return (
    <div className="nav-controls">
      <button
        className="view-btn"
        disabled={!prevId}
        onClick={() => prevId && router.push(`${basePath}/${encodeURIComponent(prevId)}`)}
      >
        ← Previous
      </button>

      {position && total && (
        <span className="nav-position">{position} / {total}</span>
      )}

      <button
        className="view-btn"
        disabled={!nextId}
        onClick={() => nextId && router.push(`${basePath}/${encodeURIComponent(nextId)}`)}
      >
        Next →
      </button>
    </div>
  );
}
