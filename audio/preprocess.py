"""Audio utilities for 16 kHz WAV preprocessing (HuBERT requirement)."""

from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

TARGET_SAMPLE_RATE = 16000


def load_audio(path: str | Path, target_sr: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """Load audio and resample to 16 kHz mono."""
    waveform, _ = librosa.load(str(path), sr=target_sr, mono=True)
    return waveform.astype(np.float32)


def save_temp_wav(waveform: np.ndarray, path: str | Path, sr: int = TARGET_SAMPLE_RATE) -> Path:
    """Save a temporary WAV clip for tone classification."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output), waveform, sr)
    return output


def normalize_waveform(waveform: np.ndarray) -> np.ndarray:
    """Peak-normalize waveform to avoid clipping issues."""
    peak = np.max(np.abs(waveform))
    if peak == 0:
        return waveform
    return waveform / peak
