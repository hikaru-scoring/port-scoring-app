# data_logic.py
# PORT-1000: Global Port Scoring - All scoring logic and data
import pandas as pd

# Streamlit is optional: when running outside Streamlit (e.g. GitHub Actions),
# st.cache_data becomes a no-op and st.secrets falls back to env vars.
try:
    import streamlit as st
except ImportError:
    import types as _types
    st = _types.ModuleType("streamlit")
    st.cache_data = lambda **kwargs: (lambda fn: fn)
    st.secrets = {}

# ---------------------------------------------------------------------------
# Axis labels
# ---------------------------------------------------------------------------
AXES_LABELS = [
    "Throughput Power",
    "Operational Efficiency",
    "Connectivity",
    "Infrastructure & Investment",
    "Geopolitical Risk",
]

# ---------------------------------------------------------------------------
# Hardcoded realistic data for 50+ world ports
# Sources: World Shipping Council, UNCTAD, Lloyd's List, individual port
# authority reports, World Bank governance indicators.
#
# Fields per port:
#   lat, lng              - coordinates
#   country               - country name
#   flag                  - country flag emoji
#   teu_million           - annual TEU in millions
#   cargo_mt              - total cargo in million tonnes
#   teu_growth_pct        - year-over-year TEU growth (%)
#   turnaround_hours      - average vessel turnaround (hours)
#   berth_occupancy_pct   - berth occupancy rate (%)
#   crane_moves_per_hour  - gross crane productivity
#   direct_routes         - number of direct liner services
#   countries_connected   - number of countries served
#   lsci                  - UNCTAD Liner Shipping Connectivity Index (0-100+)
#   berth_length_m        - total berth length in metres
#   max_draft_m           - maximum channel/berth draft in metres
#   capex_score           - recent capital investment level (0-10 scale)
#   political_stability   - World Bank political stability index (-2.5 to 2.5)
#   conflict_proximity    - proximity to active conflict zones (0=far, 10=very close)
#   sanctions_exposure    - sanctions / trade restriction risk (0-10)
# ---------------------------------------------------------------------------
PORTS_DATA = {
    "Singapore": {
        "lat": 1.2644, "lng": 103.8200, "country": "Singapore", "flag": "\U0001f1f8\U0001f1ec",
        "teu_million": 39.0, "cargo_mt": 590.0, "teu_growth_pct": 3.2,
        "turnaround_hours": 24, "berth_occupancy_pct": 72, "crane_moves_per_hour": 35,
        "direct_routes": 200, "countries_connected": 123, "lsci": 112.0,
        "berth_length_m": 16000, "max_draft_m": 18.0, "capex_score": 9,
        "political_stability": 1.5, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Shanghai": {
        "lat": 31.2304, "lng": 121.4737, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 49.0, "cargo_mt": 720.0, "teu_growth_pct": 2.8,
        "turnaround_hours": 30, "berth_occupancy_pct": 78, "crane_moves_per_hour": 32,
        "direct_routes": 220, "countries_connected": 130, "lsci": 145.0,
        "berth_length_m": 20000, "max_draft_m": 16.5, "capex_score": 10,
        "political_stability": -0.3, "conflict_proximity": 2, "sanctions_exposure": 3,
    },
    "Ningbo-Zhoushan": {
        "lat": 29.8683, "lng": 121.5440, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 35.3, "cargo_mt": 1260.0, "teu_growth_pct": 4.5,
        "turnaround_hours": 32, "berth_occupancy_pct": 76, "crane_moves_per_hour": 30,
        "direct_routes": 180, "countries_connected": 110, "lsci": 105.0,
        "berth_length_m": 18000, "max_draft_m": 17.0, "capex_score": 9,
        "political_stability": -0.3, "conflict_proximity": 2, "sanctions_exposure": 3,
    },
    "Shenzhen": {
        "lat": 22.5431, "lng": 114.0579, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 30.0, "cargo_mt": 280.0, "teu_growth_pct": 2.5,
        "turnaround_hours": 28, "berth_occupancy_pct": 74, "crane_moves_per_hour": 33,
        "direct_routes": 160, "countries_connected": 105, "lsci": 98.0,
        "berth_length_m": 14000, "max_draft_m": 17.4, "capex_score": 8,
        "political_stability": -0.3, "conflict_proximity": 2, "sanctions_exposure": 3,
    },
    "Guangzhou": {
        "lat": 23.1291, "lng": 113.2644, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 25.0, "cargo_mt": 610.0, "teu_growth_pct": 3.0,
        "turnaround_hours": 34, "berth_occupancy_pct": 70, "crane_moves_per_hour": 28,
        "direct_routes": 120, "countries_connected": 90, "lsci": 80.0,
        "berth_length_m": 12000, "max_draft_m": 15.5, "capex_score": 8,
        "political_stability": -0.3, "conflict_proximity": 2, "sanctions_exposure": 3,
    },
    "Qingdao": {
        "lat": 36.0671, "lng": 120.3826, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 26.0, "cargo_mt": 630.0, "teu_growth_pct": 5.1,
        "turnaround_hours": 30, "berth_occupancy_pct": 71, "crane_moves_per_hour": 31,
        "direct_routes": 140, "countries_connected": 100, "lsci": 88.0,
        "berth_length_m": 15000, "max_draft_m": 17.5, "capex_score": 9,
        "political_stability": -0.3, "conflict_proximity": 2, "sanctions_exposure": 3,
    },
    "Busan": {
        "lat": 35.1796, "lng": 129.0756, "country": "South Korea", "flag": "\U0001f1f0\U0001f1f7",
        "teu_million": 23.0, "cargo_mt": 450.0, "teu_growth_pct": 1.8,
        "turnaround_hours": 26, "berth_occupancy_pct": 68, "crane_moves_per_hour": 34,
        "direct_routes": 170, "countries_connected": 115, "lsci": 95.0,
        "berth_length_m": 13500, "max_draft_m": 17.0, "capex_score": 8,
        "political_stability": 0.5, "conflict_proximity": 3, "sanctions_exposure": 1,
    },
    "Hong Kong": {
        "lat": 22.3193, "lng": 114.1694, "country": "China (SAR)", "flag": "\U0001f1ed\U0001f1f0",
        "teu_million": 16.5, "cargo_mt": 260.0, "teu_growth_pct": -2.0,
        "turnaround_hours": 25, "berth_occupancy_pct": 60, "crane_moves_per_hour": 32,
        "direct_routes": 190, "countries_connected": 120, "lsci": 102.0,
        "berth_length_m": 8500, "max_draft_m": 15.5, "capex_score": 5,
        "political_stability": 0.2, "conflict_proximity": 2, "sanctions_exposure": 2,
    },
    "Tianjin": {
        "lat": 38.9860, "lng": 117.7200, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 22.0, "cargo_mt": 520.0, "teu_growth_pct": 3.5,
        "turnaround_hours": 36, "berth_occupancy_pct": 73, "crane_moves_per_hour": 27,
        "direct_routes": 110, "countries_connected": 85, "lsci": 72.0,
        "berth_length_m": 14000, "max_draft_m": 16.0, "capex_score": 8,
        "political_stability": -0.3, "conflict_proximity": 2, "sanctions_exposure": 3,
    },
    "Rotterdam": {
        "lat": 51.9244, "lng": 4.4777, "country": "Netherlands", "flag": "\U0001f1f3\U0001f1f1",
        "teu_million": 14.5, "cargo_mt": 467.0, "teu_growth_pct": 1.2,
        "turnaround_hours": 22, "berth_occupancy_pct": 65, "crane_moves_per_hour": 36,
        "direct_routes": 180, "countries_connected": 120, "lsci": 90.0,
        "berth_length_m": 12500, "max_draft_m": 24.0, "capex_score": 9,
        "political_stability": 1.3, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Dubai (Jebel Ali)": {
        "lat": 25.0150, "lng": 55.0650, "country": "UAE", "flag": "\U0001f1e6\U0001f1ea",
        "teu_million": 14.0, "cargo_mt": 190.0, "teu_growth_pct": 2.0,
        "turnaround_hours": 27, "berth_occupancy_pct": 66, "crane_moves_per_hour": 33,
        "direct_routes": 170, "countries_connected": 130, "lsci": 82.0,
        "berth_length_m": 15000, "max_draft_m": 18.0, "capex_score": 10,
        "political_stability": 0.8, "conflict_proximity": 5, "sanctions_exposure": 2,
    },
    "Port Klang": {
        "lat": 2.9990, "lng": 101.3929, "country": "Malaysia", "flag": "\U0001f1f2\U0001f1fe",
        "teu_million": 13.2, "cargo_mt": 250.0, "teu_growth_pct": 3.8,
        "turnaround_hours": 30, "berth_occupancy_pct": 68, "crane_moves_per_hour": 28,
        "direct_routes": 120, "countries_connected": 95, "lsci": 85.0,
        "berth_length_m": 10500, "max_draft_m": 16.0, "capex_score": 7,
        "political_stability": 0.3, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Antwerp-Bruges": {
        "lat": 51.2600, "lng": 4.3900, "country": "Belgium", "flag": "\U0001f1e7\U0001f1ea",
        "teu_million": 13.5, "cargo_mt": 290.0, "teu_growth_pct": 0.5,
        "turnaround_hours": 28, "berth_occupancy_pct": 62, "crane_moves_per_hour": 34,
        "direct_routes": 150, "countries_connected": 110, "lsci": 78.0,
        "berth_length_m": 11000, "max_draft_m": 16.0, "capex_score": 8,
        "political_stability": 0.8, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Xiamen": {
        "lat": 24.4798, "lng": 118.0894, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 12.5, "cargo_mt": 220.0, "teu_growth_pct": 4.0,
        "turnaround_hours": 30, "berth_occupancy_pct": 69, "crane_moves_per_hour": 30,
        "direct_routes": 100, "countries_connected": 80, "lsci": 70.0,
        "berth_length_m": 9500, "max_draft_m": 16.0, "capex_score": 7,
        "political_stability": -0.3, "conflict_proximity": 4, "sanctions_exposure": 3,
    },
    "Kaohsiung": {
        "lat": 22.6163, "lng": 120.3133, "country": "Taiwan", "flag": "\U0001f1f9\U0001f1fc",
        "teu_million": 9.8, "cargo_mt": 160.0, "teu_growth_pct": 1.5,
        "turnaround_hours": 26, "berth_occupancy_pct": 64, "crane_moves_per_hour": 32,
        "direct_routes": 130, "countries_connected": 95, "lsci": 75.0,
        "berth_length_m": 9000, "max_draft_m": 16.0, "capex_score": 6,
        "political_stability": 0.2, "conflict_proximity": 5, "sanctions_exposure": 2,
    },
    "Hamburg": {
        "lat": 53.5461, "lng": 9.9660, "country": "Germany", "flag": "\U0001f1e9\U0001f1ea",
        "teu_million": 8.7, "cargo_mt": 120.0, "teu_growth_pct": -1.0,
        "turnaround_hours": 24, "berth_occupancy_pct": 58, "crane_moves_per_hour": 35,
        "direct_routes": 130, "countries_connected": 100, "lsci": 72.0,
        "berth_length_m": 9800, "max_draft_m": 15.5, "capex_score": 7,
        "political_stability": 1.0, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Los Angeles": {
        "lat": 33.7350, "lng": -118.2640, "country": "USA", "flag": "\U0001f1fa\U0001f1f8",
        "teu_million": 9.9, "cargo_mt": 195.0, "teu_growth_pct": 0.8,
        "turnaround_hours": 42, "berth_occupancy_pct": 62, "crane_moves_per_hour": 28,
        "direct_routes": 110, "countries_connected": 85, "lsci": 98.0,
        "berth_length_m": 7500, "max_draft_m": 16.2, "capex_score": 7,
        "political_stability": 0.4, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Long Beach": {
        "lat": 33.7540, "lng": -118.2160, "country": "USA", "flag": "\U0001f1fa\U0001f1f8",
        "teu_million": 9.1, "cargo_mt": 180.0, "teu_growth_pct": 1.2,
        "turnaround_hours": 40, "berth_occupancy_pct": 60, "crane_moves_per_hour": 29,
        "direct_routes": 100, "countries_connected": 80, "lsci": 95.0,
        "berth_length_m": 7200, "max_draft_m": 16.2, "capex_score": 8,
        "political_stability": 0.4, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Tanjung Pelepas": {
        "lat": 1.3621, "lng": 103.5470, "country": "Malaysia", "flag": "\U0001f1f2\U0001f1fe",
        "teu_million": 11.2, "cargo_mt": 150.0, "teu_growth_pct": 5.0,
        "turnaround_hours": 26, "berth_occupancy_pct": 65, "crane_moves_per_hour": 35,
        "direct_routes": 90, "countries_connected": 70, "lsci": 72.0,
        "berth_length_m": 8500, "max_draft_m": 18.0, "capex_score": 8,
        "political_stability": 0.3, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Laem Chabang": {
        "lat": 13.0827, "lng": 100.8830, "country": "Thailand", "flag": "\U0001f1f9\U0001f1ed",
        "teu_million": 8.9, "cargo_mt": 145.0, "teu_growth_pct": 3.2,
        "turnaround_hours": 32, "berth_occupancy_pct": 67, "crane_moves_per_hour": 27,
        "direct_routes": 80, "countries_connected": 65, "lsci": 58.0,
        "berth_length_m": 8000, "max_draft_m": 16.0, "capex_score": 8,
        "political_stability": -0.2, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Ho Chi Minh City": {
        "lat": 10.7626, "lng": 106.6602, "country": "Vietnam", "flag": "\U0001f1fb\U0001f1f3",
        "teu_million": 9.5, "cargo_mt": 170.0, "teu_growth_pct": 6.5,
        "turnaround_hours": 35, "berth_occupancy_pct": 75, "crane_moves_per_hour": 24,
        "direct_routes": 70, "countries_connected": 55, "lsci": 52.0,
        "berth_length_m": 7000, "max_draft_m": 14.0, "capex_score": 7,
        "political_stability": 0.2, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Colombo": {
        "lat": 6.9271, "lng": 79.8612, "country": "Sri Lanka", "flag": "\U0001f1f1\U0001f1f0",
        "teu_million": 7.3, "cargo_mt": 100.0, "teu_growth_pct": 4.2,
        "turnaround_hours": 30, "berth_occupancy_pct": 72, "crane_moves_per_hour": 26,
        "direct_routes": 65, "countries_connected": 50, "lsci": 58.0,
        "berth_length_m": 6500, "max_draft_m": 18.0, "capex_score": 7,
        "political_stability": -0.7, "conflict_proximity": 2, "sanctions_exposure": 1,
    },
    "Piraeus": {
        "lat": 37.9422, "lng": 23.6463, "country": "Greece", "flag": "\U0001f1ec\U0001f1f7",
        "teu_million": 5.5, "cargo_mt": 75.0, "teu_growth_pct": 7.0,
        "turnaround_hours": 25, "berth_occupancy_pct": 70, "crane_moves_per_hour": 32,
        "direct_routes": 90, "countries_connected": 60, "lsci": 62.0,
        "berth_length_m": 6000, "max_draft_m": 18.5, "capex_score": 8,
        "political_stability": 0.2, "conflict_proximity": 3, "sanctions_exposure": 0,
    },
    "Felixstowe": {
        "lat": 51.9530, "lng": 1.3510, "country": "United Kingdom", "flag": "\U0001f1ec\U0001f1e7",
        "teu_million": 3.8, "cargo_mt": 48.0, "teu_growth_pct": 0.5,
        "turnaround_hours": 24, "berth_occupancy_pct": 65, "crane_moves_per_hour": 33,
        "direct_routes": 90, "countries_connected": 75, "lsci": 68.0,
        "berth_length_m": 4000, "max_draft_m": 16.0, "capex_score": 6,
        "political_stability": 0.7, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Valencia": {
        "lat": 39.4527, "lng": -0.3201, "country": "Spain", "flag": "\U0001f1ea\U0001f1f8",
        "teu_million": 5.8, "cargo_mt": 82.0, "teu_growth_pct": 2.0,
        "turnaround_hours": 26, "berth_occupancy_pct": 63, "crane_moves_per_hour": 30,
        "direct_routes": 95, "countries_connected": 70, "lsci": 65.0,
        "berth_length_m": 5500, "max_draft_m": 16.0, "capex_score": 6,
        "political_stability": 0.5, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Algeciras": {
        "lat": 36.1270, "lng": -5.4430, "country": "Spain", "flag": "\U0001f1ea\U0001f1f8",
        "teu_million": 5.1, "cargo_mt": 105.0, "teu_growth_pct": 1.5,
        "turnaround_hours": 22, "berth_occupancy_pct": 62, "crane_moves_per_hour": 34,
        "direct_routes": 80, "countries_connected": 65, "lsci": 66.0,
        "berth_length_m": 4800, "max_draft_m": 18.0, "capex_score": 7,
        "political_stability": 0.5, "conflict_proximity": 2, "sanctions_exposure": 0,
    },
    "Tokyo": {
        "lat": 35.6528, "lng": 139.7974, "country": "Japan", "flag": "\U0001f1ef\U0001f1f5",
        "teu_million": 4.5, "cargo_mt": 85.0, "teu_growth_pct": 0.3,
        "turnaround_hours": 22, "berth_occupancy_pct": 60, "crane_moves_per_hour": 35,
        "direct_routes": 100, "countries_connected": 80, "lsci": 80.0,
        "berth_length_m": 6000, "max_draft_m": 15.0, "capex_score": 6,
        "political_stability": 1.2, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Yokohama": {
        "lat": 35.4437, "lng": 139.6380, "country": "Japan", "flag": "\U0001f1ef\U0001f1f5",
        "teu_million": 2.9, "cargo_mt": 110.0, "teu_growth_pct": 0.5,
        "turnaround_hours": 24, "berth_occupancy_pct": 55, "crane_moves_per_hour": 34,
        "direct_routes": 85, "countries_connected": 72, "lsci": 76.0,
        "berth_length_m": 5000, "max_draft_m": 16.0, "capex_score": 5,
        "political_stability": 1.2, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Kobe": {
        "lat": 34.6901, "lng": 135.1956, "country": "Japan", "flag": "\U0001f1ef\U0001f1f5",
        "teu_million": 2.8, "cargo_mt": 95.0, "teu_growth_pct": 0.2,
        "turnaround_hours": 24, "berth_occupancy_pct": 54, "crane_moves_per_hour": 33,
        "direct_routes": 75, "countries_connected": 60, "lsci": 72.0,
        "berth_length_m": 4500, "max_draft_m": 16.0, "capex_score": 5,
        "political_stability": 1.2, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Mumbai (JNPT)": {
        "lat": 18.9500, "lng": 72.9500, "country": "India", "flag": "\U0001f1ee\U0001f1f3",
        "teu_million": 6.0, "cargo_mt": 85.0, "teu_growth_pct": 5.5,
        "turnaround_hours": 45, "berth_occupancy_pct": 78, "crane_moves_per_hour": 22,
        "direct_routes": 75, "countries_connected": 55, "lsci": 60.0,
        "berth_length_m": 6200, "max_draft_m": 15.0, "capex_score": 8,
        "political_stability": -0.6, "conflict_proximity": 3, "sanctions_exposure": 1,
    },
    "Mundra": {
        "lat": 22.8390, "lng": 69.7194, "country": "India", "flag": "\U0001f1ee\U0001f1f3",
        "teu_million": 7.0, "cargo_mt": 155.0, "teu_growth_pct": 8.0,
        "turnaround_hours": 38, "berth_occupancy_pct": 70, "crane_moves_per_hour": 24,
        "direct_routes": 60, "countries_connected": 45, "lsci": 50.0,
        "berth_length_m": 7500, "max_draft_m": 17.5, "capex_score": 9,
        "political_stability": -0.6, "conflict_proximity": 3, "sanctions_exposure": 1,
    },
    "Chittagong": {
        "lat": 22.3569, "lng": 91.7832, "country": "Bangladesh", "flag": "\U0001f1e7\U0001f1e9",
        "teu_million": 3.5, "cargo_mt": 100.0, "teu_growth_pct": 6.0,
        "turnaround_hours": 72, "berth_occupancy_pct": 85, "crane_moves_per_hour": 15,
        "direct_routes": 35, "countries_connected": 28, "lsci": 22.0,
        "berth_length_m": 4000, "max_draft_m": 9.5, "capex_score": 4,
        "political_stability": -1.0, "conflict_proximity": 2, "sanctions_exposure": 1,
    },
    "Dar es Salaam": {
        "lat": -6.8235, "lng": 39.2695, "country": "Tanzania", "flag": "\U0001f1f9\U0001f1ff",
        "teu_million": 1.2, "cargo_mt": 18.0, "teu_growth_pct": 5.5,
        "turnaround_hours": 96, "berth_occupancy_pct": 82, "crane_moves_per_hour": 12,
        "direct_routes": 25, "countries_connected": 20, "lsci": 14.0,
        "berth_length_m": 2500, "max_draft_m": 11.5, "capex_score": 5,
        "political_stability": -0.2, "conflict_proximity": 3, "sanctions_exposure": 0,
    },
    "Mombasa": {
        "lat": -4.0435, "lng": 39.6682, "country": "Kenya", "flag": "\U0001f1f0\U0001f1ea",
        "teu_million": 1.5, "cargo_mt": 35.0, "teu_growth_pct": 4.0,
        "turnaround_hours": 80, "berth_occupancy_pct": 78, "crane_moves_per_hour": 14,
        "direct_routes": 30, "countries_connected": 22, "lsci": 18.0,
        "berth_length_m": 3000, "max_draft_m": 13.0, "capex_score": 6,
        "political_stability": -0.8, "conflict_proximity": 4, "sanctions_exposure": 0,
    },
    "Durban": {
        "lat": -29.8587, "lng": 31.0292, "country": "South Africa", "flag": "\U0001f1ff\U0001f1e6",
        "teu_million": 2.8, "cargo_mt": 80.0, "teu_growth_pct": 1.0,
        "turnaround_hours": 60, "berth_occupancy_pct": 75, "crane_moves_per_hour": 18,
        "direct_routes": 50, "countries_connected": 40, "lsci": 35.0,
        "berth_length_m": 5000, "max_draft_m": 14.0, "capex_score": 5,
        "political_stability": -0.1, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Santos": {
        "lat": -23.9541, "lng": -46.3228, "country": "Brazil", "flag": "\U0001f1e7\U0001f1f7",
        "teu_million": 5.0, "cargo_mt": 140.0, "teu_growth_pct": 3.5,
        "turnaround_hours": 48, "berth_occupancy_pct": 72, "crane_moves_per_hour": 22,
        "direct_routes": 60, "countries_connected": 45, "lsci": 42.0,
        "berth_length_m": 6500, "max_draft_m": 15.0, "capex_score": 7,
        "political_stability": -0.3, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Balboa": {
        "lat": 8.9500, "lng": -79.5667, "country": "Panama", "flag": "\U0001f1f5\U0001f1e6",
        "teu_million": 3.2, "cargo_mt": 45.0, "teu_growth_pct": 2.5,
        "turnaround_hours": 30, "berth_occupancy_pct": 60, "crane_moves_per_hour": 28,
        "direct_routes": 80, "countries_connected": 55, "lsci": 50.0,
        "berth_length_m": 3500, "max_draft_m": 15.2, "capex_score": 6,
        "political_stability": 0.2, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Colon": {
        "lat": 9.3590, "lng": -79.9005, "country": "Panama", "flag": "\U0001f1f5\U0001f1e6",
        "teu_million": 4.8, "cargo_mt": 55.0, "teu_growth_pct": 3.0,
        "turnaround_hours": 28, "berth_occupancy_pct": 62, "crane_moves_per_hour": 30,
        "direct_routes": 85, "countries_connected": 60, "lsci": 55.0,
        "berth_length_m": 4200, "max_draft_m": 16.5, "capex_score": 7,
        "political_stability": 0.2, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "Bandar Abbas": {
        "lat": 27.1865, "lng": 56.2808, "country": "Iran", "flag": "\U0001f1ee\U0001f1f7",
        "teu_million": 2.8, "cargo_mt": 95.0, "teu_growth_pct": 1.0,
        "turnaround_hours": 60, "berth_occupancy_pct": 70, "crane_moves_per_hour": 16,
        "direct_routes": 30, "countries_connected": 25, "lsci": 20.0,
        "berth_length_m": 5000, "max_draft_m": 14.5, "capex_score": 3,
        "political_stability": -1.5, "conflict_proximity": 9, "sanctions_exposure": 10,
    },
    "Jeddah": {
        "lat": 21.4858, "lng": 39.1925, "country": "Saudi Arabia", "flag": "\U0001f1f8\U0001f1e6",
        "teu_million": 5.0, "cargo_mt": 75.0, "teu_growth_pct": 4.5,
        "turnaround_hours": 32, "berth_occupancy_pct": 65, "crane_moves_per_hour": 28,
        "direct_routes": 80, "countries_connected": 60, "lsci": 55.0,
        "berth_length_m": 6000, "max_draft_m": 16.0, "capex_score": 9,
        "political_stability": -0.2, "conflict_proximity": 6, "sanctions_exposure": 1,
    },
    "Salalah": {
        "lat": 16.9400, "lng": 54.0000, "country": "Oman", "flag": "\U0001f1f4\U0001f1f2",
        "teu_million": 3.8, "cargo_mt": 30.0, "teu_growth_pct": 2.0,
        "turnaround_hours": 28, "berth_occupancy_pct": 55, "crane_moves_per_hour": 30,
        "direct_routes": 55, "countries_connected": 40, "lsci": 48.0,
        "berth_length_m": 4000, "max_draft_m": 18.0, "capex_score": 6,
        "political_stability": 0.5, "conflict_proximity": 5, "sanctions_exposure": 0,
    },
    "Karachi": {
        "lat": 24.8607, "lng": 67.0011, "country": "Pakistan", "flag": "\U0001f1f5\U0001f1f0",
        "teu_million": 3.2, "cargo_mt": 55.0, "teu_growth_pct": 2.5,
        "turnaround_hours": 55, "berth_occupancy_pct": 80, "crane_moves_per_hour": 16,
        "direct_routes": 35, "countries_connected": 30, "lsci": 28.0,
        "berth_length_m": 4500, "max_draft_m": 12.5, "capex_score": 4,
        "political_stability": -1.8, "conflict_proximity": 6, "sanctions_exposure": 2,
    },
    "Haifa": {
        "lat": 32.8191, "lng": 34.9983, "country": "Israel", "flag": "\U0001f1ee\U0001f1f1",
        "teu_million": 1.5, "cargo_mt": 28.0, "teu_growth_pct": 1.0,
        "turnaround_hours": 28, "berth_occupancy_pct": 60, "crane_moves_per_hour": 28,
        "direct_routes": 55, "countries_connected": 40, "lsci": 38.0,
        "berth_length_m": 3200, "max_draft_m": 15.5, "capex_score": 7,
        "political_stability": -1.0, "conflict_proximity": 8, "sanctions_exposure": 3,
    },
    "Mersin": {
        "lat": 36.7990, "lng": 34.6330, "country": "Turkey", "flag": "\U0001f1f9\U0001f1f7",
        "teu_million": 2.1, "cargo_mt": 40.0, "teu_growth_pct": 3.5,
        "turnaround_hours": 30, "berth_occupancy_pct": 63, "crane_moves_per_hour": 26,
        "direct_routes": 60, "countries_connected": 45, "lsci": 48.0,
        "berth_length_m": 4000, "max_draft_m": 16.0, "capex_score": 7,
        "political_stability": -0.8, "conflict_proximity": 5, "sanctions_exposure": 1,
    },
    "Novorossiysk": {
        "lat": 44.7167, "lng": 37.7833, "country": "Russia", "flag": "\U0001f1f7\U0001f1fa",
        "teu_million": 1.0, "cargo_mt": 155.0, "teu_growth_pct": -5.0,
        "turnaround_hours": 55, "berth_occupancy_pct": 72, "crane_moves_per_hour": 18,
        "direct_routes": 20, "countries_connected": 18, "lsci": 12.0,
        "berth_length_m": 4800, "max_draft_m": 14.0, "capex_score": 4,
        "political_stability": -1.2, "conflict_proximity": 10, "sanctions_exposure": 9,
    },
    "Gdansk": {
        "lat": 54.3520, "lng": 18.6466, "country": "Poland", "flag": "\U0001f1f5\U0001f1f1",
        "teu_million": 3.1, "cargo_mt": 53.0, "teu_growth_pct": 8.0,
        "turnaround_hours": 26, "berth_occupancy_pct": 64, "crane_moves_per_hour": 30,
        "direct_routes": 70, "countries_connected": 55, "lsci": 40.0,
        "berth_length_m": 5000, "max_draft_m": 17.0, "capex_score": 9,
        "political_stability": 0.6, "conflict_proximity": 3, "sanctions_exposure": 0,
    },
    "Gioia Tauro": {
        "lat": 38.4308, "lng": 15.8956, "country": "Italy", "flag": "\U0001f1ee\U0001f1f9",
        "teu_million": 3.3, "cargo_mt": 38.0, "teu_growth_pct": 5.0,
        "turnaround_hours": 22, "berth_occupancy_pct": 58, "crane_moves_per_hour": 32,
        "direct_routes": 65, "countries_connected": 50, "lsci": 48.0,
        "berth_length_m": 3400, "max_draft_m": 18.0, "capex_score": 6,
        "political_stability": 0.5, "conflict_proximity": 2, "sanctions_exposure": 0,
    },
    "Tangier Med": {
        "lat": 35.8820, "lng": -5.5082, "country": "Morocco", "flag": "\U0001f1f2\U0001f1e6",
        "teu_million": 7.5, "cargo_mt": 105.0, "teu_growth_pct": 9.5,
        "turnaround_hours": 22, "berth_occupancy_pct": 68, "crane_moves_per_hour": 34,
        "direct_routes": 90, "countries_connected": 70, "lsci": 72.0,
        "berth_length_m": 6500, "max_draft_m": 18.0, "capex_score": 10,
        "political_stability": -0.2, "conflict_proximity": 1, "sanctions_exposure": 0,
    },
    "Damietta": {
        "lat": 31.4175, "lng": 31.8144, "country": "Egypt", "flag": "\U0001f1ea\U0001f1ec",
        "teu_million": 1.5, "cargo_mt": 32.0, "teu_growth_pct": 3.0,
        "turnaround_hours": 40, "berth_occupancy_pct": 58, "crane_moves_per_hour": 20,
        "direct_routes": 40, "countries_connected": 30, "lsci": 32.0,
        "berth_length_m": 3500, "max_draft_m": 14.5, "capex_score": 5,
        "political_stability": -0.8, "conflict_proximity": 4, "sanctions_exposure": 1,
    },
    "Alexandria": {
        "lat": 31.2001, "lng": 29.9187, "country": "Egypt", "flag": "\U0001f1ea\U0001f1ec",
        "teu_million": 1.8, "cargo_mt": 45.0, "teu_growth_pct": 2.0,
        "turnaround_hours": 45, "berth_occupancy_pct": 65, "crane_moves_per_hour": 18,
        "direct_routes": 45, "countries_connected": 35, "lsci": 35.0,
        "berth_length_m": 4000, "max_draft_m": 14.0, "capex_score": 5,
        "political_stability": -0.8, "conflict_proximity": 4, "sanctions_exposure": 1,
    },
    "Dalian": {
        "lat": 38.9140, "lng": 121.6147, "country": "China", "flag": "\U0001f1e8\U0001f1f3",
        "teu_million": 8.5, "cargo_mt": 310.0, "teu_growth_pct": 2.0,
        "turnaround_hours": 34, "berth_occupancy_pct": 68, "crane_moves_per_hour": 28,
        "direct_routes": 90, "countries_connected": 70, "lsci": 65.0,
        "berth_length_m": 10000, "max_draft_m": 16.0, "capex_score": 7,
        "political_stability": -0.3, "conflict_proximity": 2, "sanctions_exposure": 3,
    },
    "Colombo South": {
        "lat": 6.9380, "lng": 79.8200, "country": "Sri Lanka", "flag": "\U0001f1f1\U0001f1f0",
        "teu_million": 3.5, "cargo_mt": 50.0, "teu_growth_pct": 5.0,
        "turnaround_hours": 28, "berth_occupancy_pct": 70, "crane_moves_per_hour": 28,
        "direct_routes": 50, "countries_connected": 40, "lsci": 55.0,
        "berth_length_m": 4200, "max_draft_m": 18.0, "capex_score": 8,
        "political_stability": -0.7, "conflict_proximity": 2, "sanctions_exposure": 1,
    },
    "Savannah": {
        "lat": 32.0809, "lng": -81.0912, "country": "USA", "flag": "\U0001f1fa\U0001f1f8",
        "teu_million": 5.8, "cargo_mt": 38.0, "teu_growth_pct": 4.5,
        "turnaround_hours": 36, "berth_occupancy_pct": 58, "crane_moves_per_hour": 30,
        "direct_routes": 75, "countries_connected": 55, "lsci": 75.0,
        "berth_length_m": 5500, "max_draft_m": 14.5, "capex_score": 9,
        "political_stability": 0.4, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
    "New York/New Jersey": {
        "lat": 40.6700, "lng": -74.0400, "country": "USA", "flag": "\U0001f1fa\U0001f1f8",
        "teu_million": 9.5, "cargo_mt": 60.0, "teu_growth_pct": 2.0,
        "turnaround_hours": 38, "berth_occupancy_pct": 64, "crane_moves_per_hour": 28,
        "direct_routes": 120, "countries_connected": 85, "lsci": 95.0,
        "berth_length_m": 6500, "max_draft_m": 15.2, "capex_score": 8,
        "political_stability": 0.4, "conflict_proximity": 0, "sanctions_exposure": 0,
    },
}


# ---------------------------------------------------------------------------
# Reference ranges for normalization (based on global port data ranges)
# ---------------------------------------------------------------------------
# TEU: 0-50M, Cargo: 0-1300MT, Growth: -5 to +10%
# Turnaround: 20-100hrs (inverse), Occupancy: 50-90% (mid is best), Crane: 10-40
# Routes: 15-220, Countries: 15-130, LSCI: 10-150
# Berth: 2000-20000m, Draft: 9-24m, Capex: 0-10
# Political: -2.5 to 2.5, Conflict: 0-10, Sanctions: 0-10

def _normalize(value, low, high):
    """Normalize a value to 0.0-1.0 range, clamped."""
    if high == low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _normalize_inverse(value, low, high):
    """Normalize inversely: lower value = higher score."""
    return 1.0 - _normalize(value, low, high)


def score_throughput(port):
    """Axis 1: Throughput Power (0-200)."""
    valid = {}

    teu = port.get("teu_million")
    if teu is not None:
        valid["teu"] = _normalize(teu, 0, 50) * 0.50

    cargo = port.get("cargo_mt")
    if cargo is not None:
        valid["cargo"] = _normalize(cargo, 0, 1300) * 0.30

    growth = port.get("teu_growth_pct")
    if growth is not None:
        valid["growth"] = _normalize(growth, -5, 10) * 0.20

    if not valid:
        return None

    weight_sum = sum(valid.values())
    total_weight = sum([0.50, 0.30, 0.20][:len(valid)])
    # Proportional scaling for missing data
    if total_weight > 0:
        score = (weight_sum / total_weight) * 200
    else:
        score = 0
    return int(min(max(score, 0), 200))


def score_efficiency(port):
    """Axis 2: Operational Efficiency (0-200)."""
    valid = {}

    turnaround = port.get("turnaround_hours")
    if turnaround is not None:
        # Lower turnaround = better
        valid["turnaround"] = _normalize_inverse(turnaround, 20, 100) * 0.40

    occupancy = port.get("berth_occupancy_pct")
    if occupancy is not None:
        # Moderate occupancy (60-70%) is ideal. Too high = congestion.
        if occupancy <= 70:
            occ_score = _normalize(occupancy, 40, 70)
        else:
            occ_score = _normalize_inverse(occupancy, 70, 95)
        valid["occupancy"] = occ_score * 0.25

    crane = port.get("crane_moves_per_hour")
    if crane is not None:
        valid["crane"] = _normalize(crane, 10, 40) * 0.35

    if not valid:
        return None

    weight_sum = sum(valid.values())
    total_weight = sum([0.40, 0.25, 0.35][:len(valid)])
    if total_weight > 0:
        score = (weight_sum / total_weight) * 200
    else:
        score = 0
    return int(min(max(score, 0), 200))


def score_connectivity(port):
    """Axis 3: Connectivity (0-200)."""
    valid = {}

    routes = port.get("direct_routes")
    if routes is not None:
        valid["routes"] = _normalize(routes, 15, 220) * 0.35

    countries = port.get("countries_connected")
    if countries is not None:
        valid["countries"] = _normalize(countries, 15, 130) * 0.30

    lsci = port.get("lsci")
    if lsci is not None:
        valid["lsci"] = _normalize(lsci, 10, 150) * 0.35

    if not valid:
        return None

    weight_sum = sum(valid.values())
    total_weight = sum([0.35, 0.30, 0.35][:len(valid)])
    if total_weight > 0:
        score = (weight_sum / total_weight) * 200
    else:
        score = 0
    return int(min(max(score, 0), 200))


def score_infrastructure(port):
    """Axis 4: Infrastructure & Investment (0-200)."""
    valid = {}

    berth = port.get("berth_length_m")
    if berth is not None:
        valid["berth"] = _normalize(berth, 2000, 20000) * 0.35

    draft = port.get("max_draft_m")
    if draft is not None:
        valid["draft"] = _normalize(draft, 9, 24) * 0.30

    capex = port.get("capex_score")
    if capex is not None:
        valid["capex"] = _normalize(capex, 0, 10) * 0.35

    if not valid:
        return None

    weight_sum = sum(valid.values())
    total_weight = sum([0.35, 0.30, 0.35][:len(valid)])
    if total_weight > 0:
        score = (weight_sum / total_weight) * 200
    else:
        score = 0
    return int(min(max(score, 0), 200))


def score_geopolitical(port):
    """Axis 5: Geopolitical Risk (0-200). INVERSE: lower risk = higher score."""
    valid = {}

    stability = port.get("political_stability")
    if stability is not None:
        # Higher stability = higher score
        valid["stability"] = _normalize(stability, -2.5, 2.5) * 0.45

    conflict = port.get("conflict_proximity")
    if conflict is not None:
        # Lower conflict = higher score (inverse)
        valid["conflict"] = _normalize_inverse(conflict, 0, 10) * 0.30

    sanctions = port.get("sanctions_exposure")
    if sanctions is not None:
        # Lower sanctions = higher score (inverse)
        valid["sanctions"] = _normalize_inverse(sanctions, 0, 10) * 0.25

    if not valid:
        return None

    weight_sum = sum(valid.values())
    total_weight = sum([0.45, 0.30, 0.25][:len(valid)])
    if total_weight > 0:
        score = (weight_sum / total_weight) * 200
    else:
        score = 0
    return int(min(max(score, 0), 200))


def score_port(port_name, port_data):
    """Score a single port. Returns dict with axis scores, total, and metadata."""
    axes_funcs = {
        "Throughput Power": score_throughput,
        "Operational Efficiency": score_efficiency,
        "Connectivity": score_connectivity,
        "Infrastructure & Investment": score_infrastructure,
        "Geopolitical Risk": score_geopolitical,
    }

    axes = {}
    valid_count = 0
    for axis_name, func in axes_funcs.items():
        val = func(port_data)
        if val is not None:
            axes[axis_name] = val
            valid_count += 1
        else:
            axes[axis_name] = None

    # Proportional scaling: if some axes are None, scale up available axes
    available = {k: v for k, v in axes.items() if v is not None}
    if not available:
        total = 0
    elif len(available) == 5:
        total = sum(available.values())
    else:
        # Scale proportionally: total = (sum of available / count) * 5
        avg = sum(available.values()) / len(available)
        total = int(avg * 5)

    # Replace None with 0 for display, but keep track
    display_axes = {k: (v if v is not None else 0) for k, v in axes.items()}

    return {
        "name": port_name,
        "country": port_data.get("country", ""),
        "flag": port_data.get("flag", ""),
        "lat": port_data.get("lat", 0),
        "lng": port_data.get("lng", 0),
        "axes": display_axes,
        "total": int(min(max(total, 0), 1000)),
        "valid_axes": valid_count,
    }


@st.cache_data(ttl=86400, show_spinner=False)
def load_all_ports():
    """Load and score all ports. Returns dict keyed by port name."""
    results = {}
    for name, data in PORTS_DATA.items():
        results[name] = score_port(name, data)
    return results


def get_port_rankings():
    """Return sorted list of all ports with scores, highest first."""
    ports = load_all_ports()
    ranked = sorted(ports.values(), key=lambda x: x["total"], reverse=True)
    for i, p in enumerate(ranked):
        p["rank"] = i + 1
    return ranked


def get_port_detail(port_name):
    """Get detailed scoring data for a single port."""
    ports = load_all_ports()
    return ports.get(port_name)


def get_raw_data(port_name):
    """Get raw data dict for a port."""
    return PORTS_DATA.get(port_name)
