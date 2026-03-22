# Web Scraper — Indicadores Previsionales de Chile

Web Scraper automatizado que extrae indicadores económicos y previsionales desde [Previred](https://www.previred.com/indicadores-previsionales/), los almacena como serie histórica y publica un dashboard interactivo con gráficos de evolución temporal.

[![Scraper Pipeline](https://github.com/mechjook/DemostrationScraper/actions/workflows/scraper_pipeline.yml/badge.svg)](https://github.com/mechjook/DemostrationScraper/actions/workflows/scraper_pipeline.yml)

## Dashboard

Disponible en: **[GitHub Pages](https://mechjook.github.io/DemostrationScraper/)**

## Arquitectura del Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│  Seed Data   │───▶│   Scraper     │───▶│   Parser      │───▶│ Storage │
│  (Histórico) │    │   (Previred)  │    │  (Normaliza)  │    │ (CSV)   │
└─────────────┘    └──────────────┘    └──────────────┘    └────┬────┘
                                                                │
┌─────────────┐    ┌──────────────┐                        ┌────▼────┐
│  Dashboard   │◀──│  Validador    │◀───────────────────────│Analytics│
│  HTML+Charts │    │  Integridad   │                        │ Stats   │
└─────────────┘    └──────────────┘                        └─────────┘
```

## Etapas

| # | Etapa | Descripción |
|---|-------|-------------|
| 0 | **Seed** | Genera datos históricos simulados (26 semanas) para series temporales |
| 1 | **Scraper** | Extrae indicadores de Previred con reintentos y fallback a datos de ejemplo |
| 2 | **Parser** | Parsea formatos chilenos: montos ($1.234.567), porcentajes (11,44%) |
| 3 | **Storage** | Almacena en CSV como serie temporal (append por fecha de extracción) |
| 4 | **Analytics** | Calcula variaciones, tendencias, máximos/mínimos históricos |
| 5 | **Validador** | Verifica integridad, duplicados, tipos y rangos de los datos |
| 6 | **Dashboard** | Genera página HTML interactiva con Chart.js desplegada en GitHub Pages |

## Indicadores Monitoreados

| Categoría | Indicadores |
|-----------|-------------|
| **Económicos** | UF, UTM, UTA, Dólar Observado, Euro |
| **Topes Imponibles** | AFP (UF 81,6), IPS (UF 60), Seguro Cesantía (UF 122,6) |
| **Rentas Mínimas** | Dependientes, Menores/Mayores, Casa Particular |
| **Tasas AFP** | Capital, Cuprum, Habitat, Modelo, PlanVital, ProVida, Uno |
| **AFC** | Plazo Indefinido (Empleador/Trabajador), Plazo Fijo |
| **Otros** | Cotización Salud, APV, Asignación Familiar |

## Ejecución Local

```bash
pip install -r requirements.txt
python main.py
```

## Tests

```bash
pytest tests/ -v
```

## CI/CD

El workflow de GitHub Actions ejecuta:
1. **Tests** — pytest con validación completa
2. **Scraper Pipeline** — scraping, parsing, storage, analytics, dashboard
3. **Commit** — guarda datos actualizados al repositorio
4. **Deploy** — publica el dashboard en GitHub Pages (solo en `main`)

El scraper se ejecuta automáticamente cada lunes vía `cron schedule` y bajo demanda con `workflow_dispatch`.

## Stack

- Python 3.12
- requests / BeautifulSoup / lxml
- pandas / numpy
- Jinja2
- Chart.js 4.4
- pytest
- GitHub Actions + GitHub Pages

## Autor

**José Nicolás Candia** — [@mechjook](https://github.com/mechjook)
