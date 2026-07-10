import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import server


class ReadAloudScoringTests(unittest.TestCase):
    def test_read_aloud_score_uses_transcribe_audio_helper(self):
        client = TestClient(server.app)
        passage = {
            "id": "passage-1",
            "text": "hello world",
            "complexity": "Easy",
            "word_count": 2,
            "prep_seconds": 5,
            "max_record_seconds": 30,
        }
        fake_transcription = {
            "segments": [{"text": "hello world", "no_speech_prob": 0.1, "avg_logprob": -0.2, "end": 1.0}],
            "text": "hello world",
            "info": {},
        }

        with patch.object(server, "WHISPER_MODEL", None), \
             patch.object(server, "FASTER_WHISPER_MODEL", None), \
             patch.object(server, "transcribe_audio", return_value=fake_transcription) as mock_transcribe, \
             patch.object(server.audio_utils, "trim_silence", return_value="audio.wav"), \
             patch.object(server.forced_alignment, "align", return_value=[{"score": 0.8}]), \
             patch.object(server.forced_alignment, "detect_pauses", return_value=[]), \
             patch.object(server, "load_read_aloud", return_value=[passage]), \
             patch.object(server, "score_read_aloud", return_value={"overall": {"score": 75}}):
            response = client.post(
                "/api/read-aloud/score",
                data={"passage_id": passage["id"]},
                files={"audio": ("test.webm", b"fake-audio", "audio/webm")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["overall"]["score"], 75)
        mock_transcribe.assert_called_once()


if __name__ == "__main__":
    unittest.main()
