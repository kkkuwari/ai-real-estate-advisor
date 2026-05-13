"""Postcode-based neighbourhood enrichment with safe fallbacks."""

from __future__ import annotations

import json
import math
import re
import time
from urllib.parse import quote

import requests
import urllib3
from requests.exceptions import RequestException, SSLError
from urllib3.exceptions import InsecureRequestWarning


POSTCODES_IO_URL = "https://api.postcodes.io/postcodes/{postcode}"
POLICE_UK_URL = "https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}"
HTTP_TIMEOUT_SECONDS = 4
CACHE_TTL_SECONDS = 600

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

HIGH_SEVERITY_CATEGORIES = {
    "violent-crime",
    "robbery",
    "possession-of-weapons",
    "sexual-offences",
}

MEDIUM_SEVERITY_CATEGORIES = {
    "burglary",
    "vehicle-crime",
    "criminal-damage-arson",
    "drugs",
    "public-order",
}

LOW_SEVERITY_CATEGORIES = {
    "anti-social-behaviour",
    "shoplifting",
    "theft-from-the-person",
    "bicycle-theft",
    "other-theft",
}

POSTCODE_CACHE: dict[str, tuple[float, dict]] = {}
CRIME_CACHE: dict[str, tuple[float, dict]] = {}


def _clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _cache_get(cache: dict, key: str):
    entry = cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        cache.pop(key, None)
        return None
    return value


def _cache_set(cache: dict, key: str, value: dict) -> None:
    cache[key] = (time.time() + CACHE_TTL_SECONDS, value)


def _crime_cache_key(latitude: float, longitude: float) -> str:
    return f"{round(latitude, 3):.3f},{round(longitude, 3):.3f}"


def _clear_enrichment_caches_for_tests() -> None:
    POSTCODE_CACHE.clear()
    CRIME_CACHE.clear()


def normalise_postcode(postcode: str) -> str:
    """Normalise basic UK postcode formatting."""
    cleaned = re.sub(r"\s+", "", (postcode or "").upper())
    if len(cleaned) <= 3:
        return cleaned
    return f"{cleaned[:-3]} {cleaned[-3:]}"


def _http_get_json(url: str) -> tuple[int, dict | list]:
    headers = {"User-Agent": "ai-real-estate-advisor/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        return response.status_code, response.json()
    except SSLError as exc:
        ssl_message = str(exc)
        is_cert_verify_error = (
            "CERTIFICATE_VERIFY_FAILED" in ssl_message
            or "certificate verify failed" in ssl_message.lower()
        )
        if not is_cert_verify_error:
            raise

        # Local development fallback only:
        # if a local Python environment lacks CA certs, retry this request with verify=False.
        # This is intentionally scoped to SSL-cert failures on a single request.
        print("[enrichment] SSL certificate verification failed. Retrying request with verify=False (dev fallback).")
        urllib3.disable_warnings(InsecureRequestWarning)
        response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS, verify=False)
        return response.status_code, response.json()


def lookup_postcode(postcode: str) -> dict | None:
    """Return postcode metadata from Postcodes.io, or None on failure."""
    normalised = normalise_postcode(postcode)
    cleaned = re.sub(r"\s+", "", normalised)
    cached = _cache_get(POSTCODE_CACHE, normalised)
    if cached is not None:
        print(f"[enrichment] Postcodes.io cache hit: {normalised}")
        return cached

    url = POSTCODES_IO_URL.format(postcode=quote(cleaned))
    print(f"[enrichment] Looking up postcode: '{postcode}' -> '{normalised}'")
    print(f"[enrichment] Postcodes.io URL: {url}")

    try:
        http_status, payload = _http_get_json(url)
        api_status = payload.get("status") if isinstance(payload, dict) else None
        print(f"[enrichment] Postcodes.io HTTP status: {http_status}, API status: {api_status}")

        if not isinstance(payload, dict) or payload.get("status") != 200:
            print("[enrichment] Postcodes.io lookup failed: non-success response payload.")
            return None

        result = payload.get("result") or {}
        lat = result.get("latitude")
        lng = result.get("longitude")
        has_lat_lng = lat is not None and lng is not None
        print(f"[enrichment] Postcodes.io returned lat/lng: {has_lat_lng} (lat={lat}, lng={lng})")
        _cache_set(POSTCODE_CACHE, normalised, result)
        return result
    except RequestException as exc:
        print(f"[enrichment] Postcodes.io request error: {exc}")
        return None
    except json.JSONDecodeError as exc:
        print(f"[enrichment] Postcodes.io JSON decode error: {exc}")
        return None
    except Exception as exc:
        print(f"[enrichment] Postcodes.io unexpected error: {exc}")
        return None


def fetch_crime_data(latitude: float, longitude: float) -> dict | None:
    """Fetch crimes and convert category mix to a bounded score."""
    cache_key = _crime_cache_key(latitude, longitude)
    cached = _cache_get(CRIME_CACHE, cache_key)
    if cached is not None:
        print(f"[enrichment] Police.uk cache hit: {cache_key}")
        return cached

    url = POLICE_UK_URL.format(lat=latitude, lng=longitude)
    print(f"[enrichment] Police.uk URL: {url}")

    try:
        http_status, payload = _http_get_json(url)
        print(f"[enrichment] Police.uk HTTP status: {http_status}")
        if not isinstance(payload, list):
            print("[enrichment] Police.uk lookup failed: payload is not a list.")
            return None

        high_count = 0
        medium_count = 0
        low_count = 0
        for crime in payload:
            category = crime.get("category")
            if category in HIGH_SEVERITY_CATEGORIES:
                high_count += 1
            elif category in MEDIUM_SEVERITY_CATEGORIES:
                medium_count += 1
            elif category in LOW_SEVERITY_CATEGORIES:
                low_count += 1

        crime_count = high_count + medium_count + low_count
        if crime_count == 0:
            print("[enrichment] Police.uk returned no recognised categories.")
            return None

        print(
            "[enrichment] Police.uk counts "
            f"(high={high_count}, medium={medium_count}, low={low_count}, total={crime_count})"
        )

        weighted_severity = (
            3.0 * high_count + 2.0 * medium_count + 1.0 * low_count
        ) / crime_count
        normalized_severity = (weighted_severity - 1.0) / 2.0
        volume_factor = _clip(math.log1p(crime_count) / math.log1p(120), 0.0, 1.0)
        risk = 0.65 * normalized_severity + 0.35 * volume_factor
        crime_rate = _clip(25.0 + risk * 50.0, 20.0, 80.0)

        print(f"[enrichment] Police.uk weighted crime_rate: {crime_rate:.2f}")
        result = {"crime_rate": round(crime_rate, 2), "crime_count": crime_count}
        _cache_set(CRIME_CACHE, cache_key, result)
        return result
    except RequestException as exc:
        print(f"[enrichment] Police.uk request error: {exc}")
        return None
    except json.JSONDecodeError as exc:
        print(f"[enrichment] Police.uk JSON decode error: {exc}")
        return None
    except Exception as exc:
        print(f"[enrichment] Police.uk unexpected error: {exc}")
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
    fallback_reasons: list[str] = []

    postcode_info = lookup_postcode(postcode)
    if postcode_info:
        sources_used.append("postcodes.io")
    else:
        fallback_reasons.append("Postcodes.io unavailable: using postcode-area mapping and local defaults.")

    region = _map_to_model_region(postcode_info, postcode)
    defaults = REGIONAL_DEFAULTS[region]

    crime_rate = defaults["crime_rate"]
    latitude = (postcode_info or {}).get("latitude")
    longitude = (postcode_info or {}).get("longitude")
    if latitude is not None and longitude is not None:
        police_crime = fetch_crime_data(latitude, longitude)
        if police_crime is not None:
            crime_rate = police_crime["crime_rate"]
            sources_used.append("data.police.uk")
        else:
            fallback_reasons.append("Police.uk unavailable: crime_rate fell back to local regional default.")
    else:
        fallback_reasons.append("Postcodes.io did not return latitude/longitude: crime_rate used local default.")

    # Keep these as stable regional estimates for now.
    amenity_score = defaults["amenity_score"]
    hpi_growth = defaults["hpi_growth"]
    distance_to_station = defaults["distance_to_station"]
    fallback_reasons.append(
        "amenity_score/hpi_growth/distance_to_station currently use regional fallback estimates."
    )

    # Light consistency adjustment if crime is significantly high/low.
    amenity_score = _clip(amenity_score - (crime_rate - defaults["crime_rate"]) * 0.12, 20.0, 95.0)

    used_fallback = (
        "data.police.uk" not in sources_used
        or amenity_score == defaults["amenity_score"]
        or hpi_growth == defaults["hpi_growth"]
        or distance_to_station == defaults["distance_to_station"]
        or "postcodes.io" not in sources_used
    )
    if used_fallback:
        sources_used.append("local_defaults")
        print("[enrichment] Fallback used:")
        for reason in fallback_reasons:
            print(f"[enrichment] - {reason}")

    # De-duplicate while preserving order.
    sources_used = list(dict.fromkeys(sources_used))

    return {
        "region": region,
        "crime_rate": round(crime_rate, 2),
        "amenity_score": round(amenity_score, 2),
        "hpi_growth": round(hpi_growth, 2),
        "distance_to_station": round(distance_to_station, 2),
        "data_sources_used": sources_used,
    }

