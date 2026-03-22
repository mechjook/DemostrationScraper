"""
Etapa 6 — DASHBOARD
Genera dashboard HTML interactivo con Chart.js.
Incluye gráficos de evolución temporal, KPIs, tablas y filtros.
"""

import os
import json
from datetime import datetime

import pandas as pd
from jinja2 import Template


def generate_dashboard(stats: dict, df_history: pd.DataFrame, output_dir: str) -> str:
    """Genera el dashboard HTML interactivo."""
    print("\n" + "=" * 60)
    print("ETAPA 6: GENERACIÓN DE DASHBOARD")
    print("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    chart_data = _build_chart_data(stats, df_history)
    template = Template(HTML_TEMPLATE)

    kpis = chart_data["kpis"]

    html = template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        kpis=kpis,
        chart_data_json=json.dumps(chart_data, ensure_ascii=False, default=str),
    )

    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Dashboard generado: {html_path}")
    return html_path


def _build_chart_data(stats: dict, df_history: pd.DataFrame) -> dict:
    """Prepara todos los datos para inyectar en Chart.js."""
    data = {}

    # Series temporales de indicadores clave
    series = stats.get("series", {})
    data["series"] = {}
    for name, s in series.items():
        data["series"][name] = {
            "fechas": s.get("fechas", []),
            "valores": s.get("valores", []),
            "min": s.get("min", 0),
            "max": s.get("max", 0),
            "mean": s.get("mean", 0),
        }

    # Variaciones
    data["variaciones"] = stats.get("variaciones", {})

    # Distribución por sección (pie chart)
    por_seccion = stats.get("por_seccion", {})
    data["pie_secciones"] = {
        "labels": list(por_seccion.keys()),
        "values": list(por_seccion.values()),
    }

    # Tabla de indicadores actuales
    data["tabla_actual"] = stats.get("tabla_actual", [])

    # KPIs
    variaciones = stats.get("variaciones", {})
    uf_data = variaciones.get("UF", {})
    dolar_data = variaciones.get("Dólar Observado", {})
    utm_data = variaciones.get("UTM", {})
    euro_data = variaciones.get("Euro", {})

    data["kpis"] = {
        "total_indicadores": stats.get("total_indicadores", 0),
        "total_fechas": stats.get("total_fechas", 0),
        "total_registros": stats.get("total_registros", 0),
        "fecha_actual": stats.get("fecha_actual", ""),
        "uf_valor": uf_data.get("valor_actual", 0),
        "uf_cambio": uf_data.get("cambio_pct", 0),
        "dolar_valor": dolar_data.get("valor_actual", 0),
        "dolar_cambio": dolar_data.get("cambio_pct", 0),
        "utm_valor": utm_data.get("valor_actual", 0),
        "utm_cambio": utm_data.get("cambio_pct", 0),
        "euro_valor": euro_data.get("valor_actual", 0),
        "euro_cambio": euro_data.get("cambio_pct", 0),
    }

    return data


# ──────────────────────────────────────────────
# HTML Template
# ──────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Indicadores Previsionales Chile</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg-primary: #0F172A; --bg-card: #1E293B; --bg-hover: #334155;
  --border: #334155; --text-primary: #E2E8F0; --text-secondary: #94A3B8;
  --blue: #60A5FA; --green: #34D399; --yellow: #FBBF24; --red: #F87171;
  --purple: #A78BFA; --cyan: #22D3EE;
  --blue-bg: rgba(96,165,250,0.15); --green-bg: rgba(52,211,153,0.15);
  --yellow-bg: rgba(251,191,36,0.15); --red-bg: rgba(248,113,113,0.15);
  --purple-bg: rgba(167,139,250,0.15); --cyan-bg: rgba(34,211,238,0.15);
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg-primary); color:var(--text-primary); }

/* NAV */
.nav { position:fixed; top:0; left:0; right:0; z-index:100; background:rgba(15,23,42,0.95);
  backdrop-filter:blur(12px); border-bottom:1px solid var(--border); padding:0 2rem; display:flex;
  align-items:center; height:56px; gap:2rem; }
.nav-brand { font-weight:700; font-size:1.1rem; color:#fff; white-space:nowrap; }
.nav-links { display:flex; gap:0.25rem; overflow-x:auto; }
.nav-links a { color:var(--text-secondary); text-decoration:none; padding:0.5rem 1rem; border-radius:8px;
  font-size:0.85rem; transition:all 0.2s; white-space:nowrap; }
.nav-links a:hover, .nav-links a.active { color:#fff; background:var(--bg-hover); }
.nav-status { margin-left:auto; display:flex; align-items:center; gap:0.5rem; font-size:0.8rem; color:var(--green); }
.nav-status .dot { width:8px; height:8px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.container { max-width:1440px; margin:0 auto; padding:72px 2rem 2rem; }
section { display:none; animation:fadeIn 0.4s ease; }
section.active { display:block; }
@keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }

/* HERO */
.hero { text-align:center; padding:2.5rem 0 1.5rem; }
.hero h1 { font-size:2rem; background:linear-gradient(135deg,var(--blue),var(--green)); -webkit-background-clip:text;
  -webkit-text-fill-color:transparent; }
.hero p { color:var(--text-secondary); margin-top:0.5rem; }

/* KPI CARDS */
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1rem; margin:1.5rem 0; }
.kpi { background:var(--bg-card); border:1px solid var(--border); border-radius:16px; padding:1.5rem;
  transition:transform 0.2s, box-shadow 0.2s; cursor:default; }
.kpi:hover { transform:translateY(-4px); box-shadow:0 8px 25px rgba(0,0,0,0.3); }
.kpi .label { font-size:0.75rem; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.08em; }
.kpi .value { font-size:2rem; font-weight:800; margin:0.4rem 0 0.2rem; }
.kpi .sub { font-size:0.8rem; color:var(--text-secondary); }
.kpi .change { font-size:0.85rem; font-weight:600; margin-top:0.3rem; }
.kpi .change.up { color:var(--green); }
.kpi .change.down { color:var(--red); }
.kpi .change.neutral { color:var(--text-secondary); }
.kpi .sparkline { margin-top:0.5rem; height:32px; }
.kpi .sparkline canvas { width:100%!important; height:32px!important; }
.kpi.blue { border-left:4px solid var(--blue); }
.kpi.blue .value { color:var(--blue); }
.kpi.green { border-left:4px solid var(--green); }
.kpi.green .value { color:var(--green); }
.kpi.yellow { border-left:4px solid var(--yellow); }
.kpi.yellow .value { color:var(--yellow); }
.kpi.red { border-left:4px solid var(--red); }
.kpi.red .value { color:var(--red); }
.kpi.purple { border-left:4px solid var(--purple); }
.kpi.purple .value { color:var(--purple); }
.kpi.cyan { border-left:4px solid var(--cyan); }
.kpi.cyan .value { color:var(--cyan); }

/* CHARTS */
.chart-row { display:grid; gap:1.5rem; margin:1.5rem 0; }
.chart-row.cols-2 { grid-template-columns:1fr 1fr; }
.chart-row.cols-1 { grid-template-columns:1fr; }
@media(max-width:900px){ .chart-row.cols-2{grid-template-columns:1fr;} }
.chart-card { background:var(--bg-card); border:1px solid var(--border); border-radius:16px; padding:1.5rem;
  transition:box-shadow 0.2s; }
.chart-card:hover { box-shadow:0 4px 20px rgba(0,0,0,0.2); }
.chart-card h3 { font-size:1rem; margin-bottom:1rem; color:var(--text-primary); }
.chart-card canvas { width:100%!important; }

/* TABLES */
.table-controls { display:flex; gap:1rem; margin-bottom:1rem; flex-wrap:wrap; align-items:center; }
.search-input { background:var(--bg-primary); border:1px solid var(--border); border-radius:8px; padding:0.6rem 1rem;
  color:var(--text-primary); font-size:0.85rem; width:280px; outline:none; transition:border 0.2s; }
.search-input:focus { border-color:var(--blue); }
.search-input::placeholder { color:var(--text-secondary); }
.filter-btn { background:var(--bg-primary); border:1px solid var(--border); border-radius:8px; padding:0.5rem 1rem;
  color:var(--text-secondary); font-size:0.8rem; cursor:pointer; transition:all 0.2s; }
.filter-btn:hover, .filter-btn.active { background:var(--blue); color:#fff; border-color:var(--blue); }
.badge { display:inline-block; padding:0.2rem 0.6rem; border-radius:6px; font-size:0.75rem; font-weight:600; }
.badge-green { background:var(--green-bg); color:var(--green); }
.badge-red { background:var(--red-bg); color:var(--red); }
.badge-yellow { background:var(--yellow-bg); color:var(--yellow); }
.badge-blue { background:var(--blue-bg); color:var(--blue); }
.badge-purple { background:var(--purple-bg); color:var(--purple); }

table { width:100%; border-collapse:collapse; font-size:0.85rem; }
thead th { background:var(--bg-primary); color:var(--text-secondary); padding:0.8rem 1rem; text-align:left;
  font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; position:sticky; top:0;
  cursor:pointer; user-select:none; border-bottom:2px solid var(--border); }
thead th:hover { color:var(--blue); }
thead th .sort-icon { margin-left:0.3rem; opacity:0.4; }
thead th.sorted .sort-icon { opacity:1; color:var(--blue); }
tbody tr { border-bottom:1px solid var(--border); transition:background 0.15s; }
tbody tr:hover { background:var(--bg-hover); }
tbody td { padding:0.7rem 1rem; }
.table-wrapper { max-height:600px; overflow-y:auto; border-radius:12px; border:1px solid var(--border); }
.table-wrapper::-webkit-scrollbar { width:6px; }
.table-wrapper::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
.table-info { font-size:0.8rem; color:var(--text-secondary); margin-top:0.5rem; }
.table-pagination { display:flex; gap:0.5rem; align-items:center; margin-top:0.8rem; justify-content:center; }
.page-btn { background:var(--bg-card); border:1px solid var(--border); color:var(--text-secondary);
  padding:0.4rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.8rem; transition:all 0.2s; }
.page-btn:hover, .page-btn.active { background:var(--blue); color:#fff; border-color:var(--blue); }

/* FOOTER */
.footer { text-align:center; padding:3rem 2rem; color:var(--text-secondary); font-size:0.8rem;
  border-top:1px solid var(--border); margin-top:3rem; }
.footer a { color:var(--blue); text-decoration:none; }

/* PROGRESS BAR */
.progress-bar { width:100%; height:8px; background:var(--bg-primary); border-radius:4px; overflow:hidden; margin-top:0.5rem; }
.progress-fill { height:100%; border-radius:4px; transition:width 1.5s ease; }
</style>
</head>
<body>

<nav class="nav">
  <div class="nav-brand">Indicadores Chile</div>
  <div class="nav-links">
    <a href="#" data-section="resumen" class="active">Resumen KPIs</a>
    <a href="#" data-section="economicos">Econ&oacute;micos</a>
    <a href="#" data-section="previsionales">Previsionales</a>
    <a href="#" data-section="historico">Hist&oacute;rico</a>
    <a href="#" data-section="datos">Datos</a>
  </div>
  <div class="nav-status"><span class="dot"></span> Scraper OK &mdash; {{ generated_at }}</div>
</nav>

<div class="container">

<!-- ===================== RESUMEN ===================== -->
<section id="resumen" class="active">
  <div class="hero">
    <h1>Indicadores Econ&oacute;micos y Previsionales de Chile</h1>
    <p>Monitoreo automatizado con datos extra&iacute;dos de Previred &mdash; Actualizado: {{ kpis.fecha_actual }}</p>
  </div>

  <div class="kpi-grid">
    <div class="kpi blue">
      <div class="label">UF (Unidad de Fomento)</div>
      <div class="value">$<span data-counter="{{ kpis.uf_valor }}" data-format="money">0</span></div>
      <div class="change {{ 'up' if kpis.uf_cambio > 0 else 'down' if kpis.uf_cambio < 0 else 'neutral' }}">
        {{ '&#9650;' if kpis.uf_cambio > 0 else '&#9660;' if kpis.uf_cambio < 0 else '&#9644;' }}
        {{ "%.4f"|format(kpis.uf_cambio) }}%
      </div>
      <div class="sparkline"><canvas id="sparkUF"></canvas></div>
    </div>
    <div class="kpi green">
      <div class="label">D&oacute;lar Observado</div>
      <div class="value">$<span data-counter="{{ kpis.dolar_valor }}" data-format="money">0</span></div>
      <div class="change {{ 'up' if kpis.dolar_cambio > 0 else 'down' if kpis.dolar_cambio < 0 else 'neutral' }}">
        {{ '&#9650;' if kpis.dolar_cambio > 0 else '&#9660;' if kpis.dolar_cambio < 0 else '&#9644;' }}
        {{ "%.4f"|format(kpis.dolar_cambio) }}%
      </div>
      <div class="sparkline"><canvas id="sparkDolar"></canvas></div>
    </div>
    <div class="kpi yellow">
      <div class="label">UTM</div>
      <div class="value">$<span data-counter="{{ kpis.utm_valor }}" data-format="money">0</span></div>
      <div class="change {{ 'up' if kpis.utm_cambio > 0 else 'down' if kpis.utm_cambio < 0 else 'neutral' }}">
        {{ '&#9650;' if kpis.utm_cambio > 0 else '&#9660;' if kpis.utm_cambio < 0 else '&#9644;' }}
        {{ "%.4f"|format(kpis.utm_cambio) }}%
      </div>
      <div class="sparkline"><canvas id="sparkUTM"></canvas></div>
    </div>
    <div class="kpi purple">
      <div class="label">Euro</div>
      <div class="value">$<span data-counter="{{ kpis.euro_valor }}" data-format="money">0</span></div>
      <div class="change {{ 'up' if kpis.euro_cambio > 0 else 'down' if kpis.euro_cambio < 0 else 'neutral' }}">
        {{ '&#9650;' if kpis.euro_cambio > 0 else '&#9660;' if kpis.euro_cambio < 0 else '&#9644;' }}
        {{ "%.4f"|format(kpis.euro_cambio) }}%
      </div>
      <div class="sparkline"><canvas id="sparkEuro"></canvas></div>
    </div>
    <div class="kpi cyan">
      <div class="label">Total Indicadores</div>
      <div class="value" data-counter="{{ kpis.total_indicadores }}">0</div>
      <div class="sub">Monitoreados</div>
    </div>
    <div class="kpi green">
      <div class="label">Extracciones</div>
      <div class="value" data-counter="{{ kpis.total_fechas }}">0</div>
      <div class="sub">{{ kpis.total_registros }} registros totales</div>
    </div>
  </div>

  <div class="chart-row cols-2">
    <div class="chart-card">
      <h3>Evoluci&oacute;n Indicadores Clave (normalizado %)</h3>
      <canvas id="chartOverview"></canvas>
    </div>
    <div class="chart-card">
      <h3>Variaci&oacute;n vs Extracci&oacute;n Anterior</h3>
      <canvas id="chartVariation"></canvas>
    </div>
  </div>

  <div class="chart-row cols-1">
    <div class="chart-card">
      <h3>Resumen R&aacute;pido &mdash; Todos los Indicadores</h3>
      <div class="table-wrapper" style="max-height:400px;">
        <table id="tableResumen">
          <thead>
            <tr>
              <th>Secci&oacute;n</th>
              <th>Indicador</th>
              <th>Valor Actual</th>
              <th>Tendencia</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>
</section>

<!-- ===================== ECONÓMICOS ===================== -->
<section id="economicos">
  <div class="hero">
    <h1>Indicadores Econ&oacute;micos</h1>
    <p>Evoluci&oacute;n temporal de UF, D&oacute;lar, Euro y UTM</p>
  </div>

  <div class="chart-row cols-2">
    <div class="chart-card">
      <h3>UF &mdash; Evoluci&oacute;n Temporal</h3>
      <canvas id="chartUF"></canvas>
    </div>
    <div class="chart-card">
      <h3>D&oacute;lar Observado &mdash; Evoluci&oacute;n Temporal</h3>
      <canvas id="chartDolar"></canvas>
    </div>
  </div>
  <div class="chart-row cols-2">
    <div class="chart-card">
      <h3>UTM &mdash; Evoluci&oacute;n Temporal</h3>
      <canvas id="chartUTM"></canvas>
    </div>
    <div class="chart-card">
      <h3>Euro &mdash; Evoluci&oacute;n Temporal</h3>
      <canvas id="chartEuro"></canvas>
    </div>
  </div>

  <div class="chart-row cols-1">
    <div class="chart-card">
      <h3>Comparativo &mdash; Todos los Indicadores Econ&oacute;micos (Normalizado %)</h3>
      <canvas id="chartComparative" height="80"></canvas>
    </div>
  </div>
</section>

<!-- ===================== PREVISIONALES ===================== -->
<section id="previsionales">
  <div class="hero">
    <h1>Indicadores Previsionales</h1>
    <p>Tasas AFP, AFC, topes imponibles y rentas m&iacute;nimas</p>
  </div>

  <div class="kpi-grid" id="prevKpis"></div>

  <div class="chart-row cols-2">
    <div class="chart-card">
      <h3>Tasas de Cotizaci&oacute;n AFP (%)</h3>
      <canvas id="chartAFP"></canvas>
    </div>
    <div class="chart-card">
      <h3>Topes y Rentas M&iacute;nimas (CLP)</h3>
      <canvas id="chartTopes"></canvas>
    </div>
  </div>
</section>

<!-- ===================== HISTÓRICO ===================== -->
<section id="historico">
  <div class="hero">
    <h1>An&aacute;lisis Hist&oacute;rico</h1>
    <p>Estad&iacute;sticas y tendencias de los indicadores monitoreados</p>
  </div>

  <div class="kpi-grid">
    <div class="kpi blue">
      <div class="label">Total Extracciones</div>
      <div class="value" data-counter="{{ kpis.total_fechas }}">0</div>
    </div>
    <div class="kpi green">
      <div class="label">Total Registros</div>
      <div class="value" data-counter="{{ kpis.total_registros }}">0</div>
    </div>
    <div class="kpi yellow">
      <div class="label">Indicadores &Uacute;nicos</div>
      <div class="value" data-counter="{{ kpis.total_indicadores }}">0</div>
    </div>
  </div>

  <div class="chart-row cols-1">
    <div class="chart-card">
      <h3>Resumen Estad&iacute;stico por Indicador Clave</h3>
      <div class="table-wrapper">
        <table id="tableStats">
          <thead>
            <tr>
              <th>Indicador</th>
              <th>M&iacute;nimo</th>
              <th>M&aacute;ximo</th>
              <th>Promedio</th>
              <th>Observaciones</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>
</section>

<!-- ===================== DATOS ===================== -->
<section id="datos">
  <div class="hero">
    <h1>Tabla de Datos</h1>
    <p>Todos los indicadores de la &uacute;ltima extracci&oacute;n</p>
  </div>

  <div class="table-controls">
    <input type="text" class="search-input" id="searchIndicators" placeholder="Buscar indicador...">
    <button class="filter-btn active" data-filter="all" data-table="indicators">Todos</button>
    <button class="filter-btn" data-filter="monto" data-table="indicators">Montos</button>
    <button class="filter-btn" data-filter="porcentaje" data-table="indicators">Porcentajes</button>
  </div>
  <div class="table-wrapper">
    <table id="tableIndicators">
      <thead>
        <tr>
          <th data-sort="seccion">Secci&oacute;n <span class="sort-icon">&#x25B2;&#x25BC;</span></th>
          <th data-sort="indicador">Indicador <span class="sort-icon">&#x25B2;&#x25BC;</span></th>
          <th data-sort="valor_raw">Valor <span class="sort-icon">&#x25B2;&#x25BC;</span></th>
          <th data-sort="tipo">Tipo <span class="sort-icon">&#x25B2;&#x25BC;</span></th>
          <th>Variaci&oacute;n</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
  <div class="table-info" id="indicatorsInfo"></div>
  <div class="table-pagination" id="indicatorsPagination"></div>
</section>

</div><!-- /container -->

<div class="footer">
  <p>Generado autom&aacute;ticamente por <strong>DemostrationScraper</strong> |
  <a href="https://github.com/mechjook" target="_blank">@mechjook</a> |
  Pipeline CI/CD con GitHub Actions &mdash; Fuente: <a href="https://www.previred.com/indicadores-previsionales/" target="_blank">Previred</a></p>
</div>

<script>
// DATA
const DATA = {{ chart_data_json }};

// NAV
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
    link.classList.add('active');
    const sec = document.getElementById(link.dataset.section);
    sec.classList.add('active');
    animateCounters(sec);
  });
});

// ANIMATED COUNTERS
function animateCounters(container) {
  container.querySelectorAll('[data-counter]').forEach(el => {
    const target = parseFloat(el.dataset.counter);
    const isMoney = el.dataset.format === 'money';
    const duration = 1200;
    const start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      const val = target * ease;
      if (isMoney) el.textContent = Math.round(val).toLocaleString('es-CL');
      else el.textContent = Math.round(val).toLocaleString('es-CL');
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}
animateCounters(document.getElementById('resumen'));

// FORMAT HELPERS
const fmtMoney = v => '$' + Math.round(v).toLocaleString('es-CL');
const fmtDec = v => '$' + v.toLocaleString('es-CL', {minimumFractionDigits:2, maximumFractionDigits:2});

// CHART DEFAULTS
const BLUE = '#60A5FA', GREEN = '#34D399', YELLOW = '#FBBF24', RED = '#F87171', PURPLE = '#A78BFA', CYAN = '#22D3EE';
const BLUE_A = 'rgba(96,165,250,0.7)', GREEN_A = 'rgba(52,211,153,0.7)', YELLOW_A = 'rgba(251,191,36,0.7)';
const RED_A = 'rgba(248,113,113,0.7)', PURPLE_A = 'rgba(167,139,250,0.7)', CYAN_A = 'rgba(34,211,238,0.7)';
const COLORS = [BLUE, GREEN, YELLOW, RED, PURPLE, CYAN, '#F472B6', '#FB923C'];
const COLORS_A = [BLUE_A, GREEN_A, YELLOW_A, RED_A, PURPLE_A, CYAN_A, 'rgba(244,114,182,0.7)', 'rgba(251,146,60,0.7)'];

Chart.defaults.color = '#94A3B8';
Chart.defaults.borderColor = 'rgba(51,65,85,0.5)';
Chart.defaults.font.family = "'Segoe UI',system-ui,sans-serif";

// SPARKLINES - Mini trends inside KPI cards
function createSparkline(canvasId, seriesName, color) {
  const s = DATA.series[seriesName];
  const el = document.getElementById(canvasId);
  if (!s || !s.valores || s.valores.length === 0 || !el) return;
  const vals = s.valores.slice(-12); // last 12 points
  new Chart(el, {
    type: 'line',
    data: {
      labels: vals.map((_,i) => i),
      datasets: [{
        data: vals,
        borderColor: color,
        backgroundColor: color.replace(')', ',0.08)').replace('rgb', 'rgba'),
        fill: true, tension: 0.4, pointRadius: 0, borderWidth: 1.5
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend:{display:false}, tooltip:{enabled:false} },
      scales: { x:{display:false}, y:{display:false} },
      animation: { duration:800 }
    }
  });
}
createSparkline('sparkUF', 'UF', BLUE);
createSparkline('sparkDolar', 'D\\u00f3lar Observado', GREEN);
createSparkline('sparkUTM', 'UTM', YELLOW);
createSparkline('sparkEuro', 'Euro', PURPLE);

// OVERVIEW - Combined normalized line chart (replaces old pie)
const overviewKeys = Object.keys(DATA.series);
if (overviewKeys.length > 0) {
  const overviewColors = {
    'UF': BLUE, 'D\\u00f3lar Observado': GREEN, 'UTM': YELLOW, 'Euro': PURPLE
  };
  const allDatesOv = [...new Set(overviewKeys.flatMap(k => DATA.series[k].fechas))].sort();
  const overviewDS = overviewKeys.map(k => {
    const s = DATA.series[k];
    const baseVal = s.valores[0] || 1;
    const normalized = allDatesOv.map(d => {
      const idx = s.fechas.indexOf(d);
      return idx >= 0 ? ((s.valores[idx] / baseVal - 1) * 100) : null;
    });
    return {
      label: k, data: normalized,
      borderColor: overviewColors[k] || COLORS[overviewKeys.indexOf(k)],
      backgroundColor: 'transparent',
      tension: 0.3, pointRadius: allDatesOv.length > 20 ? 0 : 3, borderWidth: 2, spanGaps: true
    };
  });
  new Chart(document.getElementById('chartOverview'), {
    type: 'line',
    data: { labels: allDatesOv, datasets: overviewDS },
    options: {
      responsive: true,
      plugins: {
        legend: { position:'top', labels:{usePointStyle:true, padding:12} },
        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)}%` } }
      },
      scales: {
        x: { ticks:{maxTicksLimit:10, maxRotation:45} },
        y: { ticks:{ callback: v => v.toFixed(1)+'%' }, title:{display:true, text:'Variaci\\u00f3n desde inicio'} }
      },
      animation: { duration:1500 }
    }
  });
}

// RESUMEN TABLE - Quick view of all indicators grouped by section
(function() {
  const tbody = document.querySelector('#tableResumen tbody');
  if (!tbody || !DATA.tabla_actual) return;
  const grouped = {};
  DATA.tabla_actual.forEach(r => {
    if (!grouped[r.seccion]) grouped[r.seccion] = [];
    grouped[r.seccion].push(r);
  });
  let html = '';
  const sectionColors = {};
  let ci = 0;
  Object.entries(grouped).forEach(([seccion, items]) => {
    if (!sectionColors[seccion]) sectionColors[seccion] = COLORS[ci++ % COLORS.length];
    items.forEach((r, i) => {
      const arrow = r.direccion === 'up' ? '<span style="color:var(--green)">&#9650;</span>' :
                    r.direccion === 'down' ? '<span style="color:var(--red)">&#9660;</span>' :
                    '<span style="color:var(--text-secondary)">&#9644;</span>';
      const pct = r.cambio_pct !== 0 ? ` <span style="font-size:0.75rem;color:var(--text-secondary)">${r.cambio_pct.toFixed(2)}%</span>` : '';
      html += `<tr>
        ${i === 0 ? `<td rowspan="${items.length}" style="vertical-align:top;border-left:3px solid ${sectionColors[seccion]};padding-left:0.8rem;"><strong>${seccion}</strong></td>` : ''}
        <td>${r.indicador}</td>
        <td><strong>${r.valor_raw}</strong></td>
        <td>${arrow}${pct}</td>
      </tr>`;
    });
  });
  tbody.innerHTML = html;
})();

// VARIATION BAR - Variaciones vs extracción anterior
const varNames = Object.keys(DATA.variaciones);
if (varNames.length > 0) {
  const varValues = varNames.map(k => DATA.variaciones[k].cambio_pct || 0);
  new Chart(document.getElementById('chartVariation'), {
    type: 'bar',
    data: {
      labels: varNames,
      datasets: [{
        label: 'Variación %',
        data: varValues,
        backgroundColor: varValues.map(v => v >= 0 ? GREEN_A : RED_A),
        borderColor: varValues.map(v => v >= 0 ? GREEN : RED),
        borderWidth: 1, borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      plugins: { legend:{display:false}, tooltip:{ callbacks:{ label: ctx => `${ctx.parsed.y.toFixed(4)}%` }}},
      scales: { y:{ ticks:{ callback: v => v.toFixed(2)+'%' } } },
      animation: { duration:1200 }
    }
  });
}

// LINE CHARTS - Series temporales
function createLineChart(canvasId, seriesName, color, colorA) {
  const s = DATA.series[seriesName];
  if (!s || !s.fechas || s.fechas.length === 0) return;
  new Chart(document.getElementById(canvasId), {
    type: 'line',
    data: {
      labels: s.fechas,
      datasets: [{
        label: seriesName,
        data: s.valores,
        borderColor: color,
        backgroundColor: colorA,
        fill: true,
        tension: 0.3,
        pointRadius: s.fechas.length > 30 ? 0 : 4,
        pointHoverRadius: 6,
        pointBackgroundColor: color,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display:false },
        tooltip: { callbacks: { label: ctx => `${seriesName}: ${fmtDec(ctx.parsed.y)}` } }
      },
      scales: {
        x: { ticks:{ maxTicksLimit: 12, maxRotation: 45 } },
        y: { ticks:{ callback: v => fmtMoney(v) } }
      },
      animation: { duration:1500 }
    }
  });
}
createLineChart('chartUF', 'UF', BLUE, 'rgba(96,165,250,0.1)');
createLineChart('chartDolar', 'D\\u00f3lar Observado', GREEN, 'rgba(52,211,153,0.1)');
createLineChart('chartUTM', 'UTM', YELLOW, 'rgba(251,191,36,0.1)');
createLineChart('chartEuro', 'Euro', PURPLE, 'rgba(167,139,250,0.1)');

// COMPARATIVE - Normalized
const seriesKeys = Object.keys(DATA.series);
if (seriesKeys.length > 0) {
  const allDates = [...new Set(seriesKeys.flatMap(k => DATA.series[k].fechas))].sort();
  const datasets = seriesKeys.map((k, i) => {
    const s = DATA.series[k];
    const baseVal = s.valores[0] || 1;
    const normalized = allDates.map(d => {
      const idx = s.fechas.indexOf(d);
      return idx >= 0 ? ((s.valores[idx] / baseVal - 1) * 100) : null;
    });
    return {
      label: k, data: normalized,
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: 'transparent',
      tension: 0.3, pointRadius: allDates.length > 30 ? 0 : 3, borderWidth: 2,
      spanGaps: true
    };
  });
  new Chart(document.getElementById('chartComparative'), {
    type: 'line',
    data: { labels: allDates, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { position:'top', labels:{usePointStyle:true} },
        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)}%` } }
      },
      scales: {
        x: { ticks:{maxTicksLimit:12, maxRotation:45} },
        y: { ticks:{ callback: v => v.toFixed(1)+'%' }, title:{display:true, text:'Variaci\\u00f3n %'} }
      },
      animation: { duration:1500 }
    }
  });
}

// PREVISIONAL KPIs
const prevData = DATA.tabla_actual.filter(r =>
  r.tipo === 'porcentaje' || r.seccion.toLowerCase().includes('tope') ||
  r.seccion.toLowerCase().includes('renta') || r.seccion.toLowerCase().includes('afp') ||
  r.seccion.toLowerCase().includes('afc') || r.seccion.toLowerCase().includes('cesant')
);
const prevKpisEl = document.getElementById('prevKpis');
const prevColors = ['blue','green','yellow','purple','cyan','red'];
prevData.slice(0, 12).forEach((r, i) => {
  const cls = prevColors[i % prevColors.length];
  const val = r.tipo === 'porcentaje' ? r.valor_raw : fmtMoney(r.valor || 0);
  prevKpisEl.innerHTML += `<div class="kpi ${cls}">
    <div class="label">${r.indicador}</div>
    <div class="value" style="font-size:1.4rem;">${val}</div>
    <div class="sub">${r.seccion}</div>
  </div>`;
});

// AFP BAR CHART
const afpData = DATA.tabla_actual.filter(r => r.seccion.toLowerCase().includes('afp') && r.tipo === 'porcentaje');
if (afpData.length > 0) {
  new Chart(document.getElementById('chartAFP'), {
    type: 'bar',
    data: {
      labels: afpData.map(r => r.indicador),
      datasets: [{
        label: 'Tasa %',
        data: afpData.map(r => r.valor),
        backgroundColor: COLORS_A.slice(0, afpData.length),
        borderColor: COLORS.slice(0, afpData.length),
        borderWidth: 1, borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      plugins: { legend:{display:false}, tooltip:{ callbacks:{ label: ctx => `${ctx.parsed.y}%` }}},
      scales: { y:{ beginAtZero:true, ticks:{ callback: v => v+'%' } } },
      animation: { duration:1200 }
    }
  });
}

// TOPES BAR CHART
const topesData = DATA.tabla_actual.filter(r =>
  (r.seccion.toLowerCase().includes('tope') || r.seccion.toLowerCase().includes('renta')) && r.tipo === 'monto'
);
if (topesData.length > 0) {
  new Chart(document.getElementById('chartTopes'), {
    type: 'bar',
    data: {
      labels: topesData.map(r => r.indicador.substring(0, 30)),
      datasets: [{
        label: 'Monto CLP',
        data: topesData.map(r => r.valor),
        backgroundColor: COLORS_A.slice(0, topesData.length),
        borderColor: COLORS.slice(0, topesData.length),
        borderWidth: 1, borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend:{display:false}, tooltip:{ callbacks:{ label: ctx => fmtMoney(ctx.parsed.x) }}},
      scales: { x:{ ticks:{ callback: v => '$'+(v/1e6).toFixed(1)+'M' } } },
      animation: { duration:1200 }
    }
  });
}

// STATS TABLE
const statsBody = document.querySelector('#tableStats tbody');
Object.entries(DATA.series).forEach(([name, s]) => {
  statsBody.innerHTML += `<tr>
    <td><strong>${name}</strong></td>
    <td>${fmtDec(s.min)}</td>
    <td>${fmtDec(s.max)}</td>
    <td>${fmtDec(s.mean)}</td>
    <td>${s.valores.length}</td>
  </tr>`;
});

// INDICATORS TABLE
const PAGE_SIZE = 25;
let tableState = {
  data: DATA.tabla_actual,
  filtered: DATA.tabla_actual,
  page: 0,
  sort: {col:'seccion', asc:true},
  filter: 'all'
};

function renderTable() {
  const s = tableState;
  const start = s.page * PAGE_SIZE;
  const pageData = s.filtered.slice(start, start + PAGE_SIZE);
  const tbody = document.querySelector('#tableIndicators tbody');
  tbody.innerHTML = pageData.map(r => {
    const dirClass = r.direccion === 'up' ? 'badge-green' : r.direccion === 'down' ? 'badge-red' : 'badge-blue';
    const dirText = r.direccion === 'up' ? '&#9650; '+r.cambio_pct.toFixed(2)+'%' :
                    r.direccion === 'down' ? '&#9660; '+r.cambio_pct.toFixed(2)+'%' : '&#9644; 0%';
    const tipoBadge = r.tipo === 'monto' ? 'badge-blue' : r.tipo === 'porcentaje' ? 'badge-purple' : 'badge-yellow';
    return `<tr>
      <td>${r.seccion}</td>
      <td><strong>${r.indicador}</strong></td>
      <td>${r.valor_raw}</td>
      <td><span class="badge ${tipoBadge}">${r.tipo}</span></td>
      <td><span class="badge ${dirClass}">${dirText}</span></td>
    </tr>`;
  }).join('');
  document.getElementById('indicatorsInfo').textContent =
    `Mostrando ${start+1}-${Math.min(start+PAGE_SIZE, s.filtered.length)} de ${s.filtered.length} indicadores`;
  renderPagination('indicatorsPagination', s.filtered.length, s.page, p => { tableState.page = p; renderTable(); });
}

function renderPagination(containerId, total, currentPage, onClick) {
  const pages = Math.ceil(total / PAGE_SIZE);
  const c = document.getElementById(containerId);
  if (pages <= 1) { c.innerHTML = ''; return; }
  let html = '';
  const maxShow = 7;
  let startP = Math.max(0, currentPage - 3);
  let endP = Math.min(pages, startP + maxShow);
  if (endP - startP < maxShow) startP = Math.max(0, endP - maxShow);
  if (startP > 0) html += '<button class="page-btn" data-p="0">1</button><span style="color:var(--text-secondary)">...</span>';
  for (let i = startP; i < endP; i++)
    html += `<button class="page-btn ${i===currentPage?'active':''}" data-p="${i}">${i+1}</button>`;
  if (endP < pages) html += `<span style="color:var(--text-secondary)">...</span><button class="page-btn" data-p="${pages-1}">${pages}</button>`;
  c.innerHTML = html;
  c.querySelectorAll('.page-btn').forEach(btn => btn.addEventListener('click', () => onClick(parseInt(btn.dataset.p))));
}

// Sort
document.querySelectorAll('#tableIndicators th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.sort;
    if (tableState.sort.col === col) tableState.sort.asc = !tableState.sort.asc;
    else { tableState.sort.col = col; tableState.sort.asc = true; }
    document.querySelectorAll('#tableIndicators th').forEach(t => t.classList.remove('sorted'));
    th.classList.add('sorted');
    tableState.filtered.sort((a,b) => {
      const va = a[col] || '', vb = b[col] || '';
      return tableState.sort.asc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
    });
    tableState.page = 0;
    renderTable();
  });
});

// Search
document.getElementById('searchIndicators').addEventListener('input', e => {
  const q = e.target.value.toUpperCase();
  applyFilters(q, tableState.filter);
});

// Filter buttons
document.querySelectorAll('[data-table="indicators"]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('[data-table="indicators"]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    tableState.filter = btn.dataset.filter;
    applyFilters(document.getElementById('searchIndicators').value.toUpperCase(), tableState.filter);
  });
});

function applyFilters(query, filter) {
  let f = tableState.data;
  if (query) f = f.filter(r => r.indicador.toUpperCase().includes(query) || r.seccion.toUpperCase().includes(query));
  if (filter !== 'all') f = f.filter(r => r.tipo === filter);
  tableState.filtered = f;
  tableState.page = 0;
  renderTable();
}

renderTable();
</script>
</body>
</html>"""
