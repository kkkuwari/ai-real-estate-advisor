"""FastAPI backend for the AI Real Estate Investment Advisor."""

from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import PropertyAnalysis, get_db, init_db
from .model_service import analyze_property
from .schemas import PredictionRequest, PredictionResponse, SavedAnalysisResponse


app = FastAPI(title="AI Real Estate Investment Advisor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI Real Estate Investment Advisor backend is running."}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    try:
        result = analyze_property(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return PredictionResponse(**result)


@app.post("/save-analysis", response_model=SavedAnalysisResponse)
def save_analysis(payload: PredictionRequest, db: Session = Depends(get_db)) -> SavedAnalysisResponse:
    try:
        result = analyze_property(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    record = PropertyAnalysis(
        region=payload.region,
        property_type=payload.property_type,
        bedrooms=payload.bedrooms,
        purchase_price=payload.purchase_price,
        monthly_rent=payload.monthly_rent,
        crime_rate=payload.crime_rate,
        amenity_score=payload.amenity_score,
        hpi_growth=payload.hpi_growth,
        distance_to_station=payload.distance_to_station,
        predicted_yield=result["predicted_yield"],
        investment_score=result["investment_score"],
        recommendation=result["recommendation"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/analyses", response_model=List[SavedAnalysisResponse])
def get_analyses(limit: int = 100, db: Session = Depends(get_db)) -> List[SavedAnalysisResponse]:
    return (
        db.query(PropertyAnalysis)
        .order_by(PropertyAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )

