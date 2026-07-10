"""
difficulty_classifier.py
-------------------------
Simple, transparent, rule-based difficulty classifier for Repeat Sentence
questions - no ML model needed. Combines word count (matches real PTE
length brackets) with average syllables per word (catches short-but-hard
sentences with dense/technical vocabulary).
"""

import re
import string

VOWELS = "aeiouy"


def count_syllables(word: str) -> int:
    word = word.lower().strip(string.punctuation)
    if not word:
        return 0
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in VOWELS
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    # silent trailing 'e' correction (e.g. "same" -> 1 syllable, not 2)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def classify_difficulty(sentence: str) -> str:
    words = re.findall(r"[A-Za-z']+", sentence)
    word_count = len(words)
    if word_count == 0:
        return "Easy"

    total_syllables = sum(count_syllables(w) for w in words)
    avg_syllables = total_syllables / word_count

    # PTE-style length brackets, adjusted by syllable density
    if word_count <= 9 and avg_syllables < 1.6:
        return "Easy"
    elif word_count <= 14 and avg_syllables < 2.1:
        return "Medium"
    else:
        return "Difficult"


def classify_paragraph_difficulty(paragraph: str) -> str:
    """
    Separate thresholds for Read Aloud passages (typically 40-90 words) -
    the sentence-level brackets above (9/14 words) would classify every
    paragraph as Difficult, which isn't useful. Real PTE Read Aloud
    passages are usually 30-60 words for Easy/Medium and 60+ for Difficult,
    so this scales the same word-count + syllable-density approach to that
    range.
    """
    words = re.findall(r"[A-Za-z']+", paragraph)
    word_count = len(words)
    if word_count == 0:
        return "Easy"

    total_syllables = sum(count_syllables(w) for w in words)
    avg_syllables = total_syllables / word_count

    if word_count <= 40 and avg_syllables < 1.6:
        return "Easy"
    elif word_count <= 70 and avg_syllables < 2.0:
        return "Medium"
    else:
        return "Difficult"


if __name__ == "__main__":
    # quick manual check
    samples = [
        "A computer virus destroyed all my files.",
        "A preliminary bibliography is due the week before the spring break.",
        "Climate change poses a significant threat to coastal ecosystems worldwide.",
    ]
    for s in samples:
        print(f"[{classify_difficulty(s)}] {s}")
