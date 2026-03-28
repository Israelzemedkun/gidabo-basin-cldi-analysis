import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import joblib
from sklearn.preprocessing import MinMaxScaler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Gidabo Basin Land Degradation Monitor",
    layout="wide",
)

# ---------------------------------------------------------------------------
# CSS fixes
# ---------------------------------------------------------------------------
st.markdown("""
<style>
div[data-baseweb="select"] > div:last-child:empty { display: none; }
[data-testid="stMultiSelect"] ul:empty { display: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data',
                         'gidabo_degradation_samples.csv')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'rf_model.pkl')

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
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
    return compute_cldi(df)


@st.cache_resource
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STATUS_COLORS = {'Degraded': 'red', 'Stable': 'gray', 'Improved': 'green'}
PRED_COLORS   = {'Degraded': '#c62828', 'Stable': '#616161', 'Improved': '#2e7d32'}
ZONE_COLORS   = {
    'Northern Zone': '#1f77b4',
    'Central Zone':  '#ff7f0e',
    'Southern Zone': '#2ca02c',
}
FEATURES = ['NDVI_2000', 'NDVI_2024', 'BSI_2000', 'BSI_2024',
            'SI_2000', 'SI_2024', 'NDVI_Change', 'SI_Change']

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
# Load data & model
# ---------------------------------------------------------------------------
df_all   = load_data()
rf_model = load_model()

# ---------------------------------------------------------------------------
# Main layout: left 65% map | right 35% stats
# ---------------------------------------------------------------------------
col_map, col_stats = st.columns([0.65, 0.35])

# ============================================================
# RIGHT COLUMN — rendered first so df_filtered is available
# ============================================================
with col_stats:

    # ---- Section 1: Filters ----
    st.subheader("Filters")
    all_zones    = sorted(df_all['Zone'].unique())
    all_statuses = ['Degraded', 'Stable', 'Improved']

    sel_zones  = st.multiselect("Zone",   all_zones,    default=all_zones)
    sel_status = st.multiselect("Status", all_statuses, default=all_statuses)

    df_filtered = df_all[
        df_all['Zone'].isin(sel_zones) &
        df_all['Degradation_Status'].isin(sel_status)
    ].copy()

    st.divider()

    # ---- Section 2: Key Metrics ----
    st.subheader("Key Metrics")
    n_filt = len(df_filtered)

    mc1, mc2, mc3 = st.columns(3)
    for col_widget, status in [(mc1, 'Degraded'), (mc2, 'Stable'), (mc3, 'Improved')]:
        n_s   = (df_filtered['Degradation_Status'] == status).sum()
        n_all = (df_all['Degradation_Status']      == status).sum()
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

    # ---- Section 3: CLDI Distribution (350 px) ----
    st.subheader("CLDI Distribution")
    if n_filt > 0:
        fig_hist = px.histogram(
            df_filtered, x='CLDI', color='Degradation_Status',
            color_discrete_map=STATUS_COLORS,
            nbins=25, opacity=0.7, barmode='overlay',
            title='CLDI Score by Degradation Status',
            labels={'CLDI': 'CLDI Score', 'Degradation_Status': 'Status'},
        )
        fig_hist.add_vline(x=0.5, line_dash='dash', line_color='darkred',
                           annotation_text='Degraded (0.5)',
                           annotation_position='top right')
        fig_hist.add_vline(x=0.3, line_dash='dash', line_color='darkgreen',
                           annotation_text='Improved (0.3)',
                           annotation_position='top right')
        fig_hist.update_traces(
            hovertemplate='CLDI: %{x:.3f}<br>Count: %{y}<extra></extra>'
        )
        fig_hist.update_layout(
            height=350, margin=dict(l=0, r=0, t=35, b=0),
            legend=dict(orientation='h', y=-0.2, x=0, title=''),
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No data for selected filters.")

    st.divider()

    # ---- Section 4: Degraded Count by Zone ----
    st.subheader("Degraded Count by Zone")
    zone_deg = (
        df_filtered[df_filtered['Degradation_Status'] == 'Degraded']
        .groupby('Zone').size()
        .reset_index(name='Degraded')
        .sort_values('Degraded', ascending=True)
    )
    if len(zone_deg) > 0:
        fig_zone = px.bar(
            zone_deg, x='Degraded', y='Zone', orientation='h',
            color_discrete_sequence=['tomato'],
            title='Degraded Pixels per Zone',
            labels={'Degraded': 'Degraded pixel count', 'Zone': ''},
            text='Degraded',
        )
        fig_zone.update_traces(
            textposition='outside',
            hovertemplate='%{y}: %{x} degraded pixels<extra></extra>',
        )
        fig_zone.update_layout(
            height=220, margin=dict(l=0, r=40, t=35, b=0), showlegend=False,
        )
        st.plotly_chart(fig_zone, use_container_width=True)
    else:
        st.info("No degraded pixels in selection.")

    st.divider()

    # ---- Section 5: NDVI Change vs CLDI scatter ----
    st.subheader("NDVI Change vs CLDI")
    if n_filt > 0:
        fig_scatter = px.scatter(
            df_filtered, x='NDVI_Change', y='CLDI',
            color='Zone', color_discrete_map=ZONE_COLORS,
            opacity=0.65,
            title='NDVI Change vs CLDI Score by Zone',
            labels={
                'NDVI_Change': 'NDVI Change (2024 \u2212 2000)',
                'CLDI': 'CLDI (2024)',
            },
            hover_data={
                'NDVI_Change': ':.3f',
                'CLDI': ':.3f',
                'Degradation_Status': True,
                'Zone': False,
            },
        )
        fig_scatter.add_hline(y=0.5, line_dash='dash', line_color='red',
                              opacity=0.6, annotation_text='Degraded (0.5)',
                              annotation_position='top right')
        fig_scatter.add_hline(y=0.3, line_dash='dash', line_color='green',
                              opacity=0.6, annotation_text='Improved (0.3)',
                              annotation_position='bottom right')
        fig_scatter.update_layout(
            height=350, margin=dict(l=0, r=0, t=35, b=0),
            legend=dict(orientation='h', y=-0.2, x=0, title=''),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No data for selected filters.")

    st.divider()

    # ---- Download ----
    csv_data = df_filtered.to_csv(index=False)
    st.download_button(
        label="Download filtered data as CSV",
        data=csv_data,
        file_name="gidabo_degradation_filtered.csv",
        mime="text/csv",
    )

# ============================================================
# LEFT COLUMN — Interactive Map
# ============================================================
with col_map:
    st.subheader("Spatial Distribution")

    # Epoch / view toggle
    epoch_view = st.radio(
        "Map view",
        options=["Degradation Status", "NDVI 2000", "NDVI 2024",
                 "Change (2000\u21922024)"],
        horizontal=True,
        index=0,
    )

    if n_filt > 0:
        # Shared kwargs for all scatter_mapbox calls
        base_kw = dict(
            lat='latitude',
            lon='longitude',
            hover_data={
                'Degradation_Status': True,
                'CLDI': ':.3f',
                'NDVI_Change': ':.3f',
                'Zone': True,
                'WorldCover_Label': True,
                'latitude': False,
                'longitude': False,
            },
            opacity=0.7,
            zoom=8,
            center={'lat': 6.45, 'lon': 38.2},
            mapbox_style='open-street-map',
            height=600,
        )

        if epoch_view == "Degradation Status":
            fig_map = px.scatter_mapbox(
                df_filtered,
                color='Degradation_Status',
                color_discrete_map=STATUS_COLORS,
                labels={'Degradation_Status': 'Status'},
                **base_kw,
            )
        elif epoch_view == "NDVI 2000":
            fig_map = px.scatter_mapbox(
                df_filtered,
                color='NDVI_2000',
                color_continuous_scale='RdYlGn',
                range_color=[-0.1, 0.4],
                labels={'NDVI_2000': 'NDVI 2000'},
                **base_kw,
            )
        elif epoch_view == "NDVI 2024":
            fig_map = px.scatter_mapbox(
                df_filtered,
                color='NDVI_2024',
                color_continuous_scale='RdYlGn',
                range_color=[-0.1, 0.4],
                labels={'NDVI_2024': 'NDVI 2024'},
                **base_kw,
            )
        else:  # Change (2000→2024)
            fig_map = px.scatter_mapbox(
                df_filtered,
                color='NDVI_Change',
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,
                range_color=[-0.3, 0.3],
                labels={'NDVI_Change': 'NDVI Change'},
                **base_kw,
            )

        # Uniform point size applied before adding boundary trace
        fig_map.update_traces(marker=dict(size=6))

        # Basin boundary dashed rectangle
        fig_map.add_trace(go.Scattermapbox(
            lat=[6.1, 6.8, 6.8, 6.1, 6.1],
            lon=[38.0, 38.0, 38.4, 38.4, 38.0],
            mode='lines',
            line=dict(color='black', width=2),
            name='Basin boundary',
            hoverinfo='skip',
        ))

        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                title='Status' if epoch_view == "Degradation Status" else '',
                orientation='v',
                x=0.01, y=0.99,
                bgcolor='rgba(255,255,255,0.8)',
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No data to display. Adjust filters.")

# ============================================================
# PREDICTOR SECTION — full width below map/stats
# ============================================================
st.divider()
st.subheader("Degradation Risk Predictor")

if rf_model is None:
    st.warning(
        f"Model not found at `{MODEL_PATH}`. "
        "Run `scripts/ml_classifier.py` to train and save the model first."
    )
else:
    st.markdown(
        "Adjust the sliders to simulate Landsat surface reflectance measurements "
        "and predict the degradation status for a hypothetical pixel."
    )

    pred_col1, pred_col2 = st.columns(2)

    with pred_col1:
        st.markdown("**Year 2000 measurements**")
        ndvi_2000  = st.slider("NDVI 2000",   -0.10, 0.40,  0.14, 0.01)
        bsi_2000   = st.slider("BSI 2000",    -0.10, 0.15,  0.02, 0.01)
        si_2000    = st.slider("SI 2000",      9000, 14000, 11500, 100)
        ndvi_change = st.slider("NDVI Change", -0.30, 0.30,  0.06, 0.01)

    with pred_col2:
        st.markdown("**Year 2024 measurements**")
        ndvi_2024  = st.slider("NDVI 2024",   -0.10, 0.40,  0.20, 0.01)
        bsi_2024   = st.slider("BSI 2024",    -0.10, 0.15, -0.02, 0.01)
        si_2024    = st.slider("SI 2024",      8000, 14000, 10900, 100)
        si_change  = st.slider("SI Change",   -2000,  2000,  -500, 100)

    if st.button("Predict Degradation Status", type="primary"):
        input_df = pd.DataFrame([{
            'NDVI_2000':   ndvi_2000,
            'NDVI_2024':   ndvi_2024,
            'BSI_2000':    bsi_2000,
            'BSI_2024':    bsi_2024,
            'SI_2000':     si_2000,
            'SI_2024':     si_2024,
            'NDVI_Change': ndvi_change,
            'SI_Change':   si_change,
        }])[FEATURES]  # enforce column order

        prediction    = rf_model.predict(input_df)[0]
        probabilities = rf_model.predict_proba(input_df)[0]
        classes       = rf_model.classes_

        # Colored result box
        bg = PRED_COLORS.get(prediction, '#616161')
        st.markdown(
            f"""
            <div style="background:{bg};color:white;font-size:1.6rem;font-weight:700;
                        text-align:center;padding:18px;border-radius:8px;margin:12px 0;">
                {prediction}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Probability bar chart
        prob_df = pd.DataFrame({'Status': classes, 'Probability': probabilities})
        fig_prob = px.bar(
            prob_df, x='Status', y='Probability',
            color='Status',
            color_discrete_map=PRED_COLORS,
            title='Prediction Probabilities',
            labels={'Probability': 'Probability', 'Status': 'Degradation Status'},
            range_y=[0, 1],
            text=prob_df['Probability'].map('{:.1%}'.format),
        )
        fig_prob.update_traces(
            textposition='outside',
            hovertemplate='%{x}: %{y:.1%}<extra></extra>',
        )
        fig_prob.update_layout(
            height=320, showlegend=False,
            margin=dict(l=0, r=0, t=35, b=0),
        )
        st.plotly_chart(fig_prob, use_container_width=True)

        st.caption(
            "Prediction based on Random Forest classifier trained on 400 Gidabo Basin "
            "pixels. Input values represent Landsat surface reflectance measurements."
        )

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
