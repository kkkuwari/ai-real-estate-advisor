# AI Real Estate Investment Advisor

Final-year CS project prototype using Next.js, FastAPI, SQLite, and scikit-learn.

## What it does

- Predicts rental yield from:
  - postcode
  - property type
  - bedrooms
  - purchase price
  - monthly rent
- Enriches neighbourhood data using Postcodes.io and Police.uk (with fallback defaults)
- Saves analyses to SQLite
- Compares 2 or 3 properties and ranks by investment score

## Run backend

From project root:

```bash
python3 -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

## Run frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`

## Run ML pipeline

From project root:

```bash
python3 backend/ml/generate_dataset.py
python3 backend/ml/train_model.py
python3 backend/ml/evaluate_model.py
```

## Evaluation outputs

- `evaluation/model_metrics.json`
- `evaluation/predicted_vs_actual.png`
- `evaluation/feature_importance.png`
- `backend/models/training_metrics.json`

## Known limitations

- Training data is synthetic.
- Real-data enrichment is partial.
- External API reliability can vary, so fallbacks are used.
- Investment score is a simple heuristic.
