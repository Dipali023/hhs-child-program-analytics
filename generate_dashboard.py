"""
generate_dashboard.py
Reads the HHS UAC CSV and generates a beautiful standalone HTML dashboard.
Uses ONLY Python standard library — no pip installs needed.
"""
import csv
import json
import os
from datetime import datetime

# ─── Read & Clean CSV ──────────────────────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), "HHS_Unaccompanied_Alien_Children_Program.csv")
OUT_PATH   = os.path.join(os.path.dirname(__file__), "dashboard.html")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.html")

rows = []
with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        date_str = row.get('Date', '').strip()
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            continue

        def clean(v):
            try:
                return int(v.replace(',', '').strip())
            except:
                return 0

        rows.append({
            "date": dt.strftime("%Y-%m-%d"),
            "display_date": dt.strftime("%b %d, %Y"),
            "year": dt.year,
            "month": dt.month,
            "apprehended":  clean(row.get('Children apprehended and placed in CBP custody*', '0')),
            "in_cbp":       clean(row.get('Children in CBP custody', '0')),
            "transferred":  clean(row.get('Children transferred out of CBP custody', '0')),
            "in_hhs":       clean(row.get('Children in HHS Care', '0')),
            "discharged":   clean(row.get('Children discharged from HHS Care', '0')),
        })

rows.sort(key=lambda r: r["date"])

# ─── Compute KPIs ──────────────────────────────────────────────────────────────
total_apprehended = sum(r["apprehended"] for r in rows)
total_discharged  = sum(r["discharged"]  for r in rows)
peak_hhs          = max(r["in_hhs"]      for r in rows)
current_hhs       = rows[-1]["in_hhs"]   if rows else 0
total_records     = len(rows)

# ─── Compute Monthly Aggregates ────────────────────────────────────────────────
monthly = {}
for r in rows:
    key = f"{r['year']}-{r['month']:02d}"
    if key not in monthly:
        monthly[key] = {"label": datetime(r['year'], r['month'], 1).strftime("%b %Y"),
                        "apprehended": 0, "discharged": 0, "in_hhs_sum": 0, "count": 0}
    monthly[key]["apprehended"] += r["apprehended"]
    monthly[key]["discharged"]  += r["discharged"]
    monthly[key]["in_hhs_sum"]  += r["in_hhs"]
    monthly[key]["count"]       += 1

monthly_sorted = sorted(monthly.values(), key=lambda x: x["label"])
monthly_labels    = [m["label"]      for m in monthly_sorted]
monthly_appreh    = [m["apprehended"] for m in monthly_sorted]
monthly_discharged= [m["discharged"]  for m in monthly_sorted]
monthly_avg_hhs   = [round(m["in_hhs_sum"] / m["count"]) if m["count"] else 0 for m in monthly_sorted]

# Year totals
year_totals = {}
for r in rows:
    y = str(r["year"])
    if y not in year_totals:
        year_totals[y] = {"apprehended": 0, "discharged": 0, "transferred": 0}
    year_totals[y]["apprehended"] += r["apprehended"]
    year_totals[y]["discharged"]  += r["discharged"]
    year_totals[y]["transferred"] += r["transferred"]

years_list        = sorted(year_totals.keys())
yr_apprehended    = [year_totals[y]["apprehended"] for y in years_list]
yr_discharged     = [year_totals[y]["discharged"]  for y in years_list]
yr_transferred    = [year_totals[y]["transferred"] for y in years_list]

# Rolling 7-day average
def rolling_avg(data, key, n=7):
    out = []
    for i in range(len(data)):
        window = data[max(0, i-n+1):i+1]
        out.append(round(sum(r[key] for r in window) / len(window), 1))
    return out

roll_appreh = rolling_avg(rows, "apprehended")
roll_disch  = rolling_avg(rows, "discharged")

# Heatmap: year × month grid
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
heatmap_years = sorted(set(r["year"] for r in rows))
heatmap_z = []
heatmap_y = []
for y in heatmap_years:
    row_data = []
    for m in range(1, 13):
        vals = [r["in_hhs"] for r in rows if r["year"] == y and r["month"] == m]
        row_data.append(round(sum(vals)/len(vals)) if vals else None)
    heatmap_z.append(row_data)
    heatmap_y.append(str(y))

# Embed all series as JSON
dates      = [r["date"]        for r in rows]
in_hhs     = [r["in_hhs"]     for r in rows]
in_cbp     = [r["in_cbp"]     for r in rows]
apprehended= [r["apprehended"] for r in rows]
discharged = [r["discharged"]  for r in rows]
transferred= [r["transferred"] for r in rows]

data_json = json.dumps({
    "dates": dates,
    "in_hhs": in_hhs,
    "in_cbp": in_cbp,
    "apprehended": apprehended,
    "discharged": discharged,
    "transferred": transferred,
    "roll_appreh": roll_appreh,
    "roll_disch": roll_disch,
    "monthly_labels": monthly_labels,
    "monthly_appreh": monthly_appreh,
    "monthly_disch": monthly_discharged,
    "monthly_avg_hhs": monthly_avg_hhs,
    "years_list": years_list,
    "yr_apprehended": yr_apprehended,
    "yr_discharged": yr_discharged,
    "yr_transferred": yr_transferred,
    "heatmap_z": heatmap_z,
    "heatmap_y": heatmap_y,
    "heatmap_x": MONTHS,
    "rows": rows,
})

# ─── Build HTML ────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>HHS Unaccompanied Alien Children Program — Dashboard</title>
<meta name="description" content="Interactive analytics dashboard tracking daily HHS Unaccompanied Alien Children Program statistics from 2023 to 2025."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#f0f4f8;
  --surface:#ffffff;
  --border:#e2e8f0;
  --text:#1e293b;
  --muted:#64748b;
  --blue:#2563eb;
  --blue-light:#dbeafe;
  --cyan:#0891b2;
  --green:#059669;
  --green-light:#d1fae5;
  --purple:#7c3aed;
  --purple-light:#ede9fe;
  --orange:#d97706;
  --orange-light:#fef3c7;
  --red:#dc2626;
  --font:'Inter',sans-serif;
}}
html{{scroll-behavior:smooth}}
body{{
  font-family:var(--font);
  background:#f0f4f8;
  color:var(--text);
  min-height:100vh;
}}

/* ── Sidebar ── */
.layout{{display:flex;min-height:100vh}}
.sidebar{{
  width:240px;min-width:240px;
  background:#ffffff;
  border-right:1px solid var(--border);
  padding:28px 20px;
  position:sticky;top:0;height:100vh;overflow-y:auto;
  box-shadow:2px 0 12px rgba(0,0,0,0.06);
}}
.sidebar-logo{{
  font-size:1.4rem;font-weight:900;
  color:var(--blue);
  margin-bottom:4px;
}}
.sidebar-sub{{font-size:0.7rem;color:var(--muted);font-weight:500;text-transform:uppercase;letter-spacing:1px;margin-bottom:28px}}
.sidebar-section{{font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin:20px 0 10px}}
.nav-item{{
  display:flex;align-items:center;gap:10px;
  padding:9px 12px;border-radius:10px;
  font-size:0.82rem;font-weight:500;color:#475569;
  cursor:pointer;transition:all 0.2s;margin-bottom:3px;
  text-decoration:none;
}}
.nav-item:hover,.nav-item.active{{
  background:var(--blue-light);
  color:var(--blue);
}}
.nav-item.active{{border-left:3px solid var(--blue);padding-left:9px;font-weight:600}}
.nav-icon{{font-size:1rem;width:20px;text-align:center}}
hr.sidebar-divider{{border:none;border-top:1px solid var(--border);margin:20px 0}}
.sidebar-stat{{background:#f8fafc;border:1px solid var(--border);border-radius:10px;padding:12px;margin-bottom:8px}}
.sidebar-stat-label{{font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}}
.sidebar-stat-val{{font-size:1.1rem;font-weight:700;color:var(--text)}}

/* ── Main ── */
.main{{flex:1;padding:32px 36px;overflow-x:hidden;background:#f0f4f8}}
.badge{{
  display:inline-block;
  background:var(--blue);
  color:#fff;font-size:0.62rem;font-weight:800;
  text-transform:uppercase;letter-spacing:1.2px;
  padding:4px 14px;border-radius:20px;margin-bottom:12px;
}}
.page-title{{font-size:2rem;font-weight:900;line-height:1.1;color:#0f172a}}
.page-title span{{color:#64748b}}
.page-sub{{font-size:0.85rem;color:var(--muted);margin-top:6px;margin-bottom:32px}}

/* ── KPI Cards ── */
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px}}
.kpi-card{{
  background:#ffffff;
  border:1px solid var(--border);
  border-radius:16px;padding:22px 20px;
  position:relative;overflow:hidden;
  transition:transform 0.2s,box-shadow 0.2s;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);
  cursor:default;
}}
.kpi-card:hover{{transform:translateY(-4px);box-shadow:0 16px 40px rgba(0,0,0,0.12)}}
.kpi-card::before{{
  content:'';position:absolute;
  top:0;left:0;right:0;height:4px;border-radius:16px 16px 0 0;
}}
.kpi-card.blue::before  {{background:var(--blue)}}
.kpi-card.purple::before{{background:var(--purple)}}
.kpi-card.green::before {{background:var(--green)}}
.kpi-card.orange::before{{background:var(--orange)}}
.kpi-icon-wrap{{
  width:44px;height:44px;border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:1.4rem;margin-bottom:14px;
}}
.kpi-card.blue  .kpi-icon-wrap{{background:var(--blue-light)}}
.kpi-card.purple .kpi-icon-wrap{{background:var(--purple-light)}}
.kpi-card.green  .kpi-icon-wrap{{background:var(--green-light)}}
.kpi-card.orange .kpi-icon-wrap{{background:var(--orange-light)}}
.kpi-label{{font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;color:var(--muted);margin-bottom:6px}}
.kpi-value{{font-size:2rem;font-weight:900;color:#0f172a;line-height:1}}
.kpi-note{{font-size:0.72rem;color:var(--muted);margin-top:6px}}

/* ── Section headers ── */
.section-hdr{{
  font-size:0.9rem;font-weight:700;color:#0f172a;
  display:flex;align-items:center;gap:8px;
  margin:32px 0 14px;padding-bottom:12px;
  border-bottom:2px solid var(--border);
}}
.section-hdr span{{color:var(--blue)}}

/* ── Chart wrappers ── */
.chart-row{{display:grid;gap:16px;margin-bottom:16px}}
.chart-row.col-3-2{{grid-template-columns:3fr 2fr}}
.chart-row.col-2-3{{grid-template-columns:2fr 3fr}}
.chart-row.col-1{{grid-template-columns:1fr}}
.chart-row.col-2{{grid-template-columns:1fr 1fr}}
.chart-box{{
  background:#ffffff;
  border:1px solid var(--border);
  border-radius:16px;padding:16px;
  box-shadow:0 1px 3px rgba(0,0,0,0.05);
}}

/* ── Stats row ── */
.stats-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:32px}}
.stat-mini{{
  background:#ffffff;border:1px solid var(--border);
  border-radius:12px;padding:16px;text-align:center;
  box-shadow:0 1px 3px rgba(0,0,0,0.05);
}}
.stat-mini-label{{font-size:0.62rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}}
.stat-mini-val{{font-size:1.3rem;font-weight:800;color:#0f172a}}

/* ── Table ── */
.table-wrap{{overflow-x:auto;border-radius:12px;border:1px solid var(--border)}}
table{{width:100%;border-collapse:collapse;font-size:0.8rem}}
thead tr{{background:#f1f5f9}}
thead th{{padding:12px 14px;text-align:left;font-weight:700;color:#475569;
  font-size:0.72rem;text-transform:uppercase;letter-spacing:0.8px;border-bottom:1px solid var(--border)}}
tbody tr{{border-bottom:1px solid #f1f5f9;transition:background 0.15s}}
tbody tr:hover{{background:#f8fafc}}
tbody td{{padding:10px 14px;color:var(--text)}}
tbody td:first-child{{color:var(--blue);font-weight:600}}

/* ── Download btn ── */
.btn{{
  display:inline-flex;align-items:center;gap:8px;
  background:var(--blue);
  color:#fff;font-weight:700;font-size:0.8rem;
  padding:10px 22px;border-radius:10px;
  border:none;cursor:pointer;text-decoration:none;
  transition:background 0.2s,transform 0.2s;margin-top:16px;
}}
.btn:hover{{background:#1d4ed8;transform:translateY(-1px)}}

/* ── Footer ── */
.footer{{text-align:center;font-size:0.72rem;color:#94a3b8;padding:40px 0 20px;border-top:1px solid var(--border);margin-top:16px}}

/* ── Filter bar ── */
.filter-bar{{
  display:flex;align-items:center;gap:14px;
  background:#ffffff;border:1px solid var(--border);
  border-radius:12px;padding:12px 18px;margin-bottom:28px;
  flex-wrap:wrap;box-shadow:0 1px 3px rgba(0,0,0,0.05);
}}
.filter-label{{font-size:0.72rem;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:1px}}
.year-btn{{
  padding:6px 16px;border-radius:8px;border:1px solid var(--border);
  background:#f8fafc;color:#475569;font-size:0.82rem;
  cursor:pointer;transition:all 0.18s;font-family:var(--font);font-weight:500;
}}
.year-btn.active{{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:700}}
.year-btn:hover:not(.active){{border-color:var(--blue);color:var(--blue);background:var(--blue-light)}}

@media(max-width:900px){{
  .sidebar{{display:none}}
  .kpi-grid{{grid-template-columns:repeat(2,1fr)}}
  .chart-row.col-3-2,.chart-row.col-2-3{{grid-template-columns:1fr}}
  .stats-grid{{grid-template-columns:repeat(2,1fr)}}
  .main{{padding:20px}}
}}
</style>
</head>
<body>
<div class="layout">

<!-- ── Sidebar ── -->
<aside class="sidebar">
  <div class="sidebar-logo">🛡️ HHS UAC</div>
  <div class="sidebar-sub">Program Analytics</div>

  <div class="sidebar-section">Navigation</div>
  <a class="nav-item active" href="#overview"><span class="nav-icon">📊</span> Overview</a>
  <a class="nav-item" href="#trends"><span class="nav-icon">📈</span> Trend Analysis</a>
  <a class="nav-item" href="#comparison"><span class="nav-icon">📅</span> Year Comparison</a>
  <a class="nav-item" href="#heatmap"><span class="nav-icon">🗓️</span> Heatmap</a>
  <a class="nav-item" href="#data"><span class="nav-icon">🗃️</span> Data Table</a>

  <hr class="sidebar-divider"/>
  <div class="sidebar-section">Quick Stats</div>
  <div class="sidebar-stat">
    <div class="sidebar-stat-label">Total Records</div>
    <div class="sidebar-stat-val">{total_records:,}</div>
  </div>
  <div class="sidebar-stat">
    <div class="sidebar-stat-label">Date Range</div>
    <div class="sidebar-stat-val" style="font-size:0.85rem;">Jan 2023 – Dec 2025</div>
  </div>
  <div class="sidebar-stat">
    <div class="sidebar-stat-label">Peak in HHS Care</div>
    <div class="sidebar-stat-val">{peak_hhs:,}</div>
  </div>

  <hr class="sidebar-divider"/>
  <div style="font-size:0.7rem;color:#94a3b8;line-height:1.6;">
    Source: U.S. Dept. of Health &amp; Human Services<br/>
    Data updated daily by HHS/ACF
  </div>
</aside>

<!-- ── Main Content ── -->
<main class="main">

  <!-- Header -->
  <div id="overview">
    <div class="badge">🔴 Official Government Data</div>
    <div class="page-title">HHS Unaccompanied Alien<br/><span>Children Program Dashboard</span></div>
    <div class="page-sub">U.S. Department of Health &amp; Human Services &nbsp;·&nbsp; Daily Tracking 2023–2025 &nbsp;·&nbsp; {total_records:,} data points</div>
  </div>

  <!-- Filter Bar -->
  <div class="filter-bar">
    <span class="filter-label">Filter by Year:</span>
    <button class="year-btn active" onclick="filterYear('all',this)" id="btn-all">All Years</button>
    <button class="year-btn" onclick="filterYear(2023,this)" id="btn-2023">2023</button>
    <button class="year-btn" onclick="filterYear(2024,this)" id="btn-2024">2024</button>
    <button class="year-btn" onclick="filterYear(2025,this)" id="btn-2025">2025</button>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi-card blue">
      <div class="kpi-icon-wrap">🚸</div>
      <div class="kpi-label">Total Apprehended</div>
      <div class="kpi-value" id="kpi-appreh">{total_apprehended:,}</div>
      <div class="kpi-note">Children placed in CBP custody</div>
    </div>
    <div class="kpi-card purple">
      <div class="kpi-icon-wrap">🏥</div>
      <div class="kpi-label">Peak in HHS Care</div>
      <div class="kpi-value" id="kpi-peak">{peak_hhs:,}</div>
      <div class="kpi-note">Maximum single-day census</div>
    </div>
    <div class="kpi-card green">
      <div class="kpi-icon-wrap">📍</div>
      <div class="kpi-label">Current in HHS Care</div>
      <div class="kpi-value" id="kpi-current">{current_hhs:,}</div>
      <div class="kpi-note">Latest recorded count</div>
    </div>
    <div class="kpi-card orange">
      <div class="kpi-icon-wrap">✅</div>
      <div class="kpi-label">Total Discharged</div>
      <div class="kpi-value" id="kpi-disch">{total_discharged:,}</div>
      <div class="kpi-note">Released from HHS care</div>
    </div>
  </div>

  <!-- Trend Charts -->
  <div id="trends">
    <div class="section-hdr"><span>📈</span> Trend Analysis</div>
    <div class="chart-row col-3-2">
      <div class="chart-box"><div id="chart-hhs-trend" style="height:360px"></div></div>
      <div class="chart-box"><div id="chart-monthly-bar" style="height:360px"></div></div>
    </div>
  </div>

  <!-- Year Comparison -->
  <div id="comparison">
    <div class="section-hdr"><span>📊</span> Year-over-Year Comparison</div>
    <div class="chart-row col-2-3">
      <div class="chart-box"><div id="chart-yoy" style="height:320px"></div></div>
      <div class="chart-box"><div id="chart-rolling" style="height:320px"></div></div>
    </div>
  </div>

  <!-- Heatmap -->
  <div id="heatmap">
    <div class="section-hdr"><span>🗓️</span> Monthly Heatmap — Avg Children in HHS Care</div>
    <div class="chart-row col-1">
      <div class="chart-box"><div id="chart-heatmap" style="height:200px"></div></div>
    </div>
  </div>

  <!-- Stats Row -->
  <div class="section-hdr"><span>📋</span> Statistical Summary</div>
  <div class="stats-grid" id="stats-grid">
    <!-- populated by JS -->
  </div>

  <!-- Data Table -->
  <div id="data">
    <div class="section-hdr"><span>🗃️</span> Raw Data Table</div>
    <div class="chart-box">
      <div class="table-wrap">
        <table id="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Apprehended</th>
              <th>In CBP Custody</th>
              <th>Transferred to HHS</th>
              <th>In HHS Care</th>
              <th>Discharged</th>
            </tr>
          </thead>
          <tbody id="table-body"></tbody>
        </table>
      </div>
      <button class="btn" onclick="downloadCSV()" id="download-btn">⬇️ Download CSV</button>
    </div>
  </div>

  <div class="footer">🛡️ HHS Unaccompanied Alien Children Program Dashboard &nbsp;·&nbsp; Data: U.S. Dept. of Health &amp; Human Services &nbsp;·&nbsp; Built with Python &amp; Plotly.js</div>
</main>
</div>

<script>
const RAW = {data_json};

// ── Plotly theme base ──────────────────────────────────────────────────
const BG='rgba(0,0,0,0)',GRID='#e2e8f0',FC='#475569',FF="Inter, sans-serif";
function baseLayout(title,h=360){{
  return {{
    title:{{text:title,font:{{color:'#0f172a',size:14,family:FF,weight:700}},x:0.02,y:0.97}},
    paper_bgcolor:BG,plot_bgcolor:BG,height:h,
    font:{{color:FC,family:FF,size:11}},
    margin:{{l:50,r:20,t:46,b:46}},
    xaxis:{{gridcolor:GRID,zerolinecolor:GRID,tickfont:{{size:10,color:FC}}}},
    yaxis:{{gridcolor:GRID,zerolinecolor:GRID,tickfont:{{size:10,color:FC}}}},
    legend:{{bgcolor:'rgba(255,255,255,0.9)',bordercolor:'#cbd5e1',borderwidth:1,font:{{size:10,color:FC}}}},
    hovermode:'x unified',
    hoverlabel:{{bgcolor:'#ffffff',bordercolor:'#cbd5e1',font:{{color:'#0f172a',family:FF}}}},
  }};
}}
const CFG={{displayModeBar:false,responsive:true}};

// ── State ──────────────────────────────────────────────────────────────
let activeYear='all';

// ── Filter function ────────────────────────────────────────────────────
function filterYear(year, btn){{
  activeYear=year;
  document.querySelectorAll('.year-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderAll();
}}

function getFiltered(){{
  if(activeYear==='all') return RAW;
  const idx=RAW.dates.map((d,i)=>new Date(d).getFullYear()===activeYear?i:-1).filter(i=>i>=0);
  const pick=(arr)=>idx.map(i=>arr[i]);
  return {{
    dates:pick(RAW.dates),
    in_hhs:pick(RAW.in_hhs),
    in_cbp:pick(RAW.in_cbp),
    apprehended:pick(RAW.apprehended),
    discharged:pick(RAW.discharged),
    transferred:pick(RAW.transferred),
    roll_appreh:pick(RAW.roll_appreh),
    roll_disch:pick(RAW.roll_disch),
    rows:RAW.rows.filter(r=>r.year===activeYear),
  }};
}}

// ── Render all ─────────────────────────────────────────────────────────
function renderAll(){{
  const D=getFiltered();
  renderHHSTrend(D);
  renderMonthlyBar(D);
  renderRolling(D);
  renderYoY(D);
  renderHeatmap();
  renderStats(D);
  renderTable(D);
  updateKPIs(D);
}}

// ── KPI update ─────────────────────────────────────────────────────────
function fmt(n){{return n.toLocaleString()}}
function updateKPIs(D){{
  const appreh=D.apprehended.reduce((a,b)=>a+b,0);
  const disch=D.discharged.reduce((a,b)=>a+b,0);
  const peak=Math.max(...D.in_hhs);
  const current=D.in_hhs.length?D.in_hhs[D.in_hhs.length-1]:0;
  document.getElementById('kpi-appreh').textContent=fmt(appreh);
  document.getElementById('kpi-peak').textContent=fmt(peak);
  document.getElementById('kpi-current').textContent=fmt(current);
  document.getElementById('kpi-disch').textContent=fmt(disch);
}}

// ── Chart 1: HHS Care Trend ────────────────────────────────────────────
function renderHHSTrend(D){{
  const traces=[
    {{x:D.dates,y:D.in_hhs,mode:'lines',name:'In HHS Care',
      line:{{color:'#2563eb',width:2.5}},fill:'tozeroy',fillcolor:'rgba(37,99,235,0.08)',
      hovertemplate:'<b>%{{y:,}}</b> in HHS Care<extra></extra>'}},
    {{x:D.dates,y:D.in_cbp,mode:'lines',name:'In CBP Custody',
      line:{{color:'#d97706',width:1.8,dash:'dot'}},
      hovertemplate:'<b>%{{y:,}}</b> in CBP<extra></extra>'}},
  ];
  const layout={{...baseLayout('Daily Children in Custody',360)}};
  layout.yaxis.tickformat=',';
  Plotly.react('chart-hhs-trend',traces,layout,CFG);
}}

// ── Chart 2: Monthly Intake vs Discharge ───────────────────────────────
function renderMonthlyBar(D){{
  const monthly={{}};
  (D.rows||RAW.rows.filter(r=>activeYear==='all'||r.year===activeYear)).forEach(r=>{{
    const key=r.date.substring(0,7);
    if(!monthly[key])monthly[key]={{label:key,appreh:0,disch:0}};
    monthly[key].appreh+=r.apprehended;
    monthly[key].disch+=r.discharged;
  }});
  const sorted=Object.values(monthly).sort((a,b)=>a.label.localeCompare(b.label));
  const labels=sorted.map(m=>m.label);
  const appreh=sorted.map(m=>m.appreh);
  const disch=sorted.map(m=>m.disch);
  const traces=[
    {{x:labels,y:appreh,type:'bar',name:'Apprehended',marker:{{color:'#ef4444'}},
      hovertemplate:'Apprehended: <b>%{{y:,}}</b><extra></extra>'}},
    {{x:labels,y:disch,type:'bar',name:'Discharged',marker:{{color:'#10b981'}},
      hovertemplate:'Discharged: <b>%{{y:,}}</b><extra></extra>'}},
  ];
  const layout={{...baseLayout('Monthly Intake vs Discharge',360),barmode:'group'}};
  layout.xaxis.tickangle=-40;layout.xaxis.nticks=8;
  Plotly.react('chart-monthly-bar',traces,layout,CFG);
}}

// ── Chart 3: Year-over-Year ────────────────────────────────────────────
function renderYoY(D){{
  const yt={{}};
  (D.rows||RAW.rows).forEach(r=>{{
    const y=String(r.year);
    if(!yt[y])yt[y]={{a:0,d:0,t:0}};
    yt[y].a+=r.apprehended;yt[y].d+=r.discharged;yt[y].t+=r.transferred;
  }});
  const ys=Object.keys(yt).sort();
  const traces=[
    {{x:ys,y:ys.map(y=>yt[y].a),type:'bar',name:'Apprehended',marker:{{color:'#2563eb'}},
      hovertemplate:'Apprehended: <b>%{{y:,}}</b><extra></extra>'}},
    {{x:ys,y:ys.map(y=>yt[y].d),type:'bar',name:'Discharged',marker:{{color:'#10b981'}},
      hovertemplate:'Discharged: <b>%{{y:,}}</b><extra></extra>'}},
    {{x:ys,y:ys.map(y=>yt[y].t),type:'bar',name:'Transferred to HHS',marker:{{color:'#d97706'}},
      hovertemplate:'Transferred: <b>%{{y:,}}</b><extra></extra>'}},
  ];
  const layout={{...baseLayout('Totals by Year',320),barmode:'group'}};
  Plotly.react('chart-yoy',traces,layout,CFG);
}}

// ── Chart 4: Rolling Averages ──────────────────────────────────────────
function renderRolling(D){{
  const traces=[
    {{x:D.dates,y:D.roll_appreh,mode:'lines',name:'7-Day Avg Apprehended',
      line:{{color:'#ef4444',width:2.5}},
      hovertemplate:'Avg Apprehended: <b>%{{y:.1f}}</b><extra></extra>'}},
    {{x:D.dates,y:D.roll_disch,mode:'lines',name:'7-Day Avg Discharged',
      line:{{color:'#10b981',width:2.5}},
      hovertemplate:'Avg Discharged: <b>%{{y:.1f}}</b><extra></extra>'}},
    {{x:D.dates,y:D.transferred,mode:'lines',name:'Transferred to HHS',
      line:{{color:'#8b5cf6',width:1.5,dash:'dot'}},opacity:0.7,
      hovertemplate:'Transferred: <b>%{{y:,}}</b><extra></extra>'}},
  ];
  const layout={{...baseLayout('7-Day Rolling Averages',320)}};
  Plotly.react('chart-rolling',traces,layout,CFG);
}}

// ── Chart 5: Heatmap ───────────────────────────────────────────────────
function renderHeatmap(){{
  const traces=[{{
    type:'heatmap',z:RAW.heatmap_z,x:RAW.heatmap_x,y:RAW.heatmap_y,
    colorscale:[[0,'#eff6ff'],[0.3,'#93c5fd'],[0.6,'#2563eb'],[1,'#1e3a8a']],
    showscale:true,
    colorbar:{{tickfont:{{color:FC,family:FF}},outlinecolor:'#cbd5e1'}},
    hovertemplate:'<b>%{{y}} %{{x}}</b><br>Avg in HHS Care: %{{z:,}}<extra></extra>',
  }}];
  const layout={{
    paper_bgcolor:BG,plot_bgcolor:BG,height:200,
    font:{{color:FC,family:FF,size:11}},
    margin:{{l:50,r:60,t:20,b:40}},
    xaxis:{{tickfont:{{color:FC,size:11}}}},
    yaxis:{{tickfont:{{color:FC,size:11}}}},
    hoverlabel:{{bgcolor:'#ffffff',bordercolor:'#cbd5e1',font:{{color:'#0f172a',family:FF}}}},
  }};
  Plotly.react('chart-heatmap',traces,layout,CFG);
}}

// ── Stats ──────────────────────────────────────────────────────────────
function renderStats(D){{
  const avg=(arr)=>arr.length?arr.reduce((a,b)=>a+b,0)/arr.length:0;
  const stats=[
    ['Avg Daily Apprehended', avg(D.apprehended).toFixed(1)],
    ['Avg Daily Discharged',  avg(D.discharged).toFixed(1)],
    ['Avg In CBP Custody',    Math.round(avg(D.in_cbp)).toLocaleString()],
    ['Max In CBP Custody',    Math.max(...D.in_cbp).toLocaleString()],
    ['Days Tracked',          D.dates.length.toLocaleString()],
  ];
  document.getElementById('stats-grid').innerHTML=stats.map(([l,v])=>`
    <div class="stat-mini">
      <div class="stat-mini-label">${{l}}</div>
      <div class="stat-mini-val">${{v}}</div>
    </div>`).join('');
}}

// ── Table ──────────────────────────────────────────────────────────────
function renderTable(D){{
  const rows=(D.rows||RAW.rows).slice().reverse().slice(0,100);
  document.getElementById('table-body').innerHTML=rows.map(r=>`
    <tr>
      <td>${{r.display_date}}</td>
      <td>${{r.apprehended.toLocaleString()}}</td>
      <td>${{r.in_cbp.toLocaleString()}}</td>
      <td>${{r.transferred.toLocaleString()}}</td>
      <td>${{r.in_hhs.toLocaleString()}}</td>
      <td>${{r.discharged.toLocaleString()}}</td>
    </tr>`).join('');
}}

// ── CSV Download ───────────────────────────────────────────────────────
function downloadCSV(){{
  const D=getFiltered();
  const rows=D.rows||RAW.rows;
  const hdr='Date,Apprehended,In CBP Custody,Transferred to HHS,In HHS Care,Discharged\\n';
  const body=rows.map(r=>`${{r.display_date}},${{r.apprehended}},${{r.in_cbp}},${{r.transferred}},${{r.in_hhs}},${{r.discharged}}`).join('\\n');
  const blob=new Blob([hdr+body],{{type:'text/csv'}});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='HHS_UAC_filtered.csv';
  a.click();
}}

// ── Nav highlight on scroll ────────────────────────────────────────────
const sections=['overview','trends','comparison','heatmap','data'];
window.addEventListener('scroll',()=>{{
  const scrollY=window.scrollY+120;
  sections.forEach(id=>{{
    const el=document.getElementById(id);
    if(!el)return;
    if(scrollY>=el.offsetTop && scrollY<el.offsetTop+el.offsetHeight){{
      document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
      const navEl=document.querySelector(`.nav-item[href="#${{id}}"]`);
      if(navEl)navEl.classList.add('active');
    }}
  }});
}},{{passive:true}});

// ── Init ───────────────────────────────────────────────────────────────
renderAll();
</script>
</body>
</html>"""

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard generated successfully: {OUT_PATH}")
print(f"Total records processed: {total_records}")
