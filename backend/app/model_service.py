"""Model loading, prediction, and simple investment scoring."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from .enrichment_service import estimate_neighbourhood_metrics, normalise_postcode
from .schemas import PredictionRequest


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "rental_yield_model.pkl"
_MODEL = None

FEATURE_COLUMNS = [
    "region",
    "property_type",
    "bedrooms",
    "purchase_price",
    "monthly_rent",
    "crime_rate",
    "amenity_score",
    "hpi_growth",
    "distance_to_station",
]


def _clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def load_model():
    """Load the trained model once and reuse it."""
    global _MODEL
    if _MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        _MODEL = joblib.load(MODEL_PATH)
    return _MODEL


def predict_yield(payload: PredictionRequest) -> tuple[float, dict]:
    """Return predicted rental yield as a percentage."""
    enriched = estimate_neighbourhood_metrics(payload.postcode)
    model = load_model()
    row = pd.DataFrame(
        [
            {
                "region": enriched["region"],
                "property_type": payload.property_type,
                "bedrooms": payload.bedrooms,
                "purchase_price": payload.purchase_price,
                "monthly_rent": payload.monthly_rent,
                "crime_rate": enriched["crime_rate"],
                "amenity_score": enriched["amenity_score"],
                "hpi_growth": enriched["hpi_growth"],
                "distance_to_station": enriched["distance_to_station"],
            }
        ]
    )[FEATURE_COLUMNS]

    predicted_decimal = float(model.predict(row)[0])
    return round(predicted_decimal * 100.0, 2), enriched


def calculate_investment_score(
    predicted_yield: float, amenity_score: float, crime_rate: float, hpi_growth: float
) -> float:
    """Calculate a simple 0-100 investment score."""
    yield_component = _clip((predicted_yield / 8.0) * 60.0, 0.0, 60.0)
    amenity_component = _clip((amenity_score / 100.0) * 20.0, 0.0, 20.0)
    crime_component = _clip(((100.0 - crime_rate) / 100.0) * 15.0, 0.0, 15.0)
    hpi_component = _clip(((hpi_growth + 2.0) / 10.0) * 5.0, 0.0, 5.0)
    return round(yield_component + amenity_component + crime_component + hpi_component, 2)


def generate_recommendation(predicted_yield: float) -> str:
    """Return recommendation label from predicted yield percentage."""
    if predicted_yield >= 6.0:
        return "Strong Buy"
    if predicted_yield >= 4.5:
        return "Moderate"
    return "Weak"


def analyze_property(payload: PredictionRequest) -> dict:
    """Run prediction and derive recommendation fields."""
    predicted_yield, enriched = predict_yield(payload)
    investment_score = calculate_investment_score(
        predicted_yield=predicted_yield,
        amenity_score=float(enriched["amenity_score"]),
        crime_rate=float(enriched["crime_rate"]),
        hpi_growth=float(enriched["hpi_growth"]),
    )
    recommendation = generate_recommendation(predicted_yield)
    return {
        "postcode": normalise_postcode(payload.postcode),
        "region": enriched["region"],
        "predicted_yield": predicted_yield,
        "investment_score": investment_score,
        "recommendation": recommendation,
        "crime_rate": enriched["crime_rate"],
        "amenity_score": enriched["amenity_score"],
        "hpi_growth": enriched["hpi_growth"],
        "distance_to_station": enriched["distance_to_station"],
        "data_sources_used": enriched["data_sources_used"],
    }

