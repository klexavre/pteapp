"use client";

import WaveformAudioPlayer from "@/components/WaveformAudioPlayer";

export default function ScoreDisplay({ score, recordingUrl, referenceAudioUrl }) {
  if (!score && !recordingUrl && !referenceAudioUrl) return null;

  const hasScore = Boolean(score);
  const { overall, content, fluency, pronunciation, transcription, word_breakdown, pauses } = score || {};

  return (
    <div className="score-wrapper">
      {!hasScore ? (
        <p className="remark" style={{ textAlign: "center" }}>
          Recording captured. Submit when you are ready to score it.
        </p>
      ) : (
        <>
          <div className="overall-circle">
            {overall.score}/{overall.out_of}
          </div>
          <p style={{ textAlign: "center", color: "#888", marginTop: -8 }}>OVERALL SCORE</p>

          {(referenceAudioUrl || recordingUrl) && (
            <div style={{ marginTop: 16, marginBottom: 12 }}>
              {referenceAudioUrl && (
                <WaveformAudioPlayer src={referenceAudioUrl} label="Reference pronunciation" />
              )}
              {recordingUrl && (
                <WaveformAudioPlayer src={recordingUrl} label="Your recording" />
              )}
            </div>
          )}

          <div className="subscore-row">
            <span>Content</span>
            <strong>{content.score}/{content.out_of}</strong>
          </div>
          <div className="subscore-row">
            <span>Fluency</span>
            <strong>{fluency.score}/{fluency.out_of}</strong>
          </div>
          <div className="subscore-row">
            <span>Pronunciation</span>
            <strong>{pronunciation.score}/{pronunciation.out_of}</strong>
          </div>

          <p className="remark">Fluency: {fluency.remark} ({fluency.wpm} wpm)</p>
          <p className="remark">Pronunciation: {pronunciation.remark}</p>
          <p className="remark">
            Content: {content.details.substitutions} substitutions, {content.details.deletions} missed
            words, {content.details.insertions} extra words.
          </p>

          <div className="transcript-box">
            <strong>What Whisper heard:</strong> &quot;{transcription}&quot;
            <br /><br />
            <strong>Word-by-word pronunciation confidence:</strong>
            <br />
            {word_breakdown.map((w, i) => {
              const confidence = typeof w.score === "number" ? w.score : null;
              const isLowConfidence = confidence !== null && confidence < 0.5;
              return (
                <span
                  key={i}
                  className={w.class}
                  title={confidence !== null ? `confidence: ${confidence}` : ""}
                  style={{ marginRight: 6, display: "inline-block", whiteSpace: "pre-wrap" }}
                >
                  {isLowConfidence ? "___" : (w.word || "?")} 
                </span>
              );
            })}
          </div>

          {pauses && pauses.length > 0 && (
            <div className="transcript-box" style={{ marginTop: 12 }}>
              <strong>Pauses detected:</strong>
              <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
                {pauses.map((p, i) => (
                  <li key={i} style={{ fontSize: 13, color: "#777" }}>
                    {p.type === "long" ? "Long pause (//)" : "Short pause (/)"} after &quot;{p.after_word}&quot; - {p.duration}s
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
