"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchWords } from "@/lib/api";

function shuffleWords(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function buildWordSets(items, size) {
  const safeSize = Math.max(1, Number(size) || 1);
  const pool = shuffleWords(items);
  const sets = [];
  for (let i = 0; i < pool.length; i += safeSize) {
    const chunk = pool.slice(i, i + safeSize);
    if (chunk.length > 0) sets.push(chunk);
  }
  return sets;
}

export default function WordDrillList() {
  const [words, setWords] = useState([]);
  const [difficulty, setDifficulty] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState("single");
  const [setSize, setSetSize] = useState(20);
  const [sets, setSets] = useState([]);
  const [confirmedSet, setConfirmedSet] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchWords(difficulty || null, 100)
      .then((data) => {
        setWords(data);
        setSets(buildWordSets(data, setSize));
        setConfirmedSet(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [difficulty, setSize]);

  const generateSets = () => {
    if (!words.length) return;
    setSets(buildWordSets(words, setSize));
    setConfirmedSet(null);
  };

  const confirmSet = (index) => {
    setConfirmedSet(index);
  };

  const pickRandomSet = () => {
    if (!sets.length) return;
    const randomIndex = Math.floor(Math.random() * sets.length);
    setConfirmedSet(randomIndex);
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {["", "Easy", "Medium", "Difficult"].map((d) => (
          <button
            key={d || "all"}
            className="view-btn"
            style={{ background: difficulty === d ? "#1e46ac" : "#2a5bd7" }}
            onClick={() => setDifficulty(d)}
          >
            {d || "All"}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        <button className="view-btn" style={{ background: mode === "single" ? "#1e46ac" : "#2a5bd7" }} onClick={() => setMode("single")}>
          Single word
        </button>
        <button className="view-btn" style={{ background: mode === "multi" ? "#1e46ac" : "#2a5bd7" }} onClick={() => setMode("multi")}>
          Multi words
        </button>
      </div>

      {mode === "multi" && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <label style={{ fontSize: 13 }}>Words per set</label>
            <input
              type="number"
              min="1"
              value={setSize}
              onChange={(e) => setSetSize(e.target.value)}
              style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #ccc", width: 90 }}
            />
            <button className="view-btn" onClick={generateSets}>Generate sets</button>
          <button className="view-btn" onClick={pickRandomSet}>Pick a random set</button>
          </div>
          {sets.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div className="pre-practice-label">Generated sets</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
                {sets.map((set, index) => (
                  <button key={`${set[0]?.word || index}-${index}`} className="view-btn" style={{ background: confirmedSet === index ? "#1a8f4c" : "#2a5bd7" }} onClick={() => confirmSet(index)}>
                    Set {index + 1} ({set.length} words)
                  </button>
                ))}
              </div>
              {confirmedSet !== null && (
                <div style={{ marginTop: 10 }}>
                  <Link className="view-btn" href={`/words/sets?size=${Number(setSize) || 1}&difficulty=${encodeURIComponent(difficulty)}&set=${confirmedSet + 1}`}>
                    Start practicing this set
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {loading && <p className="loading-text">Loading word bank...</p>}
      {error && <p className="loading-text">Error: {error}</p>}
      {!loading && !error && words.length === 0 && (
        <p className="loading-text">
          No words found. Run <code>word_extractor.py</code> on your backend first.
        </p>
      )}

      {mode === "single" && (
        <div className="question-list">
          {words.map((w) => (
            <div className="question-row" key={w.word}>
              <div>
                <strong>{w.display}</strong>{" "}
                <span className={`complexity-badge ${w.difficulty.toLowerCase()}`}>
                  {w.difficulty}
                </span>{" "}
                <span style={{ fontSize: 12, color: "#999" }}>
                  {w.syllables} syllable{w.syllables !== 1 ? "s" : ""}
                </span>
              </div>
              <Link className="view-btn" href={`/words/${w.word}`}>
                Practice
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
