"""
audio_utils.py
---------------
Preprocessing to reduce Whisper hallucination ("hearing" words that were
never said). This is a well-known Whisper issue, and it has two main
causes in an app like this:

  1. SILENCE PADDING - short recordings (like a single sentence or word)
     often have a second or two of silence at the start/end (mic warm-up,
     or the user pausing before/after speaking). Whisper is trained on
     long-form audio and tends to "fill in" quiet stretches with
     hallucinated text (the infamous "Thank you for watching!" bug is
     exactly this - trained on YouTube outros).

  2. DECODING SETTINGS - by default Whisper conditions each chunk on its
     own previous guess and uses a temperature schedule that lets it keep
     guessing even when uncertain, both of which increase hallucination
     risk on short, isolated utterances (which is all this app ever sends
     it - single sentences or single words, never long-form audio).

This module fixes #1 (trim_silence). server.py's tuned transcribe() call
and segment filtering fixes #2 - see the comments there.
"""

import subprocess
import os


def trim_silence(input_path: str, output_path: str,
                  silence_threshold_db: int = -40,
                  padding_ms: int = 150) -> str:
    """
    Trims leading/trailing silence from an audio file using ffmpeg's
    silenceremove filter (run once forward, once reversed, to strip both
    ends). Keeps a small padding buffer so words aren't clipped.

    Falls back to the original file untouched if ffmpeg fails for any
    reason (never let audio preprocessing break the whole scoring flow).
    """
    padding_sec = padding_ms / 1000.0

    filter_chain = (
        f"silenceremove=start_periods=1:start_duration=0:"
        f"start_threshold={silence_threshold_db}dB:detection=peak,"
        f"areverse,"
        f"silenceremove=start_periods=1:start_duration=0:"
        f"start_threshold={silence_threshold_db}dB:detection=peak,"
        f"areverse,"
        f"apad=pad_dur={padding_sec}"
    )

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-af", filter_chain, output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        # Guard against ffmpeg producing an empty/near-empty file if the
        # whole recording was silence - fall back to the original in that
        # case rather than feeding Whisper an empty clip.
        if os.path.exists(output_path) and os.path.getsize(output_path) > 200:
            return output_path
    except Exception as e:
        print(f"Silence trimming failed, using original audio: {e}")

    return input_path
