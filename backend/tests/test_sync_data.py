import json
import os
import tempfile
import unittest
from unittest.mock import patch

import sync_data
from sync_data import build_progress_payload, build_read_aloud_bank, build_word_bank


class SyncDataTests(unittest.TestCase):
    def test_build_word_bank_filters_only_difficult_words(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            questions = [
                {"id": "RS_0001", "text": "A cat sat on the mat."},
                {"id": "RS_0002", "text": "The extraordinary elephant explored the environment."},
            ]
            output_path = os.path.join(tmpdir, "word_bank.json")

            words = build_word_bank(questions, output_path=output_path, only_difficult=True)

            self.assertTrue(words)
            self.assertTrue(all(word["difficulty"] == "Difficult" for word in words))
            self.assertTrue(os.path.exists(output_path))

            with open(output_path, "r", encoding="utf-8") as fh:
                saved_words = json.load(fh)

            self.assertEqual(saved_words, words)

    def test_build_read_aloud_bank_writes_expected_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            passages = [
                "The quick brown fox jumps over the lazy dog.",
                "A second passage with more detail and a longer sentence.",
            ]
            output_path = os.path.join(tmpdir, "read_aloud_bank.json")

            bank = build_read_aloud_bank(passages, output_path=output_path, prefix="RA")

            self.assertEqual(len(bank), 2)
            self.assertTrue(all(item["id"].startswith("RA_") for item in bank))
            self.assertTrue(all("text" in item for item in bank))
            self.assertTrue(os.path.exists(output_path))

            with open(output_path, "r", encoding="utf-8") as fh:
                saved_bank = json.load(fh)

            self.assertEqual(saved_bank, bank)

    def test_build_progress_payload_reports_eta(self):
        payload = build_progress_payload(
            message="Processing lines",
            completed=4,
            total=10,
            elapsed_seconds=20,
        )

        self.assertEqual(payload["percent"], 40)
        self.assertEqual(payload["completed"], 4)
        self.assertEqual(payload["total"], 10)
        self.assertEqual(payload["estimated_remaining_seconds"], 30)

    def test_reset_audio_dirs_clears_existing_audio_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            question_audio_dir = os.path.join(tmpdir, "question_audio")
            word_audio_dir = os.path.join(tmpdir, "word_audio")
            os.makedirs(question_audio_dir, exist_ok=True)
            os.makedirs(word_audio_dir, exist_ok=True)

            with open(os.path.join(question_audio_dir, "old_question.wav"), "w", encoding="utf-8") as fh:
                fh.write("old")
            with open(os.path.join(word_audio_dir, "old_word.wav"), "w", encoding="utf-8") as fh:
                fh.write("old")

            with patch.object(sync_data, "QUESTION_AUDIO_DIR", question_audio_dir), patch.object(sync_data, "WORD_AUDIO_DIR", word_audio_dir):
                sync_data.reset_audio_dirs()

            self.assertEqual(os.listdir(question_audio_dir), [])
            self.assertEqual(os.listdir(word_audio_dir), [])


if __name__ == "__main__":
    unittest.main()
