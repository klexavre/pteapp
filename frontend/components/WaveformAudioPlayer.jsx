"use client";

import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";

export default function WaveformAudioPlayer({ src, blob, label, stream, compact = false }) {
  const containerRef = useRef(null);
  const waveSurferRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!containerRef.current || (!src && !blob)) return;

    // Destroy existing instance if any
    if (waveSurferRef.current) {
      waveSurferRef.current.destroy();
    }

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#8fb3ff",
      progressColor: "#1e46ac",
      cursorColor: "#1e46ac",
      barWidth: 3,
      barGap: 2,
      barRadius: 2,
      height: compact ? 60 : 80,
      normalize: true,
      responsive: true,
    });

    waveSurferRef.current = ws;

    // Handle playback events
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleFinish = () => setIsPlaying(false);

    ws.on("play", handlePlay);
    ws.on("pause", handlePause);
    ws.on("finish", handleFinish);

    // Prefer an in-memory Blob (recording) when provided, otherwise handle src
    let localBlobUrl = null;
    if (blob) {
      try {
        localBlobUrl = URL.createObjectURL(blob);
        ws.load(localBlobUrl).catch((err) => {
          if (err.name === "AbortError") return;
          console.error("Failed to load audio blob:", err);
        });
      } catch (err) {
        console.error("Failed to create blob URL:", err);
      }
    } else if (src) {
      // Check if it's a blob URL or HTTP URL
      if (src.startsWith("blob:")) {
        // For blob URLs, load directly
        ws.load(src).catch((err) => {
          if (err.name === "AbortError") return;
          console.error("Failed to load audio:", err);
        });
      } else {
        // For HTTP URLs, fetch as blob first to avoid CORS issues and request anonymously
        (async () => {
          try {
            const response = await fetch(src, { mode: "cors", credentials: "omit" });
            if (!response.ok) {
              console.error(`Failed to fetch audio: ${response.status}`);
              return;
            }
            const fetchedBlob = await response.blob();
            const fetchedBlobUrl = URL.createObjectURL(fetchedBlob);
            ws.load(fetchedBlobUrl);
          } catch (err) {
            if (err.name === "AbortError") return;
            console.error("Failed to load audio:", err);
          }
        })();
      }
    }

    return () => {
      if (waveSurferRef.current) {
        waveSurferRef.current.unAll();
        waveSurferRef.current.destroy();
        waveSurferRef.current = null;
      }
      if (localBlobUrl) {
        try {
          URL.revokeObjectURL(localBlobUrl);
        } catch (e) {}
      }
    };
  }, [src, blob, compact]);

  const togglePlayback = () => {
    if (!waveSurferRef.current) return;
    waveSurferRef.current.playPause();
  };

  if (!src && !blob) return null;

  return (
    <div className="transcript-box" style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <strong>{label}</strong>
        <button className="view-btn" onClick={togglePlayback} style={{ padding: "6px 10px", fontSize: 12 }}>
          {isPlaying ? "Pause" : "Play"}
        </button>
      </div>
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: compact ? 60 : 80,
          borderRadius: 8,
          background: "#f5f7ff",
          overflow: "hidden",
        }}
      />
    </div>
  );
}
