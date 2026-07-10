"""
txt_to_questions.py
--------------------
Converts a "repeat sentence.txt" file of Repeat Sentence questions into the
questions.json format used by the app.

Input format (one sentence per line, numbered):
    1.  A computer virus destroyed all my files.
    2.  A lot of agricultural workers came to the east end to look for alternative work.
    ...

Output: questions.json with auto-generated id, complexity, and audio_file name.

Usage:
    python txt_to_questions.py repeat_sentence.txt
    python txt_to_questions.py repeat_sentence.txt --output questions.json --prefix RS
"""

import argparse
import json
import re

from difficulty_classifier import classify_difficulty


def parse_txt(filepath: str) -> list:
    """
    Parses lines like "1.  Sentence text." or "12) Sentence text." into a
    flat list of sentence strings, ignoring blank lines.
    """
    sentences = []
    line_pattern = re.compile(r"^\s*\d+[\.\)]\s*(.+)$")

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = line_pattern.match(line)
            if match:
                sentence = match.group(1).strip()
            else:
                sentence = line
            if sentence:
                sentences.append(sentence)
    return sentences


def build_questions(sentences: list, prefix: str) -> list:
    questions = []
    for i, sentence in enumerate(sentences, start=1):
        qid = f"{prefix}_{i:04d}"
        questions.append(
            {
                "id": qid,
                "text": sentence,
                "complexity": classify_difficulty(sentence),
                "audio_file": f"{qid}.mp3",
            }
        )
    return questions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_txt", help="Path to the .txt question bank")
    parser.add_argument("--output", default="questions.json", help="Output JSON path")
    parser.add_argument("--prefix", default="RS", help="Question ID prefix (default: RS)")
    args = parser.parse_args()

    sentences = parse_txt(args.input_txt)
    questions = build_questions(sentences, args.prefix)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"Converted {len(questions)} questions -> {args.output}")

    counts = {"Easy": 0, "Medium": 0, "Difficult": 0}
    for q in questions:
        counts[q["complexity"]] += 1
    print(f"Difficulty breakdown: {counts}")


if __name__ == "__main__":
    main()
