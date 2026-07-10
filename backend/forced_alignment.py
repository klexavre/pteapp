"""
forced_alignment.py
--------------------
Real forced alignment between the reference sentence and the user's audio,
using a Wav2Vec2 CTC acoustic model via torchaudio.

Unlike Whisper (which just transcribes freely), forced alignment answers a
different question: "given that the user was SUPPOSED to say this exact
sentence, where in the audio does each word start/end, and how confident is
the model that the sound at that position actually matches that word?"

This gives you:
  - Real per-word timestamps (not just Whisper's segment-level timestamps)
  - A per-word confidence score derived from the model's own emission
    probabilities -> a genuine acoustic-match score, not a proxy
  - Accurate gap/pause detection between words

Install:
  pip install torch torchaudio

First run will download the pretrained acoustic model (~360MB, cached after).
"""

import os
import re
import string
import subprocess
import tempfile
import wave

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency fallback
    np = None

try:
    import torch
except Exception:  # pragma: no cover - optional dependency fallback
    torch = None

try:
    import torchaudio
except Exception:  # pragma: no cover - optional dependency fallback
    torchaudio = None

DEVICE = torch.device("cuda" if torch is not None and torch.cuda.is_available() else "cpu") if torch is not None else None

# Wav2Vec2 model fine-tuned for ASR - we use its CTC output for alignment,
# not for free transcription.
_BUNDLE = None
if torchaudio is not None:
    try:
        _BUNDLE = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    except Exception:
        _BUNDLE = None
_MODEL = None
_LABELS = None
_DICTIONARY = None


def _load_model():
    """Lazy-load the model once (avoids slow reload on every request)."""
    global _MODEL, _LABELS, _DICTIONARY
    if _MODEL is None:
        if torch is None or torchaudio is None or _BUNDLE is None or DEVICE is None:
            raise RuntimeError("torch/torchaudio are not available; install them to enable forced alignment")
        print("Loading Wav2Vec2 forced-alignment model (first run downloads ~360MB)...")
        _MODEL = _BUNDLE.get_model().to(DEVICE)
        _MODEL.eval()
        _LABELS = _BUNDLE.get_labels()
        _DICTIONARY = {c: i for i, c in enumerate(_LABELS)}
        print("Forced-alignment model loaded.")
    return _MODEL, _LABELS, _DICTIONARY


def _clean_word(word: str) -> str:
    return word.upper().translate(str.maketrans("", "", string.punctuation))


def _tokens_from_text(text: str, dictionary: dict):
    """Convert reference sentence into the model's character-token ids."""
    words = [w for w in re.findall(r"[A-Za-z']+", text)]
    cleaned_words = [_clean_word(w) for w in words]
    # Model vocab uses '|' as the word-separator token
    joined = "|".join(cleaned_words)
    tokens = [dictionary[c] for c in joined if c in dictionary]
    return tokens, cleaned_words


def _get_trellis(emission, tokens, blank_id=0):
    num_frame = emission.size(0)
    num_tokens = len(tokens)
    trellis = torch.zeros((num_frame, num_tokens))
    trellis[1:, 0] = torch.cumsum(emission[1:, blank_id], 0)
    trellis[0, 1:] = -float("inf")
    trellis[-num_tokens + 1:, 0] = float("inf")

    for t in range(num_frame - 1):
        trellis[t + 1, 1:] = torch.maximum(
            trellis[t, 1:] + emission[t, blank_id],
            trellis[t, :-1] + emission[t, tokens[1:]],
        )
    return trellis


class Point:
    __slots__ = ["token_index", "time_index", "score"]

    def __init__(self, token_index, time_index, score):
        self.token_index = token_index
        self.time_index = time_index
        self.score = score


def _backtrack(trellis, emission, tokens, blank_id=0):
    t, j = trellis.size(0) - 1, trellis.size(1) - 1
    path = [Point(j, t, emission[t, blank_id].exp().item())]
    while j > 0:
        assert t > 0
        p_stay = trellis[t - 1, j] + emission[t - 1, blank_id]
        p_change = trellis[t - 1, j - 1] + emission[t - 1, tokens[j]]
        stayed = p_stay > p_change
        t -= 1
        if not stayed:
            j -= 1
        prob = emission[t, blank_id if stayed else tokens[j]].exp().item()
        path.append(Point(j, t, prob))
    while t > 0:
        prob = emission[t - 1, blank_id].exp().item()
        path.append(Point(0, t - 1, prob))
        t -= 1
    return path[::-1]


class Segment:
    def __init__(self, label, start, end, score):
        self.label = label
        self.start = start
        self.end = end
        self.score = score

    def __repr__(self):
        return f"{self.label}\t({self.score:.2f}): [{self.start}, {self.end})"


def _merge_repeats(path, transcript):
    i1, i2 = 0, 0
    segments = []
    while i1 < len(path):
        while i2 < len(path) and path[i1].token_index == path[i2].token_index:
            i2 += 1
        score = sum(path[k].score for k in range(i1, i2)) / (i2 - i1)
        segments.append(
            Segment(
                transcript[path[i1].token_index],
                path[i1].time_index,
                path[i2 - 1].time_index + 1,
                score,
            )
        )
        i1 = i2
    return segments


def _merge_words(segments, separator="|"):
    words = []
    i1, i2 = 0, 0
    while i1 < len(segments):
        if i2 >= len(segments) or segments[i2].label == separator:
            if i1 != i2:
                segs = segments[i1:i2]
                word = "".join(s.label for s in segs)
                score = sum(s.score * (s.end - s.start) for s in segs) / sum(
                    s.end - s.start for s in segs
                )
                words.append(Segment(word, segs[0].start, segs[-1].end, score))
            i1 = i2 + 1
            i2 = i1
        else:
            i2 += 1
    return words


def _load_audio_with_ffmpeg(audio_path: str):
    """Convert audio to WAV with ffmpeg, then decode it with Python's wave module
    so alignment works even when torchaudio's file backends are unavailable."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        if np is None or torch is None or torchaudio is None or _BUNDLE is None:
            raise RuntimeError("Audio alignment dependencies are not available")

        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-vn", "-ac", "1", "-ar", str(_BUNDLE.sample_rate), tmp_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with wave.open(tmp_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            frame_count = wav_file.getnframes()
            audio_bytes = wav_file.readframes(frame_count)

        if sample_width == 1:
            dtype = np.uint8
            scale = 128.0
        elif sample_width == 2:
            dtype = np.int16
            scale = 32768.0
        elif sample_width == 4:
            dtype = np.int32
            scale = 2147483648.0
        else:
            raise ValueError(f"Unsupported PCM sample width: {sample_width}")

        samples = np.frombuffer(audio_bytes, dtype=dtype).astype(np.float32)
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)
        samples = samples / scale

        waveform = torch.from_numpy(samples).unsqueeze(0)
        return waveform, sample_rate
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def align(audio_path: str, reference_text: str) -> list:
    """
    Runs forced alignment between reference_text and the audio at audio_path.

    Returns a list of dicts, one per reference word, each with:
      - word: the reference word
      - start_sec / end_sec: real timestamps in the audio
      - score: 0.0-1.0 acoustic confidence that this word was actually spoken
               clearly at that position (low score = likely mispronounced,
               mumbled, or skipped)
    """
    model, labels, dictionary = _load_model()

    waveform, sample_rate = _load_audio_with_ffmpeg(audio_path)
    if sample_rate != _BUNDLE.sample_rate:
        waveform = torchaudio.functional.resample(waveform, sample_rate, _BUNDLE.sample_rate)

    with torch.inference_mode():
        emissions, _ = model(waveform.to(DEVICE))
        emissions = torch.log_softmax(emissions, dim=-1)
    emission = emissions[0].cpu()

    tokens, cleaned_words = _tokens_from_text(reference_text, dictionary)
    if not tokens:
        return []

    trellis = _get_trellis(emission, tokens)
    path = _backtrack(trellis, emission, tokens)
    char_segments = _merge_repeats(path, [labels[t] for t in tokens])
    word_segments = _merge_words(char_segments)

    # Frame index -> seconds. Wav2Vec2 base has a fixed stride per frame.
    ratio = waveform.shape[1] / emission.size(0) / _BUNDLE.sample_rate

    results = []
    for i, seg in enumerate(word_segments):
        ref_word = cleaned_words[i] if i < len(cleaned_words) else seg.label
        results.append(
            {
                "word": ref_word,
                "start_sec": round(seg.start * ratio, 3),
                "end_sec": round(seg.end * ratio, 3),
                "score": round(seg.score, 3),
            }
        )
    return results


def detect_pauses(word_alignment: list, min_gap_seconds: float = 0.3) -> list:
    """
    Real pause detection using actual per-word timestamps from forced
    alignment (much more precise than Whisper's segment-level gaps).
    """
    pauses = []
    for i in range(1, len(word_alignment)):
        gap = word_alignment[i]["start_sec"] - word_alignment[i - 1]["end_sec"]
        if gap >= min_gap_seconds:
            pauses.append(
                {
                    "after_word": word_alignment[i - 1]["word"],
                    "before_word": word_alignment[i]["word"],
                    "duration": round(gap, 2),
                    "type": "long" if gap >= 0.6 else "short",
                }
            )
    return pauses


def pronunciation_score_from_alignment(word_alignment: list) -> dict:
    """
    Converts per-word acoustic confidence scores into an overall pronunciation
    score (0-90) plus a per-word breakdown for coloring the transcript
    (green/orange/red), similar to what commercial platforms show.
    """
    if not word_alignment:
        return {"score": 0, "out_of": 90, "word_scores": []}

    word_scores = []
    for w in word_alignment:
        if w["score"] >= 0.75:
            cls = "color-success"
        elif w["score"] >= 0.45:
            cls = "color-warning"
        else:
            cls = "color-danger"
        word_scores.append({"word": w["word"], "score": w["score"], "class": cls})

    avg_score = sum(w["score"] for w in word_alignment) / len(word_alignment)
    overall = round(avg_score * 90, 1)

    return {"score": overall, "out_of": 90, "word_scores": word_scores}
