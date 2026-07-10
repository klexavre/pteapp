import os
import tempfile
from pathlib import Path

import server


def test_resolve_audio_file_falls_back_to_wav_when_metadata_uses_mp3():
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "sample.wav"
        audio_path.write_bytes(b"RIFF")

        resolved = server.resolve_audio_file(tmpdir, "sample.mp3")

        assert resolved == "sample.wav"
        assert os.path.exists(os.path.join(tmpdir, resolved))
