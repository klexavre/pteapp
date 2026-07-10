"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchWord, submitWordRecording } from "@/lib/api";
import AutoPracticeFlow from "@/components/AutoPracticeFlow";
import NavControls from "@/components/NavControls";
import WaveformAudioPlayer from "@/components/WaveformAudioPlayer";

const VERDICT_STYLE = {
  clear: { color: "#1a8f4c", label: "Clear" },
  needs_work: { color: "#b3720a", label: "Needs work" },
  unclear: { color: "#c0392b", label: "Unclear" },
  no_speech_detected: { color: "#c0392b", label: "No speech detected" },
};

export default function WordPracticePage({ params }) {
  const { word } = params;
  const router = useRouter();

  const [wordInfo, setWordInfo] = useState(null);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordingUrl, setRecordingUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [error, setError] = useState(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    setWordInfo(null);
    setRecordedBlob(null);
    setRecordingUrl((prevUrl) => {
      if (prevUrl) URL.revokeObjectURL(prevUrl);
      return null;
    });
    setResult(null);
    setError(null);
    fetchWord(word).then(setWordInfo).catch((err) => setError(err.message));
  }, [word]);

  useEffect(() => {
    return () => {
      if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    };
  }, [recordingUrl]);

  const scoreVisible = Boolean(result);

  useEffect(() => {
    // Do not auto-advance after showing the score. Allow the user to
    // explicitly press Next when they are ready.
    return undefined;
  }, [router, scoreVisible, wordInfo?.next_word]);

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
      const scoreResult = await submitWordRecording(word, recordedBlob);
      setResult(scoreResult);
    } catch (err) {
      setError(err.message);
    } finally {
      setScoring(false);
    }
  };

  if (error) return <div className="app-shell"><p className="loading-text">Error: {error}</p></div>;
  if (!wordInfo) return <div className="app-shell"><p className="loading-text">Loading word...</p></div>;

  const verdictStyle = result ? VERDICT_STYLE[result.verdict] : null;

  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>Word Drill</h1>
        <Link className="view-btn" href="/words">All words</Link>
      </div>

      <div className={`practice-card ${isRecording ? "recording" : ""}`}>
        <div className="word-display">
          <span className={`complexity-badge ${wordInfo.difficulty.toLowerCase()}`}>
            {wordInfo.difficulty}
          </span>
          <h2>{wordInfo.display}</h2>
          <p style={{ color: "#999", fontSize: 13 }}>
            {wordInfo.syllables} syllable{wordInfo.syllables !== 1 ? "s" : ""}
            {wordInfo.source_questions?.length > 0 && (
              <> · appears in {wordInfo.source_questions.join(", ")}</>
            )}
          </p>
          {!wordInfo.audio_url && (
            <p style={{ color: "#b3720a", fontSize: 12 }}>
              No pre-generated audio yet - using your browser&apos;s built-in voice.
            </p>
          )}
        </div>

        <AutoPracticeFlow
          audioUrl={wordInfo.audio_url}
          fallbackText={wordInfo.audio_url ? null : wordInfo.display}
          maxRecordDurationMs={4000}
          preplayCountdownMs={3000}
          prerecordCountdownMs={3000}
          onRecordingComplete={handleRecordingComplete}
          onStageChange={setIsRecording}
          resetKey={wordInfo.word}
        />

        <div style={{ textAlign: "center" }}>
          <button className="big-btn" onClick={handleSubmit} disabled={!recordedBlob || scoring}>
            {scoring ? "Scoring..." : "Submit"}
          </button>
        </div>

        {scoring && <p className="loading-text">Checking your pronunciation...</p>}

        {result && (
          <div className="score-wrapper" style={{ textAlign: "center" }}>
            <p style={{ color: "#666", fontSize: 13, marginBottom: 8 }}>
              Press Next when you are ready to continue to the next word.
            </p>
            <div
              className="overall-circle"
              style={{ borderColor: verdictStyle.color, width: 90, height: 90, fontSize: 18 }}
            >
              {result.score}/{result.out_of}
            </div>
            <p style={{ color: verdictStyle.color, fontWeight: 700, marginTop: 4 }}>
              {verdictStyle.label}
            </p>
            <p className="remark">{result.remark}</p>
            {(wordInfo.audio_url || recordingUrl) && (
              <div style={{ marginTop: 16, marginBottom: 8 }}>
                {wordInfo.audio_url && (
                  <WaveformAudioPlayer src={wordInfo.audio_url} label="Reference pronunciation" />
                )}
                {recordingUrl && (
                  <WaveformAudioPlayer blob={recordedBlob} label="Your recording" />
                )}
              </div>
            )}
            {result.transcription ? (
              <p style={{ color: "#555", marginTop: 6, fontSize: 13 }}>
                Heard: {result.transcription}
              </p>
            ) : null}
          </div>
        )}

        <NavControls
          basePath="/words"
          prevId={wordInfo.prev_word}
          nextId={wordInfo.next_word}
          position={wordInfo.position}
          total={wordInfo.total}
        />
      </div>
    </div>
  );
}
