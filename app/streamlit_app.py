import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Gidabo Basin Land Degradation Monitor",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data',
                         'gidabo_degradation_samples.csv')


def compute_cldi(df):
    d = df.copy()
    drop = [c for c in d.columns if '_norm' in c or c in ('CLDI', 'CLDI_2000')]
    d = d.drop(columns=drop)
    cols = ['NDVI_2000', 'NDVI_2024', 'BSI_2000', 'BSI_2024', 'SI_2000', 'SI_2024']
    sc = MinMaxScaler()
    normed = sc.fit_transform(d[cols])
    for i, c in enumerate(cols):
        d[c + '_norm'] = normed[:, i]
    d['CLDI'] = (0.5 * (1 - d['NDVI_2024_norm'])
                 + 0.3 * d['BSI_2024_norm']
                 + 0.2 * d['SI_2024_norm'])
    return d


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = compute_cldi(df)
    return df


STATUS_COLORS = {'Degraded': 'red', 'Stable': 'gray', 'Improved': 'green'}

# ---------------------------------------------------------------------------
# Global CSS fixes
# ---------------------------------------------------------------------------
st.markdown("""
<style>
div[data-baseweb="select"] > div:last-child:empty { display: none; }
[data-testid="stMultiSelect"] ul:empty { display: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="background:#1e3a5f;padding:10px 18px;border-radius:6px;margin-bottom:10px;">
        <span style="color:white;font-size:1.3rem;font-weight:700;">
            Gidabo Basin Land Degradation Monitor
        </span>
        <span style="color:#aac8e8;font-size:0.9rem;margin-left:14px;">
            Landsat-based CLDI analysis &mdash; 2000 vs 2024 &mdash; Ethiopia
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df_all = load_data()

# ---------------------------------------------------------------------------
# Main layout: left 65% map | right 35% stats
# ---------------------------------------------------------------------------
col_map, col_stats = st.columns([0.65, 0.35])

# ============================================================
# RIGHT COLUMN — Stats panel (rendered first so filters exist)
# ============================================================
with col_stats:

    # ---- Section 1: Filters ----
    st.subheader("Filters")
    all_zones    = sorted(df_all['Zone'].unique())
    all_statuses = ['Degraded', 'Stable', 'Improved']

    sel_zones = st.multiselect("Zone", all_zones, default=all_zones)
    sel_status = st.multiselect("Status", all_statuses, default=all_statuses)

    df = df_all[
        df_all['Zone'].isin(sel_zones) &
        df_all['Degradation_Status'].isin(sel_status)
    ].copy()

    st.divider()

    # ---- Section 2: Key Metrics ----
    st.subheader("Key Metrics")
    n_total = len(df_all)
    n_filt  = len(df)

    mc1, mc2, mc3 = st.columns(3)
    for col_widget, status, color in [
        (mc1, 'Degraded', 'red'),
        (mc2, 'Stable',   'gray'),
        (mc3, 'Improved', 'green'),
    ]:
        n_s   = (df['Degradation_Status'] == status).sum()
        n_all = (df_all['Degradation_Status'] == status).sum()
        pct   = n_s / n_filt * 100 if n_filt > 0 else 0
        delta = n_s - n_all
        with col_widget:
            st.metric(
                label=f"**{status}**",
                value=f"{n_s} ({pct:.0f}%)",
                delta=f"{delta:+d} vs total" if delta != 0 else None,
                delta_color="inverse" if status == 'Degraded' else "normal",
            )

    st.divider()

    # ---- Section 3: CLDI Distribution ----
    st.subheader("CLDI Distribution")

    if len(df) > 0:
        fig_hist = px.histogram(
            df, x='CLDI', color='Degradation_Status',
            color_discrete_map=STATUS_COLORS,
            nbins=25, opacity=0.7,
            barmode='overlay',
            labels={'CLDI': 'CLDI Score', 'count': 'Count'},
        )
        fig_hist.add_vline(x=0.5, line_dash='dash', line_color='darkred',
                           annotation_text='0.5', annotation_position='top right')
        fig_hist.add_vline(x=0.3, line_dash='dash', line_color='darkgreen',
                           annotation_text='0.3', annotation_position='top right')
        fig_hist.update_layout(
            height=200, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation='h', y=-0.25, x=0),
            showlegend=True,
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No data for selected filters.")

    st.divider()

    # ---- Section 4: Zone Breakdown ----
    st.subheader("Degraded Count by Zone")

    zone_deg = (
        df[df['Degradation_Status'] == 'Degraded']
        .groupby('Zone')
        .size()
        .reset_index(name='Degraded')
        .sort_values('Degraded', ascending=True)
    )
    if len(zone_deg) > 0:
        fig_zone = px.bar(
            zone_deg, x='Degraded', y='Zone', orientation='h',
            color_discrete_sequence=['tomato'],
            labels={'Degraded': 'Degraded pixels', 'Zone': ''},
            text='Degraded',
        )
        fig_zone.update_traces(textposition='outside')
        fig_zone.update_layout(
            height=200, margin=dict(l=0, r=30, t=10, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_zone, use_container_width=True)
    else:
        st.info("No degraded pixels in selection.")

# ============================================================
# LEFT COLUMN — Interactive Map
# ============================================================
with col_map:
    st.subheader("Spatial Distribution")

    if len(df) > 0:
        # Build scatter mapbox
        fig_map = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            color='Degradation_Status',
            color_discrete_map=STATUS_COLORS,
            hover_data={
                'Degradation_Status': True,
                'CLDI': ':.3f',
                'NDVI_Change': ':.3f',
                'Zone': True,
                'WorldCover_Label': True,
                'latitude': False,
                'longitude': False,
            },
            labels={'Degradation_Status': 'Status'},
            size_max=6,
            opacity=0.7,
            zoom=8,
            center={'lat': 6.45, 'lon': 38.2},
            mapbox_style='open-street-map',
            height=600,
        )

        # Uniform point size (px.scatter_mapbox size kwarg needs a column;
        # override via marker.size in update_traces)
        fig_map.update_traces(marker=dict(size=6))

        # Basin boundary rectangle (dashed outline via 5-point closed polygon)
        lats_box = [6.1, 6.8, 6.8, 6.1, 6.1]
        lons_box = [38.0, 38.0, 38.4, 38.4, 38.0]
        fig_map.add_trace(go.Scattermapbox(
            lat=lats_box,
            lon=lons_box,
            mode='lines',
            line=dict(color='black', width=2),
            name='Basin boundary',
            hoverinfo='skip',
        ))

        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                title='Status',
                orientation='v',
                x=0.01, y=0.99,
                bgcolor='rgba(255,255,255,0.8)',
            ),
        )

        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No data to display. Adjust filters.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    """
    <hr style="margin-top:8px;margin-bottom:4px;">
    <div style="font-size:0.75rem;color:#666;">
        <b>Data sources:</b>
        Landsat 5 SR Collection 2 (2000) &middot;
        Landsat 8 SR Collection 2 (2024) &middot;
        ESA WorldCover 2021 v200 &mdash;
        accessed via Google Earth Engine.
        &nbsp;|&nbsp;
        <b>Author:</b> Israel Zemedkun Gebre &nbsp;|&nbsp;
        <b>Project:</b> Gidabo Basin CLDI Analysis
    </div>
    """,
    unsafe_allow_html=True,
)
