from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import enrichment_service


@pytest.fixture(autouse=True)
def clear_enrichment_caches():
    enrichment_service._clear_enrichment_caches_for_tests()


def test_weighted_category_scoring_prefers_higher_severity(monkeypatch):
    low_mix_payload = [{"category": "anti-social-behaviour"} for _ in range(40)]
    high_mix_payload = [{"category": "violent-crime"} for _ in range(40)]

    monkeypatch.setattr(
        enrichment_service,
        "_http_get_json",
        lambda url: (200, low_mix_payload),
    )
    low_result = enrichment_service.fetch_crime_data(53.4, -2.2)

    monkeypatch.setattr(
        enrichment_service,
        "_http_get_json",
        lambda url: (200, high_mix_payload),
    )
    high_result = enrichment_service.fetch_crime_data(53.5, -2.3)

    assert low_result is not None
    assert high_result is not None
    assert high_result["crime_rate"] > low_result["crime_rate"]
    assert 20.0 <= low_result["crime_rate"] <= 80.0
    assert 20.0 <= high_result["crime_rate"] <= 80.0


def test_lookup_postcode_uses_cache(monkeypatch):
    calls = {"count": 0}

    def fake_http(url):
        calls["count"] += 1
        return (
            200,
            {
                "status": 200,
                "result": {
                    "region": "North West",
                    "admin_district": "Manchester",
                    "latitude": 53.48,
                    "longitude": -2.24,
                },
            },
        )

    monkeypatch.setattr(enrichment_service, "_http_get_json", fake_http)

    first = enrichment_service.lookup_postcode("M1 4BT")
    second = enrichment_service.lookup_postcode("M1 4BT")

    assert first is not None
    assert second is not None
    assert calls["count"] == 1


def test_fetch_crime_data_uses_cache(monkeypatch):
    calls = {"count": 0}

    def fake_http(url):
        calls["count"] += 1
        return (
            200,
            [{"category": "violent-crime"} for _ in range(12)]
            + [{"category": "anti-social-behaviour"} for _ in range(8)],
        )

    monkeypatch.setattr(enrichment_service, "_http_get_json", fake_http)

    first = enrichment_service.fetch_crime_data(53.4801, -2.2383)
    second = enrichment_service.fetch_crime_data(53.4801, -2.2383)

    assert first is not None
    assert second is not None
    assert calls["count"] == 1
