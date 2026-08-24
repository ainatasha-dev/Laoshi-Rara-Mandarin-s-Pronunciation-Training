An intelligent Mandarin language learning prototype combining:

- **NLP / Chatbot** — rule-based Level 1 dialogue lessons
- **Speech / Deep Learning** — HuBERT fine-tuned tone classifier (T1–T4)
- **Streamlit UI** — web dashboard for chat + voice practice

## Project Structure

```
yopengyou/
├── app/
│   └── main.py              # Streamlit app (run this)
├── chatbot/
│   ├── dialogue_engine.py   # Rule-based lesson chatbot
│   └── lessons.py           # Mandarin Modern Level 1 scripts
├── audio/
│   ├── preprocess.py        # 16 kHz WAV preprocessing
│   └── tone_classifier.py   # HuBERT + tone head inference
├── scripts/
│   └── train_tone_model.py  # Fine-tune classifier head
├── data/
│   ├── lessons/             # Add textbook content here
│   └── tone_samples/        # Training audio + manifest.csv
├── models/                  # Saved tone_classifier.pt
├── tests/
├── requirements.txt
└── README.md
```

## Open in PyCharm

1. **File → Open** 
2. PyCharm will detect it as a Python project
3. **File → Settings → Project → Python Interpreter**
4. Click **Add Interpreter → Add Local Interpreter → Virtualenv**
5. Create `.venv` inside the project folder
6. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the App

From PyCharm terminal (project root):

```bash
streamlit run app/main.py
```

Or create a **Run Configuration** in PyCharm:
- Script path: `app/main.py`
- Working directory: project root
- Use module mode: `streamlit run app/main.py`

## Train the Tone Model (Week 2)

1. Add `.wav` files (16 kHz) to `data/tone_samples/`
2. Update `data/tone_samples/manifest.csv`:

```csv
filepath,tone,word,pinyin
data/tone_samples/ma1.wav,1,妈,mā
```

3. Run training:

```bash
python scripts/train_tone_model.py --epochs 10
```

4. Model saves to `models/tone_classifier.pt`
5. Restart Streamlit — real tone feedback replaces mock mode

## Team Workflow (3 Weeks)

| Week | Focus |
|------|-------|
| 1 | PyCharm setup, chatbot lessons, audio dataset |
| 2 | HuBERT fine-tuning, Streamlit audio recorder |
| 3 | Integration, testing, demo, report |

## Architecture

```
User Text  →  Dialogue Engine  →  Lesson Reply
User Audio →  HuBERT Features  →  Tone Classifier  →  Tone Feedback
                     ↑
              Streamlit Dashboard
```

## Notes

- Chatbot is **scripted** (not ChatGPT) — scoped for CSC649
- HuBERT requires **16 kHz mono WAV** input
- Use `ntu-spml/distilhubert` for faster training on limited GPU
- Until training data is added, tone feedback runs in **mock mode**

## Run Tests

```bash
pip install pytest
pytest tests/
```
