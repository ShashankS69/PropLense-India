"""
PropLens India — Geocoding Utilities
=====================================
Hardcoded coordinates for all 15 micro-markets plus optional Geopy fallback.
"""

from typing import Dict, Tuple

# ─────────────────────────────────────────────
# HARDCODED COORDINATES (lat, lon)
# Based on verified geographic data
# ─────────────────────────────────────────────

MICRO_MARKET_COORDS: Dict[str, Tuple[float, float]] = {
    # Mumbai
    "Bandra": (19.0544, 72.8406),
    "Thane": (19.1972, 72.9722),
    "Chembur": (19.0510, 72.8940),
    "Andheri": (19.1190, 72.8470),
    "Powai": (19.1164, 72.9047),

    # Bengaluru
    "Whitefield": (12.9698, 77.7499),
    "Koramangala": (12.9259, 77.6229),
    "Sarjapur": (12.8576, 77.7834),
    "Hebbal": (13.0354, 77.5988),
    "Electronic City": (12.8399, 77.6770),

    # Pune
    "Baner": (18.5600, 73.7903),
    "Hinjewadi": (18.5936, 73.7301),
    "Kharadi": (18.5545, 73.9419),
    "Viman Nagar": (18.5666, 73.9154),
    "Wakad": (18.5993, 73.7625),
}

# City centre coordinates for map zoom
CITY_CENTERS: Dict[str, Tuple[float, float]] = {
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Pune": (18.5204, 73.8567),
}

# India centre (for country-wide view)
INDIA_CENTER = (20.5937, 78.9629)

# Micro-market to city mapping
MARKET_TO_CITY: Dict[str, str] = {
    "Bandra": "Mumbai",
    "Thane": "Mumbai",
    "Chembur": "Mumbai",
    "Andheri": "Mumbai",
    "Powai": "Mumbai",
    "Whitefield": "Bengaluru",
    "Koramangala": "Bengaluru",
    "Sarjapur": "Bengaluru",
    "Hebbal": "Bengaluru",
    "Electronic City": "Bengaluru",
    "Baner": "Pune",
    "Hinjewadi": "Pune",
    "Kharadi": "Pune",
    "Viman Nagar": "Pune",
    "Wakad": "Pune",
}


def get_coordinates(micro_market: str) -> Tuple[float, float]:
    """
    Get latitude, longitude for a micro-market.

    Falls back to Geopy Nominatim if hardcoded coords are unavailable.

    Args:
        micro_market: Name of the micro-market

    Returns:
        Tuple of (latitude, longitude)
    """
    if micro_market in MICRO_MARKET_COORDS:
        return MICRO_MARKET_COORDS[micro_market]

    # Fallback: Geopy lookup with caching
    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut
        import time

        geolocator = Nominatim(user_agent="proplens_india_v2")
        city = MARKET_TO_CITY.get(micro_market, "India")
        query = f"{micro_market}, {city}, India"

        time.sleep(1)  # Rate limit: 1 req/sec for Nominatim
        location = geolocator.geocode(query, timeout=10)

        if location:
            coords = (location.latitude, location.longitude)
            # Cache for future use
            MICRO_MARKET_COORDS[micro_market] = coords
            return coords
    except (ImportError, GeocoderTimedOut, Exception):
        pass

    # Ultimate fallback: India centre
    return INDIA_CENTER


def get_all_coordinates() -> Dict[str, Tuple[float, float]]:
    """Return coordinates for all 15 micro-markets."""
    return MICRO_MARKET_COORDS.copy()
