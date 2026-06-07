"""Fine-tune a tone classification head on top of frozen HuBERT."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from transformers import AutoFeatureExtractor, HubertModel

from audio.preprocess import load_audio
from audio.tone_classifier import ToneClassificationHead, DEFAULT_HUBERT_MODEL

DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "tone_samples" / "manifest.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "tone_classifier.pt"


class ToneDataset(Dataset):
    def __init__(self, rows: list[dict], processor, max_length: int = 16000) -> None:
        self.rows = rows
        self.processor = processor
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict:
        row = self.rows[idx]
        waveform = load_audio(row["filepath"])
        if len(waveform) > self.max_length:
            waveform = waveform[: self.max_length]

        inputs = self.processor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt",
            padding="max_length",
            max_length=self.max_length,
            truncation=True,
        )
        return {
            "input_values": inputs.input_values.squeeze(0),
            "label": torch.tensor(int(row["tone"]) - 1, dtype=torch.long),
        }


def read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Manifest not found: {path}\n"
            "Create data/tone_samples/manifest.csv with columns: filepath,tone"
        )

    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            filepath = Path(row["filepath"])
            if not filepath.is_absolute():
                filepath = PROJECT_ROOT / filepath
            rows.append(
                {
                    "filepath": str(filepath),
                    "tone": row["tone"],
                }
            )
    return rows


def train_one_epoch(
    hubert: HubertModel,
    head: ToneClassificationHead,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: str,
) -> float:
    head.train()
    total_loss = 0.0

    for batch in loader:
        input_values = batch["input_values"].to(device)
        labels = batch["label"].to(device)

        with torch.no_grad():
            outputs = hubert(input_values)
            features = outputs.last_hidden_state.mean(dim=1)

        logits = head(features)
        loss = criterion(logits, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item())

    return total_loss / max(len(loader), 1)


@torch.no_grad()
def evaluate(
    hubert: HubertModel,
    head: ToneClassificationHead,
    loader: DataLoader,
    device: str,
) -> float:
    head.eval()
    correct = 0
    total = 0

    for batch in loader:
        input_values = batch["input_values"].to(device)
        labels = batch["label"].to(device)
        outputs = hubert(input_values)
        features = outputs.last_hidden_state.mean(dim=1)
        logits = head(features)
        preds = torch.argmax(logits, dim=-1)
        correct += int((preds == labels).sum().item())
        total += labels.size(0)

    return correct / max(total, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune HuBERT tone classifier head")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--model-name", type=str, default=DEFAULT_HUBERT_MODEL)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows = read_manifest(args.manifest)
    train_rows, val_rows = train_test_split(rows, test_size=0.2, random_state=42, stratify=[r["tone"] for r in rows])

    processor = AutoFeatureExtractor.from_pretrained(args.model_name)
    hubert = HubertModel.from_pretrained(args.model_name).to(device)
    hubert.eval()
    for param in hubert.parameters():
        param.requires_grad = False

    head = ToneClassificationHead(input_dim=hubert.config.hidden_size).to(device)
    train_loader = DataLoader(ToneDataset(train_rows, processor), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(ToneDataset(val_rows, processor), batch_size=args.batch_size)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(head.parameters(), lr=args.lr)

    print(f"Training on {device} using {len(train_rows)} samples...")
    for epoch in range(1, args.epochs + 1):
        loss = train_one_epoch(hubert, head, train_loader, criterion, optimizer, device)
        accuracy = evaluate(hubert, head, val_loader, device)
        print(f"Epoch {epoch:02d} | loss={loss:.4f} | val_acc={accuracy:.2%}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(head.state_dict(), args.output)
    print(f"Saved classifier head to {args.output}")


if __name__ == "__main__":
    main()
