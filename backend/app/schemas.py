"""Pydantic schemas for prediction and persistence endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    postcode: str = Field(..., example="M1 4BT")
    property_type: str = Field(..., example="Flat")
    bedrooms: int = Field(..., ge=1, le=10, example=2)
    purchase_price: float = Field(..., gt=0, example=260000)
    monthly_rent: float = Field(..., gt=0, example=1250)


class PredictionResponse(BaseModel):
    postcode: str
    region: str
    predicted_yield: float
    investment_score: float
    recommendation: str
    crime_rate: float
    amenity_score: float
    hpi_growth: float
    distance_to_station: float
    data_sources_used: list[str]


class SavedAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    postcode: str
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
    data_sources_used: list[str]
    created_at: datetime

