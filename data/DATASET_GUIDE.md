# Kaggle Dataset Setup — CSS10 Chinese Single Speaker

**Source:** [bryanpark/chinese-single-speaker-speech-dataset](https://www.kaggle.com/datasets/bryanpark/chinese-single-speaker-speech-dataset)

This is the **CSS10 Chinese** corpus (Kyubyong Park, Interspeech 2019):
- **2,971** audio clips
- **~6.5 hours** of Mandarin
- **1 speaker** (Jing Li)
- **22,050 Hz** WAV (auto-resampled to 16 kHz for HuBERT)
- Books: *Call to Arms* (呐喊) + *Dawn Blossoms* (朝花夕拾) by Lu Xun

---

## Step 1 — Download from Kaggle

### Option A: Manual (easiest)

1. Open: https://www.kaggle.com/datasets/bryanpark/chinese-single-speaker-speech-dataset
2. Log in to Kaggle
3. Click **Download**
4. Unzip into:
   ```
   C:\Users\aena zam\Downloads\speaker dataset mandarin\
   ```

You should end up with:
```
speaker dataset mandarin/
  transcript.txt
  call_to_arms/
    call_to_arms_0000.wav
    ...
  chao_hua_si_she/
    chao_hua_si_she_0000.wav
    ...
```

### Option B: Kaggle CLI

```bash
pip install kaggle
python scripts/download_kaggle_dataset.py
```

One-time setup: Kaggle → Account → **Create New API Token** → save as `C:\Users\aena zam\.kaggle\kaggle.json`

---

## Step 2 — Build training manifest

```bash
cd C:\Users\aena zam\Projects\yopengyou
python scripts/prepare_speaker_dataset.py
```

This reads `transcript.txt`, extracts tone labels from pinyin, and writes:
`data/tone_samples/manifest.csv`

By default it keeps clips **≤ 6 seconds** (better for tone labeling).

---

## Step 3 — Train HuBERT tone head

```bash
python scripts/train_tone_model.py --epochs 10
```

Saves model to: `models/tone_classifier.pt`

---

## Step 4 — Run the app

```bash
streamlit run app/main.py
```

Tone feedback switches from **mock mode** to **real HuBERT predictions**.

---

## Important notes for CSC649

| Point | Detail |
|-------|--------|
| Good for | Speech pipeline demo, HuBERT fine-tuning, CSC649 deep learning rubric |
| Limitation | Clips are **sentences**, not isolated 妈/麻/马/骂 — tone labels are approximate |
| Better accuracy | Also record 10–20 short clips per tone yourself |
| Sample rate | 22050 Hz → resampled to 16000 Hz automatically |
| Report use | Cite: Park & Mulc, "CSS10: A Collection of Single Speaker Speech Datasets for 10 Languages", Interspeech 2019 |

---

## Transcript format

Each line in `transcript.txt`:
```
call_to_arms/call_to_arms_0000.wav|Chinese text|pinyin with tone marks|duration_seconds
```

Example:
```
call_to_arms/call_to_arms_0004.wav|——几乎是每天，出入于质铺和药店里，|— — jī hū shì měi tiān ， chū rù yú zhí pù hé yào diàn lǐ ，|3.81
```

Your current folder has **transcript.txt only** — the `.wav` folders come from the Kaggle download.
