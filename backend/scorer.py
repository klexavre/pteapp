"""
scorer.py
---------
Turns a raw Whisper transcription result into PTE-style scores:
  - Content       (did they say the right words, in the right order?)
  - Fluency       (was the pace natural, no long pauses/rushing?)
  - Pronunciation (proxy score based on Whisper's per-segment confidence)

This is a from-scratch, transparent scoring approach (no black-box vendor).
It will not be as accurate as a specialised phoneme-level pronunciation
model (e.g. Azure Pronunciation Assessment), but it's fully local, free,
and good enough to practice with.
"""

import re
import string
from jiwer import wer, process_words

from tips_data import get_tips_for_score


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def score_content(reference: str, hypothesis: str) -> dict:
    """
    Word Error Rate based content score.
    Fewer substitutions/deletions/insertions -> higher score.
    """
    ref_norm = normalize(reference)
    hyp_norm = normalize(hypothesis)

    if not hyp_norm:
        return {
            "score": 0,
            "out_of": 90,
            "wer": 1.0,
            "details": {"substitutions": 0, "deletions": len(ref_norm.split()), "insertions": 0},
        }

    result = process_words(ref_norm, hyp_norm)
    error_rate = result.wer  # 0.0 = perfect, 1.0+ = very wrong

    # Convert WER into a 0-90 score. WER of 0 -> 90, WER of 1+ -> 0.
    raw_score = max(0, 90 * (1 - error_rate))

    return {
        "score": round(raw_score, 1),
        "out_of": 90,
        "wer": round(error_rate, 3),
        "details": {
            "substitutions": result.substitutions,
            "deletions": result.deletions,
            "insertions": result.insertions,
        },
    }


def score_fluency(word_count: int, duration_seconds: float, ideal_low: int = 110, ideal_high: int = 160) -> dict:
    """
    Words-per-minute based fluency score.
    Default 110-160 wpm matches Repeat Sentence's casual-speech pace.
    Read Aloud passages are read from visible text rather than recalled
    from memory, so a slightly faster natural range fits better - see
    score_read_aloud() below, which passes ideal_low=130, ideal_high=170.
    Too slow (long pauses/hesitation) or too fast (rushed) both lose points.
    """
    if duration_seconds <= 0 or word_count == 0:
        return {"score": 0, "out_of": 90, "wpm": 0, "remark": "No speech detected."}

    wpm = (word_count / duration_seconds) * 60
    if ideal_low <= wpm <= ideal_high:
        score = 90
        remark = "Great pace, natural and fluent."
    else:
        # distance from the nearest edge of the ideal range
        distance = ideal_low - wpm if wpm < ideal_low else wpm - ideal_high
        # lose ~2 points per wpm outside the ideal range, floor at 10
        score = max(10, 90 - distance * 2)
        remark = "A little slow/hesitant." if wpm < ideal_low else "A little rushed."

    return {"score": round(score, 1), "out_of": 90, "wpm": round(wpm, 1), "remark": remark}


def score_pronunciation(segments: list) -> dict:
    """
    Proxy pronunciation score using Whisper's average log-probability per
    segment as a stand-in for confidence/clarity. This is NOT true phoneme
    level nativeness scoring - it's the best signal available for free,
    fully local scoring. Documented as an approximation.
    """
    if not segments:
        return {"score": 0, "out_of": 90, "remark": "No speech detected."}

    avg_logprobs = [seg.get("avg_logprob", -5.0) for seg in segments if seg.get("text", "").strip()]
    if not avg_logprobs:
        return {"score": 0, "out_of": 90, "remark": "No speech detected."}

    mean_logprob = sum(avg_logprobs) / len(avg_logprobs)
    no_speech_probs = [seg.get("no_speech_prob", 0.0) for seg in segments]
    if any(p >= 0.7 for p in no_speech_probs):
        return {"score": 0, "out_of": 90, "remark": "No speech detected."}

    # avg_logprob from Whisper can go below -1.0 on low confidence audio.
    # Map [-1.5, 0.0] to [0, 1] for a smoother confidence scale.
    normalized = max(0.0, min(1.0, (mean_logprob + 1.5) / 1.5))
    score = 10 + normalized * 80

    if score >= 80:
        remark = "Clear and confident pronunciation."
    elif score >= 60:
        remark = "Good pronunciation, but there is room for improvement."
    elif score >= 35:
        remark = "Pronunciation can be improved. Speak more clearly and steadily."
    else:
        remark = "Pronunciation needs work. Slow down and pronounce each sound distinctly."

    return {"score": round(score, 1), "out_of": 90, "remark": remark}


def word_level_diff(reference: str, hypothesis: str) -> list:
    """
    Returns a word-by-word breakdown of the reference sentence, tagging each
    word as good/average/bad based on whether Whisper heard it correctly.
    Used to render the color-coded transcript in the UI.
    """
    ref_words = normalize(reference).split()
    hyp_words = set(normalize(hypothesis).split())

    breakdown = []
    for w in ref_words:
        if w in hyp_words:
            cls = "color-success"
        else:
            cls = "color-danger"
        breakdown.append({"word": w, "class": cls})
    return breakdown


def compute_full_score(reference: str, hypothesis: str, segments: list, duration_seconds: float,
                        alignment=None, pauses=None, ideal_wpm_low: int = 110, ideal_wpm_high: int = 160) -> dict:
    """
    alignment/pauses are optional - if forced_alignment.align() was run
    upstream (in server.py), pass its results in here for a much more
    accurate pronunciation score and real pause detection. If omitted,
    falls back to the Whisper-confidence proxy (score_pronunciation above).
    """
    word_count = len(normalize(hypothesis).split())

    content = score_content(reference, hypothesis)
    fluency = score_fluency(word_count, duration_seconds, ideal_low=ideal_wpm_low, ideal_high=ideal_wpm_high)

    if alignment:
        # Real forced-alignment based pronunciation score (preferred)
        from forced_alignment import pronunciation_score_from_alignment
        pron_result = pronunciation_score_from_alignment(alignment)
        pronunciation = {"score": pron_result["score"], "out_of": 90,
                          "remark": "Score based on real forced-alignment acoustic confidence."}
        word_breakdown = pron_result["word_scores"]
    else:
        # Fallback: Whisper segment-confidence proxy
        pronunciation = score_pronunciation(segments)
        word_breakdown = word_level_diff(reference, hypothesis)

    overall = round((content["score"] + fluency["score"] + pronunciation["score"]) / 3, 1)

    tips = get_tips_for_score(
        content_score=content["score"],
        fluency_score=fluency["score"],
        pronunciation_score=pronunciation["score"],
    )

    return {
        "overall": {"score": overall, "out_of": 90},
        "content": content,
        "fluency": fluency,
        "pronunciation": pronunciation,
        "transcription": hypothesis,
        "word_breakdown": word_breakdown,
        "pauses": pauses or [],
        "tips": tips,
    }


def score_single_word(word: str, alignment: list, transcription: str = "") -> dict:
    """
    Scores a single-word drill recording. `alignment` is the result of
    forced_alignment.align(audio_path, word) - for a one-word reference,
    this returns a single-item list with that word's acoustic confidence.

    If a transcript is available, it is used as a strong signal for whether
    the spoken word matches the target. The final score blends acoustic
    confidence with transcript correctness so the result is more stable and
    closer to the user's real performance.
    """
    normalized_target = normalize(word)
    normalized_transcription = normalize(transcription)
    matched = bool(normalized_transcription and normalized_transcription == normalized_target)

    if not alignment:
        if matched:
            score = 80.0
            verdict = "clear"
            remark = "You said the word clearly."
        else:
            return {
                "word": word,
                "score": 0,
                "out_of": 90,
                "verdict": "no_speech_detected",
                "remark": "No speech detected - make sure your microphone is working and try again.",
                "transcription": transcription,
            }
    else:
        confidence = alignment[0]["score"]  # 0.0 - 1.0
        score = round(confidence * 90, 1)
        if matched:
            score = min(90.0, round((score * 0.6) + (80.0 * 0.4), 1))

    if score >= 70:
        verdict = "clear"
        remark = "Clear pronunciation - nice work."
    elif score >= 45:
        verdict = "needs_work"
        remark = "Understandable, but not fully clear yet. Try again, speaking a little slower."
    else:
        verdict = "unclear"
        remark = "Hard to make out. Slow down and exaggerate each sound, then try again."

    if not matched and normalized_transcription:
        verdict = "unclear"
        remark = f"You said '{transcription}', but the target word was '{word}'."
        score = max(10.0, score * 0.7)

    return {
        "word": word,
        "score": score,
        "out_of": 90,
        "verdict": verdict,
        "remark": remark,
        "transcription": normalized_transcription or transcription,
    }


def score_read_aloud(reference: str, hypothesis: str, segments: list, duration_seconds: float,
                      alignment=None, pauses=None) -> dict:
    """
    Thin wrapper around compute_full_score using Read Aloud's ideal pace
    (130-170 wpm) instead of Repeat Sentence's (110-160 wpm) - reading
    visible text aloud is naturally a bit faster than recalling and
    repeating a heard sentence from memory. Everything else (Content via
    WER, Pronunciation via forced-alignment confidence, tips) is identical.
    """
    return compute_full_score(
        reference=reference,
        hypothesis=hypothesis,
        segments=segments,
        duration_seconds=duration_seconds,
        alignment=alignment,
        pauses=pauses,
        ideal_wpm_low=130,
        ideal_wpm_high=170,
    )
