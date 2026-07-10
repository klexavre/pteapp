"""
server.py
---------
Local FastAPI backend for the PTE Repeat Sentence practice app.

Endpoints:
  GET  /api/questions            -> list of practice questions
  GET  /api/questions/{id}       -> single question + audio URL
  POST /api/score                -> upload a recording, get Whisper-based scoring
  GET  /api/words                -> list of single-word drills (filter by difficulty)
  GET  /api/words/{word}         -> word info + audio URL (if pre-generated)
  POST /api/words/score          -> upload a word recording, get pronunciation score
  GET  /api/read-aloud           -> list of Read Aloud passages (search/filter/paginate)
  GET  /api/read-aloud/{id}      -> single passage + timing info
  POST /api/read-aloud/score     -> upload a recording, get Whisper + forced-alignment scoring
  GET  /audio/{filename}         -> serve pre-generated question audio files
  GET  /word_audio/{filename}    -> serve pre-generated word-drill audio files

Run with:
  uvicorn server:app --reload --port 8000
"""

import json
import os
import tempfile
import time
from pathlib import Path

try:
    import whisper
except Exception:  # pragma: no cover - optional dependency fallback
    whisper = None

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover - optional dependency fallback
    WhisperModel = None

from scorer import compute_full_score, score_single_word, score_read_aloud
import forced_alignment
import audio_utils
import threading
from sync_data import (
    find_voice_model,
    resolve_piper_binary,
    run_sync as run_sync_pipeline,
    plan_sync,
    synthesize_audio,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(APP_DIR, "questions.json")
AUDIO_DIR = os.path.join(APP_DIR, "question_audio")
WORD_BANK_FILE = os.path.join(APP_DIR, "word_bank.json")
WORD_AUDIO_DIR = os.path.join(APP_DIR, "word_audio")
READ_ALOUD_FILE = os.path.join(APP_DIR, "read_aloud_bank.json")
READ_ALOUD_AUDIO_DIR = os.path.join(APP_DIR, "read_aloud_audio")

app = FastAPI(title="PTE Repeat Sentence API")

# Allow the Next.js dev server to call this API during local development.
# This accepts any localhost/127.0.0.1 port so the frontend can change
# ports without needing a backend restart or manual CORS updates.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    expose_headers=["*"],
    max_age=3600,
)

# Serve audio files with proper CORS headers through routes
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(WORD_AUDIO_DIR, exist_ok=True)
os.makedirs(READ_ALOUD_AUDIO_DIR, exist_ok=True)


@app.get("/audio/{filename}")
def get_question_audio(filename: str):
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    response = FileResponse(filepath, media_type="audio/wav")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.options("/audio/{filename}")
def options_question_audio(filename: str):
    response = Response(status_code=204)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.get("/word_audio/{filename}")
def get_word_audio(filename: str):
    filepath = os.path.join(WORD_AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    response = FileResponse(filepath, media_type="audio/wav")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.options("/word_audio/{filename}")
def options_word_audio(filename: str):
    response = Response(status_code=204)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# -----
# Load Whisper model ONCE at startup. Model size is configurable via env var
# WHISPER_MODEL_SIZE - "small" is the default here (meaningfully more
# accurate transcription than "base", at a moderate speed cost). Use "medium"
# for even better accuracy if your machine has the CPU/GPU headroom, or
# "base"/"tiny" if you need faster turnaround and can accept more errors.
# ---------------------------------------------------------------------------
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")
WHISPER_MODEL = None
FASTER_WHISPER_MODEL = None

if WhisperModel is not None:
    print(f"Loading Faster-Whisper model '{WHISPER_MODEL_SIZE}' (this can take a moment on first run)...")
    FASTER_WHISPER_MODEL = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    print("Faster-Whisper model loaded.")
elif whisper is not None:
    print(f"Loading Whisper model '{WHISPER_MODEL_SIZE}' (this can take a moment on first run)...")
    WHISPER_MODEL = whisper.load_model(WHISPER_MODEL_SIZE)
    print("Whisper model loaded.")
else:
    print("Whisper packages are not installed; transcription will be unavailable. Install openai-whisper or faster-whisper to enable scoring.")


def transcribe_audio(audio_path: str) -> dict:
    if FASTER_WHISPER_MODEL is not None:
        segments, info = FASTER_WHISPER_MODEL.transcribe(audio_path, language="en")
        normalized_segments = []
        for segment in segments:
            normalized_segments.append(
                {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "avg_logprob": getattr(segment, "avg_logprob", None),
                    "no_speech_prob": getattr(segment, "no_speech_prob", None),
                }
            )
        return {
            "segments": normalized_segments,
            "text": " ".join(seg["text"] for seg in normalized_segments).strip(),
            "info": info,
        }

    if WHISPER_MODEL is None:
        return {"segments": [], "text": "", "info": {"error": "Whisper not available"}}

    result = WHISPER_MODEL.transcribe(
        audio_path,
        language="en",
        fp16=False,
        condition_on_previous_text=False,
        temperature=0.0,
        no_speech_threshold=0.6,
        logprob_threshold=-1.0,
        compression_ratio_threshold=2.4,
    )
    return result


def load_questions():
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)


def load_word_bank():
    if not os.path.exists(WORD_BANK_FILE):
        return []
    with open(WORD_BANK_FILE, "r") as f:
        return json.load(f)


def load_read_aloud():
    if not os.path.exists(READ_ALOUD_FILE):
        return []
    with open(READ_ALOUD_FILE, "r") as f:
        return json.load(f)


def ensure_read_aloud_audio(passage: dict) -> str | None:
    os.makedirs(READ_ALOUD_AUDIO_DIR, exist_ok=True)
    output_path = os.path.join(READ_ALOUD_AUDIO_DIR, f"{passage['id']}.wav")
    if os.path.exists(output_path):
        return f"{passage['id']}.wav"

    resolved_voice = find_voice_model()
    if not resolved_voice:
        return None

    piper_bin = resolve_piper_binary()
    if synthesize_audio(piper_bin, resolved_voice, passage.get("text", ""), output_path):
        return f"{passage['id']}.wav"
    return None


def resolve_audio_file(audio_dir: str, requested_name: str | None) -> str | None:
    if not requested_name:
        return None

    requested_path = Path(audio_dir) / requested_name
    if requested_path.exists():
        return requested_name

    stem = Path(requested_name).stem
    candidates = [requested_name, f"{stem}.wav", f"{stem}.mp3"]
    for candidate in candidates:
        candidate_path = Path(audio_dir) / candidate
        if candidate_path.exists():
            return candidate

    return None


SYNC_STATE = {
    "status": "idle",
    "step": 0,
    "total": 3,
    "percent": 0,
    "message": "No sync run yet.",
    "error": None,
}
SYNC_THREAD = None


def update_sync_state(payload: dict):
    global SYNC_STATE
    SYNC_STATE = {
        **SYNC_STATE,
        **payload,
    }


def run_sync_worker():
    global SYNC_THREAD
    try:
        # Frontend-triggered sync should avoid generating large Read Aloud
        # passage audio by default (the frontend generally needs the JSON
        # and word/question audio). Use the new `skip_read_aloud_audio`
        # flag to speed up sync runs initiated from the UI.
        run_sync_pipeline(
            progress_callback=update_sync_state,
            only_difficult=True,
            skip_read_aloud_audio=True,
        )
        update_sync_state({
            "status": "complete",
            "percent": 100,
            "message": "Sync completed successfully.",
        })
    except Exception as exc:
        update_sync_state({
            "status": "error",
            "percent": 0,
            "message": str(exc),
            "error": str(exc),
        })
    finally:
        SYNC_THREAD = None


@app.post("/api/sync-data")
def trigger_sync_data():
    global SYNC_THREAD
    if SYNC_THREAD and SYNC_THREAD.is_alive():
        return {"status": "running", **SYNC_STATE}

    update_sync_state({
        "status": "running",
        "step": 1,
        "total": 3,
        "percent": 0,
        "message": "Starting sync...",
        "error": None,
    })
    SYNC_THREAD = threading.Thread(target=run_sync_worker, daemon=True)
    SYNC_THREAD.start()
    return {"status": "started", **SYNC_STATE}


@app.get("/api/sync-data/status")
def get_sync_status():
    return SYNC_STATE


@app.get("/api/sync-data/plan")
def get_sync_plan(skip_read_aloud: bool = True):
    """Return a plan describing what audio files would be generated by a sync
    run. By default this skips Read Aloud passage audio to keep the plan
    focused on the quicker, frontend-relevant work.
    """
    try:
        plan = plan_sync(only_difficult=True, skip_read_aloud_audio=skip_read_aloud)
        return {"status": "ok", **plan}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/words")
def get_words(difficulty: str = None, limit: int = 50):
    """
    List single-word drills, generated ahead of time from your question
    bank by word_extractor.py. Optionally filter by difficulty
    (Easy/Medium/Difficult) and limit the count returned.
    """
    words = load_word_bank()
    if difficulty:
        words = [w for w in words if w["difficulty"].lower() == difficulty.lower()]
    return words[:limit]


@app.get("/api/words/{word}")
def get_word(word: str):
    words = load_word_bank()
    index = next((i for i, w in enumerate(words) if w["word"] == word.lower()), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Word not found")
    match = words[index]

    resolved_audio = resolve_audio_file(WORD_AUDIO_DIR, match.get("audio_file"))
    has_audio = resolved_audio is not None

    return {
        **match,
        "audio_url": f"http://127.0.0.1:8000/word_audio/{resolved_audio}" if has_audio else None,
        "prev_word": words[index - 1]["word"] if index > 0 else None,
        "next_word": words[index + 1]["word"] if index < len(words) - 1 else None,
        "position": index + 1,
        "total": len(words),
    }


@app.post("/api/words/score")
async def score_word_recording(word: str = Form(...), audio: UploadFile = File(...)):
    suffix = os.path.splitext(audio.filename or "recording.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    trimmed_path = None
    transcription_text = ""
    try:
        trimmed_path = tmp_path.replace(suffix, "_trimmed.wav")
        audio_path = audio_utils.trim_silence(tmp_path, trimmed_path)

        try:
            transcription_result = transcribe_audio(audio_path)
            transcription_text = (transcription_result.get("text") or "").strip()
        except Exception as e:
            print(f"Word transcription failed: {e}")

        try:
            alignment = forced_alignment.align(audio_path, word)
        except Exception as e:
            print(f"Word alignment failed: {e}")
            alignment = []

        result = score_single_word(word, alignment, transcription=transcription_text)
        return result
    except Exception as e:
        print(f"Word scoring failed: {e}")
        return score_single_word(word, [], transcription=transcription_text)
    finally:
        os.remove(tmp_path)
        if trimmed_path and os.path.exists(trimmed_path):
            os.remove(trimmed_path)


@app.post("/api/words/score-batch")
async def score_word_batch(words: list = Form(...), audio: list[UploadFile] = File(...)):
    results = []
    for idx, word in enumerate(words):
        audio_file = audio[idx] if idx < len(audio) else None
        if audio_file is None:
            results.append(score_single_word(word, [], transcription=""))
            continue

        suffix = os.path.splitext(audio_file.filename or "recording.webm")[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio_file.read())
            tmp_path = tmp.name

        trimmed_path = None
        transcription_text = ""
        try:
            trimmed_path = tmp_path.replace(suffix, "_trimmed.wav")
            audio_path = audio_utils.trim_silence(tmp_path, trimmed_path)

            try:
                transcription_result = transcribe_audio(audio_path)
                transcription_text = (transcription_result.get("text") or "").strip()
            except Exception as e:
                print(f"Batch word transcription failed: {e}")

            try:
                alignment = forced_alignment.align(audio_path, word)
            except Exception as e:
                print(f"Batch word alignment failed: {e}")
                alignment = []

            results.append(score_single_word(word, alignment, transcription=transcription_text))
        except Exception as e:
            print(f"Batch word scoring failed: {e}")
            results.append(score_single_word(word, [], transcription=transcription_text))
        finally:
            os.remove(tmp_path)
            if trimmed_path and os.path.exists(trimmed_path):
                os.remove(trimmed_path)

    return results


@app.get("/api/questions")
def get_questions():
    questions = load_questions()
    # Don't leak the raw reference text in the list view (keeps it like a real exam)
    return [
        {"id": q["id"], "complexity": q["complexity"]}
        for q in questions
    ]


@app.get("/api/questions/{question_id}")
def get_question(question_id: str):
    questions = load_questions()
    index = next((i for i, q in enumerate(questions) if q["id"] == question_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Question not found")
    match = questions[index]

    resolved_audio = resolve_audio_file(AUDIO_DIR, match.get("audio_file"))
    has_audio = resolved_audio is not None

    return {
        "id": match["id"],
        "complexity": match["complexity"],
        "text": match["text"],
        "audio_url": f"http://127.0.0.1:8000/audio/{resolved_audio}" if has_audio else None,
        "prev_id": questions[index - 1]["id"] if index > 0 else None,
        "next_id": questions[index + 1]["id"] if index < len(questions) - 1 else None,
        "position": index + 1,
        "total": len(questions),
    }


@app.post("/api/score")
async def score_recording(question_id: str = Form(...), audio: UploadFile = File(...)):
    questions = load_questions()
    question = next((q for q in questions if q["id"] == question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Save the uploaded recording to a temp file so Whisper/ffmpeg can read it
    suffix = os.path.splitext(audio.filename or "recording.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    trimmed_path = None
    try:
        # Fix #1 for Whisper hallucination: strip leading/trailing silence.
        # Short recordings with quiet padding are the single biggest cause
        # of Whisper "hearing" words that were never said.
        trimmed_path = tmp_path.replace(suffix, "_trimmed.wav")
        audio_path = audio_utils.trim_silence(tmp_path, trimmed_path)

        start = time.time()
        # Fix #2 for Whisper hallucination: tuned decoding settings.
        #   - condition_on_previous_text=False: each clip here is a single
        #     isolated utterance, not part of a longer stream - letting
        #     Whisper condition on "previous text" (which doesn't really
        #     exist for us) increases made-up continuations.
        #   - temperature=0.0: greedy decoding, no random sampling that can
        #     invent words during uncertain/quiet stretches.
        #   - no_speech_threshold: segments Whisper itself flags as likely
        #     silence get marked, so we can filter them out below.
        #   - logprob_threshold: segments with low average confidence are
        #     flagged the same way.
        result = transcribe_audio(audio_path)
        elapsed = time.time() - start

        # Fix #2b: drop any segment Whisper itself wasn't confident about,
        # rather than trusting every segment blindly. This catches most
        # remaining hallucinated fragments that slip past the settings above.
        clean_segments = [
            seg for seg in result["segments"]
            if seg.get("no_speech_prob", 0) < 0.5 and seg.get("avg_logprob", -1) > -1.0
        ]
        clean_text = " ".join(seg["text"].strip() for seg in clean_segments).strip()

        print(f"Whisper transcribed in {elapsed:.2f}s: {clean_text!r}"
              f" (dropped {len(result['segments']) - len(clean_segments)} low-confidence segment(s))")

        duration_seconds = clean_segments[-1]["end"] if clean_segments else 0.0

        # Real forced alignment: exact per-word timing + acoustic confidence
        # against the REFERENCE sentence (not just Whisper's free transcript).
        # Falls back gracefully to the Whisper-confidence proxy if it errors.
        alignment = None
        pauses = None
        try:
            alignment = forced_alignment.align(audio_path, question["text"])
            pauses = forced_alignment.detect_pauses(alignment)
        except Exception as e:
            print(f"Forced alignment failed, falling back to Whisper-only scoring: {e}")

        scores = compute_full_score(
            reference=question["text"],
            hypothesis=clean_text,
            segments=clean_segments,
            duration_seconds=duration_seconds,
            alignment=alignment,
            pauses=pauses,
        )
        return scores
    finally:
        os.remove(tmp_path)
        if trimmed_path and os.path.exists(trimmed_path):
            os.remove(trimmed_path)


@app.get("/api/read-aloud")
def get_read_aloud_list(
    search: str = "",
    order: str = "newest",
    complexity: str = "",
    page: int = 1,
    limit: int = 10,
):
    """
    Same filter/pagination surface as /api/questions (search, complexity,
    newest/oldest, page/limit) - kept consistent so ReadAloudList.jsx can
    reuse the same UI pattern as QuestionList.jsx.
    """
    passages = load_read_aloud()

    if complexity:
        passages = [p for p in passages if p["complexity"].lower() == complexity.lower()]

    if search:
        search_lower = search.lower()
        passages = [p for p in passages if search_lower in p["text"].lower() or search_lower in p["id"].lower()]

    if order == "oldest":
        passages = list(reversed(passages))

    total = len(passages)
    total_pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    end = start + limit
    page_items = passages[start:end]

    return {
        "items": [
            {
                "id": p["id"],
                "complexity": p["complexity"],
                "word_count": p["word_count"],
                "preview": (p["text"][:90] + "...") if len(p["text"]) > 90 else p["text"],
            }
            for p in page_items
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }

@app.get("/api/read-aloud/{passage_id}")
def get_read_aloud_item(passage_id: str):
    passages = load_read_aloud()
    index = next((i for i, p in enumerate(passages) if p["id"] == passage_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Passage not found")
    match = passages[index]
    audio_filename = ensure_read_aloud_audio(match)
    return {
        **match,
        "audio_url": f"http://127.0.0.1:8000/api/read-aloud/{passage_id}/audio" if audio_filename else None,
        "prev_id": passages[index - 1]["id"] if index > 0 else None,
        "next_id": passages[index + 1]["id"] if index < len(passages) - 1 else None,
        "position": index + 1,
        "total": len(passages),
    }

@app.get("/api/read-aloud/{passage_id}/audio")
def get_read_aloud_audio(passage_id: str):
    passages = load_read_aloud()
    passage = next((p for p in passages if p["id"] == passage_id), None)
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")

    audio_filename = ensure_read_aloud_audio(passage)
    if not audio_filename:
        raise HTTPException(status_code=404, detail="Audio unavailable")

    filepath = os.path.join(READ_ALOUD_AUDIO_DIR, audio_filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")

    response = FileResponse(filepath, media_type="audio/wav")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.post("/api/read-aloud/score")
async def score_read_aloud_recording(passage_id: str = Form(...), audio: UploadFile = File(...)):
    passages = load_read_aloud()
    passage = next((p for p in passages if p["id"] == passage_id), None)
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")

    suffix = os.path.splitext(audio.filename or "recording.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    trimmed_path = None
    try:
        trimmed_path = tmp_path.replace(suffix, "_trimmed.wav")
        audio_path = audio_utils.trim_silence(tmp_path, trimmed_path)

        start = time.time()
        result = transcribe_audio(audio_path)
        elapsed = time.time() - start

        clean_segments = [
            seg for seg in result["segments"]
            if seg.get("no_speech_prob", 0) < 0.5 and seg.get("avg_logprob", -1) > -1.0
        ]
        clean_text = " ".join(seg["text"].strip() for seg in clean_segments).strip()

        print(f"[Read Aloud] Whisper transcribed in {elapsed:.2f}s: {len(clean_text)} chars"
              f" (dropped {len(result['segments']) - len(clean_segments)} low-confidence segment(s))")

        duration_seconds = clean_segments[-1]["end"] if clean_segments else 0.0

        alignment = None
        pauses = None
        try:
            alignment = forced_alignment.align(audio_path, passage["text"])
            pauses = forced_alignment.detect_pauses(alignment)
        except Exception as e:
            print(f"Forced alignment failed for Read Aloud, falling back to Whisper-only scoring: {e}")

        scores = score_read_aloud(
            reference=passage["text"],
            hypothesis=clean_text,
            segments=clean_segments,
            duration_seconds=duration_seconds,
            alignment=alignment,
            pauses=pauses,
        )
        return scores
    finally:
        os.remove(tmp_path)
        if trimmed_path and os.path.exists(trimmed_path):
            os.remove(trimmed_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
