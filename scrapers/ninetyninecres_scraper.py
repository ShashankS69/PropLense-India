"""
99acres Scraper for PropLens India.

Extends :class:`BaseScraper` to extract residential property listings
from 99acres.com, handling search pages and pagination.
"""

import re
from typing import Dict, List, Optional

import pandas as pd
from selenium.webdriver.common.by import By

from scrapers.base_scraper import BaseScraper, PROJECT_ROOT


class NinetyNineAcresScraper(BaseScraper):
    """Scraper for 99acres.com residential sale listings.

    URL pattern:
        ``https://www.99acres.com/search/property/buy/{city}``
    """

    BASE_URL: str = "https://www.99acres.com/search/property/buy/{city}"

    def __init__(self, timeout: int = 30, headless: bool = True) -> None:
        super().__init__(
            source_name="99acres",
            timeout=timeout,
            headless=headless,
        )

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _build_url(
        self,
        city: str,
        micro_market: Optional[str] = None,
        page: int = 1,
    ) -> str:
        """Build the 99acres search URL.

        Args:
            city: Target city.
            micro_market: Optional locality filter.
            page: 1-indexed page number.

        Returns:
            Fully-qualified search URL.
        """
        city_slug = city.lower().replace(" ", "-")
        url = self.BASE_URL.format(city=city_slug)
        if micro_market:
            locality_slug = micro_market.lower().replace(" ", "-")
            url += f"/{locality_slug}"
        if page > 1:
            url += f"?page={page}"
        return url

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_price(text: str) -> Optional[int]:
        """Parse 99acres price strings into integer INR.

        Handles: '₹ 2.5 Cr', '₹ 65 Lac', plain numbers.

        Args:
            text: Raw price text.

        Returns:
            Price in INR or ``None``.
        """
        if not text:
            return None
        text = text.strip().replace(",", "").replace("₹", "").strip()
        cr = re.search(r"([\d.]+)\s*Cr", text, re.IGNORECASE)
        if cr:
            return int(float(cr.group(1)) * 1_00_00_000)
        lac = re.search(r"([\d.]+)\s*(?:Lac|Lakh|L)", text, re.IGNORECASE)
        if lac:
            return int(float(lac.group(1)) * 1_00_000)
        digits = re.search(r"([\d]+)", text)
        if digits:
            return int(digits.group(1))
        return None

    @staticmethod
    def _parse_area(text: str) -> Optional[int]:
        """Extract area in sqft.

        Args:
            text: Raw area text.

        Returns:
            Area as integer or ``None``.
        """
        if not text:
            return None
        match = re.search(r"([\d,]+)\s*(?:sq\.?\s*ft|sqft)", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def _parse_bhk(text: str) -> Optional[str]:
        """Extract BHK label.

        Args:
            text: Raw property-type text.

        Returns:
            Normalised BHK string or ``None``.
        """
        if not text:
            return None
        match = re.search(r"(\d)\s*BHK", text, re.IGNORECASE)
        return f"{match.group(1)} BHK" if match else None

    # ------------------------------------------------------------------
    # Core scrape logic
    # ------------------------------------------------------------------

    def _scrape_page(self, city: str, micro_market: str) -> List[Dict]:
        """Parse listing cards from the current 99acres page.

        Args:
            city: City name.
            micro_market: Micro-market name.

        Returns:
            List of listing dictionaries.
        """
        records: List[Dict] = []
        try:
            cards = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[class*='srp__card'], div[class*='projectTuple'], section[class*='srp__card']",
            )
        except Exception:
            self.logger.warning("No property cards found.")
            return records

        for card in cards:
            try:
                name_el = card.find_elements(By.CSS_SELECTOR, "a[class*='body_med'], h2[class*='projectName']")
                name = name_el[0].text.strip() if name_el else None

                price_el = card.find_elements(By.CSS_SELECTOR, "span[class*='price'], div[class*='price']")
                price_text = price_el[0].text.strip() if price_el else ""

                area_el = card.find_elements(By.CSS_SELECTOR, "span[class*='area'], div[class*='area']")
                area_text = area_el[0].text.strip() if area_el else ""

                config_el = card.find_elements(By.CSS_SELECTOR, "span[class*='config'], td[class*='config']")
                config_text = config_el[0].text.strip() if config_el else ""

                link_el = card.find_elements(By.CSS_SELECTOR, "a[href]")
                listing_url = link_el[0].get_attribute("href") if link_el else ""

                sale_price = self._parse_price(price_text)
                area_sqft = self._parse_area(area_text)
                bhk = self._parse_bhk(config_text)

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
        """Check for a pagination 'Next' link.

        Returns:
            ``True`` if next page exists.
        """
        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a[class*='pgsel'], a[aria-label='Next']",
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
        """Scrape 99acres for the given city and micro-markets.

        Args:
            city: Target city.
            micro_markets: Localities to scrape.
            max_pages: Max pages per micro-market.

        Returns:
            DataFrame of listings.
        """
        all_records: List[Dict] = []
        self.logger.info("Starting 99acres scrape for %s …", city)

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
        self.logger.info("Total 99acres listings: %d", len(df))
        return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with NinetyNineAcresScraper() as scraper:
        df = scraper.scrape(
            city="Bengaluru",
            micro_markets=["Whitefield", "Koramangala", "Sarjapur"],
        )
        output = PROJECT_ROOT / "data" / "raw" / "99acres_listings.csv"
        scraper.save_to_csv(df, output)
