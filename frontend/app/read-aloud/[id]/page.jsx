"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { fetchReadAloudItem, submitReadAloudRecording, submitReport } from "@/lib/api";
import ReadAloudPracticeFlow from "@/components/ReadAloudPracticeFlow";
import ScoreDisplay from "@/components/ScoreDisplay";
import TipsPanel from "@/components/TipsPanel";
import NavControls from "@/components/NavControls";
import {
  getAttempt, recordAttempt, addTimeSpent, setTag, formatTimeSpent,
} from "@/lib/attempts";

const TAG_OPTIONS = ["No Tag", "Red", "Green", "Yellow"];

export default function ReadAloudPracticePage({ params }) {
  const { id } = params;

  const [passage, setPassage] = useState(null);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [score, setScore] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [error, setError] = useState(null);

  const [attempt, setAttempt] = useState({ attemptCount: 0, lastScore: null, history: [], tag: null, timeSpentSeconds: 0 });
  const [resultTab, setResultTab] = useState("me");
  const [reportOpen, setReportOpen] = useState(false);
  const [reportMessage, setReportMessage] = useState("");
  const [reportSent, setReportSent] = useState(false);

  const sessionSecondsRef = useRef(0);
  const timerRef = useRef(null);

  useEffect(() => {
    setPassage(null);
    setRecordedBlob(null);
    setScore(null);
    setError(null);
    setReportOpen(false);
    setReportSent(false);
    fetchReadAloudItem(id).then(setPassage).catch((err) => setError(err.message));
    setAttempt(getAttempt(id));

    sessionSecondsRef.current = 0;
    timerRef.current = setInterval(() => {
      sessionSecondsRef.current += 1;
    }, 1000);

    return () => {
      clearInterval(timerRef.current);
      if (sessionSecondsRef.current > 0) {
        addTimeSpent(id, sessionSecondsRef.current);
      }
    };
  }, [id]);

  const handleRecordingComplete = (blob) => setRecordedBlob(blob);

  const handleSubmit = async () => {
    if (!recordedBlob) return;
    setScoring(true);
    setError(null);
    try {
      const result = await submitReadAloudRecording(id, recordedBlob);
      setScore(result);
      const updated = recordAttempt(id, result.overall.score);
      setAttempt(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setScoring(false);
    }
  };

  const handleTagChange = (e) => {
    const updated = setTag(id, e.target.value);
    setAttempt(updated);
  };

  const handleReportSubmit = async () => {
    if (!reportMessage.trim()) return;
    try {
      await submitReport(id, reportMessage);
      setReportSent(true);
      setReportMessage("");
    } catch (err) {
      setError(err.message);
    }
  };

  if (error) return <div className="app-shell"><p className="loading-text">Error: {error}</p></div>;
  if (!passage) return <div className="app-shell"><p className="loading-text">Loading passage...</p></div>;

  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>{passage.id}</h1>
        <Link className="view-btn" href="/read-aloud">All passages</Link>
      </div>

      <div className="practice-card">
        <div className="meta-header">
          <span className={`complexity-badge ${passage.complexity.toLowerCase()}`}>
            {passage.complexity}
          </span>
          <span className="passage-meta">{passage.word_count} words</span>
          {attempt.attemptCount > 0 && <span className="status-pill attempted">Attempted</span>}

          <select className="tag-select" value={attempt.tag || "No Tag"} onChange={handleTagChange}>
            {TAG_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>

          <span className="time-spent-pill">
            Time Spent: {formatTimeSpent(attempt.timeSpentSeconds)}
          </span>
        </div>

        <p className="ra-page-intro">
          Look at the text below. In {passage.prep_seconds} seconds, you must read this text aloud
          as naturally and clearly as possible. Recording starts automatically after the beep, and
          you have up to {passage.max_record_seconds} seconds - press Stop early if you finish sooner.
        </p>

        <ReadAloudPracticeFlow
          text={passage.text}
          prepSeconds={passage.prep_seconds}
          maxRecordDurationMs={passage.max_record_seconds * 1000}
          audioUrl={passage.audio_url}
          onRecordingComplete={handleRecordingComplete}
          resetKey={passage.id}
        />

        <div className="ra-action-row">
          <button className="big-btn" onClick={handleSubmit} disabled={!recordedBlob || scoring}>
            {scoring ? "Scoring with Whisper..." : "Submit"}
          </button>
        </div>

        {scoring && <p className="loading-text">Running local Whisper transcription, please wait...</p>}

        <div className="stats-row">
          <span className="stat-pill">{attempt.attemptCount}× Attempted</span>
          {attempt.lastScore !== null && (
            <span className="stat-pill">AI Score: {attempt.lastScore}/90</span>
          )}
          <button className="view-btn" onClick={() => setReportOpen((o) => !o)}>Report</button>
        </div>

        {reportOpen && (
          <div className="report-box">
            {reportSent ? (
              <p>Thanks - your report was saved locally.</p>
            ) : (
              <>
                <textarea
                  placeholder="Describe the issue with this passage..."
                  value={reportMessage}
                  onChange={(e) => setReportMessage(e.target.value)}
                />
                <button className="view-btn" onClick={handleReportSubmit}>Send Report</button>
              </>
            )}
          </div>
        )}

        <ScoreDisplay score={score} />
        {score && <TipsPanel tips={score.tips} />}

        {attempt.history.length > 0 && (
          <div className="me-others-wrapper">
            <div className="nav-tabs">
              <button className={`nav-tab-btn ${resultTab === "me" ? "active" : ""}`} onClick={() => setResultTab("me")}>Me</button>
              <button className={`nav-tab-btn ${resultTab === "others" ? "active" : ""}`} onClick={() => setResultTab("others")}>Others</button>
            </div>
            {resultTab === "me" ? (
              <ul className="attempt-history">
                {attempt.history.slice().reverse().map((h, i) => (
                  <li key={i}>Score {h.score}/90 - {new Date(h.at).toLocaleString()}</li>
                ))}
              </ul>
            ) : (
              <p className="loading-text">
                Community answers aren&apos;t available in this local build (no shared backend/accounts).
              </p>
            )}
          </div>
        )}

        <NavControls
          basePath="/read-aloud"
          prevId={passage.prev_id}
          nextId={passage.next_id}
          position={passage.position}
          total={passage.total}
        />
      </div>
    </div>
  );
}
