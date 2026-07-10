"use client";

import { useEffect, useRef, useState } from "react";
import { playBeep } from "@/lib/beep";

/**
 * ReadAloudPracticeFlow
 * -----------------------
 * Unlike AutoPracticeFlow (Repeat Sentence / Word Drills), there is no
 * audio to listen to here - the user reads the passage text directly off
 * the screen. The sequence is:
 *
 *   1. PREP        - passage text is shown, countdown (prep_seconds,
 *                     scaled to passage length by txt_to_readaloud.py)
 *   2. BEEP         - short beep tone
 *   3. RECORDING    - microphone records automatically; auto-stops at
 *                     maxRecordDurationMs, but the user can also press
 *                     Stop early once they've finished reading (real Read
 *                     Aloud doesn't force you to use all the time)
 *   4. RECORDED     - ready to submit or restart
 */

const STAGES = {
  PREP: "prep",
  BEEP: "beep",
  RECORDING: "recording",
  RECORDED: "recorded",
  ERROR: "error",
};

export default function ReadAloudPracticeFlow({
  text,
  prepSeconds = 30,
  maxRecordDurationMs = 45000,
  audioUrl = null,
  onRecordingComplete,
  resetKey,
}) {
  const [stage, setStage] = useState(STAGES.PREP);
  const [countdown, setCountdown] = useState(prepSeconds);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);
  const [playingModelAudio, setPlayingModelAudio] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timersRef = useRef([]);
  const recordingIntervalRef = useRef(null);

  const clearAllTimers = () => {
    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
    if (recordingIntervalRef.current) {
      clearInterval(recordingIntervalRef.current);
      recordingIntervalRef.current = null;
    }
  };

  const runPrepCountdown = () => {
    setCountdown(prepSeconds);
    for (let i = 1; i <= prepSeconds; i++) {
      const t = setTimeout(() => setCountdown(prepSeconds - i), i * 1000);
      timersRef.current.push(t);
    }
    const finalTimer = setTimeout(async () => {
      setStage(STAGES.BEEP);
      await playBeep();
      startRecording();
    }, prepSeconds * 1000);
    timersRef.current.push(finalTimer);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        setStage(STAGES.RECORDED);
        if (onRecordingComplete) onRecordingComplete(blob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setStage(STAGES.RECORDING);
      setRecordingSeconds(0);

      recordingIntervalRef.current = setInterval(() => {
        setRecordingSeconds((s) => s + 1);
      }, 1000);

      const t = setTimeout(() => stopRecording(), maxRecordDurationMs);
      timersRef.current.push(t);
    } catch (err) {
      console.error(err);
      setErrorMessage("Microphone access denied or unavailable.");
      setStage(STAGES.ERROR);
    }
  };

  const stopRecording = () => {
    clearAllTimers();
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const restart = () => {
    clearAllTimers();
    if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    setErrorMessage(null);
    setStage(STAGES.PREP);
    runPrepCountdown();
  };

  const handlePlayModelAudio = async () => {
    if (!audioUrl) return;
    if (typeof window === "undefined") return;

    const audio = new Audio(audioUrl);
    audio.onended = () => setPlayingModelAudio(false);
    audio.onerror = () => setPlayingModelAudio(false);
    try {
      setPlayingModelAudio(true);
      await audio.play();
    } catch (err) {
      console.error(err);
      setPlayingModelAudio(false);
    }
  };

  useEffect(() => {
    restart();
    return () => {
      clearAllTimers();
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey]);

  return (
    <div className="auto-flow read-aloud-flow">
      <div className={`stage-indicator stage-${stage}`}>
        {stage === STAGES.PREP && `Get ready to read... starts in ${countdown}s`}
        {stage === STAGES.BEEP && "Recording starts now!"}
        {stage === STAGES.RECORDING && (
          <>
            <span className="rec-dot" /> Recording... {recordingSeconds}s
          </>
        )}
        {stage === STAGES.RECORDED && "Recording complete."}
        {stage === STAGES.ERROR && (errorMessage || "Something went wrong.")}
      </div>

      {/* The passage text is always visible during PREP and RECORDING -
          this is the core difference from Repeat Sentence, where the text
          is hidden until after scoring. */}
      {(stage === STAGES.PREP || stage === STAGES.BEEP || stage === STAGES.RECORDING) && (
        <div className="read-aloud-text">{text}</div>
      )}

      {audioUrl && (
        <div className="ra-action-row">
          <button className="view-btn" onClick={handlePlayModelAudio} disabled={stage === STAGES.RECORDING}>
            {playingModelAudio ? "Playing..." : "▶ Listen to model reading"}
          </button>
        </div>
      )}

      {stage === STAGES.RECORDING && (
        <div className="ra-action-row">
          <button className="big-btn" onClick={stopRecording}>
            ⏹ Stop
          </button>
        </div>
      )}

      {stage === STAGES.ERROR && (
        <div className="ra-action-row">
          <button className="big-btn" onClick={restart}>Retry</button>
        </div>
      )}

      {stage === STAGES.RECORDED && (
        <div className="ra-action-row">
          <button className="view-btn" onClick={restart}>Restart this passage</button>
        </div>
      )}
    </div>
  );
}
