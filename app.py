# app.py
# PORT-1000: Global Port Scoring - Streamlit UI
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
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


def _score_to_color_rgba(score, max_score=1000):
    """Map score to RGBA list for pydeck. Green = high, Red = low."""
    ratio = max(0.0, min(1.0, score / max_score))
    r = int(220 * (1 - ratio))
    g = int(200 * ratio)
    b = 60
    return [r, g, b, 180]


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


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(f"""
<div style="text-align:center; margin-bottom:10px;">
    <div style="font-size:38px; font-weight:900; color:{PRIMARY_COLOR};">\u2693 PORT-1000</div>
    <div style="font-size:16px; color:#64748B; margin-top:-4px;">Global Port Scoring</div>
    <div style="font-size:13px; color:#999; margin-top:2px;">Scoring 50+ major ports worldwide on Throughput, Efficiency, Connectivity, Infrastructure, and Geopolitical Risk.</div>
</div>
""", unsafe_allow_html=True)

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

    # World Map (pydeck)
    st.markdown("<div class='section-title'>World Map</div>", unsafe_allow_html=True)

    map_data = []
    for p in rankings:
        map_data.append({
            "name": p["name"],
            "country": p["country"],
            "lat": p["lat"],
            "lng": p["lng"],
            "total": p["total"],
            "color": _score_to_color_rgba(p["total"]),
            "radius": max(30000, p["total"] * 80),
        })

    map_df = pd.DataFrame(map_data)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position='[lng, lat]',
        get_radius='radius',
        get_fill_color='color',
        pickable=True,
        opacity=0.7,
        stroked=True,
        get_line_color=[50, 50, 50, 100],
        line_width_min_pixels=1,
    )

    view_state = pdk.ViewState(
        latitude=20,
        longitude=30,
        zoom=1.5,
        pitch=0,
    )

    tooltip = {
        "html": "<b>{name}</b> ({country})<br/>Score: {total}/1000",
        "style": {
            "backgroundColor": PRIMARY_COLOR,
            "color": "white",
            "fontSize": "13px",
            "padding": "8px",
            "borderRadius": "6px",
        },
    }

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v11",
    )

    st.pydeck_chart(deck, use_container_width=True)


# ===================================================================
# PORT DETAIL TAB
# ===================================================================
with tab_detail:
    port_names = [f'{p["flag"]} {p["name"]}' for p in rankings]
    selected_display = st.selectbox("Select a port to view details", port_names)

    if selected_display:
        selected_name = selected_display.split(" ", 1)[1] if " " in selected_display else selected_display
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
                    desc = AXES_DESCRIPTIONS.get(ax_name, "")
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

            # Key Metrics
            st.markdown("#### Key Metrics")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Annual TEU (2023)", f'{raw.get("teu_million", "N/A")}M')
                st.metric("TEU Growth YoY", f'{raw.get("teu_growth_pct", "N/A")}%')
            with m2:
                st.metric("Cargo Volume", f'{raw.get("cargo_mt", "N/A")} MT')
                st.metric("Max Draft", f'{raw.get("max_draft_m", "N/A")} m')
            with m3:
                st.metric("Berth Length", f'{raw.get("berth_length_m", "N/A")} m')
                st.metric("Number of Berths", raw.get("num_berths", "N/A"))

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

    table_rows = []
    for p in rankings:
        row = {
            "Rank": p["rank"],
            "Port": f'{p["flag"]} {p["name"]}',
            "Country": p["country"],
            "Total /1000": p["total"],
        }
        for axis in AXES_LABELS:
            row[f"{axis} /200"] = p["axes"].get(axis, 0)
        table_rows.append(row)

    df_table = pd.DataFrame(table_rows)
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        height=450,
    )

    with st.expander("Scoring Methodology"):
        st.markdown("### PORT-1000 Scoring System")
        st.markdown("Each port is scored on 5 axes, each worth 0-200 points, for a maximum total of 1,000.")
        st.markdown("")
        for ax, desc in AXES_DESCRIPTIONS.items():
            st.markdown(f"**{ax}** (0-200): {desc}")
        st.markdown("")
        st.markdown("Port-level data curated from UNCTAD, port authority annual reports, and Lloyd's List (2023). Country-level data from World Bank Open Data API.")
