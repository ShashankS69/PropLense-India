"""
Cross-Source Deduplicator for PropLens India.

Identifies and merges duplicate property listings across multiple
platforms using blocking, fuzzy name matching, and composite scoring.

Blocking strategy:
    city → micro_market → bhk

Composite similarity score:
    0.35 × name_similarity + 0.25 × locality_similarity
    + 0.20 × price_proximity + 0.20 × area_proximity

Threshold: ≥ 85 → auto-merge.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from scrapers.base_scraper import PROJECT_ROOT

logger = logging.getLogger("proplens.deduplicator")
if not logger.handlers:
    handler = logging.StreamHandler()
    fmt = logging.Formatter(
        "[%(asctime)s] %(name)s — %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------


def name_similarity(a: str, b: str) -> float:
    """Compute fuzzy token-set-ratio similarity between two property names.

    Args:
        a: First property name.
        b: Second property name.

    Returns:
        Similarity score 0–100.
    """
    if not a or not b:
        return 0.0
    return fuzz.token_set_ratio(a.lower().strip(), b.lower().strip())


def locality_similarity(a: str, b: str) -> float:
    """Compute fuzzy similarity between two locality names.

    Args:
        a: First locality / micro-market name.
        b: Second locality / micro-market name.

    Returns:
        Similarity score 0–100.
    """
    if not a or not b:
        return 0.0
    return fuzz.token_set_ratio(a.lower().strip(), b.lower().strip())


def price_proximity(a: Optional[float], b: Optional[float]) -> float:
    """Compute proximity score for two prices.

    Uses: ``100 × (1 - |a - b| / max(a, b))``. Returns 100 if both are
    ``None`` or zero.

    Args:
        a: First price.
        b: Second price.

    Returns:
        Proximity score 0–100.
    """
    if a is None or b is None or (a == 0 and b == 0):
        return 100.0
    if a == 0 or b == 0:
        return 0.0
    return max(0.0, 100.0 * (1.0 - abs(a - b) / max(a, b)))


def area_proximity(a: Optional[float], b: Optional[float]) -> float:
    """Compute proximity score for two area values.

    Args:
        a: First area in sqft.
        b: Second area in sqft.

    Returns:
        Proximity score 0–100.
    """
    return price_proximity(a, b)  # Same formula


def composite_score(
    name_a: str,
    name_b: str,
    locality_a: str,
    locality_b: str,
    price_a: Optional[float],
    price_b: Optional[float],
    area_a: Optional[float],
    area_b: Optional[float],
) -> float:
    """Compute the weighted composite similarity score.

    Weights: name=0.35, locality=0.25, price=0.20, area=0.20.

    Args:
        name_a: Property name A.
        name_b: Property name B.
        locality_a: Locality A.
        locality_b: Locality B.
        price_a: Sale price A.
        price_b: Sale price B.
        area_a: Area sqft A.
        area_b: Area sqft B.

    Returns:
        Composite score 0–100.
    """
    return (
        0.35 * name_similarity(name_a, name_b)
        + 0.25 * locality_similarity(locality_a, locality_b)
        + 0.20 * price_proximity(price_a, price_b)
        + 0.20 * area_proximity(area_a, area_b)
    )


# ---------------------------------------------------------------------------
# Record merging
# ---------------------------------------------------------------------------


def _completeness(row: pd.Series) -> int:
    """Count non-null fields in a row (higher = more complete).

    Args:
        row: A DataFrame row.

    Returns:
        Count of non-null values.
    """
    return row.notna().sum()


def _merge_pair(primary: pd.Series, secondary: pd.Series) -> pd.Series:
    """Merge two duplicate records, preferring the more complete one.

    Fills NaN fields of the primary record from the secondary.
    Accumulates ``source_count``.

    Args:
        primary: The more-complete record.
        secondary: The less-complete record.

    Returns:
        Merged record as a Series.
    """
    merged = primary.copy()
    for col in merged.index:
        if pd.isna(merged[col]) and pd.notna(secondary[col]):
            merged[col] = secondary[col]

    # Accumulate source_count
    sc_p = primary.get("source_count", 1) or 1
    sc_s = secondary.get("source_count", 1) or 1
    merged["source_count"] = max(sc_p, sc_s, int(sc_p) + int(sc_s) - 1)
    return merged


# ---------------------------------------------------------------------------
# Main deduplication logic
# ---------------------------------------------------------------------------


def deduplicate(
    df: pd.DataFrame,
    threshold: float = 85.0,
) -> pd.DataFrame:
    """Deduplicate property listings across sources.

    Uses blocking on (city, micro_market, bhk) to reduce pairwise
    comparisons, then applies composite fuzzy scoring.

    Args:
        df: Combined listings DataFrame (may contain duplicates).
        threshold: Minimum composite score to auto-merge.

    Returns:
        Deduplicated DataFrame with updated ``source_count``.
    """
    if df.empty:
        logger.warning("Empty DataFrame — nothing to deduplicate.")
        return df

    logger.info("Starting deduplication on %d records (threshold=%.1f) …", len(df), threshold)

    # Ensure required columns exist
    if "source_count" not in df.columns:
        df["source_count"] = 1

    # Normalise NaN strings
    df["property_name"] = df["property_name"].fillna("")
    df["micro_market"] = df["micro_market"].fillna("")

    # Blocking keys
    block_cols = ["city", "micro_market", "bhk"]
    for col in block_cols:
        if col not in df.columns:
            df[col] = ""

    deduplicated: List[pd.Series] = []
    total_merged = 0

    grouped = df.groupby(block_cols, dropna=False)

    for block_key, block_df in grouped:
        block_df = block_df.reset_index(drop=True)
        n = len(block_df)
        removed: Set[int] = set()

        for i in range(n):
            if i in removed:
                continue
            current = block_df.iloc[i]

            for j in range(i + 1, n):
                if j in removed:
                    continue
                candidate = block_df.iloc[j]

                score = composite_score(
                    str(current.get("property_name", "")),
                    str(candidate.get("property_name", "")),
                    str(current.get("micro_market", "")),
                    str(candidate.get("micro_market", "")),
                    current.get("sale_price"),
                    candidate.get("sale_price"),
                    current.get("area_sqft"),
                    candidate.get("area_sqft"),
                )

                if score >= threshold:
                    # Merge: keep the more complete record
                    if _completeness(current) >= _completeness(candidate):
                        current = _merge_pair(current, candidate)
                    else:
                        current = _merge_pair(candidate, current)
                    removed.add(j)
                    total_merged += 1

            deduplicated.append(current)

    result = pd.DataFrame(deduplicated)
    logger.info(
        "Deduplication complete: %d → %d records (%d merges).",
        len(df),
        len(result),
        total_merged,
    )
    return result.reset_index(drop=True)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Load combined data, deduplicate, and save."""
    processed_dir = PROJECT_ROOT / "data" / "processed"
    input_path = processed_dir / "combined_listings.csv"

    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        logger.info("Run synthetic_data.py first to generate combined_listings.csv")
        return

    logger.info("Loading %s …", input_path)
    df = pd.read_csv(input_path)
    logger.info("Loaded %d records.", len(df))

    deduped = deduplicate(df)

    output_path = processed_dir / "combined_listings.csv"
    deduped.to_csv(output_path, index=False)
    logger.info("Saved deduplicated data → %s (%d records)", output_path, len(deduped))

    # Summary
    print("\n— Deduplication Summary —")
    print(f"  Input records:  {len(df):,}")
    print(f"  Output records: {len(deduped):,}")
    print(f"  Duplicates removed: {len(df) - len(deduped):,}")
    if "source_count" in deduped.columns:
        multi = (deduped["source_count"] > 1).sum()
        print(f"  Multi-source listings: {multi:,}")


if __name__ == "__main__":
    main()
