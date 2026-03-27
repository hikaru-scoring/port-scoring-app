# data_logic.py
# PORT-1000: Global Port Scoring - All scoring logic and data
#
# Hybrid approach:
#   - Port-level metrics: Curated from UNCTAD, port authority reports, Lloyd's List (port_data.json)
#   - Country-level metrics: Fetched live from World Bank API (free, no key needed)

import json
import os
import numpy as np

try:
    import streamlit as st
except ImportError:
    import types as _types
    st = _types.ModuleType("streamlit")
    st.cache_data = lambda **kwargs: (lambda fn: fn)
    st.secrets = {}

try:
    import requests
except ImportError:
    requests = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AXES_LABELS = [
    "Throughput Power",
    "Operational Efficiency",
    "Connectivity",
    "Infrastructure",
    "Geopolitical Risk",
]

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PORT_DATA_FILE = os.path.join(DATA_DIR, "port_data.json")


# ---------------------------------------------------------------------------
# Port data loader
# ---------------------------------------------------------------------------
def load_port_data():
    """Load port_data.json with curated port-level metrics."""
    with open(PORT_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# World Bank API fetchers
# ---------------------------------------------------------------------------
def _wb_api_get(url):
    """Wrapper for World Bank API GET with retry."""
    if requests is None:
        return None
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) >= 2:
                    return data
        except Exception:
            pass
    return None


@st.cache_data(ttl=86400)
def fetch_world_bank_indicator(indicator, year_range="2019:2023"):
    """Fetch country-level indicator from World Bank API.
    Returns dict: {country_iso2: latest_non_null_value}
    """
    results = {}
    page = 1
    total_pages = 1

    while page <= total_pages:
        url = (
            f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
            f"?format=json&date={year_range}&per_page=1000&page={page}"
        )
        data = _wb_api_get(url)
        if data is None:
            break

        meta = data[0]
        total_pages = meta.get("pages", 1)
        records = data[1] if len(data) > 1 else []

        for rec in records:
            iso2 = rec.get("country", {}).get("id", "")
            val = rec.get("value")
            year = rec.get("date", "")
            if val is not None and len(iso2) == 2:
                # Keep the latest year value per country
                if iso2 not in results or year > results[iso2][1]:
                    results[iso2] = (val, year)

        page += 1

    # Return just the values (strip the year)
    return {k: v[0] for k, v in results.items()}


@st.cache_data(ttl=86400)
def fetch_political_stability():
    """World Bank PV.EST: Political Stability and Absence of Violence (-2.5 to 2.5)."""
    return fetch_world_bank_indicator("PV.EST")


@st.cache_data(ttl=86400)
def fetch_logistics_performance():
    """World Bank LP.LPI.OVRL.XQ: Logistics Performance Index Overall (1-5)."""
    return fetch_world_bank_indicator("LP.LPI.OVRL.XQ", "2018:2023")


@st.cache_data(ttl=86400)
def fetch_infrastructure_quality():
    """World Bank LP.LPI.INFR.XQ: LPI Infrastructure quality (1-5)."""
    return fetch_world_bank_indicator("LP.LPI.INFR.XQ", "2018:2023")


@st.cache_data(ttl=86400)
def fetch_customs_efficiency():
    """World Bank LP.LPI.CUST.XQ: LPI Customs efficiency (1-5)."""
    return fetch_world_bank_indicator("LP.LPI.CUST.XQ", "2018:2023")


@st.cache_data(ttl=86400)
def fetch_tracking_tracing():
    """World Bank LP.LPI.TRAC.XQ: LPI Tracking and tracing (1-5)."""
    return fetch_world_bank_indicator("LP.LPI.TRAC.XQ", "2018:2023")


@st.cache_data(ttl=86400)
def fetch_trade_openness():
    """World Bank TG.VAL.TOTL.GD.ZS: Trade (% of GDP)."""
    return fetch_world_bank_indicator("TG.VAL.TOTL.GD.ZS")


@st.cache_data(ttl=86400)
def fetch_country_data():
    """Fetch all country-level indicators and bundle them."""
    political = fetch_political_stability()
    lpi = fetch_logistics_performance()
    infra = fetch_infrastructure_quality()
    customs = fetch_customs_efficiency()
    tracking = fetch_tracking_tracing()
    trade = fetch_trade_openness()

    return {
        "political_stability": political or {},
        "lpi_overall": lpi or {},
        "lpi_infrastructure": infra or {},
        "lpi_customs": customs or {},
        "lpi_tracking": tracking or {},
        "trade_openness": trade or {},
    }


# ---------------------------------------------------------------------------
# Percentile ranking helper
# ---------------------------------------------------------------------------
def _percentile_rank(values):
    """Given a list of (key, value) pairs, return dict {key: percentile 0-1}.
    Higher values get higher percentile.
    None values are excluded and get None in the result.
    """
    valid = [(k, v) for k, v in values if v is not None]
    if not valid:
        return {k: None for k, _ in values}

    sorted_vals = sorted(valid, key=lambda x: x[1])
    n = len(sorted_vals)
    ranks = {}
    for i, (k, v) in enumerate(sorted_vals):
        ranks[k] = i / max(1, n - 1)

    result = {}
    for k, v in values:
        result[k] = ranks.get(k, None)
    return result


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score_port(port_key, port, all_ports, country_data):
    """
    Score a single port (0-1000, 5 axes x 200 max each).

    Axis 1: Throughput Power (200)
        - TEU volume (60%), TEU growth YoY (20%), cargo tonnage (20%)
    Axis 2: Operational Efficiency (200)
        - LPI overall (40%), LPI customs (30%), LPI tracking (30%)
    Axis 3: Connectivity (200)
        - Trade openness % GDP (50%), LPI overall (50%)
    Axis 4: Infrastructure (200)
        - Port berth_length (25%), max_draft (25%), num_berths (25%), LPI infra (25%)
    Axis 5: Geopolitical Risk (200)
        - Political stability (100%) - INVERSE: lower risk = higher score
    """
    iso2 = port.get("country_iso2", "")
    teu_2023 = port.get("teu_2023")
    teu_2022 = port.get("teu_2022")
    cargo = port.get("cargo_tonnage_mt")
    berth_len = port.get("berth_length_m")
    draft = port.get("max_draft_m")
    berths = port.get("num_berths")

    # Compute TEU growth
    teu_growth = None
    if teu_2023 is not None and teu_2022 is not None and teu_2022 > 0:
        teu_growth = (teu_2023 - teu_2022) / teu_2022

    # Collect all port values for percentile ranking
    all_teu = [(k, p.get("teu_2023")) for k, p in all_ports.items()]
    all_cargo = [(k, p.get("cargo_tonnage_mt")) for k, p in all_ports.items()]
    all_berth_len = [(k, p.get("berth_length_m")) for k, p in all_ports.items()]
    all_draft = [(k, p.get("max_draft_m")) for k, p in all_ports.items()]
    all_berths = [(k, p.get("num_berths")) for k, p in all_ports.items()]

    # TEU growth
    all_growth = []
    for k, p in all_ports.items():
        t23 = p.get("teu_2023")
        t22 = p.get("teu_2022")
        if t23 is not None and t22 is not None and t22 > 0:
            all_growth.append((k, (t23 - t22) / t22))
        else:
            all_growth.append((k, None))

    # Percentile ranks for port-level metrics
    pct_teu = _percentile_rank(all_teu)
    pct_cargo = _percentile_rank(all_cargo)
    pct_growth = _percentile_rank(all_growth)
    pct_berth_len = _percentile_rank(all_berth_len)
    pct_draft = _percentile_rank(all_draft)
    pct_berths = _percentile_rank(all_berths)

    # Country-level percentile ranks
    ps = country_data.get("political_stability", {})
    lpi = country_data.get("lpi_overall", {})
    infra = country_data.get("lpi_infrastructure", {})
    customs = country_data.get("lpi_customs", {})
    tracking = country_data.get("lpi_tracking", {})
    trade = country_data.get("trade_openness", {})

    # We need to compute percentiles among ports (using their country values)
    all_ps = [(k, ps.get(p.get("country_iso2", ""), None)) for k, p in all_ports.items()]
    all_lpi = [(k, lpi.get(p.get("country_iso2", ""), None)) for k, p in all_ports.items()]
    all_infra = [(k, infra.get(p.get("country_iso2", ""), None)) for k, p in all_ports.items()]
    all_customs = [(k, customs.get(p.get("country_iso2", ""), None)) for k, p in all_ports.items()]
    all_tracking = [(k, tracking.get(p.get("country_iso2", ""), None)) for k, p in all_ports.items()]
    all_trade = [(k, trade.get(p.get("country_iso2", ""), None)) for k, p in all_ports.items()]

    pct_ps = _percentile_rank(all_ps)
    pct_lpi = _percentile_rank(all_lpi)
    pct_infra = _percentile_rank(all_infra)
    pct_customs = _percentile_rank(all_customs)
    pct_tracking = _percentile_rank(all_tracking)
    pct_trade = _percentile_rank(all_trade)

    # --- Axis 1: Throughput Power (200) ---
    components_1 = []
    weights_1 = []
    if pct_teu.get(port_key) is not None:
        components_1.append(pct_teu[port_key])
        weights_1.append(0.60)
    if pct_growth.get(port_key) is not None:
        components_1.append(pct_growth[port_key])
        weights_1.append(0.20)
    if pct_cargo.get(port_key) is not None:
        components_1.append(pct_cargo[port_key])
        weights_1.append(0.20)
    axis_1 = _weighted_score(components_1, weights_1, 200)

    # --- Axis 2: Operational Efficiency (200) ---
    components_2 = []
    weights_2 = []
    if pct_lpi.get(port_key) is not None:
        components_2.append(pct_lpi[port_key])
        weights_2.append(0.40)
    if pct_customs.get(port_key) is not None:
        components_2.append(pct_customs[port_key])
        weights_2.append(0.30)
    if pct_tracking.get(port_key) is not None:
        components_2.append(pct_tracking[port_key])
        weights_2.append(0.30)
    axis_2 = _weighted_score(components_2, weights_2, 200)

    # --- Axis 3: Connectivity (200) ---
    components_3 = []
    weights_3 = []
    if pct_trade.get(port_key) is not None:
        components_3.append(pct_trade[port_key])
        weights_3.append(0.50)
    if pct_lpi.get(port_key) is not None:
        components_3.append(pct_lpi[port_key])
        weights_3.append(0.50)
    axis_3 = _weighted_score(components_3, weights_3, 200)

    # --- Axis 4: Infrastructure (200) ---
    components_4 = []
    weights_4 = []
    if pct_berth_len.get(port_key) is not None:
        components_4.append(pct_berth_len[port_key])
        weights_4.append(0.25)
    if pct_draft.get(port_key) is not None:
        components_4.append(pct_draft[port_key])
        weights_4.append(0.25)
    if pct_berths.get(port_key) is not None:
        components_4.append(pct_berths[port_key])
        weights_4.append(0.25)
    if pct_infra.get(port_key) is not None:
        components_4.append(pct_infra[port_key])
        weights_4.append(0.25)
    axis_4 = _weighted_score(components_4, weights_4, 200)

    # --- Axis 5: Geopolitical Risk (200) --- (higher stability = higher score)
    components_5 = []
    weights_5 = []
    if pct_ps.get(port_key) is not None:
        components_5.append(pct_ps[port_key])
        weights_5.append(1.0)
    axis_5 = _weighted_score(components_5, weights_5, 200)

    axes = {
        "Throughput Power": axis_1,
        "Operational Efficiency": axis_2,
        "Connectivity": axis_3,
        "Infrastructure": axis_4,
        "Geopolitical Risk": axis_5,
    }
    total = sum(axes.values())

    return {
        "axes": axes,
        "total": total,
    }


def _weighted_score(components, weights, max_score):
    """Compute weighted score with proportional scaling for available data."""
    if not components:
        return 0
    total_weight = sum(weights)
    if total_weight == 0:
        return 0
    raw = sum(c * w for c, w in zip(components, weights)) / total_weight
    return int(round(raw * max_score))


# ---------------------------------------------------------------------------
# Raw data for detail view
# ---------------------------------------------------------------------------
def get_raw_data(port_name):
    """Return raw data dict for a port by name (for the detail view)."""
    ports = load_port_data()
    for key, p in ports.items():
        if p.get("name") == port_name:
            teu_m = None
            if p.get("teu_2023") is not None:
                teu_m = round(p["teu_2023"] / 1_000_000, 1)
            teu_growth = None
            if p.get("teu_2023") is not None and p.get("teu_2022") is not None and p["teu_2022"] > 0:
                teu_growth = round((p["teu_2023"] - p["teu_2022"]) / p["teu_2022"] * 100, 1)
            return {
                "teu_million": teu_m,
                "teu_growth_pct": teu_growth,
                "cargo_mt": p.get("cargo_tonnage_mt"),
                "max_draft_m": p.get("max_draft_m"),
                "berth_length_m": p.get("berth_length_m"),
                "num_berths": p.get("num_berths"),
                "source": p.get("source", "N/A"),
            }
    return None


# ---------------------------------------------------------------------------
# Main ranking function
# ---------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def get_port_rankings():
    """Load all data, score all ports, return sorted list of dicts."""
    ports = load_port_data()
    country_data = fetch_country_data()

    scored = {}
    for key, port in ports.items():
        result = score_port(key, port, ports, country_data)
        scored[key] = {
            "name": port["name"],
            "country": port["country"],
            "country_iso2": port.get("country_iso2", ""),
            "flag": port.get("flag", ""),
            "lat": port.get("lat", 0),
            "lng": port.get("lng", 0),
            "total": result["total"],
            "axes": result["axes"],
        }

    # Sort by total descending
    ranked = sorted(scored.values(), key=lambda x: x["total"], reverse=True)
    for i, p in enumerate(ranked):
        p["rank"] = i + 1

    return ranked


def load_all_ports():
    """Load all ports with scores. Used by record_scores.py."""
    rankings = get_port_rankings()
    result = {}
    for p in rankings:
        result[p["name"]] = p
    return result


def get_port_detail(port_name):
    """Get a single port detail from rankings."""
    rankings = get_port_rankings()
    for p in rankings:
        if p["name"] == port_name:
            return p
    return None
