"""
Download the CSS10 Chinese Single Speaker dataset from Kaggle.

Dataset: https://www.kaggle.com/datasets/bryanpark/chinese-single-speaker-speech-dataset
Paper:   CSS10 — Kyubyong Park & Thomas Mulc (Interspeech 2019)

Contents after download:
  chinese-single-speaker-speech-dataset/
    transcript.txt
    call_to_arms/*.wav      (~22050 Hz mono)
    chao_hua_si_she/*.wav
    zh/transcript.txt       (duplicate in some versions)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

KAGGLE_DATASET = "bryanpark/chinese-single-speaker-speech-dataset"
DEFAULT_DOWNLOAD_DIR = Path(r"C:\Users\aena zam\Downloads\speaker dataset mandarin")
PROJECT_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "speaker_corpus"


def run_kaggle_download(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        KAGGLE_DATASET,
        "-p",
        str(target_dir),
        "--unzip",
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def find_transcript(root: Path) -> Path | None:
    for candidate in [root / "transcript.txt", root / "zh" / "transcript.txt"]:
        if candidate.exists():
            return candidate
    return None


def count_wavs(root: Path) -> int:
    return len(list(root.rglob("*.wav")))


def extract_zip_if_needed(download_dir: Path) -> None:
    for zip_path in download_dir.glob("*.zip"):
        print(f"Extracting {zip_path.name}...")
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(download_dir)


def verify_dataset(root: Path) -> dict:
    transcript = find_transcript(root)
    wav_count = count_wavs(root)
    return {
        "transcript": transcript,
        "wav_count": wav_count,
        "ready": transcript is not None and wav_count > 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Kaggle Chinese speaker dataset")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_DOWNLOAD_DIR,
        help="Folder to download and extract into",
    )
    parser.add_argument(
        "--link-only",
        action="store_true",
        help="Print manual download steps without calling Kaggle CLI",
    )
    args = parser.parse_args()

    if args.link_only:
        print_manual_steps(args.output)
        return

    try:
        run_kaggle_download(args.output)
    except FileNotFoundError:
        print("Kaggle CLI not found.")
        print_manual_steps(args.output)
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("\nKaggle download failed — usually missing API token.")
        print_manual_steps(args.output)
        sys.exit(1)

    extract_zip_if_needed(args.output)
    status = verify_dataset(args.output)

    print(f"\nTranscript: {status['transcript']}")
    print(f"WAV files:  {status['wav_count']}")

    if status["ready"]:
        print("\n✅ Dataset ready!")
        print("Next steps:")
        print("  python scripts/prepare_speaker_dataset.py")
        print("  python scripts/train_tone_model.py")
    else:
        print("\n⚠️  Download finished but audio not found.")
        print("Check the folder and unzip any remaining .zip files manually.")
        print_manual_steps(args.output)


def print_manual_steps(output_dir: Path) -> None:
    print(
        f"""
=== Manual Download (no Kaggle CLI) ===

1. Open: https://www.kaggle.com/datasets/bryanpark/chinese-single-speaker-speech-dataset
2. Click "Download" (you must be logged in to Kaggle)
3. Unzip the file into:
   {output_dir}

4. You should see:
   {output_dir}\\transcript.txt
   {output_dir}\\call_to_arms\\*.wav
   {output_dir}\\chao_hua_si_she\\*.wav

=== Kaggle CLI setup (one-time) ===

1. Kaggle → Account → Create New API Token → saves kaggle.json
2. Move kaggle.json to: C:\\Users\\aena zam\\.kaggle\\kaggle.json
3. Install CLI:  pip install kaggle
4. Run:
   python scripts/download_kaggle_dataset.py

=== After download ===

python scripts/prepare_speaker_dataset.py
python scripts/train_tone_model.py
streamlit run app/main.py
"""
    )


if __name__ == "__main__":
    main()
