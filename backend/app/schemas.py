"""Pydantic schemas for prediction and persistence endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    region: str = Field(..., example="Manchester")
    property_type: str = Field(..., example="Flat")
    bedrooms: int = Field(..., ge=1, le=10, example=2)
    purchase_price: float = Field(..., gt=0, example=260000)
    monthly_rent: float = Field(..., gt=0, example=1250)
    crime_rate: float = Field(..., ge=0, le=100, example=55)
    amenity_score: float = Field(..., ge=0, le=100, example=70)
    hpi_growth: float = Field(..., ge=-10, le=20, example=4.1)
    distance_to_station: float = Field(..., ge=0, le=50, example=2.3)


class PredictionResponse(BaseModel):
    predicted_yield: float
    investment_score: float
    recommendation: str


class SavedAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    region: str
    property_type: str
    bedrooms: int
    purchase_price: float
    monthly_rent: float
    crime_rate: float
    amenity_score: float
    hpi_growth: float
    distance_to_station: float
    predicted_yield: float
    investment_score: float
    recommendation: str
    created_at: datetime

