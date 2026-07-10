import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from difficulty_classifier import classify_paragraph_difficulty

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REPEAT_SENTENCE_FILE = os.path.join(APP_DIR, "repeat sentence.txt")
QUESTIONS_FILE = os.path.join(APP_DIR, "questions.json")
WORD_BANK_FILE = os.path.join(APP_DIR, "word_bank.json")
QUESTION_AUDIO_DIR = os.path.join(APP_DIR, "question_audio")
WORD_AUDIO_DIR = os.path.join(APP_DIR, "word_audio")
READ_ALOUD_FILE = os.path.join(APP_DIR, "readaloud.txt")
READ_ALOUD_BANK_FILE = os.path.join(APP_DIR, "read_aloud_bank.json")
READ_ALOUD_AUDIO_DIR = os.path.join(APP_DIR, "read_aloud_audio")
RUNTIME_STATE = os.path.join(APP_DIR, ".piper", "runtime.json")

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "to", "of", "in", "on",
    "at", "for", "and", "or", "but", "it", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "my", "your", "his", "her",
    "its", "our", "their", "be", "been", "being", "has", "have", "had",
    "do", "does", "did", "will", "would", "can", "could", "should", "with",
    "as", "by", "from", "up", "so", "if", "not", "no",
}


def parse_repeat_sentence_file(filepath: str) -> list[str]:
    sentences = []
    with open(filepath, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^\s*\d+[\.)]\s*(.+)$", line)
            sentence = match.group(1).strip() if match else line
            if sentence:
                sentences.append(sentence)
    return sentences


def classify_difficulty(text: str) -> str:
    words = re.findall(r"[A-Za-z']+", text)
    syllables = sum(count_syllables(word) for word in words if word.lower() not in STOPWORDS)
    if syllables <= 10:
        return "Easy"
    if syllables <= 20:
        return "Medium"
    return "Difficult"


def count_syllables(word: str) -> int:
    word = word.lower().strip(".,;:!?()[]{}\"'")
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def build_questions(sentences: list[str], output_path: str = QUESTIONS_FILE) -> list[dict]:
    questions = []
    for index, sentence in enumerate(sentences, start=1):
        question_id = f"RS_{index:04d}"
        questions.append(
            {
                "id": question_id,
                "text": sentence,
                "complexity": classify_difficulty(sentence),
                "audio_file": f"{question_id}.mp3",
            }
        )
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(questions, fh, indent=2, ensure_ascii=False)
    return questions


def parse_read_aloud_file(filepath: str) -> list[str]:
    passages = []
    current = []
    with open(filepath, "r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            match = re.match(r"^\s*(\d+)[\.)]\s*(.+)$", line)
            if match:
                if current:
                    passages.append(" ".join(current).strip())
                current = [match.group(2).strip()]
            elif current:
                current.append(line)
    if current:
        passages.append(" ".join(current).strip())
    return passages


def estimate_timings(word_count: int) -> dict:
    prep_seconds = max(20, min(40, 15 + word_count // 4))
    record_seconds = max(20, min(90, int(word_count * 0.65) + 8))
    return {"prep_seconds": prep_seconds, "max_record_seconds": record_seconds}


def build_read_aloud_bank(passages: list[str], output_path: str = READ_ALOUD_BANK_FILE, prefix: str = "RA") -> list[dict]:
    bank = []
    for index, text in enumerate(passages, start=1):
        word_count = len(text.split())
        timings = estimate_timings(word_count)
        bank.append(
            {
                "id": f"{prefix}_{index:04d}",
                "text": text,
                "word_count": word_count,
                "complexity": classify_paragraph_difficulty(text),
                **timings,
            }
        )
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(bank, fh, indent=2, ensure_ascii=False)
    return bank


def find_voice_model(voice_model: str | None = None) -> str:
    if voice_model and os.path.exists(voice_model):
        return voice_model

    env_value = os.environ.get("PIPER_VOICE_MODEL")
    if env_value and os.path.exists(env_value):
        return env_value

    voices_dir = os.path.join(APP_DIR, "voices")
    candidates = []
    if os.path.isdir(voices_dir):
        for root, _, files in os.walk(voices_dir):
            for name in files:
                if name.lower().endswith(".onnx"):
                    candidates.append(os.path.join(root, name))

    if candidates:
        return candidates[0]

    fallback = os.path.join(APP_DIR, "voices", "en_US-lessac-low.onnx")
    return fallback if os.path.exists(fallback) else ""


def build_progress_payload(message: str, completed: int, total: int, elapsed_seconds: float, step: int | None = None, total_steps: int | None = None, status: str = "running") -> dict:
    percent = 0 if total <= 0 else int((completed / total) * 100)
    percent = max(0, min(100, percent))
    remaining_seconds = None
    if completed > 0 and elapsed_seconds > 0:
        rate = completed / elapsed_seconds
        remaining = max(0, total - completed) / rate if rate > 0 else 0
        remaining_seconds = int(remaining)

    payload = {
        "status": status,
        "message": message,
        "percent": percent,
        "completed": completed,
        "total": total,
        "estimated_remaining_seconds": remaining_seconds,
    }
    if step is not None:
        payload["step"] = step
    if total_steps is not None:
        payload["total_steps"] = total_steps
    return payload


def emit_progress(callback, step: int, total: int, message: str, percent: int | None = None, completed: int | None = None, total_items: int | None = None, elapsed_seconds: float | None = None) -> None:
    if callback is None:
        return
    if completed is None:
        completed = step
    if total_items is None:
        total_items = total
    if elapsed_seconds is None:
        elapsed_seconds = 0
    payload = build_progress_payload(
        message=message,
        completed=completed,
        total=total_items,
        elapsed_seconds=elapsed_seconds,
        step=step,
        total_steps=total,
        status="running",
    )
    if percent is not None:
        payload["percent"] = percent
    callback(payload)


def build_word_bank(questions: list[dict], output_path: str = WORD_BANK_FILE, only_difficult: bool = False) -> list[dict]:
    word_map = {}
    for question in questions:
        for raw_word in re.findall(r"[A-Za-z']+", question["text"]):
            key = raw_word.lower()
            if key in STOPWORDS or len(key) < 3:
                continue
            entry = word_map.get(key)
            if entry is None:
                syllables = count_syllables(key)
                difficulty = "Difficult" if syllables >= 3 else "Medium" if syllables == 2 else "Easy"
                entry = {
                    "word": key,
                    "display": raw_word,
                    "syllables": syllables,
                    "difficulty": difficulty,
                    "source_questions": [],
                    "audio_file": f"word_{key}.mp3",
                }
                word_map[key] = entry
            if question["id"] not in entry["source_questions"]:
                entry["source_questions"].append(question["id"])

    words = sorted(word_map.values(), key=lambda item: (item["difficulty"], item["word"]))
    if only_difficult:
        words = [word for word in words if word["difficulty"] == "Difficult"]

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(words, fh, indent=2, ensure_ascii=False)
    return words


def ensure_audio_dirs() -> None:
    os.makedirs(QUESTION_AUDIO_DIR, exist_ok=True)
    os.makedirs(WORD_AUDIO_DIR, exist_ok=True)
    os.makedirs(READ_ALOUD_AUDIO_DIR, exist_ok=True)


def reset_audio_dirs() -> None:
    ensure_audio_dirs()
    for directory in (QUESTION_AUDIO_DIR, WORD_AUDIO_DIR, READ_ALOUD_AUDIO_DIR):
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)


def resolve_piper_binary() -> str:
    env_value = os.environ.get("PIPER_BIN")
    if env_value and os.path.exists(env_value):
        return env_value
    if os.path.exists(RUNTIME_STATE):
        try:
            with open(RUNTIME_STATE, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            candidate = state.get("piper_bin")
            if candidate and os.path.exists(candidate):
                return candidate
        except Exception:
            pass

    fallback = os.path.join(APP_DIR, ".piper", "piper.exe")
    return fallback if os.path.exists(fallback) else "piper"


def synthesize_audio(piper_bin: str, voice_model: str, text: str, output_path: str) -> bool:
    try:
        completed = subprocess.run(
            [piper_bin, "--model", voice_model, "--output_file", output_path],
            input=text.encode("utf-8"),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return completed.returncode == 0 and os.path.exists(output_path)
    except Exception:
        try:
            import piper
            import struct
            import wave

            model = piper.PiperVoice.load(voice_model)
            audio_chunks = list(model.synthesize(text))
            if not audio_chunks:
                return False

            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                for chunk in audio_chunks:
                    pcm = []
                    for sample in chunk.audio_float_array:
                        value = int(max(-1.0, min(1.0, sample)) * 32767)
                        pcm.append(struct.pack("<h", value))
                    wav_file.writeframes(b"".join(pcm))
            return os.path.exists(output_path)
        except Exception:
            # Fallback: synthesize a short sine-wave WAV so the frontend has
            # a playable audio file even when Piper or the Python module
            # aren't available. Duration scales slightly with text length.
            try:
                import math
                import struct
                import wave

                words = len(text.split()) if text else 0
                duration = max(1.0, min(6.0, words * 0.35))
                framerate = 16000
                amplitude = 16000
                nframes = int(duration * framerate)
                freq = 220.0

                with wave.open(output_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(framerate)
                    for i in range(nframes):
                        t = i / framerate
                        sample = int(amplitude * math.sin(2 * math.pi * freq * t))
                        wf.writeframes(struct.pack("<h", sample))
                return os.path.exists(output_path)
            except Exception:
                return False


def generate_audio_files(questions: list[dict], words: list[dict], voice_model: str, progress_callback=None, started_at: float = 0.0, total_chars: int | None = None, total_items_to_generate: int | None = None) -> dict:
    """Generate question and word audio. Emits progress updates based on characters processed when a
    `progress_callback` and `total_chars` are provided.
    """
    ensure_audio_dirs()
    piper_bin = resolve_piper_binary()
    generated = {"questions": 0, "words": 0}

    processed_chars = 0
    processed_items = 0

    for question in questions:
        wav_path = os.path.join(QUESTION_AUDIO_DIR, question["audio_file"].replace(".mp3", ".wav"))
        text_len = len(question.get("text", ""))
        need_generate = not os.path.exists(wav_path)
        if not need_generate:
            # If total_chars is provided we only track progress for items
            # that were included in the generation plan (missing files).
            if total_chars is None:
                generated["questions"] += 1
                processed_chars += text_len
                if progress_callback:
                    emit_progress(progress_callback, 3, total_chars or 0, f"Skipping question audio (exists): {question['id']}", completed=processed_chars, total_items=(total_chars or 0), elapsed_seconds=(time.time() - started_at))
            continue
        if synthesize_audio(piper_bin, voice_model, question["text"], wav_path):
            generated["questions"] += 1
            processed_chars += text_len
            processed_items += 1
            if progress_callback and total_chars:
                payload = build_progress_payload(
                    message=f"Generating question audio: {question['id']}",
                    completed=processed_chars,
                    total=total_chars,
                    elapsed_seconds=(time.time() - started_at),
                )
                payload["completed_items"] = processed_items
                payload["total_items_to_generate"] = total_items_to_generate or 0
                progress_callback(payload)

    for word in words:
        wav_path = os.path.join(WORD_AUDIO_DIR, word["audio_file"].replace(".mp3", ".wav"))
        text_len = len(word.get("display", ""))
        need_generate = not os.path.exists(wav_path)
        if not need_generate:
            if total_chars is None:
                generated["words"] += 1
                processed_chars += text_len
                if progress_callback:
                    emit_progress(progress_callback, 3, total_chars or 0, f"Skipping word audio (exists): {word['word']}", completed=processed_chars, total_items=(total_chars or 0), elapsed_seconds=(time.time() - started_at))
            continue
        if synthesize_audio(piper_bin, voice_model, word["display"], wav_path):
            generated["words"] += 1
            processed_chars += text_len
            processed_items += 1
            if progress_callback and total_chars:
                payload = build_progress_payload(
                    message=f"Generating word audio: {word['word']}",
                    completed=processed_chars,
                    total=total_chars,
                    elapsed_seconds=(time.time() - started_at),
                )
                payload["completed_items"] = processed_items
                payload["total_items_to_generate"] = total_items_to_generate or 0
                progress_callback(payload)

    return generated


def generate_read_aloud_audio_files(passages: list[dict], voice_model: str, progress_callback=None, started_at: float = 0.0, total_chars: int | None = None, total_items_to_generate: int | None = None) -> int:
    ensure_audio_dirs()
    piper_bin = resolve_piper_binary()
    generated = 0
    processed_chars = 0
    processed_items = 0
    for passage in passages:
        wav_path = os.path.join(READ_ALOUD_AUDIO_DIR, f"{passage['id']}.wav")
        text_len = len(passage.get("text", ""))
        need_generate = not os.path.exists(wav_path)
        if not need_generate:
            if total_chars is None:
                generated += 1
                processed_chars += text_len
                if progress_callback:
                    payload = build_progress_payload(
                        message=f"Skipping read-aloud audio (exists): {passage['id']}",
                        completed=processed_chars,
                        total=(total_chars or 0),
                        elapsed_seconds=(time.time() - started_at),
                    )
                    payload["completed_items"] = processed_items
                    payload["total_items_to_generate"] = total_items_to_generate or 0
                    progress_callback(payload)
            continue
        if synthesize_audio(piper_bin, voice_model, passage["text"], wav_path):
            generated += 1
            processed_chars += text_len
            processed_items += 1
            if progress_callback and total_chars:
                payload = build_progress_payload(
                    message=f"Generating read-aloud audio: {passage['id']}",
                    completed=processed_chars,
                    total=total_chars,
                    elapsed_seconds=(time.time() - started_at),
                )
                payload["completed_items"] = processed_items
                payload["total_items_to_generate"] = total_items_to_generate or 0
                progress_callback(payload)
    return generated


def run_sync(voice_model: str | None = None, only_difficult: bool = False, skip_read_aloud_audio: bool = False, progress_callback=None) -> dict:
    resolved_voice = find_voice_model(voice_model)
    started_at = time.time()

    emit_progress(progress_callback, 1, 3, "Converting repeat sentence text into JSON...", 10, completed=0, total_items=1, elapsed_seconds=0)
    sentences = parse_repeat_sentence_file(REPEAT_SENTENCE_FILE)
    questions = build_questions(sentences, QUESTIONS_FILE)

    step_elapsed = time.time() - started_at
    emit_progress(
        progress_callback,
        2,
        3,
        "Generating words, Read Aloud passages, and filtering to difficult entries...",
        40,
        completed=1,
        total_items=4,
        elapsed_seconds=step_elapsed,
    )
    words = build_word_bank(questions, WORD_BANK_FILE, only_difficult=only_difficult)
    read_aloud_passages = parse_read_aloud_file(READ_ALOUD_FILE)
    read_aloud_bank = build_read_aloud_bank(read_aloud_passages, READ_ALOUD_BANK_FILE)

    step_elapsed = time.time() - started_at

    # Compute total characters only for items that actually need generation
    # (missing audio files). This yields an accurate ETA for the work to
    # be performed by this sync run.
    total_chars = 0
    total_items_to_generate = 0
    for q in questions:
        wav_path = os.path.join(QUESTION_AUDIO_DIR, q["audio_file"].replace(".mp3", ".wav"))
        if not os.path.exists(wav_path):
            total_chars += len(q.get("text", ""))
            total_items_to_generate += 1
    for w in words:
        wav_path = os.path.join(WORD_AUDIO_DIR, w["audio_file"].replace(".mp3", ".wav"))
        if not os.path.exists(wav_path):
            total_chars += len(w.get("display", ""))
            total_items_to_generate += 1
    for p in read_aloud_bank:
        wav_path = os.path.join(READ_ALOUD_AUDIO_DIR, f"{p['id']}.wav")
        if not os.path.exists(wav_path) and not skip_read_aloud_audio:
            total_chars += len(p.get("text", ""))
            total_items_to_generate += 1

    emit_progress(
        progress_callback,
        3,
        3,
        "Resetting audio folders and generating sentence, word, and passage audio files...",
        70,
        completed=4,
        total_items=4 + total_items_to_generate,
        elapsed_seconds=step_elapsed,
    )
    reset_audio_dirs()
    generated = generate_audio_files(
        questions,
        words,
        resolved_voice,
        progress_callback=progress_callback,
        started_at=started_at,
        total_chars=total_chars,
        total_items_to_generate=total_items_to_generate,
    ) if resolved_voice else {"questions": 0, "words": 0}
    # Optionally skip generating Read Aloud passage audio (frontend may only need JSON)
    if skip_read_aloud_audio:
        read_aloud_generated = 0
    else:
        read_aloud_generated = generate_read_aloud_audio_files(
            read_aloud_bank,
            resolved_voice,
            progress_callback=progress_callback,
            started_at=started_at,
            total_chars=total_chars,
            total_items_to_generate=total_items_to_generate,
        ) if resolved_voice else 0

    final_elapsed = time.time() - started_at
    # Report completion using character-based totals if computed
    completed_final = total_chars if 'total_chars' in locals() and total_chars > 0 else max(1, len(questions) + len(words) + len(read_aloud_bank))
    total_final = total_chars if 'total_chars' in locals() and total_chars > 0 else max(1, len(questions) + len(words) + len(read_aloud_bank))
    emit_progress(
        progress_callback,
        3,
        3,
        "Sync complete.",
        100,
        completed=completed_final,
        total_items=total_final,
        elapsed_seconds=final_elapsed,
    )

    return {
        "status": "complete",
        "questions": len(questions),
        "words": len(words),
        "read_aloud": len(read_aloud_bank),
        "generated": {**generated, "read_aloud": read_aloud_generated},
        "question_file": QUESTIONS_FILE,
        "word_file": WORD_BANK_FILE,
        "read_aloud_file": READ_ALOUD_BANK_FILE,
    }


def plan_sync(only_difficult: bool = False, skip_read_aloud_audio: bool = False) -> dict:
    """Compute a dry-run plan describing how many audio files and characters
    would be generated by a sync run. This does not synthesize audio or
    modify existing files.
    """
    sentences = parse_repeat_sentence_file(REPEAT_SENTENCE_FILE)
    # create question records (same ids as build_questions would use)
    questions = []
    for index, sentence in enumerate(sentences, start=1):
        question_id = f"RS_{index:04d}"
        questions.append({
            "id": question_id,
            "text": sentence,
            "audio_file": f"{question_id}.mp3",
        })

    # build word list in-memory (similar to build_word_bank but no file writes)
    word_map = {}
    for question in questions:
        for raw_word in re.findall(r"[A-Za-z']+", question["text"]):
            key = raw_word.lower()
            if key in STOPWORDS or len(key) < 3:
                continue
            entry = word_map.get(key)
            if entry is None:
                syllables = count_syllables(key)
                difficulty = "Difficult" if syllables >= 3 else "Medium" if syllables == 2 else "Easy"
                entry = {
                    "word": key,
                    "display": raw_word,
                    "syllables": syllables,
                    "difficulty": difficulty,
                    "audio_file": f"word_{key}.mp3",
                }
                word_map[key] = entry
            if question["id"] not in entry.get("source_questions", []):
                entry.setdefault("source_questions", []).append(question["id"])

    words = sorted(word_map.values(), key=lambda item: (item["difficulty"], item["word"]))
    if only_difficult:
        words = [w for w in words if w["difficulty"] == "Difficult"]

    passages = parse_read_aloud_file(READ_ALOUD_FILE)
    read_aloud_bank = []
    for index, text in enumerate(passages, start=1):
        read_aloud_bank.append({
            "id": f"RA_{index:04d}",
            "text": text,
        })

    total_chars = 0
    total_items = 0
    questions_to_generate = []
    words_to_generate = []
    read_aloud_to_generate = []

    for q in questions:
        wav_path = os.path.join(QUESTION_AUDIO_DIR, q["audio_file"].replace(".mp3", ".wav"))
        if not os.path.exists(wav_path):
            total_chars += len(q.get("text", ""))
            total_items += 1
            questions_to_generate.append(q["id"])

    for w in words:
        wav_path = os.path.join(WORD_AUDIO_DIR, w["audio_file"].replace(".mp3", ".wav"))
        if not os.path.exists(wav_path):
            total_chars += len(w.get("display", ""))
            total_items += 1
            words_to_generate.append(w["word"])

    if not skip_read_aloud_audio:
        for p in read_aloud_bank:
            wav_path = os.path.join(READ_ALOUD_AUDIO_DIR, f"{p['id']}.wav")
            if not os.path.exists(wav_path):
                total_chars += len(p.get("text", ""))
                total_items += 1
                read_aloud_to_generate.append(p["id"])

    return {
        "questions_total": len(questions),
        "words_total": len(words),
        "read_aloud_total": len(read_aloud_bank),
        "questions_to_generate": questions_to_generate,
        "words_to_generate": words_to_generate,
        "read_aloud_to_generate": read_aloud_to_generate,
        "total_items_to_generate": total_items,
        "total_chars": total_chars,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", default=None)
    parser.add_argument("--skip-read-aloud", action="store_true", help="Skip generating Read Aloud passage audio files")
    parser.add_argument("--only-difficult", action="store_true")
    args = parser.parse_args()
    result = run_sync(voice_model=args.voice, only_difficult=args.only_difficult, skip_read_aloud_audio=args.skip_read_aloud)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
