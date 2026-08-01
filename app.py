"""
HHS Unaccompanied Alien Children Program — Interactive Dashboard
Built with Python · Streamlit · Plotly · Pandas
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import io

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HHS UAC Program Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        background-attachment: fixed;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    /* KPI Cards */
    .kpi-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .kpi-card.blue::before   { background: linear-gradient(90deg, #4facfe, #00f2fe); }
    .kpi-card.purple::before { background: linear-gradient(90deg, #a18cd1, #fbc2eb); }
    .kpi-card.green::before  { background: linear-gradient(90deg, #43e97b, #38f9d7); }
    .kpi-card.orange::before { background: linear-gradient(90deg, #f7971e, #ffd200); }

    .kpi-icon { font-size: 2rem; margin-bottom: 8px; }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: rgba(255,255,255,0.5) !important;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff !important;
        line-height: 1.1;
    }
    .kpi-delta {
        font-size: 0.75rem;
        margin-top: 6px;
        color: rgba(255,255,255,0.4) !important;
    }
    .kpi-delta.up   { color: #43e97b !important; }
    .kpi-delta.down { color: #f8717a !important; }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin: 28px 0 14px 0;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Chart containers */
    .chart-container {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 8px;
        margin-bottom: 16px;
    }

    /* Dashboard title */
    .dash-title {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
        margin: 0;
    }
    .dash-subtitle {
        font-size: 0.88rem;
        color: rgba(255,255,255,0.5);
        margin-top: 4px;
    }
    .dash-badge {
        display: inline-block;
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        color: #000;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 10px;
    }

    /* Plotly chart background override */
    .js-plotly-plot .plotly, .js-plotly-plot .plotly div {
        border-radius: 12px;
    }

    /* Streamlit default element cleanup */
    .stMetric { display: none; }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Sidebar title styling */
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .sidebar-logo {
        font-size: 1.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }

    /* Table styling */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Separator */
    hr { border-color: rgba(255,255,255,0.08); }

    /* Slider and selectbox */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #fff !important;
        border-radius: 10px !important;
    }
    .stMultiSelect > div > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
    }
    .stDateInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #fff !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Data Loading & Cleaning ───────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(
        r"C:\Users\Dipali\OneDrive\Documents\Project 1\HHS_Unaccompanied_Alien_Children_Program.csv"
    )

    # Drop empty rows
    df.dropna(how='all', inplace=True)
    df = df[df['Date'].notna()].copy()

    # Parse dates
    df['Date'] = pd.to_datetime(df['Date'], format='%B %d, %Y', errors='coerce')
    df.dropna(subset=['Date'], inplace=True)

    # Clean numeric columns (remove commas)
    numeric_cols = [
        'Children apprehended and placed in CBP custody*',
        'Children in CBP custody',
        'Children transferred out of CBP custody',
        'Children in HHS Care',
        'Children discharged from HHS Care',
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(',', '', regex=False),
            errors='coerce'
        )

    # Rename columns for brevity
    df.rename(columns={
        'Children apprehended and placed in CBP custody*': 'Apprehended',
        'Children in CBP custody':                        'In CBP Custody',
        'Children transferred out of CBP custody':        'Transferred to HHS',
        'Children in HHS Care':                           'In HHS Care',
        'Children discharged from HHS Care':              'Discharged',
    }, inplace=True)

    # Extract time features
    df['Year']  = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Month_Name'] = df['Date'].dt.strftime('%b')
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)

    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

df_raw = load_data()

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🛡️ HHS UAC</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Program Dashboard</div>', unsafe_allow_html=True)

    st.markdown("### 🗓️ Filters")

    # Year filter
    all_years = sorted(df_raw['Year'].unique().tolist())
    selected_years = st.multiselect(
        "Select Year(s)",
        options=all_years,
        default=all_years,
    )

    # Date range
    min_date = df_raw['Date'].min().date()
    max_date = df_raw['Date'].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("---")
    st.markdown("### 📌 About")
    st.markdown(
        """
        <div style='font-size:0.78rem; color:rgba(255,255,255,0.45); line-height:1.6;'>
        Data source: U.S. Department of Health & Human Services<br><br>
        Tracks daily numbers of unaccompanied children in custody and care from 2023–2025.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Apply Filters ─────────────────────────────────────────────────────────────
df = df_raw[df_raw['Year'].isin(selected_years)].copy()

if len(date_range) == 2:
    start_d, end_d = date_range
    df = df[(df['Date'].dt.date >= start_d) & (df['Date'].dt.date <= end_d)]

# ─── Plotly Theme ──────────────────────────────────────────────────────────────
CHART_BG    = 'rgba(0,0,0,0)'
GRID_COLOR  = 'rgba(255,255,255,0.06)'
FONT_COLOR  = '#c0cce0'
FONT_FAMILY = 'Inter, sans-serif'

def base_layout(title="", height=380):
    return dict(
        title=dict(text=title, font=dict(color='#ffffff', size=15, family=FONT_FAMILY), x=0.02, y=0.97),
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=FONT_COLOR, family=FONT_FAMILY, size=12),
        height=height,
        margin=dict(l=50, r=20, t=48, b=40),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont=dict(size=11)),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont=dict(size=11)),
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(255,255,255,0.1)',
                    borderwidth=1, font=dict(size=11)),
        hovermode='x unified',
    )

# ─── KPI Calculations ──────────────────────────────────────────────────────────
total_apprehended = int(df['Apprehended'].sum())
peak_hhs          = int(df['In HHS Care'].max()) if len(df) > 0 else 0
current_hhs       = int(df.iloc[-1]['In HHS Care']) if len(df) > 0 else 0
total_discharged  = int(df['Discharged'].sum())
avg_daily_apprehended = df['Apprehended'].mean()

# Period deltas
if len(df) >= 14:
    recent    = df.tail(7)['Apprehended'].mean()
    prev      = df.iloc[-14:-7]['Apprehended'].mean()
    pct_change = ((recent - prev) / prev * 100) if prev else 0
else:
    pct_change = 0

# ─── Header ────────────────────────────────────────────────────────────────────
col_title, col_spacer = st.columns([3, 1])
with col_title:
    st.markdown('<div class="dash-badge">🔴 Live Government Data</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dash-title">HHS Unaccompanied Alien Children</div>'
        '<div class="dash-title" style="color:rgba(255,255,255,0.6);">Program Analytics Dashboard</div>'
        '<div class="dash-subtitle">U.S. Department of Health & Human Services · Daily Tracking</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card blue">
        <div class="kpi-icon">🚸</div>
        <div class="kpi-label">Total Apprehended</div>
        <div class="kpi-value">{total_apprehended:,}</div>
        <div class="kpi-delta">Children placed in CBP custody</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card purple">
        <div class="kpi-icon">🏥</div>
        <div class="kpi-label">Peak in HHS Care</div>
        <div class="kpi-value">{peak_hhs:,}</div>
        <div class="kpi-delta">Maximum single-day census</div>
    </div>""", unsafe_allow_html=True)

with k3:
    arrow = "▲" if pct_change >= 0 else "▼"
    cls   = "up" if pct_change >= 0 else "down"
    st.markdown(f"""
    <div class="kpi-card green">
        <div class="kpi-icon">📍</div>
        <div class="kpi-label">Current in HHS Care</div>
        <div class="kpi-value">{current_hhs:,}</div>
        <div class="kpi-delta {cls}">{arrow} Latest recorded count</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card orange">
        <div class="kpi-icon">✅</div>
        <div class="kpi-label">Total Discharged</div>
        <div class="kpi-value">{total_discharged:,}</div>
        <div class="kpi-delta">Children released from HHS care</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Chart Row 1: HHS Care Trend + Apprehensions vs Discharges ─────────────────
st.markdown('<div class="section-header">📈 Trend Analysis</div>', unsafe_allow_html=True)

c1, c2 = st.columns([3, 2])

with c1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig_trend = go.Figure()

    fig_trend.add_trace(go.Scatter(
        x=df['Date'], y=df['In HHS Care'],
        mode='lines',
        name='Children in HHS Care',
        line=dict(color='#4facfe', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(79,172,254,0.10)',
        hovertemplate='<b>%{y:,}</b> children<extra></extra>',
    ))

    fig_trend.add_trace(go.Scatter(
        x=df['Date'], y=df['In CBP Custody'],
        mode='lines',
        name='Children in CBP Custody',
        line=dict(color='#f7971e', width=1.8, dash='dot'),
        hovertemplate='<b>%{y:,}</b> children<extra></extra>',
    ))

    layout = base_layout("Children in Custody Over Time", height=380)
    layout['yaxis']['tickformat'] = ','
    fig_trend.update_layout(**layout)
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    # Monthly aggregation
    monthly = df.groupby('YearMonth').agg(
        Apprehended=('Apprehended', 'sum'),
        Discharged=('Discharged', 'sum'),
    ).reset_index()
    monthly = monthly.tail(24)

    fig_flow = go.Figure()
    fig_flow.add_trace(go.Bar(
        x=monthly['YearMonth'], y=monthly['Apprehended'],
        name='Monthly Apprehended', marker_color='rgba(248,113,122,0.85)',
        hovertemplate='Apprehended: <b>%{y:,}</b><extra></extra>',
    ))
    fig_flow.add_trace(go.Bar(
        x=monthly['YearMonth'], y=monthly['Discharged'],
        name='Monthly Discharged', marker_color='rgba(67,233,123,0.85)',
        hovertemplate='Discharged: <b>%{y:,}</b><extra></extra>',
    ))
    layout2 = base_layout("Monthly Intake vs Discharge", height=380)
    layout2['barmode'] = 'group'
    layout2['xaxis']['tickangle'] = -40
    layout2['xaxis']['nticks'] = 8
    fig_flow.update_layout(**layout2)
    st.plotly_chart(fig_flow, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Chart Row 2: Year-over-Year + Daily Transfer Rate ─────────────────────────
st.markdown('<div class="section-header">📊 Year-over-Year Comparison</div>', unsafe_allow_html=True)

c3, c4 = st.columns([2, 3])

with c3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    yoy = df.groupby('Year').agg(
        Apprehended=('Apprehended', 'sum'),
        Discharged=('Discharged', 'sum'),
        Transferred=('Transferred to HHS', 'sum'),
    ).reset_index()

    fig_yoy = go.Figure()
    colors = ['#4facfe', '#43e97b', '#f7971e']
    for col, color in zip(['Apprehended', 'Discharged', 'Transferred'], colors):
        fig_yoy.add_trace(go.Bar(
            x=yoy['Year'].astype(str), y=yoy[col],
            name=col, marker_color=color,
            hovertemplate=f'{col}: <b>%{{y:,}}</b><extra></extra>',
        ))

    layout3 = base_layout("Totals by Year", height=340)
    layout3['barmode'] = 'group'
    fig_yoy.update_layout(**layout3)
    st.plotly_chart(fig_yoy, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

with c4:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    # Rolling 7-day average
    df_roll = df.copy()
    df_roll['Roll_Apprehended'] = df_roll['Apprehended'].rolling(7, min_periods=1).mean()
    df_roll['Roll_Discharged']  = df_roll['Discharged'].rolling(7, min_periods=1).mean()

    fig_roll = go.Figure()
    fig_roll.add_trace(go.Scatter(
        x=df_roll['Date'], y=df_roll['Roll_Apprehended'],
        mode='lines', name='7-Day Avg Apprehended',
        line=dict(color='#f8717a', width=2.5),
        hovertemplate='Avg Apprehended: <b>%{y:.1f}</b><extra></extra>',
    ))
    fig_roll.add_trace(go.Scatter(
        x=df_roll['Date'], y=df_roll['Roll_Discharged'],
        mode='lines', name='7-Day Avg Discharged',
        line=dict(color='#43e97b', width=2.5),
        hovertemplate='Avg Discharged: <b>%{y:.1f}</b><extra></extra>',
    ))
    fig_roll.add_trace(go.Scatter(
        x=df_roll['Date'], y=df_roll['Transferred to HHS'],
        mode='lines', name='Transferred to HHS',
        line=dict(color='#a18cd1', width=1.5, dash='dot'),
        opacity=0.7,
        hovertemplate='Transferred: <b>%{y:,}</b><extra></extra>',
    ))

    layout4 = base_layout("7-Day Rolling Averages — All Metrics", height=340)
    fig_roll.update_layout(**layout4)
    st.plotly_chart(fig_roll, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Monthly Heatmap ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🗓️ Monthly Heatmap — Avg Children in HHS Care</div>', unsafe_allow_html=True)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
heatmap_data = df.groupby(['Year','Month'])['In HHS Care'].mean().reset_index()
heatmap_pivot = heatmap_data.pivot(index='Year', columns='Month', values='In HHS Care')
heatmap_pivot.columns = [month_names[m-1] for m in heatmap_pivot.columns]

fig_heat = go.Figure(data=go.Heatmap(
    z=heatmap_pivot.values,
    x=heatmap_pivot.columns.tolist(),
    y=heatmap_pivot.index.astype(str).tolist(),
    colorscale=[
        [0.0, '#0f0c29'],
        [0.3, '#302b63'],
        [0.6, '#4facfe'],
        [1.0, '#00f2fe'],
    ],
    showscale=True,
    hovertemplate='<b>%{y} %{x}</b><br>Avg in HHS Care: %{z:,.0f}<extra></extra>',
    colorbar=dict(
        tickfont=dict(color=FONT_COLOR, family=FONT_FAMILY),
        outlinecolor='rgba(255,255,255,0.1)',
    ),
))

layout5 = base_layout("", height=200)
layout5['margin'] = dict(l=50, r=60, t=20, b=40)
layout5.pop('xaxis', None)
layout5.pop('yaxis', None)
fig_heat.update_layout(**layout5)
fig_heat.update_xaxes(tickfont=dict(color=FONT_COLOR, size=12), side='bottom')
fig_heat.update_yaxes(tickfont=dict(color=FONT_COLOR, size=12))
st.plotly_chart(fig_heat, use_container_width=True, config={'displayModeBar': False})
st.markdown('</div>', unsafe_allow_html=True)

# ─── Stats Summary ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Statistical Summary</div>', unsafe_allow_html=True)

s1, s2, s3, s4, s5 = st.columns(5)
stat_cols = [
    (s1, "Avg Daily Apprehended",  f"{df['Apprehended'].mean():.1f}",  "Per day (filtered period)"),
    (s2, "Avg Daily Discharged",   f"{df['Discharged'].mean():.1f}",   "Per day (filtered period)"),
    (s3, "Avg In CBP Custody",     f"{df['In CBP Custody'].mean():.0f}","Daily average"),
    (s4, "Max In CBP Custody",     f"{int(df['In CBP Custody'].max()):,}","Single-day peak"),
    (s5, "Total Days Tracked",     f"{len(df):,}",                     "Data points in period"),
]
for col, label, val, note in stat_cols:
    with col:
        st.markdown(f"""
        <div class="kpi-card blue" style="padding:14px 16px;">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="font-size:1.5rem;">{val}</div>
            <div class="kpi-delta">{note}</div>
        </div>""", unsafe_allow_html=True)

# ─── Data Table ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">🗃️ Raw Data Table</div>', unsafe_allow_html=True)

with st.expander("📂 View & Download Data", expanded=False):
    display_df = df[['Date','Apprehended','In CBP Custody','Transferred to HHS','In HHS Care','Discharged']].copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%B %d, %Y')

    st.dataframe(
        display_df,
        use_container_width=True,
        height=320,
    )

    csv_bytes = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv_bytes,
        file_name="HHS_UAC_filtered.csv",
        mime="text/csv",
    )

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; font-size:0.75rem; color:rgba(255,255,255,0.2); padding: 20px 0;'>
    🛡️ HHS Unaccompanied Alien Children Program Dashboard &nbsp;·&nbsp;
    Data: U.S. Dept. of Health & Human Services &nbsp;·&nbsp;
    Built with Python · Streamlit · Plotly
</div>
""", unsafe_allow_html=True)
