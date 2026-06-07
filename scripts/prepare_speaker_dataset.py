"""
Prepare the Kaggle CSS10 Chinese speaker dataset for YoPengyou tone training.

Dataset: https://www.kaggle.com/datasets/bryanpark/chinese-single-speaker-speech-dataset

Expected layout after download:
  speaker dataset mandarin/
    transcript.txt          # wav_path|chinese|pinyin|duration
    call_to_arms/*.wav      # 22050 Hz — resampled to 16 kHz by audio/preprocess.py
    chao_hua_si_she/*.wav

Download first:
  python scripts/download_kaggle_dataset.py
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(r"C:\Users\aena zam\Downloads\speaker dataset mandarin")
DEFAULT_OUTPUT_MANIFEST = PROJECT_ROOT / "data" / "tone_samples" / "manifest.csv"
DEFAULT_OUTPUT_AUDIO = PROJECT_ROOT / "data" / "tone_samples" / "speaker"

# Pinyin tone mark → tone number (1-4)
TONE_VOWELS = {
    "ā": 1, "á": 2, "ǎ": 3, "à": 4,
    "ē": 1, "é": 2, "ě": 3, "è": 4,
    "ī": 1, "í": 2, "ǐ": 3, "ì": 4,
    "ō": 1, "ó": 2, "ǒ": 3, "ò": 4,
    "ū": 1, "ú": 2, "ǔ": 3, "ù": 4,
    "ǖ": 1, "ǘ": 2, "ǚ": 3, "ǜ": 4,
    "ü": 5,  # neutral — skipped
}


def tone_from_syllable(syllable: str) -> int | None:
    """Extract tone 1-4 from a pinyin syllable with tone marks."""
    for char in syllable:
        if char in TONE_VOWELS:
            tone = TONE_VOWELS[char]
            return tone if tone <= 4 else None
    return None


def parse_transcript_line(line: str) -> dict | None:
    parts = line.strip().split("|")
    if len(parts) < 4:
        return None
    return {
        "wav_rel": parts[0].strip(),
        "chinese": parts[1].strip(),
        "pinyin": parts[2].strip(),
        "duration": parts[3].strip(),
    }


def dominant_tone(pinyin: str) -> int | None:
    """Pick the most common tone in a pinyin string (rough label for long clips)."""
    tones = []
    for token in re.split(r"[\s，。、；：！？,.;:!?\-—]+", pinyin.lower()):
        token = token.strip("·()[]\"'")
        if not token:
            continue
        tone = tone_from_syllable(token)
        if tone:
            tones.append(tone)
    if not tones:
        return None
    return max(set(tones), key=tones.count)


def scan_dataset(source_dir: Path, max_duration: float | None = None) -> dict:
    transcript = source_dir / "transcript.txt"
    if not transcript.exists():
        transcript = source_dir / "zh" / "transcript.txt"

    if not transcript.exists():
        raise FileNotFoundError(f"No transcript.txt found in {source_dir}")

    rows: list[dict] = []
    missing_wav = 0
    found_wav = 0

    with transcript.open(encoding="utf-8") as handle:
        for line in handle:
            parsed = parse_transcript_line(line)
            if not parsed:
                continue

            wav_path = source_dir / parsed["wav_rel"]
            tone = dominant_tone(parsed["pinyin"])
            try:
                duration = float(parsed["duration"])
            except ValueError:
                duration = None

            if max_duration is not None and duration is not None and duration > max_duration:
                continue

            entry = {
                "filepath": str(wav_path),
                "tone": tone,
                "chinese": parsed["chinese"][:80],
                "pinyin": parsed["pinyin"][:80],
                "duration_sec": parsed["duration"],
                "exists": wav_path.exists(),
            }

            if wav_path.exists():
                found_wav += 1
            else:
                missing_wav += 1

            if tone is not None:
                rows.append(entry)

    return {
        "rows": rows,
        "found_wav": found_wav,
        "missing_wav": missing_wav,
        "transcript_path": transcript,
    }


def write_manifest(rows: list[dict], output: Path, only_existing: bool = True) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["filepath", "tone", "chinese", "pinyin", "duration_sec"],
        )
        writer.writeheader()

        for row in rows:
            if only_existing and not row["exists"]:
                continue
            writer.writerow(
                {
                    "filepath": row["filepath"],
                    "tone": row["tone"],
                    "chinese": row["chinese"],
                    "pinyin": row["pinyin"],
                    "duration_sec": row["duration_sec"],
                }
            )
            written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan speaker dataset and build training manifest")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--include-missing", action="store_true", help="Include rows even if wav is missing")
    parser.add_argument(
        "--max-duration",
        type=float,
        default=6.0,
        help="Skip clips longer than N seconds (shorter clips work better for tone labels)",
    )
    args = parser.parse_args()

    print(f"Scanning: {args.source}")
    result = scan_dataset(args.source, max_duration=args.max_duration)
    rows = result["rows"]

    print(f"Transcript: {result['transcript_path']}")
    print(f"Total labeled rows: {len(rows)}")
    print(f"WAV files found:    {result['found_wav']}")
    print(f"WAV files missing:  {result['missing_wav']}")

    if result["found_wav"] == 0:
        print("\n⚠️  NO AUDIO FILES FOUND.")
        print("You only have transcript.txt right now.")
        print("Download from Kaggle:")
        print("  https://www.kaggle.com/datasets/bryanpark/chinese-single-speaker-speech-dataset")
        print("Or run: python scripts/download_kaggle_dataset.py")
        return

    written = write_manifest(rows, args.output, only_existing=not args.include_missing)
    print(f"\nWrote {written} rows to {args.output}")
    print("Next step: python scripts/train_tone_model.py")


if __name__ == "__main__":
    main()
