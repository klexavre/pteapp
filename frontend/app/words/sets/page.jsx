"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { fetchWords, submitWordSetRecordings } from "@/lib/api";
import { playBeep } from "@/lib/beep";

const SPEAK_WINDOW_MS = 2000;

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

function WordSetPracticePageInner() {
  const searchParams = useSearchParams();
  const requestedSize = Math.max(1, Number(searchParams.get("size")) || 10);
  const requestedDifficulty = searchParams.get("difficulty") || "";
  const requestedSet = Math.max(1, Number(searchParams.get("set")) || 1);

  const [words, setWords] = useState([]);
  const [allSets, setAllSets] = useState([]);
  const [activeSetIndex, setActiveSetIndex] = useState(Math.max(0, requestedSet - 1));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [stage, setStage] = useState("ready");
  const [countdown, setCountdown] = useState(2);
  const [recordings, setRecordings] = useState([]);
  const [scoring, setScoring] = useState(false);
  const [results, setResults] = useState(null);
  const [isRecording, setIsRecording] = useState(false);

  const setOverallScore = useMemo(() => {
    if (!results || !results.length) return null;
    const total = results.reduce((sum, item) => sum + Number(item.score || 0), 0);
    return Math.round((total / results.length) * 10) / 10;
  }, [results]);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const timersRef = useRef([]);

  const clearTimers = () => {
    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
  };

  const resetPractice = () => {
    clearTimers();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCurrentIndex(0);
    setStage("ready");
    setCountdown(2);
    setRecordings([]);
    setResults(null);
    setScoring(false);
    setError(null);
  };

  useEffect(() => {
    setLoading(true);
    fetchWords(requestedDifficulty || null, 100)
      .then((data) => {
        const generatedSets = buildWordSets(data, requestedSize);
        setAllSets(generatedSets);
        const safeIndex = Math.min(Math.max(requestedSet - 1, 0), Math.max(generatedSets.length - 1, 0));
        setActiveSetIndex(safeIndex);
        setWords(generatedSets[safeIndex] || []);
        resetPractice();
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));

    return () => {
      clearTimers();
      if (streamRef.current) streamRef.current.getTracks().forEach((track) => track.stop());
    };
  }, [requestedDifficulty, requestedSet, requestedSize]);

  useEffect(() => {
    if (words.length === 0 || stage !== "ready") return;
    startNextWord();
  }, [words, currentIndex, stage]);

  useEffect(() => {
    setIsRecording(stage === "speaking");
  }, [stage]);

  const startNextWord = async () => {
    clearTimers();

    if (currentIndex >= words.length) {
      setStage("submit");
      return;
    }

    setStage("showing");
    setCountdown(2);

    const timer = setTimeout(() => setCountdown(1), 1000);
    timersRef.current.push(timer);
    const finalTimer = setTimeout(async () => {
      await playBeep();
      await captureWord();
    }, 2000);
    timersRef.current.push(finalTimer);
  };

  const captureWord = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setRecordings((prev) => [...prev, blob]);
        setStage("review");
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setStage("speaking");

      const stopTimer = setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
          mediaRecorderRef.current.stop();
        }
      }, SPEAK_WINDOW_MS);
      timersRef.current.push(stopTimer);
    } catch (err) {
      console.error(err);
      setError("Microphone access denied or unavailable.");
      setStage("error");
    }
  };

  const handleSubmit = async () => {
    if (recordings.length !== words.length) return;
    setScoring(true);
    setError(null);
    try {
      const payload = await submitWordSetRecordings(words.map((w) => w.word), recordings);
      setResults(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setScoring(false);
    }
  };

  const handleAdvance = () => {
    if (currentIndex + 1 >= words.length) {
      setStage("submit");
      return;
    }

    setCurrentIndex((prevIndex) => prevIndex + 1);
    setStage("ready");
  };

  const handleRetry = () => {
    setWords(allSets[activeSetIndex] || []);
    resetPractice();
  };

  const handleNextSet = () => {
    if (activeSetIndex + 1 < allSets.length) {
      const nextIndex = activeSetIndex + 1;
      setActiveSetIndex(nextIndex);
      setWords(allSets[nextIndex] || []);
      resetPractice();
    }
  };

  const promptText = useMemo(() => words[currentIndex]?.display || "", [words, currentIndex]);
  const setLabel = useMemo(() => `${activeSetIndex + 1} of ${allSets.length || 1}`, [activeSetIndex, allSets.length]);

  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>Word Set Practice</h1>
        <Link className="view-btn" href="/words">← Back</Link>
      </div>

      <div className={`practice-card ${isRecording ? "recording" : ""}`}>
        {loading && <p className="loading-text">Loading word set...</p>}
        {error && <p className="loading-text">Error: {error}</p>}

        {!loading && !error && words.length > 0 && (
          <>
            <div className="word-display">
              <p style={{ color: "#666", marginBottom: 6 }}>Set {setLabel}</p>
              <h2>{promptText}</h2>
            </div>

            {stage === "ready" && <p className="loading-text">Preparing next word...</p>}
            {stage === "showing" && <p className="loading-text">Word shown for {countdown} second{countdown !== 1 ? "s" : ""}...</p>}
            {stage === "speaking" && <p className="loading-text">Recording for 2 seconds...</p>}
            {stage === "review" && (
              <div style={{ textAlign: "center" }}>
                <p className="loading-text">Recording saved. {currentIndex + 1 < words.length ? "Move to the next word." : "Ready to submit the set."}</p>
                <button className="big-btn" onClick={handleAdvance}>
                  {currentIndex + 1 < words.length ? "Next word" : "Submit set"}
                </button>
              </div>
            )}
            {stage === "submit" && (
              <div style={{ textAlign: "center" }}>
                <p className="loading-text">All {words.length} words recorded. Submit to score the set.</p>
                <button className="big-btn" onClick={handleSubmit} disabled={scoring || recordings.length !== words.length}>
                  {scoring ? "Scoring..." : "Submit set"}
                </button>
              </div>
            )}
          </>
        )}

        {results && (
          <div className="score-wrapper">
            <div className="pre-practice-title" style={{ marginBottom: 10 }}>Set results</div>
            {setOverallScore !== null && (
              <p className="remark" style={{ marginBottom: 8 }}>
                Overall set score: {setOverallScore}/{results[0]?.out_of}
              </p>
            )}
            {results.map((result, index) => {
              const roundedScore = Math.round(Number(result.score) * 2) / 2;
              return (
                <div key={`${result.word}-${index}`} style={{ marginBottom: 10 }}>
                  <strong>{result.word}</strong>: {roundedScore}/{result.out_of} · {result.verdict}
                  {result.transcription ? <div className="remark">Heard: {result.transcription}</div> : null}
                </div>
              );
            })}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 16 }}>
              <button className="view-btn" onClick={handleRetry}>Try again</button>
              {activeSetIndex + 1 < allSets.length && (
                <button className="view-btn" onClick={handleNextSet}>Next set</button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WordSetPracticePage() {
  return (
    <Suspense fallback={<div className="app-shell"><div className="practice-card"><p className="loading-text">Loading set practice...</p></div></div>}>
      <WordSetPracticePageInner />
    </Suspense>
  );
}
