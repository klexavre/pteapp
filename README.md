# PTE Practice Platform v2 (Next.js + Python, Fully Local)

A professional local testing/practice environment for PTE Repeat Sentence
and single-word pronunciation drills. Real Whisper transcription, real
forced-alignment pronunciation scoring, exam-style auto-play/auto-record
timing - all running on your own machine.

```
pte-app-v2/
├── backend/
│   ├── server.py                 FastAPI app - all API endpoints
│   ├── scorer.py                 Content / Fluency / Pronunciation scoring
│   ├── forced_alignment.py       Wav2Vec2 forced alignment (real word timing + confidence)
│   ├── audio_utils.py            Silence trimming (fixes Whisper hallucination)
│   ├── difficulty_classifier.py  Sentence difficulty auto-tagging
│   ├── word_extractor.py         Builds word_bank.json from questions.json
│   ├── tips_data.py              Tiered tips + pre-practice plans
│   ├── txt_to_questions.py       Converts a numbered .txt bank -> questions.json
│   ├── generate_audio.py         Piper TTS - sentence audio generation
│   ├── generate_word_audio.py    Piper TTS - word audio generation
│   ├── questions.json
│   ├── word_bank.json
│   └── requirements.txt
└── frontend/                      Next.js 14 (App Router)
    ├── app/
    │   ├── page.jsx                Home page (Repeat Sentence / Word Drills)
    │   ├── sentences/page.jsx      Sentence list
    │   ├── sentences/[id]/page.jsx Sentence practice (auto-flow + next/prev)
    │   ├── words/page.jsx          Word list
    │   └── words/[word]/page.jsx   Word practice (auto-flow + next/prev)
    ├── components/
    │   ├── AutoPracticeFlow.jsx    Auto-play -> countdown -> beep -> auto-record
    │   ├── NavControls.jsx         Previous/Next navigation
    │   ├── ScoreDisplay.jsx
    │   ├── TipsPanel.jsx
    │   ├── QuestionList.jsx
    │   └── WordDrillList.jsx
    └── lib/
        ├── api.js                  All backend fetch calls
        └── beep.js                 Synthesized beep tone (no audio file needed)
```

## Quick start

The easiest way to get started is from the repository root:

```bash
npm run setup
npm run dev
```

That will:
- create a Python virtual environment in the backend folder,
- install Python dependencies,
- generate the question and word banks,
- install frontend dependencies,
- start both the backend and frontend together.

### Docker option

If you prefer containers:

```bash
docker compose up --build
```

Then open:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## 1. Backend setup

Requires Python 3.9+ and ffmpeg (`sudo apt install ffmpeg` / `brew install ffmpeg`).

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

First run downloads:
- Whisper "small" model (~500MB) - configurable, see below
- Wav2Vec2 forced-alignment model (~360MB)

Both are cached after the first download - fully offline after that.

### Build your question and word banks

```bash
python txt_to_questions.py repeat_sentence.txt --output questions.json
python word_extractor.py --questions questions.json --output word_bank.json
```

### Add audio (optional but recommended)

```bash
pip install piper-tts
# download a voice model from https://github.com/rhasspy/piper/releases
python generate_audio.py --voice voices/en_GB-alan-medium.onnx
python generate_word_audio.py --voice voices/en_GB-alan-medium.onnx
```

If you skip this, word drills fall back automatically to the browser's
built-in voice. Sentence audio requires a real file (there's no sentence-
level browser-TTS fallback, since exam-quality sentence audio should be
consistent and pre-generated).

### Run the backend

```bash
uvicorn server:app --reload --port 8000
```

On Windows, and when using the included virtual environment, run the
backend from the `backend` folder with the `.venv` Python binary so the
local `piper` package and bundled `piper.exe` are available. If you
see an OpenMP startup error when loading certain native libraries, set
the `KMP_DUPLICATE_LIB_OK` environment variable to avoid the crash.

PowerShell (Windows) example:

```powershell
Set-Location backend
# Use the virtualenv Python executable created by the setup script:
.\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
# If you hit an OpenMP duplicate-lib error, try:
$env:KMP_DUPLICATE_LIB_OK='TRUE'
.\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### Whisper accuracy tuning

Model size is configurable via environment variable:
```bash
WHISPER_MODEL_SIZE=medium uvicorn server:app --reload --port 8000
```
Options: `tiny` (fastest, least accurate) -> `base` -> `small` (default) ->
`medium` -> `large` (slowest, most accurate). `small` is a solid default
balance for a local CPU machine.

## 2. Frontend setup (Next.js)

Requires Node.js 18+.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

If you want to run the frontend on a different port (dev only):

```powershell
Set-Location frontend
$env:PORT='3000'
npm run dev
```

Quick tip: the frontend now exposes a pre-sync plan endpoint the UI
uses to show how many audio files will be generated before starting a
sync run: `GET /api/sync-data/plan` (defaults to skipping heavy Read
Aloud audio so the plan is quick to compute).

## Stop & resume (developer convenience)

If you want to stop the local dev servers and resume later from the
same place, here are simple PowerShell snippets to stop running servers
and to restart them when you're ready.

Stop backend (port 8000) and frontend (port 3000):

```powershell
# Stop any process listening on port 8000 (backend)
$p = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess; if ($p) { Stop-Process -Id $p -Force }
# Stop any process listening on port 3000 (frontend)
$p = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess; if ($p) { Stop-Process -Id $p -Force }
```

Start them again later (from the repository root):

```powershell
Set-Location backend
$env:KMP_DUPLICATE_LIB_OK='TRUE'
.\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000

# In a separate shell
Set-Location frontend
$env:PORT='3000'
npm run dev
```

This lets you shut down quickly and resume work later without losing
your local environment state.

If your backend runs somewhere other than `localhost:8000`, set:
```bash
NEXT_PUBLIC_API_URL=http://your-backend-host:8000 npm run dev
```

## 3. How the practice flow works

Every practice page (sentence or word) runs the same automatic sequence,
matching real exam timing:

1. **3 second countdown** before the audio plays (`AutoPracticeFlow.jsx`)
2. **Question audio plays once**
3. **3 second countdown** ("get ready")
4. **Beep** (synthesized tone, no audio file needed)
5. **Recording starts automatically** - no button press needed
6. **Recording auto-stops** after the max duration (15s for sentences, 4s
   for single words)
7. User reviews, then presses **Submit** to get scored

Next/Previous buttons at the bottom of every practice page move between
questions or words in sequence, using `prev_id`/`next_id` (or
`prev_word`/`next_word`) returned directly by the backend - no extra
round-trips needed.

## 4. Whisper hallucination fix (accurate transcription)

Whisper can occasionally "hear" words that were never said, especially on
short clips with silence padding. Two fixes are built in:

- **`audio_utils.py`** strips leading/trailing silence with ffmpeg before
  Whisper ever sees the recording - the single biggest cause of
  hallucination on short clips.
- **`server.py`** uses tuned decoding (`condition_on_previous_text=False`,
  `temperature=0.0`) and drops any segment Whisper itself flags as
  low-confidence (high `no_speech_prob` or low `avg_logprob`) before
  scoring.

If you still see occasional extra words, bump `WHISPER_MODEL_SIZE` to
`medium` - larger models hallucinate noticeably less.

## 5. Pronunciation scoring - how it actually works

- **Whisper** transcribes what you said (free transcription).
- **Wav2Vec2 forced alignment** (`forced_alignment.py`) separately aligns
  your audio against the *exact reference sentence/word*, producing real
  per-word timestamps and acoustic confidence scores - this drives the
  Pronunciation score and the color-coded word breakdown.
- **Content score** = Word Error Rate between Whisper's transcript and the
  reference text.
- **Fluency score** = words-per-minute against an ideal speaking pace,
  plus real pause detection from the forced-alignment timestamps.

## Honest limitations

- Pronunciation scoring is real **word-level acoustic confidence**, not
  full phoneme-level IPA nativeness scoring (that would need a
  specialised commercial model, e.g. Azure Pronunciation Assessment).
- Difficulty auto-tagging (sentences and words) is a transparent heuristic
  (word count + syllable density) - spot-check and adjust manually if
  needed.
- Browser autoplay policies may block the very first audio playback until
  you've clicked once on the page - `AutoPracticeFlow.jsx` surfaces a
  clear retry message if this happens, rather than failing silently.
- Recording format is `.webm` from the browser's MediaRecorder - both
  Whisper and forced alignment handle this fine via ffmpeg, no manual
  conversion needed.
