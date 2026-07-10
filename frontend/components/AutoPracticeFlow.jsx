"use client";

import { useEffect, useRef, useState } from "react";
import { playBeep } from "@/lib/beep";

/**
 * AutoPracticeFlow
 * -----------------
 * Drives the full PTE-style timing sequence used by both sentence and
 * word practice pages:
 *
 *   1. PREPARING   - 3 second countdown before the question audio plays
 *   2. PLAYING      - question audio plays once
 *   3. GET_READY    - 3 second countdown after audio ends, before recording
 *   4. BEEP         - short beep tone plays
 *   5. RECORDING    - microphone records automatically, up to maxDuration
 *   6. RECORDED     - recording complete, ready to submit or retry
 *
 * This mirrors real exam timing so practice conditions match the real
 * thing, rather than requiring manual button presses at each step.
 */

const STAGES = {
  PREPARING: "preparing",
  PLAYING: "playing",
  GET_READY: "get_ready",
  BEEP: "beep",
  RECORDING: "recording",
  RECORDED: "recorded",
  ERROR: "error",
};

export default function AutoPracticeFlow({
  audioUrl,
  fallbackText,
  maxRecordDurationMs = 15000,
  preplayCountdownMs = 3000,
  prerecordCountdownMs = 3000,
  onRecordingComplete,
  onStageChange,
  resetKey, // change this value (e.g. question id) to restart the flow
}) {
  const [stage, setStage] = useState(STAGES.PREPARING);
  const [countdown, setCountdown] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);

  const audioElRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timersRef = useRef([]);
  const playbackGuardRef = useRef(false);

  const clearAllTimers = () => {
    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
  };

  const finishPlayback = () => {
    if (playbackGuardRef.current) return;
    playbackGuardRef.current = true;
    handleAudioEnded();
  };

  const setStageWithCallback = (nextStage) => {
    setStage(nextStage);
    if (onStageChange) onStageChange(nextStage === STAGES.RECORDING);
  };

  const runCountdown = (totalMs, onDone) => {
    const seconds = Math.ceil(totalMs / 1000);
    setCountdown(seconds);
    for (let i = 1; i <= seconds; i++) {
      const t = setTimeout(() => setCountdown(seconds - i), i * 1000);
      timersRef.current.push(t);
    }
    const finalTimer = setTimeout(onDone, totalMs);
    timersRef.current.push(finalTimer);
  };

  const selectPreferredVoice = (voices) => {
    const englishUsVoices = voices.filter((voice) => /en(-|_)us/i.test(voice.lang));
    const preferredVoices = englishUsVoices.filter((voice) => /(google|microsoft)/i.test(voice.name));

    if (preferredVoices.length > 0) return preferredVoices[0];

    const englishVoices = voices.filter((voice) => /^en\b/i.test(voice.lang));
    const englishPreferred = englishVoices.find((voice) => /(google|microsoft)/i.test(voice.name));
    if (englishPreferred) return englishPreferred;
    if (englishVoices.length > 0) return englishVoices[0];

    return voices[0];
  };

  const playQuestionAudio = () => {
    playbackGuardRef.current = false;
    setStageWithCallback(STAGES.PLAYING);
    if (audioUrl && audioElRef.current) {
      audioElRef.current.play().catch(() => {
        setErrorMessage("Click anywhere on the page once, then try again (browser blocked autoplay).");
        setStageWithCallback(STAGES.ERROR);
      });
    } else {
      handleAudioEnded();
    }
  };

  const handleAudioEnded = () => {
    setStageWithCallback(STAGES.GET_READY);
    runCountdown(prerecordCountdownMs, async () => {
      setStageWithCallback(STAGES.BEEP);
      await playBeep();
      startRecording();
    });
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
        setStageWithCallback(STAGES.RECORDED);
        if (onRecordingComplete) onRecordingComplete(blob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setStageWithCallback(STAGES.RECORDING);

      const t = setTimeout(() => stopRecording(), maxRecordDurationMs);
      timersRef.current.push(t);
    } catch (err) {
      console.error(err);
      setErrorMessage("Microphone access denied or unavailable.");
      setStageWithCallback(STAGES.ERROR);
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
    playbackGuardRef.current = false;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    setErrorMessage(null);
    setStageWithCallback(STAGES.PREPARING);
    runCountdown(preplayCountdownMs, playQuestionAudio);
  };

  useEffect(() => {
    restart();
    return () => {
      clearAllTimers();
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey]);

  const stageLabel = {
    [STAGES.PREPARING]: `Get ready... starting in ${countdown}s`,
    [STAGES.PLAYING]: "Playing question audio...",
    [STAGES.GET_READY]: `Recording starts in ${countdown}s`,
    [STAGES.BEEP]: "Recording starts now!",
    [STAGES.RECORDING]: "Recording... speak now",
    [STAGES.RECORDED]: "Recording complete.",
    [STAGES.ERROR]: errorMessage || "Something went wrong.",
  }[stage];

  return (
    <div className="auto-flow">
      <audio ref={audioElRef} src={audioUrl || undefined} onEnded={handleAudioEnded} />

      <div className={`stage-indicator stage-${stage}`}>
        {stage === STAGES.RECORDING && <span className="rec-dot" />}
        {stageLabel}
      </div>

      {stage === STAGES.RECORDING && (
        <button className="view-btn" onClick={stopRecording} style={{ marginTop: 12 }}>
          Stop recording
        </button>
      )}

      {stage === STAGES.ERROR && (
        <button className="big-btn" onClick={restart}>
          Retry
        </button>
      )}

      {stage === STAGES.RECORDED && (
        <button className="view-btn" onClick={restart}>
          Restart this question
        </button>
      )}
    </div>
  );
}
