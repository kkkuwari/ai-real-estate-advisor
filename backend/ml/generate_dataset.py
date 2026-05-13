"""Create a UK-style synthetic property dataset."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


RNG_SEED = 42
N_ROWS = 3000


def _clip(value: float, lower: float, upper: float) -> float:
    """Keep a value inside a fixed range."""
    return float(max(lower, min(upper, value)))


def generate_uk_property_dataset(n_rows: int = N_ROWS, seed: int = RNG_SEED) -> pd.DataFrame:
    """Generate property records with realistic UK-inspired patterns."""
    rng = np.random.default_rng(seed)

    # Region-level assumptions: typical prices, yields, and local context.
    region_priors = {
        "London": {"price": 640_000, "yield": 0.041, "crime": 58, "amenity": 79, "hpi": 3.9, "station_km": 1.8},
        "Manchester": {"price": 285_000, "yield": 0.054, "crime": 55, "amenity": 69, "hpi": 4.2, "station_km": 2.8},
        "Birmingham": {"price": 260_000, "yield": 0.053, "crime": 56, "amenity": 66, "hpi": 3.8, "station_km": 3.0},
        "Leeds": {"price": 245_000, "yield": 0.056, "crime": 52, "amenity": 64, "hpi": 4.0, "station_km": 3.2},
        "Bristol": {"price": 375_000, "yield": 0.045, "crime": 47, "amenity": 74, "hpi": 3.5, "station_km": 2.4},
        "Liverpool": {"price": 225_000, "yield": 0.058, "crime": 57, "amenity": 62, "hpi": 3.9, "station_km": 3.3},
        "Newcastle": {"price": 210_000, "yield": 0.057, "crime": 51, "amenity": 60, "hpi": 3.6, "station_km": 3.5},
        "Nottingham": {"price": 235_000, "yield": 0.055, "crime": 53, "amenity": 63, "hpi": 3.7, "station_km": 3.1},
        "Sheffield": {"price": 220_000, "yield": 0.056, "crime": 50, "amenity": 61, "hpi": 3.8, "station_km": 3.4},
        "Edinburgh": {"price": 355_000, "yield": 0.046, "crime": 43, "amenity": 76, "hpi": 3.3, "station_km": 2.2},
    }
    region_names = list(region_priors.keys())
    region_weights = np.array([0.20, 0.12, 0.11, 0.09, 0.09, 0.09, 0.07, 0.08, 0.06, 0.09], dtype=float)
    region_weights /= region_weights.sum()

    property_types = ["Flat", "Terraced", "Semi-Detached", "Detached"]
    property_type_weights = np.array([0.38, 0.28, 0.22, 0.12], dtype=float)
    type_price_multiplier = {"Flat": 0.92, "Terraced": 0.96, "Semi-Detached": 1.07, "Detached": 1.24}
    type_rent_multiplier = {"Flat": 0.98, "Terraced": 1.00, "Semi-Detached": 1.03, "Detached": 1.08}
    type_station_distance_shift = {"Flat": -0.6, "Terraced": -0.2, "Semi-Detached": 0.4, "Detached": 0.9}

    rows: list[dict[str, float | int | str]] = []
    for _ in range(n_rows):
        region = rng.choice(region_names, p=region_weights)
        p_type = rng.choice(property_types, p=property_type_weights)
        prior = region_priors[region]

        # Bedroom mix depends on property type.
        if p_type == "Flat":
            bedrooms = int(rng.choice([1, 2, 3], p=[0.30, 0.54, 0.16]))
        elif p_type == "Terraced":
            bedrooms = int(rng.choice([2, 3, 4], p=[0.30, 0.50, 0.20]))
        elif p_type == "Semi-Detached":
            bedrooms = int(rng.choice([2, 3, 4, 5], p=[0.16, 0.45, 0.29, 0.10]))
        else:
            bedrooms = int(rng.choice([3, 4, 5, 6], p=[0.20, 0.44, 0.26, 0.10]))

        bedroom_price_factor = 1.0 + (bedrooms - 2) * 0.13
        purchase_price_mu = prior["price"] * type_price_multiplier[p_type] * bedroom_price_factor
        purchase_price = _clip(rng.normal(purchase_price_mu, purchase_price_mu * 0.13), 95_000, 1_350_000)

        # Local context features.
        crime_rate = _clip(rng.normal(prior["crime"], 8.0), 18, 90)
        amenity_score = _clip(rng.normal(prior["amenity"], 9.5), 25, 98)
        hpi_growth = _clip(rng.normal(prior["hpi"], 1.2), -1.5, 9.5)
        distance_to_station = _clip(
            rng.normal(prior["station_km"] + type_station_distance_shift[p_type], 1.25),
            0.2,
            15.0,
        )

        # Build expected gross yield with light context effects.
        expected_yield = (
            prior["yield"]
            + 0.0032 * (type_rent_multiplier[p_type] - 1.0)
            + 0.0008 * (bedrooms - 2)
            + 0.00009 * (amenity_score - 65)
            - 0.00010 * (crime_rate - 52)
            + 0.00035 * (hpi_growth - 3.5)
            - 0.00018 * (distance_to_station - 3.0)
            + rng.normal(0, 0.0023)
        )
        expected_yield = _clip(expected_yield, 0.028, 0.095)

        monthly_rent = (purchase_price * expected_yield / 12.0) * rng.normal(1.0, 0.06)
        monthly_rent = _clip(monthly_rent, 450, 7_800)

        # Final target is rent/price with small amenity/crime adjustments.
        base_yield_from_price_rent = (monthly_rent * 12.0) / purchase_price
        rental_yield = (
            base_yield_from_price_rent
            + 0.00007 * (amenity_score - 65)
            - 0.00008 * (crime_rate - 52)
            + rng.normal(0, 0.0017)
        )
        rental_yield = _clip(rental_yield, 0.025, 0.10)

        rows.append(
            {
                "region": region,
                "property_type": p_type,
                "bedrooms": bedrooms,
                "purchase_price": round(purchase_price, 2),
                "monthly_rent": round(monthly_rent, 2),
                "crime_rate": round(crime_rate, 2),
                "amenity_score": round(amenity_score, 2),
                "hpi_growth": round(hpi_growth, 2),
                "distance_to_station": round(distance_to_station, 2),
                "rental_yield": round(rental_yield, 5),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    """Generate the dataset and write it to CSV."""
    output_path = Path(__file__).resolve().parents[1] / "data" / "uk_property_data.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dataset = generate_uk_property_dataset()
    dataset.to_csv(output_path, index=False)

    print(f"Dataset generated with {len(dataset)} rows.")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()

