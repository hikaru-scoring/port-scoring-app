# app.py
# PORT-1000: Global Port Scoring - Streamlit UI
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

from data_logic import (
    AXES_LABELS,
    get_port_rankings,
    get_port_detail,
    get_raw_data,
)
from ui_components import inject_css, render_radar_chart

APP_TITLE = "PORT-1000"
PRIMARY_COLOR = "#0077B6"
SCORES_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "scores_history.json")

AXES_DESCRIPTIONS = {
    "Throughput Power": "Annual TEU volume and cargo tonnage. Higher throughput = higher score.",
    "Operational Efficiency": "Vessel turnaround time, crane productivity, dwell time. Faster operations = higher score.",
    "Connectivity": "Number of shipping routes, transshipment ratio, liner connectivity index. More connected = higher score.",
    "Infrastructure": "Berth length, max draft, number of berths, equipment. Better facilities = higher score.",
    "Geopolitical Risk": "Political stability, trade openness, logistics performance. Lower risk = higher score (inverse scoring).",
}

SHORT_DESCRIPTIONS = {
    "Throughput Power": "TEU volume, cargo tonnage, growth rate",
    "Operational Efficiency": "Logistics performance, customs efficiency",
    "Connectivity": "Trade openness, tracking capability",
    "Infrastructure": "Berth length, draft, berths, infra quality",
    "Geopolitical Risk": "Political stability index (inverse)",
}

WHY_EXPLANATIONS = {
    "Throughput Power": "Based on annual TEU volume, cargo tonnage, and year-over-year growth.",
    "Operational Efficiency": "Based on country-level logistics performance and customs efficiency (World Bank LPI).",
    "Connectivity": "Based on trade openness and tracking capability (World Bank indicators).",
    "Infrastructure": "Based on berth length, max draft, number of berths, and infrastructure quality index.",
    "Geopolitical Risk": "Based on political stability index (World Bank WGI). Higher stability = higher score.",
}

st.set_page_config(
    page_title="PORT-1000: Global Port Scoring",
    page_icon="\u2693",
    layout="wide",
)

# ---------------------------------------------------------------------------
# CSS Injection (shared across all scoring apps)
# ---------------------------------------------------------------------------
inject_css()
st.markdown("""
<style>
.block-container { padding-top: 1rem !important; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
.viewerBadge_container__r5tak { display: none !important; }
.styles_viewerBadge__CvC9N { display: none !important; }
[data-testid="stActionButtonIcon"] { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
a[href*="github.com"] img { display: none !important; }
div[class*="viewerBadge"] { display: none !important; }
div[class*="StatusWidget"] { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
iframe[title="streamlit_lottie.streamlit_lottie"] { display: none !important; }
.stDeployButton { display: none !important; }
div[class*="stToolbar"] { display: none !important; }
div.embeddedAppMetaInfoBar_container__DxxL1 { display: none !important; }
div[class*="embeddedAppMetaInfoBar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_scores_history():
    if os.path.exists(SCORES_HISTORY_FILE):
        with open(SCORES_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}


def score_color(score):
    """Return a hex color based on score thresholds."""
    if score >= 800:
        return "#10b981"  # green
    elif score >= 600:
        return "#2E7BE6"  # blue
    elif score >= 400:
        return "#f59e0b"  # amber
    else:
        return "#ef4444"  # red


def render_score_delta(asset_name: str, current_total: int):
    history = _load_scores_history()
    if not history:
        return
    dates = sorted(history.keys(), reverse=True)
    prev_score = None
    for d in dates:
        s = history[d].get(asset_name)
        if s is not None:
            prev_score = s
            break
    if prev_score is None:
        return
    delta = current_total - prev_score
    if delta > 0:
        color, arrow = "#10b981", "&#9650;"
    elif delta < 0:
        color, arrow = "#ef4444", "&#9660;"
    else:
        color, arrow = "#94a3b8", "&#9644;"
    st.markdown(
        f'<div style="text-align:center; font-size:1.1em; font-weight:700; color:{color}; margin-top:-8px; margin-bottom:10px;">'
        f'{arrow} {delta:+d} from last record ({prev_score})'
        f'</div>',
        unsafe_allow_html=True,
    )


rankings = get_port_rankings()

if not rankings:
    st.error("No data available.")
    st.stop()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_dash, tab_detail, tab_rankings = st.tabs(["Dashboard", "Port Detail", "Rankings"])

# ===================================================================
# DASHBOARD TAB
# ===================================================================
with tab_dash:
    st.markdown(
        "<div style='font-size:1.5em; font-weight:900; color:#1e3a8a; margin-bottom:5px;'>"
        "Global Port Dashboard</div>"
        "<p style='color:#64748b; margin-bottom:20px;'>"
        f"Real-time overview of {len(rankings)} major ports worldwide scored on a 1000-point scale.</p>",
        unsafe_allow_html=True,
    )

    with st.expander("How to use PORT-1000"):
        st.markdown("""
**Dashboard** shows the overall Port Health Score, top/bottom movers, and port cards at a glance.

**Port Detail** lets you drill into any port. View radar charts, score breakdowns, key metrics, and score history.

**Rankings** shows the full ranking table and scoring methodology.

**Data Sources**: UNCTAD, port authority annual reports, Lloyd's List (2023), World Bank Open Data API. All public.
""")

    # Sort by total score descending
    all_scores = sorted(rankings, key=lambda x: x["total"], reverse=True)

    # Port Health Score
    avg_score = int(sum(s["total"] for s in all_scores) / len(all_scores))
    if avg_score >= 700:
        health_color, health_label = "#10b981", "STRONG"
    elif avg_score >= 500:
        health_color, health_label = "#2E7BE6", "MODERATE"
    else:
        health_color, health_label = "#ef4444", "WEAK"

    st.markdown(
        f"""<div style="text-align:center; padding:25px; background:linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-radius:20px; margin-bottom:25px;">
        <div style="font-size:0.9em; color:#64748b; font-weight:700; letter-spacing:2px;">
        PORT HEALTH SCORE</div>
        <div style="font-size:4em; font-weight:900; color:{health_color}; line-height:1.1;">
        {avg_score}</div>
        <div style="font-size:1em; font-weight:700; color:{health_color};">{health_label}</div>
        <div style="font-size:0.8em; color:#94a3b8; margin-top:5px;">
        Average across {len(all_scores)} ports</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Top / Bottom movers
    history = _load_scores_history()
    if history:
        dates = sorted(history.keys(), reverse=True)
        if dates:
            prev = history[dates[0]]
            deltas = []
            for s in all_scores:
                prev_score = prev.get(s["name"])
                if prev_score is not None:
                    deltas.append({"name": s["name"], "delta": s["total"] - prev_score})

            if deltas and any(d["delta"] != 0 for d in deltas):
                deltas.sort(key=lambda x: x["delta"], reverse=True)
                top_movers = deltas[:3]
                bottom_movers = sorted(deltas, key=lambda x: x["delta"])[:3]

                mv1, mv2 = st.columns(2)
                with mv1:
                    st.markdown("<div style='font-size:1em; font-weight:700; color:#10b981; margin-bottom:10px;'>Top Movers</div>", unsafe_allow_html=True)
                    for m in top_movers:
                        if m["delta"] > 0:
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:#f0fdf4; border-radius:8px; margin-bottom:6px;">
                                <span style="font-weight:600; color:#1e293b;">{m['name']}</span>
                                <span style="font-weight:700; color:#10b981;">&#9650; {m['delta']:+d}</span>
                            </div>
                            """, unsafe_allow_html=True)
                with mv2:
                    st.markdown("<div style='font-size:1em; font-weight:700; color:#ef4444; margin-bottom:10px;'>Bottom Movers</div>", unsafe_allow_html=True)
                    for m in bottom_movers:
                        if m["delta"] < 0:
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:#fef2f2; border-radius:8px; margin-bottom:6px;">
                                <span style="font-weight:600; color:#1e293b;">{m['name']}</span>
                                <span style="font-weight:700; color:#ef4444;">&#9660; {m['delta']:+d}</span>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    # Port cards grid
    st.markdown("<div class='section-title'>All Ports</div>", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, s in enumerate(all_scores):
        score = s["total"]
        if score >= 700:
            border_color = "#10b981"
        elif score >= 500:
            border_color = "#2E7BE6"
        elif score >= 300:
            border_color = "#f59e0b"
        else:
            border_color = "#ef4444"

        with cols[i % 3]:
            st.markdown(
                f"""<div style="background:#fff; border-radius:12px; padding:18px; margin-bottom:12px;
                border-left:4px solid {border_color}; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                <div style="font-size:0.75em; color:#94a3b8; font-weight:600;">{s['country']}</div>
                <div style="font-size:0.95em; font-weight:700; color:#1e293b; margin:2px 0;">
                {s['flag']} {s['name']}</div>
                <div style="display:flex; justify-content:space-between; align-items:baseline;">
                <span style="font-size:1.8em; font-weight:900; color:{border_color};">{score}</span>
                <span style="font-size:0.8em; color:#94a3b8;">Rank #{s['rank']}</span>
                </div></div>""",
                unsafe_allow_html=True,
            )



# ===================================================================
# PORT DETAIL TAB
# ===================================================================
with tab_detail:
    # World Map (Scattergeo) at top of Port Detail
    all_scores_map = sorted(rankings, key=lambda x: x["total"], reverse=True)
    min_score = min(p["total"] for p in rankings)
    max_score = max(p["total"] for p in rankings)

    fig_map = go.Figure()
    fig_map.add_trace(go.Scattergeo(
        lat=[p["lat"] for p in rankings],
        lon=[p["lng"] for p in rankings],
        text=[f'{p["flag"]} {p["name"]} ({p["country"]})\nScore: {p["total"]}' for p in rankings],
        mode="markers",
        marker=dict(
            size=[max(8, p["total"] / 50) for p in rankings],
            color=[p["total"] for p in rankings],
            colorscale=[[0, "#d32f2f"], [0.5, "#ffd54f"], [1, "#2e7d32"]],
            cmin=min_score, cmax=max_score,
            colorbar=dict(title="Score", thickness=15, len=0.6),
            line=dict(width=1, color="#333"),
        ),
        hoverinfo="text",
    ))
    fig_map.update_layout(
        geo=dict(
            showland=True, landcolor="#f0f0f0",
            showocean=True, oceancolor="#E8F4FD",
            showcountries=True, countrycolor="#ccc",
            showcoastlines=True, coastlinecolor="#999",
            projection_type="natural earth",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        paper_bgcolor="white",
        dragmode=False,
    )
    _map_event = st.plotly_chart(fig_map, use_container_width=True, config={
        "displayModeBar": False, "scrollZoom": False, "doubleClick": False,
    }, on_select="rerun", key="port_map_detail")

    # Handle click to update selectbox
    if _map_event:
        try:
            _points = _map_event.selection.points
            if _points:
                _idx = _points[0].get("pointIndex", None)
                if _idx is not None and _idx < len(rankings):
                    st.session_state["port_detail_select"] = f'{rankings[_idx]["flag"]} {rankings[_idx]["name"]}'
        except Exception:
            pass

    port_names = [f'{p["flag"]} {p["name"]}' for p in rankings]
    port_lookup = {f'{p["flag"]} {p["name"]}': p["name"] for p in rankings}
    selected_display = st.selectbox("Select a port to view details", port_names, key="port_detail_select")

    if selected_display:
        selected_name = port_lookup.get(selected_display, selected_display)
        detail = get_port_detail(selected_name)
        raw = get_raw_data(selected_name)

        if detail and raw:
            total = detail["total"]
            axes = detail["axes"]
            sc = score_color(total)

            # Find rank
            rank_num = "?"
            total_ports = len(rankings)
            for r in rankings:
                if r["name"] == selected_name:
                    rank_num = r["rank"]
                    break

            st.markdown(f"""
            <div style="text-align:center; margin-bottom:4px;">
                <div style="font-size:22px; font-weight:700; color:#333;">{detail['flag']} {detail['name']} <span style="font-size:16px; color:#999;">({detail['country']}) Rank #{rank_num} of {total_ports}</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Total score centered
            st.markdown(f"""
            <div style="text-align:center; margin-top:4px; margin-bottom:10px;">
                <div style="font-size:14px; letter-spacing:2px; color:#666;">TOTAL SCORE</div>
                <div style="font-size:90px; font-weight:800; color:#2E7BE6; line-height:1;">
                    {total}
                    <span style="font-size:35px; color:#BBB;">/ 1000</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Score delta from last record
            render_score_delta(selected_name, total)

            # Layout: Radar Chart (left) + Score Cards (right)
            col_left, col_right = st.columns([1.5, 1])

            with col_left:
                st.markdown("<div style='font-size: 1.1em; font-weight: bold; color: #333; margin-top: -10px; margin-bottom: 5px;'>I. Intelligence Radar</div>", unsafe_allow_html=True)

                fig_r = render_radar_chart(
                    {"axes": axes, "name": selected_name},
                    None,
                    AXES_LABELS,
                )
                st.plotly_chart(fig_r, use_container_width=True)

            with col_right:
                st.markdown("<div style='font-size: 0.9em; font-weight: bold; color: #333; margin-top: -10px; margin-bottom: 15px; border-left: 3px solid #2E7BE6; padding-left: 8px;'>II. ANALYSIS SCORE METRICS</div>", unsafe_allow_html=True)
                # Individual axis score cards
                for ax_name in AXES_LABELS:
                    ax_val = axes.get(ax_name, 0)
                    desc = SHORT_DESCRIPTIONS.get(ax_name, "")
                    st.markdown(f"""
                    <div style="
                        background-color: #FFFFFF;
                        padding: 20px;
                        border-radius: 12px;
                        margin-bottom: 12px;
                        border: 1px solid #E0E0E0;
                        border-left: 8px solid #2E7BE6;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.07);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 1.4em; font-weight: 800; color: #333333;">{ax_name}</span>
                            <span style="font-size: 1.9em; font-weight: 900; line-height: 1;">
                                <span style="color: #2E7BE6;">{ax_val}</span>
                                <span style="color:#bbb;font-size:0.5em;font-weight:600;"> /200</span>
                            </span>
                        </div>
                        <p style="font-size: 1.05em; color: #777777; margin: 0; line-height: 1.3; font-weight: 500;">{desc}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander(f"Why {int(ax_val)}?", expanded=False):
                        if ax_name == "Throughput Power":
                            st.markdown(f"""
**Formula:** `Percentile rank of TEU volume + tonnage + growth rate`

**Raw Data:** TEU: {raw.get('teu_million', 'N/A')}M | Growth: {raw.get('teu_growth_pct', 'N/A')}% | Cargo: {raw.get('cargo_mt', 'N/A')} MT

**Source:** UNCTAD, Lloyd's List, Port Authority Reports
                            """)
                        elif ax_name == "Operational Efficiency":
                            st.markdown("""
**Formula:** `Country-level LPI score + Customs efficiency (World Bank)`

**Source:** World Bank Logistics Performance Index (LPI)
                            """)
                        elif ax_name == "Connectivity":
                            st.markdown("""
**Formula:** `Trade openness (Trade/GDP) + Tracking capability (LPI)`

**Source:** World Bank Trade & LPI Indicators
                            """)
                        elif ax_name == "Infrastructure":
                            st.markdown(f"""
**Formula:** `Percentile of berth length + max draft + berth count + LPI infra`

**Raw Data:** Berths: {raw.get('num_berths', 'N/A')} | Max Draft: {raw.get('max_draft_m', 'N/A')}m | Berth Length: {raw.get('berth_length_m', 'N/A')}m

**Source:** Port Authority Reports, World Bank LPI Infrastructure
                            """)
                        elif ax_name == "Geopolitical Risk":
                            st.markdown("""
**Formula:** `Political Stability Index (World Bank WGI), inverted: higher stability = higher score`

**Source:** World Bank Worldwide Governance Indicators (WGI)
                            """)

            # Key Metrics (snapshot style)
            st.markdown(
                "<div style='font-size: 0.9em; font-weight: bold; color: #333; margin-top: 10px; margin-bottom: 15px; border-left: 3px solid #2E7BE6; padding-left: 8px;'>III. KEY METRICS SNAPSHOT</div>",
                unsafe_allow_html=True,
            )

            # TOTAL / STRONGEST / WEAKEST summary row
            sc1, sc2, sc3 = st.columns(3)
            _best_ax = max(axes, key=axes.get) if axes else "N/A"
            _best_val = int(axes.get(_best_ax, 0))
            _worst_ax = min(axes, key=axes.get) if axes else "N/A"
            _worst_val = int(axes.get(_worst_ax, 0))
            sc1.markdown(f"""
            <div style="background:#f8fafc; border-radius:10px; padding:14px; margin-bottom:10px; border:1px solid #e2e8f0;">
                <div style="font-size:0.75em; color:#64748b; font-weight:600;">TOTAL SCORE</div>
                <div style="font-size:1.5em; font-weight:900; color:#1e293b; line-height:1.2;">{total} <span style="font-size:0.5em; color:#999;">/1000</span></div>
            </div>
            """, unsafe_allow_html=True)
            sc2.markdown(f"""
            <div style="background:#f0fdf4; border-radius:10px; padding:14px; margin-bottom:10px; border:1px solid #bbf7d0;">
                <div style="font-size:0.75em; color:#64748b; font-weight:600;">STRONGEST</div>
                <div style="font-size:1.5em; font-weight:900; color:#10b981; line-height:1.2;">{_best_ax} ({_best_val})</div>
            </div>
            """, unsafe_allow_html=True)
            sc3.markdown(f"""
            <div style="background:#fef2f2; border-radius:10px; padding:14px; margin-bottom:10px; border:1px solid #fecaca;">
                <div style="font-size:0.75em; color:#64748b; font-weight:600;">WEAKEST</div>
                <div style="font-size:1.5em; font-weight:900; color:#ef4444; line-height:1.2;">{_worst_ax} ({_worst_val})</div>
            </div>
            """, unsafe_allow_html=True)

            snapshot_items = [
                ("Annual TEU (2023)", f'{raw.get("teu_million", "N/A")}M'),
                ("TEU Growth YoY", f'{raw.get("teu_growth_pct", "N/A")}%'),
                ("Cargo Volume", f'{raw.get("cargo_mt", "N/A")} MT'),
                ("Max Draft", f'{raw.get("max_draft_m", "N/A")} m'),
                ("Berth Length", f'{raw.get("berth_length_m", "N/A"):,} m' if raw.get("berth_length_m") else "N/A"),
                ("Number of Berths", str(raw.get("num_berths", "N/A"))),
            ]

            snap_cols = st.columns(3)
            for idx, (label, val) in enumerate(snapshot_items):
                with snap_cols[idx % 3]:
                    st.markdown(f"""
                    <div style="background:#f8fafc; border-radius:10px; padding:14px; margin-bottom:10px; border:1px solid #e2e8f0;">
                        <div style="font-size:0.75em; color:#64748b; font-weight:600;">{label}</div>
                        <div style="font-size:1.5em; font-weight:900; color:#1e293b; line-height:1.2;">{val}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Score History
            history_data = _load_scores_history()
            if history_data:
                st.markdown("#### Score History")
                dates = sorted(history_data.keys())
                hist_values = []
                hist_dates = []
                for d_date in dates:
                    val = history_data[d_date].get(selected_name)
                    if val is not None:
                        hist_dates.append(d_date)
                        hist_values.append(val)
                if hist_values:
                    fig_daily = go.Figure()
                    fig_daily.add_trace(go.Scatter(
                        x=hist_dates,
                        y=hist_values,
                        mode='lines+markers',
                        line=dict(color='#2E7BE6', width=2),
                        marker=dict(size=5),
                        fill='tozeroy',
                        fillcolor='rgba(46,123,230,0.05)',
                        name=selected_name,
                    ))
                    fig_daily.update_layout(
                        yaxis=dict(range=[0, 1000], title="Score"),
                        height=250,
                        margin=dict(l=0, r=0, t=10, b=0),
                        plot_bgcolor='white',
                        hovermode="x unified",
                        clickmode='none',
                        dragmode=False,
                    )
                    st.plotly_chart(fig_daily, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No history recorded for this port yet.")


# ===================================================================
# RANKINGS TAB
# ===================================================================
with tab_rankings:
    st.markdown("#### Full Rankings")

    sorted_ports = sorted(rankings, key=lambda x: x["total"], reverse=True)
    history = _load_scores_history()
    prev_scores = {}
    if history:
        dates = sorted(history.keys(), reverse=True)
        if dates:
            prev_scores = history[dates[0]]

    for i, p in enumerate(sorted_ports, 1):
        name = p["name"]
        flag = p.get("flag", "")
        country = p.get("country", "")
        score = p["total"]
        badge_color = "#0077B6"

        # Score color
        if score >= 800:
            bar_color = "#10b981"
        elif score >= 600:
            bar_color = "#2E7BE6"
        elif score >= 400:
            bar_color = "#f59e0b"
        else:
            bar_color = "#ef4444"

        # Change indicator
        prev = prev_scores.get(name)
        if prev is not None:
            delta = score - prev
            if delta > 0:
                change_html = f'<span style="font-size:0.8em; font-weight:700; color:#10b981;">&#9650; +{delta}</span>'
            elif delta < 0:
                change_html = f'<span style="font-size:0.8em; font-weight:700; color:#ef4444;">&#9660; {delta}</span>'
            else:
                change_html = '<span style="font-size:0.8em; font-weight:700; color:#94a3b8;">&#9644; 0</span>'
        else:
            change_html = ""

        st.markdown(f"""
<div style="display:flex; align-items:center; padding:14px 20px; background:#fff; border-radius:12px; margin-bottom:8px; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:1.4em; font-weight:900; color:#94a3b8; width:40px;">#{i}</div>
    <div style="flex:1;">
        <div style="font-size:1.05em; font-weight:700; color:#1e293b;">{flag} {name}</div>
        <span style="font-size:0.75em; background:{badge_color}; color:#fff; padding:2px 8px; border-radius:20px;">{country}</span>
        {change_html}
    </div>
    <div style="text-align:right; min-width:80px;">
        <div style="font-size:1.5em; font-weight:900; color:{bar_color};">{score}</div>
        <div style="background:#f1f5f9; border-radius:4px; height:6px; width:80px; margin-top:4px;">
            <div style="background:{bar_color}; height:6px; border-radius:4px; width:{score/10}%;"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    with st.expander("Scoring Methodology"):
        st.markdown("### PORT-1000 Scoring System")
        st.markdown("Each port is scored on 5 axes, each worth 0-200 points, for a maximum total of 1,000.")
        st.markdown("")
        for ax, desc in AXES_DESCRIPTIONS.items():
            st.markdown(f"**{ax}** (0-200): {desc}")
        st.markdown("")
        st.markdown("Port-level data curated from UNCTAD, port authority annual reports, and Lloyd's List (2023). Country-level data from World Bank Open Data API.")
