"""
txt_to_readaloud.py
--------------------
Converts a numbered .txt file of Read Aloud passages into
read_aloud_bank.json. Unlike txt_to_questions.py (Repeat Sentence, always
one short line per item), Read Aloud passages can wrap across multiple
lines in the source file - this parser handles both cases: it starts a
new entry whenever it sees a line beginning with "N." or "N)", and appends
any following non-numbered lines to that same entry until the next
numbered line appears.

Input format:
    1.  The speaker reminisces about his views of the English Revolution...
    2.  History is selective. What history books tell us about the past...

(also handles passages that wrap onto multiple lines before the next
number appears)

Usage:
    python txt_to_readaloud.py read_aloud.txt --output read_aloud_bank.json
"""

import argparse
import json
import re

from difficulty_classifier import classify_paragraph_difficulty

LINE_START_PATTERN = re.compile(r"^\s*(\d+)[\.\)]\s*(.+)$")


def parse_txt(filepath: str) -> list:
    """Returns a list of passage strings, correctly merging wrapped lines."""
    passages = []
    current = []

    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            match = LINE_START_PATTERN.match(line)
            if match:
                if current:
                    passages.append(" ".join(current).strip())
                current = [match.group(2).strip()]
            else:
                # Continuation of the current (wrapped) passage
                if current:
                    current.append(line)
                # If a file starts with an unnumbered line, it's ignored -
                # Read Aloud passages should always start with a number.

    if current:
        passages.append(" ".join(current).strip())

    return passages


def estimate_timings(word_count: int) -> dict:
    """
    Real Read Aloud timing scales with passage length: longer passages get
    more prep time and more recording time. These approximate the real
    exam's variable timing rather than using one fixed duration for every
    passage length.
    """
    prep_seconds = max(20, min(40, 15 + word_count // 4))
    record_seconds = max(20, min(90, int(word_count * 0.65) + 8))
    return {"prep_seconds": prep_seconds, "max_record_seconds": record_seconds}


def build_bank(passages: list, prefix: str) -> list:
    bank = []
    for i, text in enumerate(passages, start=1):
        word_count = len(text.split())
        timings = estimate_timings(word_count)
        bank.append({
            "id": f"{prefix}_{i:04d}",
            "text": text,
            "word_count": word_count,
            "complexity": classify_paragraph_difficulty(text),
            **timings,
        })
    return bank


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_txt")
    parser.add_argument("--output", default="read_aloud_bank.json")
    parser.add_argument("--prefix", default="RA")
    args = parser.parse_args()

    passages = parse_txt(args.input_txt)
    bank = build_bank(passages, args.prefix)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)

    counts = {"Easy": 0, "Medium": 0, "Difficult": 0}
    for item in bank:
        counts[item["complexity"]] += 1

    print(f"Converted {len(bank)} passages -> {args.output}")
    print(f"Difficulty breakdown: {counts}")


if __name__ == "__main__":
    main()
