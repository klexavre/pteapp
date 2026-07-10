import io
import os
import unittest

from fastapi.testclient import TestClient

import server


class WordBatchScorerTests(unittest.TestCase):
    def test_score_batch_endpoint_returns_one_result_per_word(self):
        client = TestClient(server.app)
        files = [
            ("audio", ("w1.webm", b"fake-audio", "audio/webm")),
            ("audio", ("w2.webm", b"fake-audio", "audio/webm")),
        ]
        data = {"words": ["hello", "world"]}

        response = client.post("/api/words/score-batch", data=data, files=files)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["word"], "hello")
        self.assertEqual(payload[1]["word"], "world")


if __name__ == "__main__":
    unittest.main()
