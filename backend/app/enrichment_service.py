"""Postcode-based neighbourhood enrichment with safe fallbacks."""

from __future__ import annotations

import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen


POSTCODES_IO_URL = "https://api.postcodes.io/postcodes/{postcode}"
POLICE_UK_URL = "https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}"
HTTP_TIMEOUT_SECONDS = 4

# These regions match model training categories.
MODEL_REGIONS = {
    "London",
    "Manchester",
    "Birmingham",
    "Leeds",
    "Bristol",
    "Liverpool",
    "Newcastle",
    "Nottingham",
    "Sheffield",
    "Edinburgh",
}

REGIONAL_DEFAULTS = {
    "London": {"crime_rate": 58.0, "amenity_score": 79.0, "hpi_growth": 3.9, "distance_to_station": 1.8},
    "Manchester": {"crime_rate": 55.0, "amenity_score": 69.0, "hpi_growth": 4.2, "distance_to_station": 2.8},
    "Birmingham": {"crime_rate": 56.0, "amenity_score": 66.0, "hpi_growth": 3.8, "distance_to_station": 3.0},
    "Leeds": {"crime_rate": 52.0, "amenity_score": 64.0, "hpi_growth": 4.0, "distance_to_station": 3.2},
    "Bristol": {"crime_rate": 47.0, "amenity_score": 74.0, "hpi_growth": 3.5, "distance_to_station": 2.4},
    "Liverpool": {"crime_rate": 57.0, "amenity_score": 62.0, "hpi_growth": 3.9, "distance_to_station": 3.3},
    "Newcastle": {"crime_rate": 51.0, "amenity_score": 60.0, "hpi_growth": 3.6, "distance_to_station": 3.5},
    "Nottingham": {"crime_rate": 53.0, "amenity_score": 63.0, "hpi_growth": 3.7, "distance_to_station": 3.1},
    "Sheffield": {"crime_rate": 50.0, "amenity_score": 61.0, "hpi_growth": 3.8, "distance_to_station": 3.4},
    "Edinburgh": {"crime_rate": 43.0, "amenity_score": 76.0, "hpi_growth": 3.3, "distance_to_station": 2.2},
}


def _clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def normalise_postcode(postcode: str) -> str:
    """Normalise basic UK postcode formatting."""
    cleaned = re.sub(r"\s+", "", (postcode or "").upper())
    if len(cleaned) <= 3:
        return cleaned
    return f"{cleaned[:-3]} {cleaned[-3:]}"


def _http_get_json(url: str):
    request = Request(url, headers={"User-Agent": "ai-real-estate-advisor/1.0"})
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def lookup_postcode(postcode: str) -> dict | None:
    """Return postcode metadata from Postcodes.io, or None on failure."""
    try:
        normalised = normalise_postcode(postcode)
        url = POSTCODES_IO_URL.format(postcode=quote(normalised))
        payload = _http_get_json(url)
        if payload.get("status") != 200:
            return None
        return payload.get("result")
    except Exception:
        return None


def fetch_crime_data(latitude: float, longitude: float) -> float | None:
    """Fetch crime records and convert density to a 0-100 score."""
    try:
        url = POLICE_UK_URL.format(lat=latitude, lng=longitude)
        payload = _http_get_json(url)
        if not isinstance(payload, list):
            return None

        crime_count = len(payload)
        # Simple bounded transformation for prototype scoring.
        crime_rate = _clip(crime_count * 1.8, 5.0, 100.0)
        return round(crime_rate, 2)
    except Exception:
        return None


def _map_to_model_region(postcode_lookup: dict | None, postcode: str) -> str:
    """Map API/admin data into one of the trained model region categories."""
    region_raw = (postcode_lookup or {}).get("region")
    admin_district = (postcode_lookup or {}).get("admin_district", "")
    area = re.match(r"^[A-Z]+", normalise_postcode(postcode))
    postcode_area = area.group(0) if area else ""

    if region_raw in MODEL_REGIONS:
        return region_raw

    district_to_region = {
        "Manchester": "Manchester",
        "Birmingham": "Birmingham",
        "Leeds": "Leeds",
        "Bristol": "Bristol",
        "Liverpool": "Liverpool",
        "Newcastle upon Tyne": "Newcastle",
        "Nottingham": "Nottingham",
        "Sheffield": "Sheffield",
        "Edinburgh": "Edinburgh",
    }
    if admin_district in district_to_region:
        return district_to_region[admin_district]

    london_areas = {"E", "EC", "N", "NW", "SE", "SW", "W", "WC"}
    if postcode_area in london_areas:
        return "London"
    if postcode_area == "M":
        return "Manchester"
    if postcode_area in {"B"}:
        return "Birmingham"
    if postcode_area in {"LS"}:
        return "Leeds"
    if postcode_area in {"BS"}:
        return "Bristol"
    if postcode_area in {"L"}:
        return "Liverpool"
    if postcode_area in {"NE"}:
        return "Newcastle"
    if postcode_area in {"NG"}:
        return "Nottingham"
    if postcode_area in {"S"}:
        return "Sheffield"
    if postcode_area in {"EH"}:
        return "Edinburgh"

    return "Manchester"


def estimate_neighbourhood_metrics(postcode: str) -> dict:
    """Estimate model-required neighbourhood features from postcode."""
    sources_used: list[str] = []

    postcode_info = lookup_postcode(postcode)
    if postcode_info:
        sources_used.append("postcodes.io")

    region = _map_to_model_region(postcode_info, postcode)
    defaults = REGIONAL_DEFAULTS[region]

    crime_rate = defaults["crime_rate"]
    latitude = (postcode_info or {}).get("latitude")
    longitude = (postcode_info or {}).get("longitude")
    if latitude is not None and longitude is not None:
        police_crime = fetch_crime_data(latitude, longitude)
        if police_crime is not None:
            crime_rate = police_crime
            sources_used.append("data.police.uk")

    # Keep these as stable regional estimates for now.
    amenity_score = defaults["amenity_score"]
    hpi_growth = defaults["hpi_growth"]
    distance_to_station = defaults["distance_to_station"]

    # Light consistency adjustment if crime is significantly high/low.
    amenity_score = _clip(amenity_score - (crime_rate - defaults["crime_rate"]) * 0.12, 20.0, 95.0)

    if not sources_used:
        sources_used.append("local_defaults")

    return {
        "region": region,
        "crime_rate": round(crime_rate, 2),
        "amenity_score": round(amenity_score, 2),
        "hpi_growth": round(hpi_growth, 2),
        "distance_to_station": round(distance_to_station, 2),
        "data_sources_used": sources_used,
    }

