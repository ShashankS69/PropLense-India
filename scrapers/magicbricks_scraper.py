"""
MagicBricks Scraper for PropLens India.

Extends :class:`BaseScraper` to extract residential property listings
from magicbricks.com, handling pagination and property-card parsing.
"""

import re
from typing import Dict, List, Optional

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapers.base_scraper import BaseScraper, PROJECT_ROOT


class MagicBricksScraper(BaseScraper):
    """Scraper for magicbricks.com residential sale listings.

    URL pattern:
        ``https://www.magicbricks.com/property-for-sale/residential-real-estate?cityName={city}``

    Attributes:
        BASE_URL: Root URL template for city-level search.
    """

    BASE_URL: str = (
        "https://www.magicbricks.com/property-for-sale/"
        "residential-real-estate?cityName={city}"
    )

    def __init__(self, timeout: int = 30, headless: bool = True) -> None:
        super().__init__(
            source_name="MagicBricks",
            timeout=timeout,
            headless=headless,
        )

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _build_url(self, city: str, micro_market: Optional[str] = None, page: int = 1) -> str:
        """Build the search URL for a city / micro-market / page.

        Args:
            city: City name.
            micro_market: Optional locality filter.
            page: 1-indexed page number.

        Returns:
            Fully-qualified search URL.
        """
        url = self.BASE_URL.format(city=city.replace(" ", "-"))
        if micro_market:
            locality_slug = micro_market.lower().replace(" ", "-")
            url += f"&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment&Locality={locality_slug}"
        if page > 1:
            url += f"&page={page}"
        return url

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_price(text: str) -> Optional[int]:
        """Parse a MagicBricks price string into an integer (₹).

        Handles formats like '₹ 1.25 Cr', '₹ 85 Lac', '₹ 45,00,000'.

        Args:
            text: Raw price text from the page.

        Returns:
            Price in INR as an integer, or ``None`` if unparseable.
        """
        if not text:
            return None
        text = text.strip().replace(",", "").replace("₹", "").strip()
        cr_match = re.search(r"([\d.]+)\s*Cr", text, re.IGNORECASE)
        if cr_match:
            return int(float(cr_match.group(1)) * 1_00_00_000)
        lac_match = re.search(r"([\d.]+)\s*(?:Lac|Lakh|L)", text, re.IGNORECASE)
        if lac_match:
            return int(float(lac_match.group(1)) * 1_00_000)
        num_match = re.search(r"([\d]+)", text)
        if num_match:
            return int(num_match.group(1))
        return None

    @staticmethod
    def _parse_area(text: str) -> Optional[int]:
        """Extract area in sqft from text like '1200 sqft'.

        Args:
            text: Raw area text.

        Returns:
            Area in sqft as an integer, or ``None``.
        """
        if not text:
            return None
        match = re.search(r"([\d,]+)\s*(?:sq\.?\s*ft|sqft)", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def _parse_bhk(text: str) -> Optional[str]:
        """Extract BHK type from text like '2 BHK Apartment'.

        Args:
            text: Raw property-type text.

        Returns:
            Normalised BHK string (e.g. ``'2 BHK'``), or ``None``.
        """
        if not text:
            return None
        match = re.search(r"(\d)\s*BHK", text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} BHK"
        return None

    # ------------------------------------------------------------------
    # Core scrape logic
    # ------------------------------------------------------------------

    def _scrape_page(self, city: str, micro_market: str) -> List[Dict]:
        """Extract listing data from the currently-loaded page.

        Args:
            city: City name for the ``city`` column.
            micro_market: Micro-market name for the ``micro_market`` column.

        Returns:
            List of dicts, each representing one property listing.
        """
        records: List[Dict] = []
        try:
            cards = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.mb-srp__card, div[data-card='property']",
            )
        except Exception:
            self.logger.warning("No property cards found on current page.")
            return records

        for card in cards:
            try:
                name_el = card.find_elements(By.CSS_SELECTOR, "h2.mb-srp__card--title, a.mb-srp__card--title")
                name = name_el[0].text.strip() if name_el else None

                price_el = card.find_elements(By.CSS_SELECTOR, "div.mb-srp__card__price--amount, span.mb-srp__card__price--amount")
                price_text = price_el[0].text.strip() if price_el else ""

                area_el = card.find_elements(By.CSS_SELECTOR, "div.mb-srp__card__summary--value, span[data-summary='area']")
                area_text = area_el[0].text.strip() if area_el else ""

                bhk_el = card.find_elements(By.CSS_SELECTOR, "div.mb-srp__card__summary--value, span[data-summary='bhk']")
                bhk_text = bhk_el[0].text.strip() if bhk_el else ""

                link_el = card.find_elements(By.CSS_SELECTOR, "a[href]")
                listing_url = link_el[0].get_attribute("href") if link_el else ""

                sale_price = self._parse_price(price_text)
                area_sqft = self._parse_area(area_text)
                bhk = self._parse_bhk(bhk_text)

                price_per_sqft = (
                    round(sale_price / area_sqft) if sale_price and area_sqft else None
                )

                records.append(
                    {
                        "property_name": name,
                        "bhk": bhk,
                        "sale_price": sale_price,
                        "rent_price": None,
                        "area_sqft": area_sqft,
                        "price_per_sqft": price_per_sqft,
                        "micro_market": micro_market,
                        "city": city,
                        "source": self.source_name,
                        "listing_url": listing_url,
                    }
                )
            except Exception as exc:
                self.logger.debug("Skipping card: %s", exc)
                continue

        return records

    def _has_next_page(self) -> bool:
        """Check if a 'Next' pagination button exists and is clickable.

        Returns:
            ``True`` if a next page is available.
        """
        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a.mb-pagination__next, a[aria-label='Next']",
            )
            return bool(next_btns and next_btns[0].is_enabled())
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def scrape(
        self,
        city: str,
        micro_markets: List[str],
        max_pages: int = 5,
    ) -> pd.DataFrame:
        """Scrape MagicBricks listings for a city and its micro-markets.

        Args:
            city: Target city (e.g. ``'Mumbai'``).
            micro_markets: List of localities to scrape.
            max_pages: Maximum pages to paginate per micro-market.

        Returns:
            DataFrame of scraped listings.
        """
        all_records: List[Dict] = []
        self.logger.info("Starting MagicBricks scrape for %s …", city)

        for market in micro_markets:
            self.logger.info("  → Micro-market: %s", market)
            for page in range(1, max_pages + 1):
                url = self._build_url(city, market, page)
                if not self._retry_request(url):
                    break

                records = self._scrape_page(city, market)
                if not records:
                    self.logger.info("    No listings on page %d — stopping.", page)
                    break

                all_records.extend(records)
                self.logger.info("    Page %d: %d listings", page, len(records))

                if not self._has_next_page():
                    break
                self._rate_limit()

        df = pd.DataFrame(all_records)
        df = self.validate_schema(df)
        self.logger.info("Total MagicBricks listings: %d", len(df))
        return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with MagicBricksScraper() as scraper:
        df = scraper.scrape(
            city="Mumbai",
            micro_markets=["Bandra", "Andheri", "Powai"],
        )
        output = PROJECT_ROOT / "data" / "raw" / "magicbricks_listings.csv"
        scraper.save_to_csv(df, output)
