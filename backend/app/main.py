"""FastAPI backend for the AI Real Estate Investment Advisor."""

from __future__ import annotations

import json
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
        postcode=result["postcode"],
        region=result["region"],
        property_type=payload.property_type,
        bedrooms=payload.bedrooms,
        purchase_price=payload.purchase_price,
        monthly_rent=payload.monthly_rent,
        crime_rate=result["crime_rate"],
        amenity_score=result["amenity_score"],
        hpi_growth=result["hpi_growth"],
        distance_to_station=result["distance_to_station"],
        predicted_yield=result["predicted_yield"],
        investment_score=result["investment_score"],
        recommendation=result["recommendation"],
        data_sources_used=json.dumps(result["data_sources_used"]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return SavedAnalysisResponse(
        id=record.id,
        postcode=record.postcode,
        region=record.region,
        property_type=record.property_type,
        bedrooms=record.bedrooms,
        purchase_price=record.purchase_price,
        monthly_rent=record.monthly_rent,
        crime_rate=record.crime_rate,
        amenity_score=record.amenity_score,
        hpi_growth=record.hpi_growth,
        distance_to_station=record.distance_to_station,
        predicted_yield=record.predicted_yield,
        investment_score=record.investment_score,
        recommendation=record.recommendation,
        data_sources_used=json.loads(record.data_sources_used or "[]"),
        created_at=record.created_at,
    )


@app.get("/analyses", response_model=List[SavedAnalysisResponse])
def get_analyses(limit: int = 100, db: Session = Depends(get_db)) -> List[SavedAnalysisResponse]:
    records = (
        db.query(PropertyAnalysis)
        .order_by(PropertyAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        SavedAnalysisResponse(
            id=record.id,
            postcode=record.postcode,
            region=record.region,
            property_type=record.property_type,
            bedrooms=record.bedrooms,
            purchase_price=record.purchase_price,
            monthly_rent=record.monthly_rent,
            crime_rate=record.crime_rate,
            amenity_score=record.amenity_score,
            hpi_growth=record.hpi_growth,
            distance_to_station=record.distance_to_station,
            predicted_yield=record.predicted_yield,
            investment_score=record.investment_score,
            recommendation=record.recommendation,
            data_sources_used=json.loads(record.data_sources_used or "[]"),
            created_at=record.created_at,
        )
        for record in records
    ]

