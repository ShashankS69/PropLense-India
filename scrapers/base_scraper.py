"""
Base Scraper for PropLens India.

Provides an abstract base class with Selenium WebDriver management,
rate limiting, retry logic, schema validation, CSV persistence,
and structured logging. All site-specific scrapers extend this class.
"""

import logging
import os
import random
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical output columns — every scraper must produce this exact schema.
REQUIRED_COLUMNS: List[str] = [
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
]

# Rate-limiting defaults (seconds)
MIN_DELAY: float = 2.0
MAX_DELAY: float = 5.0

# Retry defaults
MAX_RETRIES: int = 3
BACKOFF_BASE: float = 2.0

# Project root (parent of scrapers/)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


def _setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create a consistently-formatted logger.

    Args:
        name: Logger name (usually the scraper module name).
        level: Logging level.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            "[%(asctime)s] %(name)s — %(levelname)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


class BaseScraper(ABC):
    """Abstract base class for PropLens web scrapers.

    Subclasses must implement :meth:`scrape` to handle site-specific
    extraction logic. The base class manages driver setup, rate limiting,
    retries, schema validation, and CSV export.

    Attributes:
        source_name: Human-readable platform name (e.g. ``"MagicBricks"``).
        timeout: Page-load timeout in seconds.
        logger: Module-level logger.
    """

    def __init__(
        self,
        source_name: str,
        timeout: int = 30,
        headless: bool = True,
    ) -> None:
        """Initialise the scraper.

        Args:
            source_name: Platform name used in CSV ``source`` column.
            timeout: Selenium page-load timeout in seconds.
            headless: Whether to run Chrome in headless mode.
        """
        self.source_name: str = source_name
        self.timeout: int = timeout
        self.headless: bool = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.logger: logging.Logger = _setup_logger(
            f"proplens.{source_name.lower().replace(' ', '_')}"
        )

    # ------------------------------------------------------------------
    # Driver lifecycle
    # ------------------------------------------------------------------

    def setup_driver(self) -> webdriver.Chrome:
        """Create and return a headless Chrome WebDriver with a random User-Agent.

        Returns:
            A configured ``webdriver.Chrome`` instance.
        """
        ua = UserAgent()
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f"user-agent={ua.random}")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(10)

        self.driver = driver
        self.logger.info("WebDriver initialised (headless=%s).", self.headless)
        return driver

    def teardown_driver(self) -> None:
        """Quit the WebDriver and release resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("WebDriver closed.")

    # ------------------------------------------------------------------
    # Rate limiting & retries
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Sleep for a random interval between requests."""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        self.logger.debug("Rate-limit sleep %.1fs.", delay)
        time.sleep(delay)

    def _retry_request(
        self,
        url: str,
        max_retries: int = MAX_RETRIES,
    ) -> bool:
        """Load a URL with retry + exponential backoff.

        Args:
            url: The URL to navigate to.
            max_retries: Maximum number of attempts.

        Returns:
            ``True`` if the page loaded successfully, ``False`` otherwise.
        """
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info("GET %s (attempt %d/%d)", url, attempt, max_retries)
                self.driver.get(url)  # type: ignore[union-attr]
                return True
            except Exception as exc:
                wait = BACKOFF_BASE ** attempt + random.uniform(0, 1)
                self.logger.warning(
                    "Attempt %d failed: %s — retrying in %.1fs",
                    attempt,
                    exc,
                    wait,
                )
                time.sleep(wait)
        self.logger.error("All %d attempts exhausted for %s.", max_retries, url)
        return False

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure the DataFrame contains the required columns.

        Missing columns are added with ``NaN``; extra columns are preserved.

        Args:
            df: Raw scraped DataFrame.

        Returns:
            DataFrame with at least all :data:`REQUIRED_COLUMNS`.
        """
        missing: Set[str] = set(REQUIRED_COLUMNS) - set(df.columns)
        for col in missing:
            df[col] = pd.NA
        return df

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_to_csv(self, df: pd.DataFrame, filepath: str | Path) -> Path:
        """Validate schema and save DataFrame to CSV.

        Args:
            df: DataFrame of scraped listings.
            filepath: Destination file path (directories created automatically).

        Returns:
            Resolved ``Path`` to the saved CSV.
        """
        df = self.validate_schema(df)
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        self.logger.info("Saved %d records → %s", len(df), path)
        return path

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def scrape(
        self,
        city: str,
        micro_markets: List[str],
    ) -> pd.DataFrame:
        """Scrape property listings for the given city and micro-markets.

        Args:
            city: Target city name.
            micro_markets: List of micro-market / locality names.

        Returns:
            DataFrame conforming to :data:`REQUIRED_COLUMNS`.
        """
        ...

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "BaseScraper":
        self.setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.teardown_driver()
