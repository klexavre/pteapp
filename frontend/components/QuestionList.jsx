"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchQuestions } from "@/lib/api";

export default function QuestionList() {
  const router = useRouter();
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const handleRandomQuestion = () => {
    if (!questions.length) return;
    const randomQuestion = questions[Math.floor(Math.random() * questions.length)];
    router.push(`/sentences/${randomQuestion.id}`);
  };

  useEffect(() => {
    fetchQuestions()
      .then(setQuestions)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="loading-text">Loading questions...</p>;
  if (error) return <p className="loading-text">Error: {error}</p>;

  return (
    <>
      <div style={{ marginBottom: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button className="view-btn" onClick={handleRandomQuestion}>
          Practice a random question
        </button>
      </div>
      <div className="question-list">
        {questions.map((q) => (
          <div className="question-row" key={q.id}>
            <div>
              <strong>{q.id}</strong>{" "}
              <span className={`complexity-badge ${q.complexity.toLowerCase()}`}>
                {q.complexity}
              </span>
            </div>
            <Link className="view-btn" href={`/sentences/${q.id}`}>
              Practice
            </Link>
          </div>
        ))}
      </div>
    </>
  );
}
