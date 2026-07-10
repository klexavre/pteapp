"""
word_extractor.py
------------------
Builds a single-word drill bank from your existing sentence question bank
(questions.json). Extracts unique words, strips common stopwords (not
useful to drill in isolation), tags each word with a syllable-based
difficulty, and tracks which sentence(s) each word came from - so the UI
can show "this word appears in RS_0002, RS_0007..." for context.

Usage:
    python word_extractor.py
    python word_extractor.py --questions questions.json --output word_bank.json
"""

import argparse
import json
import re
import string

# Common function words are excluded by default - drilling "the" or "a" in
# isolation isn't useful pronunciation practice. Toggle with --keep-stopwords.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "to", "of", "in", "on",
    "at", "for", "and", "or", "but", "it", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "my", "your", "his", "her",
    "its", "our", "their", "be", "been", "being", "has", "have", "had",
    "do", "does", "did", "will", "would", "can", "could", "should", "with",
    "as", "by", "from", "up", "so", "if", "not", "no",
}


def count_syllables(word: str) -> int:
    word = word.lower().strip(string.punctuation)
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def word_difficulty(syllables: int) -> str:
    """Simpler, word-level difficulty scale (distinct from sentence-level)."""
    if syllables <= 1:
        return "Easy"
    elif syllables <= 3:
        return "Medium"
    else:
        return "Difficult"


def extract_words(questions: list, keep_stopwords: bool = False) -> dict:
    """
    Returns a dict keyed by lowercase word, each value containing display
    form, syllable count, difficulty, and which question ids it appeared in.
    """
    word_map = {}

    for q in questions:
        raw_words = re.findall(r"[A-Za-z']+", q["text"])
        for raw in raw_words:
            key = raw.lower()
            if not keep_stopwords and key in STOPWORDS:
                continue
            if len(key) < 3:  # skip very short fragments like "a", "ok" leftovers
                continue

            if key not in word_map:
                syllables = count_syllables(key)
                word_map[key] = {
                    "word": key,
                    "display": raw,
                    "syllables": syllables,
                    "difficulty": word_difficulty(syllables),
                    "source_questions": [],
                    "audio_file": f"word_{key}.mp3",
                }
            if q["id"] not in word_map[key]["source_questions"]:
                word_map[key]["source_questions"].append(q["id"])

    return word_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="questions.json")
    parser.add_argument("--output", default="word_bank.json")
    parser.add_argument("--keep-stopwords", action="store_true")
    args = parser.parse_args()

    with open(args.questions, "r", encoding="utf-8") as f:
        questions = json.load(f)

    word_map = extract_words(questions, keep_stopwords=args.keep_stopwords)
    word_list = sorted(word_map.values(), key=lambda w: (w["difficulty"], w["word"]))

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(word_list, f, indent=2, ensure_ascii=False)

    counts = {"Easy": 0, "Medium": 0, "Difficult": 0}
    for w in word_list:
        counts[w["difficulty"]] += 1

    print(f"Extracted {len(word_list)} unique words -> {args.output}")
    print(f"Difficulty breakdown: {counts}")


if __name__ == "__main__":
    main()
