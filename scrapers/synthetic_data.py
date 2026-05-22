"""
Synthetic Data Generator for PropLens India.

Generates realistic residential property listings across Mumbai, Bengaluru,
and Pune with accurate micro-market pricing, weighted BHK distributions,
multi-platform sourcing, and derived financial metrics.

This is the primary fallback data source for development and demo purposes.
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------

# Price ranges per micro-market (₹/sqft): (min, max)
MICRO_MARKET_PRICES: Dict[str, Dict[str, Tuple[int, int]]] = {
    "Mumbai": {
        "Bandra": (43_000, 81_000),
        "Thane": (15_000, 20_000),
        "Chembur": (31_000, 33_500),
        "Andheri": (26_000, 37_000),
        "Powai": (26_500, 40_000),
    },
    "Bengaluru": {
        "Whitefield": (11_000, 15_000),
        "Koramangala": (12_000, 25_000),
        "Sarjapur": (7_000, 18_000),
        "Hebbal": (9_000, 16_000),
        "Electronic City": (6_000, 12_500),
    },
    "Pune": {
        "Baner": (10_000, 15_500),
        "Hinjewadi": (6_500, 12_600),
        "Kharadi": (9_000, 13_600),
        "Viman Nagar": (12_000, 15_300),
        "Wakad": (8_000, 11_000),
    },
}

# BHK types with weighted distribution (heavier on 2BHK & 3BHK)
BHK_CONFIG: Dict[str, Dict[str, Tuple[int, int]]] = {
    "1 BHK": {"area_range": (400, 650), "weight": 15},
    "2 BHK": {"area_range": (650, 1200), "weight": 35},
    "3 BHK": {"area_range": (1000, 2000), "weight": 35},
    "4 BHK": {"area_range": (1800, 3500), "weight": 15},
}

# Rental yield ranges by city (annual %)
RENTAL_YIELD_RANGES: Dict[str, Tuple[float, float]] = {
    "Mumbai": (2.0, 3.5),
    "Bengaluru": (3.0, 5.0),
    "Pune": (2.5, 4.5),
}

# Source platforms
PLATFORMS: List[str] = ["MagicBricks", "99acres", "Housing.com", "NoBroker"]

# URL patterns per platform
URL_PATTERNS: Dict[str, str] = {
    "MagicBricks": "https://www.magicbricks.com/property/{listing_id}",
    "99acres": "https://www.99acres.com/property/{listing_id}",
    "Housing.com": "https://housing.com/buy/{listing_id}",
    "NoBroker": "https://www.nobroker.in/property/{listing_id}",
}

# Real developer / project names by city for realistic property names
PROJECT_PREFIXES: Dict[str, List[str]] = {
    "Mumbai": [
        "Lodha", "Oberoi", "Hiranandani", "Godrej", "Rustomjee",
        "Kalpataru", "Runwal", "Mahindra", "Dosti", "Shapoorji",
        "Tata", "L&T", "Piramal", "Wadhwa", "Kanakia",
    ],
    "Bengaluru": [
        "Prestige", "Brigade", "Sobha", "Puravankara", "Salarpuria",
        "Godrej", "Shriram", "Total Environment", "Mantri", "Embassy",
        "Assetz", "Tata", "Mahindra", "Adarsh", "Divyasree",
    ],
    "Pune": [
        "Kumar", "Kolte Patil", "Panchshil", "Godrej", "Majestique",
        "VTP", "Rohan", "Lodha", "Shapoorji", "Nyati",
        "Pristine", "Kohinoor", "Pharande", "Paranjape", "Marvel",
    ],
}

PROJECT_SUFFIXES: List[str] = [
    "Palava", "Luxuria", "Heights", "Residency", "Greens",
    "Paradise", "Towers", "Gardens", "Enclave", "Habitat",
    "Meadows", "Springs", "Lakeside", "Skyline", "Regent",
    "Premia", "Exotica", "Serenity", "Grandeur", "Panorama",
    "Riviera", "Boulevard", "Crown", "Sapphire", "Emerald",
    "Phase 1", "Phase 2", "Phase 3", "City", "Megapolis",
    "Nest", "Bliss", "Haven", "Vista", "Pinnacle",
]

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _generate_property_name(city: str, rng: np.random.Generator) -> str:
    """Generate a realistic Indian property name for the given city.

    Args:
        city: City name to choose developer prefix from.
        rng: NumPy random generator instance.

    Returns:
        A property name like 'Lodha Palava Phase 2'.
    """
    prefix = rng.choice(PROJECT_PREFIXES[city])
    suffix = rng.choice(PROJECT_SUFFIXES)
    return f"{prefix} {suffix}"


def _generate_listing_url(platform: str, rng: np.random.Generator) -> str:
    """Generate a platform-specific listing URL with a random ID.

    Args:
        platform: Source platform name.
        rng: NumPy random generator instance.

    Returns:
        A realistic-looking listing URL string.
    """
    listing_id = rng.integers(100_000, 9_999_999)
    pattern = URL_PATTERNS.get(
        platform,
        "https://www.example.com/property/{listing_id}",
    )
    return pattern.format(listing_id=listing_id)


def _pick_bhk(rng: np.random.Generator) -> Tuple[str, int, int]:
    """Pick a BHK type using weighted distribution.

    Args:
        rng: NumPy random generator instance.

    Returns:
        Tuple of (bhk_label, area_min, area_max).
    """
    labels = list(BHK_CONFIG.keys())
    weights = np.array([BHK_CONFIG[b]["weight"] for b in labels], dtype=float)
    weights /= weights.sum()
    choice = rng.choice(labels, p=weights)
    area_min, area_max = BHK_CONFIG[choice]["area_range"]
    return choice, area_min, area_max


# ---------------------------------------------------------------------------
# Main Generator
# ---------------------------------------------------------------------------


def generate_synthetic_data(
    listings_per_city: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a DataFrame of synthetic property listings.

    Creates realistic residential listings across Mumbai, Bengaluru, and Pune
    using actual market price ranges, weighted BHK distributions, and
    multi-source platform assignments.

    Args:
        listings_per_city: Number of listings to generate per city.
        seed: Random seed for reproducibility.

    Returns:
        pd.DataFrame with columns: property_name, bhk, sale_price, rent_price,
        area_sqft, price_per_sqft, micro_market, city, source, listing_url,
        gross_rental_yield, source_count, affordability_index.
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)  # for any stdlib random usage
    records: List[Dict] = []

    for city, micro_markets in MICRO_MARKET_PRICES.items():
        market_names = list(micro_markets.keys())
        num_markets = len(market_names)
        per_market = listings_per_city // num_markets
        remainder = listings_per_city % num_markets

        for idx, (micro_market, (price_min, price_max)) in enumerate(
            micro_markets.items()
        ):
            count = per_market + (1 if idx < remainder else 0)

            for _ in range(count):
                # BHK & area
                bhk_label, area_min, area_max = _pick_bhk(rng)
                area_sqft = int(rng.integers(area_min, area_max + 1))

                # Price per sqft with triangular-ish distribution
                price_per_sqft = int(
                    rng.triangular(price_min, (price_min + price_max) / 2, price_max)
                )

                # Sale price with ±5% noise
                noise = rng.uniform(0.95, 1.05)
                sale_price = round(area_sqft * price_per_sqft * noise)

                # Rental yield & rent price
                yield_min, yield_max = RENTAL_YIELD_RANGES[city]
                annual_yield = rng.uniform(yield_min, yield_max) / 100.0
                rent_price = round(sale_price * annual_yield / 12)

                # Property name
                property_name = _generate_property_name(city, rng)

                # Source platform(s) — ~20% chance of multi-source
                if rng.random() < 0.20:
                    num_sources = int(rng.choice([2, 3], p=[0.7, 0.3]))
                    sources = list(rng.choice(PLATFORMS, size=num_sources, replace=False))
                else:
                    sources = [str(rng.choice(PLATFORMS))]

                source_count = len(sources)

                # Create one record per source (simulates cross-platform listing)
                for source in sources:
                    listing_url = _generate_listing_url(source, rng)
                    records.append(
                        {
                            "property_name": property_name,
                            "bhk": bhk_label,
                            "sale_price": sale_price,
                            "rent_price": rent_price,
                            "area_sqft": area_sqft,
                            "price_per_sqft": price_per_sqft,
                            "micro_market": micro_market,
                            "city": city,
                            "source": source,
                            "listing_url": listing_url,
                            "source_count": source_count,
                        }
                    )

    df = pd.DataFrame(records)

    # --- Derived columns ---
    # Gross rental yield (annual %)
    df["gross_rental_yield"] = round(
        (df["rent_price"] * 12) / df["sale_price"] * 100, 2
    )

    # Affordability index: price_per_sqft / city_median_price_per_sqft × 100
    city_medians = df.groupby("city")["price_per_sqft"].transform("median")
    df["affordability_index"] = round(df["price_per_sqft"] / city_medians * 100, 2)

    # Reorder columns to exact spec
    column_order = [
        "property_name",
        "bhk",
        "sale_price",
        "rent_price",
        "area_sqft",
        "price_per_sqft",
        "micro_market",
        "city",
        "source",
        "listing_url",
        "gross_rental_yield",
        "source_count",
        "affordability_index",
    ]
    df = df[column_order]

    return df


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def _save_raw_per_source(df: pd.DataFrame, raw_dir: Path) -> None:
    """Save separate CSVs per source platform to data/raw/.

    Args:
        df: Combined DataFrame.
        raw_dir: Path to the raw data directory.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    for source in df["source"].unique():
        source_df = df[df["source"] == source]
        safe_name = source.lower().replace(".", "").replace(" ", "_")
        filepath = raw_dir / f"{safe_name}_listings.csv"
        source_df.to_csv(filepath, index=False)
        print(f"  ✓ {filepath} — {len(source_df):,} listings")


def _save_combined(df: pd.DataFrame, processed_dir: Path) -> None:
    """Save combined CSV to data/processed/.

    Args:
        df: Combined DataFrame.
        processed_dir: Path to the processed data directory.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    filepath = processed_dir / "combined_listings.csv"
    df.to_csv(filepath, index=False)
    print(f"  ✓ {filepath} — {len(df):,} listings")


def main() -> None:
    """Generate synthetic data and save to disk."""
    print("=" * 60)
    print("PropLens India — Synthetic Data Generator")
    print("=" * 60)

    # Resolve project root (parent of scrapers/)
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    print("\n→ Generating synthetic listings …")
    df = generate_synthetic_data(listings_per_city=1000)

    print(f"\n  Total records generated: {len(df):,}")
    print(f"  Cities: {df['city'].nunique()}")
    print(f"  Micro-markets: {df['micro_market'].nunique()}")
    print(f"  BHK types: {sorted(df['bhk'].unique())}")
    print(f"  Sources: {sorted(df['source'].unique())}")

    print("\n→ Saving raw CSVs per source …")
    _save_raw_per_source(df, raw_dir)

    print("\n→ Saving combined CSV …")
    _save_combined(df, processed_dir)

    # Quick summary statistics
    print("\n— Summary Statistics —")
    print(
        df.groupby("city")
        .agg(
            listings=("property_name", "count"),
            median_price_sqft=("price_per_sqft", "median"),
            median_sale_price=("sale_price", "median"),
            avg_rental_yield=("gross_rental_yield", "mean"),
        )
        .round(2)
        .to_string()
    )

    print("\n" + "=" * 60)
    print("✅ Synthetic data generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
