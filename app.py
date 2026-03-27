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
    PORTS_DATA,
    load_all_ports,
    get_port_rankings,
    get_port_detail,
    get_raw_data,
)

st.set_page_config(
    page_title="PORT-1000: Global Port Scoring",
    page_icon="\u2693",
    layout="wide",
)

SCORES_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "scores_history.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_scores_history():
    if os.path.exists(SCORES_HISTORY_FILE):
        with open(SCORES_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}


def _score_to_color(score, max_score=1000):
    """Map score to RGB color. Green = high, Red = low."""
    ratio = max(0.0, min(1.0, score / max_score))
    r = int(220 * (1 - ratio))
    g = int(200 * ratio)
    b = 60
    return [r, g, b, 180]


def _score_to_hex(score, max_score=1000):
    c = _score_to_color(score, max_score)
    return "#{:02x}{:02x}{:02x}".format(c[0], c[1], c[2])


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 2.4em;
        font-weight: 800;
        color: #0077B6;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 1.1em;
        color: #64748B;
        margin-top: -8px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, #F0F8FF 0%, #E0F0FF 100%);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        border: 1px solid #B8D8F8;
    }
    .metric-card h3 {
        margin: 0;
        color: #0077B6;
        font-size: 1.8em;
    }
    .metric-card p {
        margin: 4px 0 0 0;
        color: #64748B;
        font-size: 0.9em;
    }
    .score-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 8px;
        color: white;
        font-weight: 700;
        font-size: 0.95em;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Page
# ---------------------------------------------------------------------------
st.markdown('<div class="main-title">\u2693 PORT-1000: Global Port Scoring</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Scoring 50+ major ports worldwide on Throughput, Efficiency, Connectivity, Infrastructure, and Geopolitical Risk</div>', unsafe_allow_html=True)

rankings = get_port_rankings()

# Summary stats
total_ports = len(rankings)
avg_score = int(sum(p["total"] for p in rankings) / total_ports)
top_port = rankings[0]
bottom_port = rankings[-1]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h3>{total_ports}</h3><p>Ports Scored</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>{avg_score}</h3><p>Average Score /1000</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h3>{top_port["flag"]} {top_port["name"]}</h3><p>Top Port ({top_port["total"]}/1000)</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h3>{bottom_port["flag"]} {bottom_port["name"]}</h3><p>Bottom Port ({bottom_port["total"]}/1000)</p></div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# World Map (pydeck)
# ---------------------------------------------------------------------------
st.subheader("World Port Map")

map_data = []
for p in rankings:
    map_data.append({
        "name": p["name"],
        "country": p["country"],
        "lat": p["lat"],
        "lng": p["lng"],
        "total": p["total"],
        "color": _score_to_color(p["total"]),
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
        "backgroundColor": "#0077B6",
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

st.caption("Circle size and color reflect the port score. Green = high score, Red = low score.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Ranking Table
# ---------------------------------------------------------------------------
st.subheader("Full Ranking Table")

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
    height=600,
)

st.markdown("---")

# Top 10 / Bottom 10
col_top, col_bot = st.columns(2)

with col_top:
    st.subheader("Top 10 Ports")
    for p in rankings[:10]:
        color = _score_to_hex(p["total"])
        st.markdown(
            f'**#{p["rank"]}** {p["flag"]} **{p["name"]}** ({p["country"]}) '
            f'<span class="score-badge" style="background:{color};">{p["total"]}/1000</span>',
            unsafe_allow_html=True,
        )

with col_bot:
    st.subheader("Bottom 10 Ports")
    for p in rankings[-10:]:
        color = _score_to_hex(p["total"])
        st.markdown(
            f'**#{p["rank"]}** {p["flag"]} **{p["name"]}** ({p["country"]}) '
            f'<span class="score-badge" style="background:{color};">{p["total"]}/1000</span>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# ---------------------------------------------------------------------------
# Detail View
# ---------------------------------------------------------------------------
st.subheader("Port Detail View")

port_names = [f'{p["flag"]} {p["name"]}' for p in rankings]
selected_display = st.selectbox("Select a port", port_names)

# Extract actual port name from display string (remove flag emoji)
if selected_display:
    selected_name = selected_display.split(" ", 1)[1] if " " in selected_display else selected_display
    detail = get_port_detail(selected_name)
    raw = get_raw_data(selected_name)

    if detail and raw:
        st.markdown(f"### {detail['flag']} {detail['name']} ({detail['country']})")
        st.markdown(f"**Total Score: {detail['total']} / 1000** (Rank #{detail.get('rank', '?')})")

        # Find rank from rankings
        for r in rankings:
            if r["name"] == selected_name:
                st.markdown(f"**Rank: #{r['rank']} of {total_ports}**")
                break

        col_radar, col_bar = st.columns(2)

        # Radar chart
        with col_radar:
            st.markdown("#### Score Radar")
            categories = AXES_LABELS + [AXES_LABELS[0]]  # close the polygon
            values = [detail["axes"].get(a, 0) for a in AXES_LABELS]
            values_closed = values + [values[0]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=categories,
                fill='toself',
                fillcolor='rgba(0, 119, 182, 0.2)',
                line=dict(color='#0077B6', width=2),
                name=selected_name,
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 200]),
                ),
                showlegend=False,
                margin=dict(l=60, r=60, t=30, b=30),
                height=380,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Bar chart
        with col_bar:
            st.markdown("#### Score Breakdown")
            fig_bar = go.Figure()
            colors = ['#0077B6', '#00A6D6', '#48CAE4', '#90E0EF', '#ADE8F4']
            for i, axis in enumerate(AXES_LABELS):
                fig_bar.add_trace(go.Bar(
                    x=[axis],
                    y=[detail["axes"].get(axis, 0)],
                    name=axis,
                    marker_color=colors[i % len(colors)],
                    text=[f'{detail["axes"].get(axis, 0)}/200'],
                    textposition='outside',
                ))
            fig_bar.update_layout(
                yaxis=dict(range=[0, 220], title="Score /200"),
                showlegend=False,
                margin=dict(l=40, r=20, t=30, b=80),
                height=380,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Key Metrics
        st.markdown("#### Key Metrics")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Annual TEU", f'{raw.get("teu_million", "N/A")}M')
            st.metric("TEU Growth", f'{raw.get("teu_growth_pct", "N/A")}%')
        with m2:
            st.metric("Cargo Volume", f'{raw.get("cargo_mt", "N/A")} MT')
            st.metric("Turnaround", f'{raw.get("turnaround_hours", "N/A")} hrs')
        with m3:
            st.metric("Direct Routes", raw.get("direct_routes", "N/A"))
            st.metric("Countries Connected", raw.get("countries_connected", "N/A"))
        with m4:
            st.metric("Max Draft", f'{raw.get("max_draft_m", "N/A")} m')
            st.metric("LSCI Index", raw.get("lsci", "N/A"))

        # Historical context / notes
        st.markdown("#### Notes")
        notes = {
            "Singapore": "World's busiest transshipment hub. Consistently ranked as the top maritime capital. The Tuas mega-port expansion will consolidate all operations by 2040, adding 65M TEU capacity.",
            "Shanghai": "World's largest container port by TEU volume since 2010. The Yangshan deep-water port is fully automated. Key gateway for Chinese exports.",
            "Ningbo-Zhoushan": "Largest port by total cargo tonnage globally. Rapid growth driven by bulk commodity imports. Expanding automation across all terminals.",
            "Shenzhen": "Major export hub for the Pearl River Delta manufacturing region. Comprises Yantian, Chiwan, and Shekou terminals.",
            "Rotterdam": "Europe's largest port. Gateway to the European hinterland via Rhine river. Major investments in digitalization and energy transition.",
            "Dubai (Jebel Ali)": "Largest port in the Middle East. Operated by DP World. Key transshipment hub connecting Asia, Europe, and Africa.",
            "Busan": "South Korea's principal port and major transshipment hub for Northeast Asia. New port expansion ongoing.",
            "Tangier Med": "Africa's largest container port. Strategic location at the Strait of Gibraltar. Fastest-growing port globally in recent years.",
            "Bandar Abbas": "Iran's largest port, heavily affected by international sanctions. Limited connectivity due to trade restrictions.",
            "Novorossiysk": "Russia's largest port on the Black Sea. Severely impacted by sanctions following the conflict in Ukraine. Declining container volumes.",
        }
        note = notes.get(selected_name, f"{selected_name} is one of the world's major ports, handling significant container and cargo volumes for its region.")
        st.info(note)


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("Score History")

history = _load_scores_history()
if history:
    dates = sorted(history.keys())
    if dates:
        # Let user pick a port to see history
        hist_port = st.selectbox("Select port for history", [p["name"] for p in rankings], key="hist_port")
        hist_values = []
        hist_dates = []
        for d in dates:
            val = history[d].get(hist_port)
            if val is not None:
                hist_dates.append(d)
                hist_values.append(val)
        if hist_values:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=hist_dates,
                y=hist_values,
                mode="lines+markers",
                line=dict(color="#0077B6", width=2),
                marker=dict(size=6),
                name=hist_port,
            ))
            fig_hist.update_layout(
                yaxis=dict(range=[0, 1000], title="Score /1000"),
                xaxis=dict(title="Date"),
                margin=dict(l=40, r=20, t=30, b=40),
                height=350,
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.caption("No history recorded for this port yet.")
else:
    st.caption("No daily score records yet. Records will appear after the GitHub Actions workflow runs.")

st.markdown("---")
st.caption("PORT-1000 v1.0. Data is based on publicly available port statistics and indices. Scores update daily via automated recording.")
