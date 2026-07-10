"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchQuestion, submitRecording } from "@/lib/api";
import AutoPracticeFlow from "@/components/AutoPracticeFlow";
import ScoreDisplay from "@/components/ScoreDisplay";
import TipsPanel from "@/components/TipsPanel";
import NavControls from "@/components/NavControls";

export default function SentencePracticePage({ params }) {
  const { id } = params;

  const [question, setQuestion] = useState(null);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordingUrl, setRecordingUrl] = useState(null);
  const [score, setScore] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setQuestion(null);
    setRecordedBlob(null);
    setRecordingUrl((prevUrl) => {
      if (prevUrl) URL.revokeObjectURL(prevUrl);
      return null;
    });
    setScore(null);
    setError(null);
    fetchQuestion(id).then(setQuestion).catch((err) => setError(err.message));
  }, [id]);

  useEffect(() => {
    return () => {
      if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    };
  }, [recordingUrl]);

  const handleRecordingComplete = (blob) => {
    setRecordedBlob(blob);
    setRecordingUrl((prevUrl) => {
      if (prevUrl) URL.revokeObjectURL(prevUrl);
      return URL.createObjectURL(blob);
    });
  };

  const handleSubmit = async () => {
    if (!recordedBlob) return;
    setScoring(true);
    setError(null);
    try {
      const result = await submitRecording(id, recordedBlob);
      setScore(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setScoring(false);
    }
  };

  if (error) return <div className="app-shell"><p className="loading-text">Error: {error}</p></div>;
  if (!question) return <div className="app-shell"><p className="loading-text">Loading question...</p></div>;

  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>{question.id}</h1>
        <Link className="view-btn" href="/sentences">All questions</Link>
      </div>

      <div className="practice-card">
        <p className="instructions">
          You will hear a sentence. Please repeat the sentence exactly as you hear it.
          You will hear the sentence only once. Recording starts automatically after the beep.
        </p>

        <AutoPracticeFlow
          audioUrl={question.audio_url}
          fallbackText={null}
          maxRecordDurationMs={15000}
          preplayCountdownMs={3000}
          prerecordCountdownMs={3000}
          onRecordingComplete={handleRecordingComplete}
          resetKey={question.id}
        />

        <div style={{ textAlign: "center" }}>
          <button className="big-btn" onClick={handleSubmit} disabled={!recordedBlob || scoring}>
            {scoring ? "Scoring with Whisper..." : "Submit"}
          </button>
        </div>

        {scoring && <p className="loading-text">Running local Whisper transcription, please wait...</p>}

        <ScoreDisplay score={score} recordingUrl={recordingUrl} referenceAudioUrl={question.audio_url} />
        {score && <TipsPanel tips={score.tips} />}

        <NavControls
          basePath="/sentences"
          prevId={question.prev_id}
          nextId={question.next_id}
          position={question.position}
          total={question.total}
        />
      </div>
    </div>
  );
}
