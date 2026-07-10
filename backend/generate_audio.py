"""
generate_audio.py
------------------
One-time script to pre-generate MP3 audio for every question in
questions.json, using Piper TTS (free, fully offline, runs on CPU).

Setup (run once):
  pip install piper-tts
  # Download a voice model, e.g. en_GB-alan-medium or en_US-lessac-medium,
  # from https://github.com/rhasspy/piper/releases (look for "voices")
  # Place the .onnx and .onnx.json files in a `voices/` folder next to this script.

Usage:
  python generate_audio.py --voice voices/en_GB-alan-medium.onnx
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

APP_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(APP_DIR, "questions.json")
AUDIO_DIR = os.path.join(APP_DIR, "question_audio")
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

        model = piper.PiperVoice.load(voice_model_path)
        audio_chunks = list(model.synthesize(text))
        if not audio_chunks:
            raise RuntimeError("Piper produced no audio chunks")

        import struct
        import wave

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
    os.makedirs(AUDIO_DIR, exist_ok=True)

    with open(QUESTIONS_FILE, "r") as f:
        questions = json.load(f)

    for q in questions:
        wav_path = os.path.join(AUDIO_DIR, q["audio_file"].replace(".mp3", ".wav"))
        mp3_path = os.path.join(AUDIO_DIR, q["audio_file"])

        if os.path.exists(wav_path):
            print(f"Skipping existing audio for {q['id']}: {wav_path}")
            continue

        print(f"Generating audio for {q['id']}: {q['text']!r}")

        piper_bin = resolve_piper_binary()

        synthesize_with_piper(piper_bin, voice_model_path, q["text"], wav_path)

        if os.path.exists(wav_path):
            print(f"  -> saved {wav_path}")
        else:
            print(f"  -> failed to create {wav_path}")

    print("\nAll question audio generated successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voice",
        required=True,
        help="Path to a Piper .onnx voice model, e.g. voices/en_GB-alan-medium.onnx",
    )
    args = parser.parse_args()
    main(args.voice)
