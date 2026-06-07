"""HuBERT-based Mandarin tone classifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from transformers import HubertModel

from audio.preprocess import TARGET_SAMPLE_RATE, load_audio, normalize_waveform

DEFAULT_HUBERT_MODEL = "ntu-spml/distilhubert"
FALLBACK_HUBERT_MODEL = "facebook/hubert-base-ls960"


@dataclass
class TonePrediction:
    tone: int
    confidence: float
    label: str
    used_mock: bool = False


class ToneClassificationHead(nn.Module):
    """Simple linear head on top of frozen HuBERT features."""

    def __init__(self, input_dim: int = 768, num_tones: int = 4) -> None:
        super().__init__()
        self.classifier = nn.Linear(input_dim, num_tones)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.classifier(features)


class ToneClassifier:
    """Load HuBERT, run inference, and return tone predictions."""

    TONE_LABELS = {
        1: "Tone 1 (第一声)",
        2: "Tone 2 (第二声)",
        3: "Tone 3 (第三声)",
        4: "Tone 4 (第四声)",
    }

    def __init__(
        self,
        model_name: str = DEFAULT_HUBERT_MODEL,
        checkpoint_path: str | Path | None = None,
        device: str | None = None,
    ) -> None:
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self._hubert: HubertModel | None = None
        self._head: ToneClassificationHead | None = None
        self._processor = None
        self._ready = False

    def load(self) -> None:
        """Load HuBERT and optional fine-tuned classification head."""
        from transformers import AutoFeatureExtractor

        try:
            self._processor = AutoFeatureExtractor.from_pretrained(self.model_name)
            self._hubert = HubertModel.from_pretrained(self.model_name)
        except OSError:
            self.model_name = FALLBACK_HUBERT_MODEL
            self._processor = AutoFeatureExtractor.from_pretrained(self.model_name)
            self._hubert = HubertModel.from_pretrained(self.model_name)

        self._hubert.to(self.device)
        self._hubert.eval()
        for param in self._hubert.parameters():
            param.requires_grad = False

        hidden_size = self._hubert.config.hidden_size
        self._head = ToneClassificationHead(input_dim=hidden_size).to(self.device)

        if self.checkpoint_path and self.checkpoint_path.exists():
            state = torch.load(self.checkpoint_path, map_location=self.device)
            self._head.load_state_dict(state)
        else:
            # Untrained head — use mock predictions until fine-tuning is done.
            pass

        self._head.eval()
        self._ready = True

    def predict_from_file(self, audio_path: str | Path) -> TonePrediction:
        waveform = normalize_waveform(load_audio(audio_path))
        return self.predict_from_array(waveform)

    def predict_from_array(self, waveform: np.ndarray) -> TonePrediction:
        if not self._ready:
            self.load()

        assert self._hubert is not None
        assert self._head is not None
        assert self._processor is not None

        if self.checkpoint_path is None or not self.checkpoint_path.exists():
            return self._mock_prediction(waveform)

        inputs = self._processor(
            waveform,
            sampling_rate=TARGET_SAMPLE_RATE,
            return_tensors="pt",
        )
        input_values = inputs.input_values.to(self.device)

        with torch.no_grad():
            outputs = self._hubert(input_values)
            pooled = outputs.last_hidden_state.mean(dim=1)
            logits = self._head(pooled)
            probs = torch.softmax(logits, dim=-1)
            tone_idx = int(torch.argmax(probs, dim=-1).item()) + 1
            confidence = float(probs[0, tone_idx - 1].item())

        return TonePrediction(
            tone=tone_idx,
            confidence=confidence,
            label=self.TONE_LABELS[tone_idx],
            used_mock=False,
        )

    def _mock_prediction(self, waveform: np.ndarray) -> TonePrediction:
        """
        Placeholder until your team fine-tunes the classifier.
        Uses simple energy/pitch heuristics so the app is demoable.
        """
        if len(waveform) < 100:
            tone = 1
        else:
            slope = float(np.mean(np.diff(waveform)))
            if slope > 0.001:
                tone = 2
            elif slope < -0.001:
                tone = 4
            elif np.std(waveform) > 0.15:
                tone = 3
            else:
                tone = 1

        return TonePrediction(
            tone=tone,
            confidence=0.55,
            label=self.TONE_LABELS[tone],
            used_mock=True,
        )
