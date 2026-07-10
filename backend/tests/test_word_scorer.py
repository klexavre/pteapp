import unittest

from scorer import score_single_word


class WordScorerTests(unittest.TestCase):
    def test_score_single_word_uses_transcription_for_match(self):
        result = score_single_word("hello", alignment=[], transcription="hello")
        self.assertEqual(result["verdict"], "clear")
        self.assertGreaterEqual(result["score"], 70)
        self.assertEqual(result["transcription"], "hello")


if __name__ == "__main__":
    unittest.main()
