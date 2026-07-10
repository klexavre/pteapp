"""
generate_word_audio.py
------------------------
Pre-generates MP3 audio for every word in word_bank.json, using Piper TTS
(same engine as generate_audio.py, just pointed at single words instead of
full sentences). If you skip this step, WordDrillPractice.jsx automatically
falls back to the browser's built-in speechSynthesis voice - so this script
is optional, but pre-generated audio sounds more consistent.

Usage:
    python word_extractor.py                 # build word_bank.json first
    python generate_word_audio.py --voice voices/en_GB-alan-medium.onnx
"""

import argparse
import json
import os
import subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))
WORD_BANK_FILE = os.path.join(APP_DIR, "word_bank.json")
WORD_AUDIO_DIR = os.path.join(APP_DIR, "word_audio")
RUNTIME_STATE = os.path.join(APP_DIR, ".piper", "runtime.json")


def resolve_piper_binary() -> str:
    env_value = os.environ.get("PIPER_BIN")
    if env_value and os.path.exists(env_value):
        return env_value

    if os.path.exists(RUNTIME_STATE):
        try:
            with open(RUNTIME_STATE, "r", encoding="utf-8") as f:
                state = json.load(f)
            candidate = state.get("piper_bin")
            if candidate and os.path.exists(candidate):
                return candidate
        except Exception:
            pass

    return "piper"


def synthesize_with_piper(piper_bin: str, voice_model_path: str, text: str, wav_path: str) -> None:
    try:
        subprocess.run(
            [piper_bin, "--model", voice_model_path, "--output_file", wav_path],
            input=text.encode("utf-8"),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        import piper
        import struct
        import wave

        model = piper.PiperVoice.load(voice_model_path)
        audio_chunks = list(model.synthesize(text))
        if not audio_chunks:
            raise RuntimeError("Piper produced no audio chunks")

        with wave.open(wav_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            for chunk in audio_chunks:
                pcm = []
                for sample in chunk.audio_float_array:
                    value = int(max(-1.0, min(1.0, sample)) * 32767)
                    pcm.append(struct.pack("<h", value))
                wav_file.writeframes(b"".join(pcm))


def main(voice_model_path: str):
    os.makedirs(WORD_AUDIO_DIR, exist_ok=True)

    if not os.path.exists(WORD_BANK_FILE):
        print("word_bank.json not found - run word_extractor.py first.")
        return

    with open(WORD_BANK_FILE, "r") as f:
        words = json.load(f)

    for w in words:
        wav_path = os.path.join(WORD_AUDIO_DIR, w["audio_file"].replace(".mp3", ".wav"))
        mp3_path = os.path.join(WORD_AUDIO_DIR, w["audio_file"])

        if os.path.exists(wav_path):
            print(f"Skipping existing audio for: {w['display']}")
            continue

        print(f"Generating audio for: {w['display']}")

        piper_bin = resolve_piper_binary()

        synthesize_with_piper(piper_bin, voice_model_path, w["display"], wav_path)
        if os.path.exists(wav_path):
            print(f"  -> saved {wav_path}")
        else:
            print(f"  -> failed to create {wav_path}")

    print(f"\nDone. Word audio saved in {WORD_AUDIO_DIR}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", required=True, help="Path to a Piper .onnx voice model")
    args = parser.parse_args()
    main(args.voice)
