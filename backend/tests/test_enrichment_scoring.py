from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import enrichment_service


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
    high_result = enrichment_service.fetch_crime_data(53.4, -2.2)

    assert low_result is not None
    assert high_result is not None
    assert high_result["crime_rate"] > low_result["crime_rate"]
    assert 20.0 <= low_result["crime_rate"] <= 80.0
    assert 20.0 <= high_result["crime_rate"] <= 80.0
