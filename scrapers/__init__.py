# PropLens India — Scrapers Package
"""
Scraper pipeline for Indian residential real estate data.

Modules:
    synthetic_data          – Realistic demo/development data generator
    base_scraper            – Abstract base class for all scrapers
    magicbricks_scraper     – MagicBricks.com scraper
    ninetyninecres_scraper  – 99acres.com scraper
    housing_scraper         – Housing.com scraper
    nobroker_scraper        – NoBroker.in scraper
    deduplicator            – Cross-source fuzzy deduplication engine
"""

from scrapers.synthetic_data import generate_synthetic_data
from scrapers.deduplicator import deduplicate

__all__ = [
    "generate_synthetic_data",
    "deduplicate",
]
