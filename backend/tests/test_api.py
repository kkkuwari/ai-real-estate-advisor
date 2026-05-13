from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import enrichment_service
from backend.app.database import Base, PropertyAnalysis, get_db
from backend.app.main import app


@pytest.fixture()
def test_client(tmp_path):
    db_file = tmp_path / "test_real_estate_advisor.db"
    test_engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    test_engine.dispose()


@pytest.fixture()
def valid_payload():
    return {
        "postcode": "M1 4BT",
        "property_type": "Flat",
        "bedrooms": 2,
        "purchase_price": 260000,
        "monthly_rent": 1250,
    }


def _mock_enrichment_success(monkeypatch):
    monkeypatch.setattr(
        enrichment_service,
        "lookup_postcode",
        lambda postcode: {
            "region": "North West",
            "admin_district": "Manchester",
            "latitude": 53.480058,
            "longitude": -2.238381,
        },
    )
    monkeypatch.setattr(
        enrichment_service,
        "fetch_crime_data",
        lambda latitude, longitude: {"crime_rate": 19.8, "crime_count": 11},
    )


def test_predict_valid_payload_returns_expected_fields(test_client, valid_payload, monkeypatch):
    client, _ = test_client
    _mock_enrichment_success(monkeypatch)

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 200
    payload = response.json()
    assert "predicted_yield" in payload
    assert "investment_score" in payload
    assert "recommendation" in payload
    assert "data_sources_used" in payload
    assert payload["postcode"] == "M1 4BT"
    assert isinstance(payload["data_sources_used"], list)


def test_save_analysis_persists_record(test_client, valid_payload, monkeypatch):
    client, TestingSessionLocal = test_client
    _mock_enrichment_success(monkeypatch)

    response = client.post("/save-analysis", json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] >= 1
    assert body["postcode"] == "M1 4BT"

    session = TestingSessionLocal()
    try:
        assert session.query(PropertyAnalysis).count() == 1
    finally:
        session.close()


def test_get_analyses_returns_list_and_handles_empty_db(test_client):
    client, _ = test_client

    response = client.get("/analyses")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []


def test_predict_invalid_payload_returns_validation_error(test_client):
    client, _ = test_client
    invalid_payload = {
        "postcode": "",
        "property_type": "Flat",
        "bedrooms": -1,
        "purchase_price": -100,
        "monthly_rent": 0,
    }

    response = client.post("/predict", json=invalid_payload)

    assert response.status_code == 422


def test_enrichment_fallback_still_predicts(test_client, valid_payload, monkeypatch):
    client, _ = test_client
    monkeypatch.setattr(enrichment_service, "lookup_postcode", lambda postcode: None)
    monkeypatch.setattr(enrichment_service, "fetch_crime_data", lambda latitude, longitude: None)

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 200
    payload = response.json()
    assert "predicted_yield" in payload
    assert "local_defaults" in payload["data_sources_used"]
