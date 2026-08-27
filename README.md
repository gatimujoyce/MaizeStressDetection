# Maize Stress Detection System

A multimodal system that fuses maize leaf image classification (disease + nutrient deficiency) with environmental sensor data to detect crop stress early and alert farmers, via a PWA dashboard.

## Architecture overview

| Component | Purpose |
|---|---|
| Leaf/not-leaf gate | Rejects non-leaf input before classification |
| Core EfficientNet branch | Classifies Healthy / Common Rust / Northern Leaf Blight / Gray Leaf Spot |
| Nutrient EfficientNet head | Classifies Nutrient-Normal / Nitrogen / Phosphorus / Potassium / Zinc deficiency |
| MLP sensor branch | Classifies Normal / Drought Stress / Heat Stress / Waterlogging Risk from soil, temp, humidity, soil type, growth stage, leaf wetness |
| Fusion layer | Combines image + sensor predictions into a single actionable alert |
| Confidence gate | Below-threshold predictions return "Inconclusive," are excluded from alerts and SMS |
| Feedback loop | Farmer confirm/correct on alerts, logged to FeedbackLog; automated retraining is future work, not built this cycle |
| API | Serves inference to the dashboard |
| Dashboard (PWA) | Farmer and Admin-facing interface, works offline, includes per-farm trend/history view |

Full design rationale lives in `docs/architecture_decision_log.md`.

## Repo structure

```
maize-stress-detection/
├── data/               # raw/processed/negative samples (gitignored)
├── models/             # per-model training code + checkpoints (checkpoints gitignored)
├── api/                # inference-serving layer
├── dashboard/          # PWA frontend
├── db/                 # schema, migrations
├── notebooks/          # exploratory/training notebooks
├── tests/              # unit + integration tests
└── docs/               # data dictionary, model cards, decision log, evaluation, limitations
```

## Setup

### Model / API (Track A)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
> Fill in exact steps once `requirements.txt` exists.

### Dashboard (Track B)
```bash
cd dashboard
npm install
npm run dev
```
> Fill in exact steps once the PWA scaffold is committed.

## Development workflow

- `main` — always working. Never commit directly.
- `develop` — integration branch, merge target for weekly checkpoints.
- Feature branches: `track-a/<short-description>` or `track-b/<short-description>`.
- See `docs/api_spec.md` for the contract between the model API and the dashboard.
- See open Issues / Project board for current status per week.

## Docs index

- `docs/data_dictionary.md` — every data field, source, units, valid range
- `docs/architecture_decision_log.md` — why key design choices were made (fusion logic, class structure, etc.)
- `docs/model_cards/` — per-model training data, metrics, known weaknesses
- `docs/api_spec.md` — endpoint contract
- `docs/evaluation_report.md` — consolidated metrics, confusion matrices
- `docs/limitations.md` — known, documented weaknesses
- `docs/test_plan.md` — what's tested and how

## Status

Currently in active development — see the Project board for real-time progress against the weekly roadmap.
