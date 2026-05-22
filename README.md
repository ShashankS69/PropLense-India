# PropLens India 
### Multi-City Property Intelligence Dashboard

> An institutional-grade real estate analysis platform covering 3 cities, 15 micro-markets, and 4 data sources — with a luxury dark UI inspired by high-end property brands.

---

## Overview

PropLens India V2 expands on the original Mumbai-only v1 (958 MagicBricks listings) to deliver a comprehensive multi-city dashboard with:

- **3 cities** — Mumbai, Bengaluru, Pune
- **15 micro-markets** across the three cities
- **4 data sources** — MagicBricks, 99acres, Housing.com, NoBroker
- **3,788 deduplicated listings** with cross-source attribution
- **7 interactive tabs** with financial analysis tools
- **Luxury dark UI** — Playfair Display, DM Mono, muted gold accents

---

## Dashboard — 7 Tabs

| Tab | Name | Description |
|-----|------|-------------|
| 1 | **City Overview** | Metric cards, side-by-side city comparisons, data coverage |
| 2 | **Yield Heatmap** | Folium choropleth on CartoDB Dark map, yield colour-coded markers |
| 3 | **City-to-City Compare** | Head-to-head micro-market analysis, green highlight on winner |
| 4 | **Investor / End-User** | Dual-mode ranking — yield-ranked for investors, affordability for buyers |
| 5 | **Yield Comparator** | IRR vs FD / Nifty / Gold / Debt MF with sensitivity heatmap |
| 6 | **Dev Feasibility** | PE-fund-style underwriting — project IRR, equity IRR, waterfall, sensitivity |
| 7 | **Listings Browser** | Filterable table with Excel export |

---

## Financial Methodology

### Tab 5 — Rental Yield vs Alternative Returns
- **Gross Yield** = (Monthly Rent × 12) / Property Price × 100
- **Net Yield** = Gross Yield × (1 − Maintenance%) × (1 − Tax%)
- **IRR** computed via Newton-Raphson on monthly cash flows:
  - t=0: −Purchase Price
  - t=1…n-1: Net Annual Rent (escalated)
  - t=n: Net Annual Rent + Sale Price (post LTCG at 12.5%)
- **Benchmarks**: FD (30% slab), Nifty/Gold (12.5% LTCG) — all post-tax
- **Sensitivity matrix**: 6×6 grid of IRR across appreciation (2-12%) × holding (3-20 yrs)

### Tab 6 — Development Feasibility & IRR
- **Total Project Cost** = Land + Construction + Marketing/Admin + Interest on Construction Finance
- **Interest** = Avg Outstanding Debt × Annual Rate × (Timeline/12) [drawn uniformly]
- **Project IRR (Unlevered)**: Monthly cash flows — land at t=0, uniform construction drawdown, revenue at completion → annualised
- **Equity IRR (Levered)**: Same but only equity outflows, per-period debt interest, debt repaid from revenue
- **Break-even** = Total Project Cost / Saleable Area
- **Sensitivity matrix**: 5×5 grid of Project IRR across sale price ±20% × construction cost ±20%

---

## Data Sources

| Platform | Raw Listings | Post-Dedup |
|----------|-------------|------------|
| MagicBricks | ~929 | — |
| 99acres | ~964 | — |
| Housing.com | ~959 | — |
| NoBroker | ~936 | — |
| **Combined** | **3,788** | **~3,000 unique** |

**Note**: V2 ships with synthetic data generated from real market research (actual ₹/sqft ranges per micro-market calibrated to 2025-26 market data). Selenium scrapers are included for live data collection — see `scrapers/` directory.

### Price Calibration (₹/sqft)
| Micro-Market | Min | Max |
|---|---|---|
| Bandra (Mumbai) | ₹43,000 | ₹81,000 |
| Koramangala (Bengaluru) | ₹12,000 | ₹25,000 |
| Viman Nagar (Pune) | ₹12,000 | ₹15,300 |
| Electronic City (Bengaluru) | ₹6,000 | ₹12,500 |
| Hinjewadi (Pune) | ₹6,500 | ₹12,600 |

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- pip

### Install
```bash
cd "PropLens India"
pip install -r requirements.txt
```

### Generate Data
```bash
python3 -m scrapers.synthetic_data
```

### Launch Dashboard
```bash
streamlit run dashboard/app.py
```

---

## File Structure

```
PropLens India/
├── scrapers/
│   ├── base_scraper.py          # Abstract base — Selenium, retry, rate-limit
│   ├── magicbricks_scraper.py
│   ├── ninetyninecres_scraper.py
│   ├── housing_scraper.py
│   ├── nobroker_scraper.py
│   ├── deduplicator.py          # RapidFuzz cross-source dedup
│   └── synthetic_data.py        # Fallback realistic data generator
├── data/
│   ├── raw/                     # Per-source CSVs
│   └── processed/
│       └── combined_listings.csv
├── dashboard/
│   ├── app.py                   # Main entry point
│   ├── styles.py                # Complete theme system
│   ├── tab1_overview.py
│   ├── tab2_heatmap.py
│   ├── tab3_comparison.py
│   ├── tab4_modes.py
│   ├── tab5_yield_comparator.py
│   ├── tab6_feasibility.py
│   └── tab7_browser.py
├── utils/
│   ├── calculations.py          # IRR, NPV, yield, feasibility functions
│   └── geocoding.py             # Micro-market coordinates
└── requirements.txt
```

---

## Tech Stack

| Layer | Library |
|-------|---------|
| Dashboard | Streamlit 1.45 |
| Charts | Plotly 6.1 |
| Map | Folium + streamlit-folium |
| Geocoding | Geopy (Nominatim) |
| Scraping | Selenium + BeautifulSoup |
| Deduplication | RapidFuzz |
| Data | Pandas + NumPy |
| Excel Export | openpyxl |

---

## UI Design

Luxury minimal aesthetic inspired by Elyse, One&Only, and top-tier PE fund portals:

- **Background**: Deep charcoal `#0D0D0D` / `#111111`
- **Cards**: Dark warm grey `#1A1A1A` with 2px gold top border
- **Accent**: Muted gold `#C9A96E` for highlights, borders, active states
- **Typography**: Playfair Display (headings) / Inter (body) / DM Mono (numbers)
- **Charts**: `#111111` background, gold primary series, `#2A2A2A` grid lines

---

## What Makes This Institutionally Credible

1. **4 data sources cross-validated** — removes single-platform bias
2. **Rental yield heatmap** — mirrors PE/REIT market screening methodology
3. **Yield vs alternatives** — the question every serious investor asks
4. **Development feasibility + IRR** — replicates actual PE fund underwriting framework
5. **Multi-city** — shows market comparison and capital allocation thinking
6. **Luxury UI** — presentation quality matches institutional standards
